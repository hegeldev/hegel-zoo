# sprintf

[sprintf](https://github.com/tjol/sprintf-rs) is a "clone of C s(n)printf in Rust" for targets
without a libc: `sprintf!("%d + %d = %d", 3, 9, 12)`, `vsprintf(fmt, &[&dyn Printf])`, a
`parser` module, runtime type checking of the arguments (`PrintfError::{ParseError, WrongType,
TooManyArgs, NotEnoughArgs}`); 1.1M downloads. It "follows the standard C semantics" except the
`'`/`I` extensions, `%a`, and length modifiers (checked, ignored — the argument's type is used).
Written in the zoo at 0.4.3 (upstream HEAD `953a1f6`, 2025-10-07); tests in `tests/hegel.rs`.

## The oracle

glibc's `snprintf`, called through `libc` (already the crate's dev-dependency: its own test
suite compares a list of examples the same way) one conversion at a time, with the `ll` length
modifier written for 64-bit arguments so that C reads them; strings go as `CString`s, `char`s
as `int`s. The properties:

- `integers_match_libc`: `d i u x X o` with every flag and width for `i64`, `u64` and `i32`.
- `floats_match_libc`: `f F e E g G` of values with at most six significant digits and at
  most 14 digits requested — from the 15th the exact binary value shows through (sprintf/6).
- `non_finite_floats_match_libc`, `strings_and_chars_match_libc` (ASCII with precision;
  multi-byte strings pad by bytes, as glibc does and the upstream tests pin).
- `format_strings_compose`: several conversions with verbatim text and `%%` are the
  concatenation of the pieces; `parse_format_string` sees the pieces; one argument too few or
  too many is the documented error. `wrong_types_are_errors`.
- The general generators avoid the pinned shapes: a zero for `%e`/`%g`, a `%g` whose fraction
  strips away, exact decimal ties, `%.0e` with a leading 9, `#` on a zero or a float, `%u` of a
  signed argument with a sign flag, `+` together with the space flag on a float, `.*`, and
  negative `*` widths.

## Bugs (16)

- **sprintf/1** (crash, high; `g_of_zero_matches_libc`): `%g` of 0.0 panics — `log10(0)` as the
  exponent overflows the precision arithmetic.
- **sprintf/2** (wrong-result, high; `e_of_zero_matches_libc`): `%e` of 0.0 is
  `NaN.000000e-2147483648`.
- **sprintf/3** (wrong-result, medium; `g_strips_the_decimal_point_with_the_zeros`): `%g` of
  100.0 is `100.`, of 1e-5 `1.e-05`.
- **sprintf/4** (wrong-result, medium; `ties_round_like_libc`): exact ties round half away —
  `%.0f` of 0.5 is `1`, `%.2f` of 0.125 `0.13` (glibc `0`, `0.12`).
- **sprintf/5** (wrong-result, low; `zero_precision_e_carries_into_the_exponent`): `%.0e` of
  9.5 is `10e+00`.
- **sprintf/6** (wrong-result, medium; `float_digits_are_exact`): digits past the 15th are
  invented, precision 20 overflows (`%.20f` of 0.5 is `1.000…`), `%.0f` of 1e23 prints Rust's
  shortest representation.
- **sprintf/7** (wrong-result, low; `subnormals_format`): `%e` of 5e-324 is `inf.000000e-324`.
- **sprintf/8** (wrong-result, medium; `integer_precision_is_a_minimum_digit_count`): `%.3d` of
  5 is `5`, `%.5x` of 255 `ff`.
- **sprintf/9** (crash, low; `i64_min_formats`): `%d` of `i64::MIN` panics in debug builds.
- **sprintf/10** (wrong-result, low; `alternate_form_of_zero_has_no_prefix`): `%#x` of 0 is
  `0x0`, `%#o` `00`.
- **sprintf/11** (wrong-result, low; `alternate_form_applies_to_floats`): `#` ignored for
  floats (`%#.0f` of 3 is `3`, `%#g` of 2.5 `2.5`).
- **sprintf/12** (contract, low; `u_is_unsigned`): `%u` is `%d` — `-42` stays `-42`, `%+u`
  prints `+`.
- **sprintf/13** (wrong-result, low; `negative_star_width_means_left_adjustment`): `%*d` with
  -5 ignores the width instead of left-adjusting.
- **sprintf/14** (crash, low; `huge_widths_are_parse_errors`): a width above `i32::MAX` in the
  format string panics instead of `ParseError`.
- **sprintf/15** (wrong-result, low; `plus_overrides_space_for_floats`): `%+ f` of 1.0 is
  ` 1.000000` (integers get `+1`). Found by the differential.
- **sprintf/16** (wrong-result, medium; `precision_from_argument_is_consumed`): `.*` never
  works — the "unspecified" placeholder and "from argument" are the same enum value, so the
  default precision is used and the argument is taken as the value (`WrongType`/`TooManyArgs`,
  or garbage when the types line up).

## Not bugs

- Length modifiers ignored, `%a` missing, no `'`/`I`: documented exceptions.
- Multi-byte strings are padded and truncated by bytes (rounded down to a character boundary
  when truncating): glibc's byte semantics, pinned by the upstream tests.
- `sprintf!("literal")` with no arguments does not compile (the macro needs a comma);
  `vsprintf` takes an empty slice.
- `%c` of a non-ASCII `char` prints the UTF-8 (C has no such argument).
