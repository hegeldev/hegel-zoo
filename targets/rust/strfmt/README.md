# strfmt

[strfmt](https://github.com/vitiral/strfmt) formats strings known only at run time with
`std::fmt`'s syntax: `strfmt("{name:>10.3}", &HashMap<String, T>)`, the `Format` trait
(`"…".format(&vars)`), `strfmt_map(fmt, |Formatter| …)` with `Formatter::{str, i64, f64, …}`
and `skip()`, the `strfmt!` macro; 5.9M downloads, unmaintained by its author's own account
("I accept pull requests"). The parser is a port of CPython's `formatter_unicode.c`; the number
text comes from `write!`. Written in the zoo at 0.2.5 (upstream HEAD `1948f91`, 2025-07-21);
tests in `tests/hegel.rs`.

## The oracle

Rust's `format!`. The README's goal is "all of the formatting options defined in `std::fmt`",
and every spec the generators draw — `[[fill]align][+][#][width][.precision][type]` over eight
fills, three alignments and the `b o x X e E` types — is rebuilt with literal format strings in
two stages: the core (`{:+#x}`, `{:.prec$e}`) and then the padding (`{:fill<width$}`), which is
what `std::fmt` itself does for every spec without the `0` flag. The properties:

- `strings_format_like_rust`, `integers_format_like_rust` (i8, i32, i64, u8, u64),
  `floats_format_like_rust` (f32, f64): one field against `format!`.
- `format_strings_compose`: literal text, `{{`/`}}` escapes and several fields; the output is
  the unescaped text with the `format!`-formatted values in place.
- `skipped_fields_are_verbatim`: a `strfmt_map` that `skip()`s every field returns the format
  string with only its escapes reduced.
- `malformed_format_strings_are_errors`: `{}`, `{:3}`, a single brace, an unterminated field,
  an unknown type, a missing key — `Invalid`/`TypeError`/`KeyError` as documented.
- `doc_examples`: the README and rustdoc examples.
- The general generators avoid the pinned shapes: `+` or `#` with a width, `0>`, `+` on a
  negative zero, `+` with a radix type of a negative integer, `#` without a type, the space
  sign; and the shapes strfmt documents or pins as errors (the `0` flag, `,`, `=`, a sign, `#`
  or `,` on a string).

## Bugs (7)

- **strfmt/1** (wrong-result, medium; `sign_and_prefix_are_inside_the_width`): `{x:>+7}` of
  42 is `+     42`, `{x:#8x}` `0x      2a` — the sign and prefix are written before the padded
  field, which is then one or two characters too wide.
- **strfmt/2** (contract, medium; `explicit_zero_fill_right_aligns_numbers`): `{x:0>5}` of a
  number is refused as "sign aware 0 padding" (it is a fill); strings accept it.
- **strfmt/3** (wrong-result, low; `plus_sign_of_negative_zero`): `{x:+}` of −0.0 is `+-0`.
- **strfmt/4** (wrong-result, low; `plus_sign_applies_to_radix_forms_of_negatives`): `{x:+x}`
  of −1i32 is `ffffffff`; `format!` gives `+ffffffff`.
- **strfmt/5** (contract, low; `sign_is_unspecified_is_not_inverted`): `Sign::is_unspecified`
  returns the opposite of its name.
- **strfmt/6** (contract, low; `std_fmt_integer_specs_are_accepted`): `{x:#}`, `{x:e}`,
  `{x:E}`, `{x:?}` on integers are errors; `format!` accepts them all.
- **strfmt/7** (contract, low; `space_sign_is_rejected`): `{x: }` is accepted and the space
  sign silently dropped, where every other unimplemented option is an error.

## Not bugs

- The `0` flag (`{x:05}`, "sign aware zero padding") and `,` return `Invalid("not yet
  supported")`: documented (README, and pinned as TODO in the upstream tests).
- A sign, `#` or `,` on a string is a `TypeError`, `s` is a string type, `f` is Rust's `{}`:
  pinned upstream (Python's rules).
- `{x:0=1}` on a string that needs no padding is accepted while `{x:0=5}` is refused — the `=`
  alignment is Python's, not std::fmt's; not compared.
- Exponent output is Rust's (`4.24e1`), not Python's: the number text is `write!`'s by design.
