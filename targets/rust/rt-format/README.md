# rt-format

[rt-format](https://github.com/vstojkovic/rt-format) is the "fully-runtime equivalent of the
`format!` macro": `ParsedFormat::parse(fmt, &positional, &named)` parses a `std::fmt` format
string at run time against values implementing `FormatArgument`, and the result `Display`s as
`format!` would — "all the formatting features of the `format!` macro, except for the fill
character"; 649k downloads. Written in the zoo at 0.3.1 (upstream HEAD `1538a9f`, 2022-05-20);
tests in `tests/hegel.rs`.

## The oracle

Rust's `format!`. The crate's `format_value` is a generated tree of `write!` calls with literal
specs, so the text of one substitution is `std::fmt`'s by construction; what the crate adds is a
regex parser and the routing of arguments, and that is what the properties exercise, with the
expected text built as `std::fmt` composes it (the core `{:+#.prec$x}`, then space padding to
the width; sign-aware zero padding through its own family of literal specs):

- `substitutions_format_like_rust`: one `{:spec}` over every alignment, sign, `#`, width,
  precision and type an `Int`, `Float` or `Str` value supports.
- `zero_padding_formats_like_rust`: `{:+#010x}`, `{:08.3}` — and alignment ignored, as in
  `format!`.
- `format_strings_compose`: text, `{{`/`}}`, implicit, indexed and named arguments, `N$` and
  `name$` widths and precisions, `.*` — the unescaped text with the values in place, routed as
  `format!` routes them.
- `specifiers_round_trip`: `Specifier`'s `Display` parses back to the same `Specifier`.
- `malformed_format_strings_fail_at_the_brace`: a lone brace, an unknown name, an index out of
  range, an unsupported format, an unknown spec, a bad `$` size, `.*` without arguments — `Err`
  with the byte offset of the offending brace.
- `doc_examples`: the rustdoc example and the upstream smoke test.
- The general generators avoid the pinned shapes: `_`/non-ASCII in `$` names, widths above
  65535, `x?`/`X?`, the `-` flag; `Str` with `?` is never padded (`str`'s `Debug` ignores width
  and precision in `format!` too).

## Bugs (5)

- **rt-format/1** (contract, medium; `dollar_names_are_identifiers`): `{:my_width$}`,
  `{:_w$}`, `{:.größe$}` are errors — the `$` name regex is `[[:alpha:]][[:alnum:]]*` while
  argument names are full identifiers.
- **rt-format/2** (crash, medium; `huge_widths_do_not_panic`): `{:70000}`, `{:.70000}` and
  `{:1$}` with 70000 parse and then panic ("Formatting argument out of range") when displayed.
- **rt-format/3** (contract, low; `debug_hex_formats`): `{:x?}`/`{:X?}` rejected.
- **rt-format/4** (contract, low; `minus_flag_is_accepted`): `{:-}`/`{:-5}` rejected.
- **rt-format/5** (contract, low; `parse_specifier_rejects_trailing_text`): the public
  `parse_specifier("5xjunk")` succeeds, ignoring `junk`.

## Not bugs

- No fill character: documented.
- `Specifier { width: AtLeast { width: 0 }, .. }` displays as `0`, which parses back as the `0`
  flag with no width — the two format identically (`std::fmt`'s grammar has the same ambiguity).
- A value's own `Debug` deciding how width applies (the upstream `Variant`'s derived `Debug`
  pads inside the parentheses) is the value's business, not the crate's.
