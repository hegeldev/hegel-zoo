# format_num

[format_num](https://github.com/askanium/format_num) formats a number from a format-spec
mini-language "modeled after Python 3's" (`[[fill]align][sign][symbol][0][width][,][.precision][type]`
with the types `e`, `f`, `s`, `%`, `b`, `o`, `d`, `x`, `X`), a port of d3-format's `format`;
260k downloads. Written in the zoo at 0.1.0 (upstream HEAD `74e4a89`, 2020-04-20, the only
release); tests in `tests/hegel.rs`, which drive `/usr/bin/python3` as a child process.

## The oracles

- **Python's `format()`** for everything the two mini-languages share: the types `f`, `e`, `%`,
  `d`, `b`, `o`, `x`, `X` with fill, alignment, sign, `#`, `0`, width, grouping and precision
  (`python_formats_the_same`). Rust's and CPython's float formatting both round the exact
  binary value half-to-even, so the digits must agree exactly. The documented deviations are
  emulated on the Python side or avoided by the generator: a negative value that prints as zero
  loses its sign unless `+` was requested (d3's rule), `#X` prefixes `0x`, the `0` flag
  overrides an explicit alignment, a zero-padded grouped field is widened by its sign or `0x`
  prefix (pinned upstream), `,` and a precision are not combined with the integer types (Python
  rejects them), `#` is not combined with `%` (format_num/9), and a zero-padded grouped field
  keeps its padding at least as long as its digits (format_num/11).
- **d3-format's SI placement** for `s` (`si_prefix_matches_the_model`): Python's `.{p-1}e`
  supplies the significant digits and exponent, the model places the decimal point against the
  prefix table as `formatPrefixAuto` does, from one yocto up.
- **The documented padding** (`layout_matches_the_documented_padding`): for every type
  including `s`, the padded result is the unpadded result laid out by the `<`, `>`, `^`, `=`
  and `0` rules, with any fill (a wide fill with `^` is format_num/4; a `µ` prefix is
  format_num/5).
- The `format_num!` macro is the method; the crate's doc examples as a guard on the harness.

## Bugs (11)

- **format_num/1** (crash, medium; `non_finite_values_format_as_text`): `e`, `E` and `s` panic
  on ±inf and NaN; `b`/`o`/`x`/`X` print `i64::MAX` for infinity. `f`, `d`, `%` print `inf`/`NaN`.
- **format_num/2** (crash, low; `si_prefix_handles_sub_yocto_values`): `s` below one yocto
  panics when the precision is smaller than the leading zeros — `format("s", 1e-31)`,
  `format(".2s", 1e-27)` (a `usize` wrap before the `max`).
- **format_num/3** (crash, low; `capital_e_is_the_upper_case_exponent_form`): the coded `E`
  type always panics.
- **format_num/4** (crash, medium; `fill_can_be_any_character`): `^` with a multi-byte fill
  splits the padding at a byte index — `format("é^10d", 12345)`, `format("→^6d", 12345)`.
- **format_num/5** (wrong-result, low; `width_counts_characters`): the width is in bytes, so a
  field with the `µ` prefix is one column short.
- **format_num/6** (wrong-result, low; `integer_types_round_to_integer`): `b`/`o`/`x`/`X`
  truncate (`format("x", 3.7)` = `3`) where the doc says rounded and `d` rounds.
- **format_num/7** (wrong-result, medium; `integer_types_are_exact_in_the_u64_range`):
  `b`/`o`/`x`/`X` saturate at `i64::MAX` — `format("x", 1e19)` = `7fffffffffffffff`.
- **format_num/8** (wrong-result, low; `hex_of_a_value_that_prints_as_zero_has_no_sign`):
  `format("x", -0.4)` = `-0`.
- **format_num/9** (wrong-result, low; `alternate_form_applies_to_percent`): `#.0%` prints no
  decimal point.
- **format_num/10** (contract, low; `unimplemented_spec_combinations_are_rejected`): unknown
  type letters format as `f`, `$` is ignored, `,x` groups the leading decimal digits.
- **format_num/11** (wrong-result, high; `zero_padded_grouping_keeps_every_digit`): a
  zero-padded grouped field drops leading digits when the separators outnumber the padding —
  `format("010,d", 123456789)` = `23,456,789`. Found by the Python differential at 1000 cases;
  d3-format's `formatGroup` has the same cut.

## Not bugs

- The d3 rules the crate documents or pins: `-0.4` with `.0f` prints `0` (Python `-0`), `#X`
  gives `0xBEEF`, `<08d` zero-pads on the right of the sign like `=`, `013,.8d` of `-42000000`
  is 14 characters wide (the sign is added on top of the grouped width), and no type means
  fixed notation with six decimals.
- The `s` branch below one yocto prints one significant digit fewer than d3 where it does not
  panic (noted under format_num/2).
- A pattern the regex does not match panics (`format("abc", 1)`); `format` has no error
  channel, so that is the crate's rejection, and format_num/10 asks for the same on the
  accepted-but-unimplemented patterns.
