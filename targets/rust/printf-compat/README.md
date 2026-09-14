# printf-compat

[printf-compat](https://github.com/lights0123/printf-compat) is "printf reimplemented in Rust":
`format(fmt, va_list, handler)` parses a C format string, pulls the arguments off a `VaList`
and hands each `Argument` to a handler — `output::fmt_write` (into a `fmt::Write`),
`output::io_write` (into an `io::Write`, non-UTF-8 allowed) or your own. For C libraries with a
`printf`-style log callback, and for `no_std` targets that have to provide `printf` themselves;
150k downloads. Written in the zoo at 0.4.0 (upstream HEAD `4504f8f`, 2026-08-22); tests in
`tests/hegel.rs`.

The crate uses C variadics (`args: ...`), stable from Rust 1.99; the target runs on
`nightly-2026-09-01` (`[run] setup` installs it, a no-op where it is present) until stable
catches up.

## The oracle

glibc's `snprintf`, given the very same variadic arguments as the crate: a variadic Rust
function passes its `VaList` to `printf_compat::format` twice (through `fmt_write` and through
`io_write`, into writers that refuse output beyond 128 KiB so that a runaway padding loop is an
error rather than an out-of-memory), and the format string and arguments go to `snprintf` in
the same call. Both writers must produce glibc's bytes and report their length. The properties:

- `integers_match_libc`: `d i u x X o` with `hh h l ll z t`, every flag and width (precision
  on integers is a documented deviation, issue #50; `#` only with `x` of a non-zero value).
- `floats_match_libc`: `f`/`F` of finite doubles with every flag, width and precision — both
  sides round the exact binary value, so `%.20f` and `%.0f` of 1e23 agree.
- `strings_chars_and_pointers_match_libc`: `%s` of ASCII and of null (`(null)`), `%c` of
  ASCII, `%p` of non-null pointers, with width, precision and `-`.
- `format_strings_compose`: several `int` conversions, `*` widths, `%%` and verbatim text.
- `doc_examples`: the upstream test cases.
- The general generators avoid the pinned shapes: `e`/`E`, `-` with the space flag and no
  width, negative `*` values, widths above 65535, non-finite values, `#` on floats or on a zero,
  non-ASCII strings, null `%p`, `%c` above 127.

## Bugs (12)

- **printf-compat/1** (wrong-result, high; `e_exponent_has_a_sign_and_two_digits`): `%e` of
  1234.0 is `1.234000e3`, of 1.5e-7 `1.500000e-7` — Rust's exponent, not C's `e+03`/`e-07`.
- **printf-compat/2** (crash, high; `left_adjust_with_space_and_no_width_formats`): `%- d`
  and `%- f` panic ("Formatting argument out of range": a width of 0 wrapped to `usize::MAX`).
- **printf-compat/3** (crash, medium; `negative_star_width_means_left_adjustment`): `%*d`
  with -5 panics; C left-adjusts in a field of 5.
- **printf-compat/4** (crash, low; `widths_above_u16_format`): `%70000d`, `%.70000f` panic
  (Rust's formatter takes widths up to 65535).
- **printf-compat/5** (crash, low; `width_digits_overflow_is_an_error`): `%99999999999d`
  panics on integer overflow (debug) or wraps (release); glibc returns -1.
- **printf-compat/6** (wrong-result, medium; `non_finite_floats_match_libc`): `NaN` for
  `nan`, `inf` for `%F`'s `INF`, `NaN` for `+nan`/`-nan`, `00000inf` for `%08f`.
- **printf-compat/7** (wrong-result, low; `alternate_form_applies_to_floats`): `%#.0f` of 3
  is `3`, not `3.` (the `Flags` docs promise the point).
- **printf-compat/8** (wrong-result, low; `alternate_form_of_zero_has_no_prefix`): `%#x` of
  0 is `0x0`, `%#o` of 0 `0o0`; C prints `0`.
- **printf-compat/9** (wrong-result, medium; `string_width_counts_bytes`): `%5s` of `é` pads
  to five characters in `fmt_write`, five bytes in `io_write` and C; the writers disagree.
- **printf-compat/10** (wrong-result, low; `null_pointer_prints_nil`): `%p` of null is
  `0x0`, not `(nil)`.
- **printf-compat/11** (crash, medium; `negative_star_precision_means_omitted`): `%.*f` with
  -1 panics; C ignores a negative precision.
- **printf-compat/12** (wrong-result, low; `char_conversion_writes_one_byte`): `%c` of 0xE9
  through `io_write` writes `C3 A9` and counts 2; C writes `E9`.

## Not bugs

- Precision on integers ignored (issue #50), `%g`/`%G` and `%a`/`%A` printed as `%f`, `0x`
  before uppercase hex and `0o` before octal, `%n` refused, UTF-8 only in `fmt_write`: the
  documented differences.
- `%s` of a null pointer with a precision below 6: glibc prints nothing, musl (and the crate)
  truncate `(null)` — implementation-defined, not compared.
- `%5%` prints `%` in both; a lone trailing `%` or an unknown conversion returns -1 (undefined
  in C; glibc fails or echoes).
- `%c` of a byte above 127 through `fmt_write` cannot write the byte at all (UTF-8 only); only
  the `io_write` half is counted (printf-compat/12).
