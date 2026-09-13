# humansize

[LeopoldArkham/humansize](https://github.com/LeopoldArkham/humansize): human-readable sizes —
`format_size(1_000_000u64, DECIMAL)` → `1 MB` — with `DECIMAL`/`BINARY`/`WINDOWS` presets and
a `FormatSizeOptions` builder (bits or bytes, kilo 1000/1024 independent of the unit spelling,
decimal places for fractional and for whole quotients, `fixed_at` a unit, long units with
pluralisation, space, suffix, thousands separator), signed variants (`format_size_i`,
`ISizeFormatter`), the non-allocating `SizeFormatter`, `make_format` closures and the
`impl_style` traits; inputs are anything `ToF64` (all integer widths, `f32`, `f64`). 450 lines,
`no_std`, computes in `f64` with `libm`.

Written in the zoo (not imported from the predecessor). Built with `--features impl_style`
(`no_alloc` removes the allocating API and is not tested). The crate's own tests run alongside
`tests/hegel.rs`.

## What is tested

**`tests/hegel.rs`** — option sets are drawn over every field (places 0..=10, zeroes 0..=5, all
nine `fixed_at` levels, five suffixes, five ASCII separators); byte counts over the whole `u64`
range with a bias to the 1000ⁿ/1024ⁿ boundaries, to rounding ties and near-carries (`x.995`,
`x.9995` of a unit), to `1.x`/`0.99x` of a unit and to the 2⁵³ edge. The oracle is exact
`u128` arithmetic on the value the crate renders (its `f64`).
- `renderings_have_the_right_unit_and_a_correctly_rounded_mantissa`: the unit is the largest
  power of the kilo that fits (capped at the yotta entry) or the fixed one, spelled from the
  right one of the eight tables (kilo and unit spellings independent — `WINDOWS`), with the
  space and suffix; the mantissa has `decimal_zeroes` decimals when the exact quotient is whole
  and `decimal_places` otherwise (either when the quotient is within two f64 ulps of a whole
  number), no leading zero, the sign, and `|M·kiloᵏ − value·10ᵖ| ≤ kiloᵏ/2 + value·2⁻⁴⁷ + 1`
  (half a last digit plus the repeated-division error); the presets are what their names say.
- `every_entry_point_renders_alike`: `format_size`, `format_size_i`, `SizeFormatter`,
  `ISizeFormatter`, `make_format`, `make_format_i`, the `FormatSize`/`FormatSizeI` traits,
  options by value and by reference, and every integer type that holds the value (`u8`…`u128`,
  `i8`…`i128`, `f32`/`f64` for exact integers) render the same text; a negative value is the
  positive text with a sign (up to pluralisation).
- `wide_values_render_to_the_capped_scale`: `u128` inputs up to `u128::MAX` — the scale stops at
  the yotta entry and the mantissa is the f64 quotient.
- `float_inputs_render_without_panicking_and_group_alike`: finite `f64` inputs (fractions of a
  byte, ±1e300) — unit choice and mantissa against the f64 quotient.
- Pinned (each its own domain, see Bugs): `grouped_renderings_are_the_plain_rendering_with_separators`
  (humansize/1), `grouped_negative_renderings_keep_their_decimals` (humansize/2),
  `grouped_integer_parts_beyond_2_53_are_the_f64_digits` (humansize/3),
  `non_ascii_separators_are_inserted_as_characters` (humansize/4),
  `non_finite_inputs_render_their_float_spelling` (humansize/5),
  `pluralisation_follows_the_printed_value` (humansize/6),
  `long_binary_bit_table_is_capitalised` (humansize/7). The thousands-separator path's oracle is
  the plain rendering with separators inserted into its integer part.

## Oracles

Exact `u128` arithmetic (unit powers, quotient bounds, whole-number test), the crate's unit
tables, and — for the thousands-separator path — the crate's own plain rendering (Rust's `{:.p}`
formatting rounds correctly).

## Not tested

`no_alloc`; `decimal_places` above 10 (the separator path computes `10^places` in f64 and
`round(...) as u64`, which saturates from 20 places); `SizeFormatter` ignoring width/alignment
(open upstream #28, the crate's own commented-out test); the sign of `-0.0`; the exact rounding
direction of ties (the mantissa is checked to half a last digit, not re-implemented).

## Bugs

All seven found on the first 100-case run or by reading the 160-line formatter first; six are
in the `thousands_separator` branch, which re-implements number formatting on a byte buffer.
- **humansize/1** (medium): a fraction that rounds up loses its carry — 1999 bytes is `1.00 kB`
  where the plain path prints `2.00 kB`; 12 029 of the 1 999 001 counts in 1000..=2 000 000
  differ from the plain rendering.
- **humansize/2** (medium): negative values lose their decimals — `-1500` is `-1.00 kB`
  (`-1.50 kB`), the crate's own `-16196.26 KiB` case is `-16_196.00 KiB` with a separator.
- **humansize/3** (low): integer parts above 2⁵³ print drifting digits — `u64::MAX` fixed at
  bytes is `18,446,744,073,709,552,046 B` for the f64 `18446744073709551616`.
- **humansize/4** (low): a non-ASCII separator (`'\u{a0}'`, `'\u{202f}'`) panics with a
  `Utf8Error` inside `Display`; `'’'` prints the control character U+0019.
- **humansize/5** (low): NaN and ±infinity with a separator panic (`attempt to subtract with
  overflow`; hang/overrun in release) — the shape of open upstream #39, which reports the
  published 2.1.3 hanging on `f32::INFINITY` even without a separator.
- **humansize/6** (low): pluralisation follows the truncated quotient, not the printed number —
  `2.00 Kilobyte` for 1999 bytes, and negatives are never singular (`-1 Bytes`).
- **humansize/7** (low): the long binary bit scale spells `bits` where the decimal one spells
  `Bits`.

## History

- 2026-09-13: written in the zoo against `be4ac44adcb8` (2025-01-06, 2.1.3 + the unreleased
  thousands-separator commit) with hegeltest 0.44.1. The formatter was read first: the
  separator branch's `round(fpart × 10^places) as u64`, `sep as u8` and f64 digit loop were the
  suspects (humansize/1–5), the `bits`/`Bits` slip was seen in the tables (humansize/7); the
  first run confirmed them all and found humansize/6. The plain path is clean at 100 + 3 × 1 000
  + 10 000 cases. Test defects on the way: the tables spelled `Bits` where the crate says `bits`
  (fixed to the crate's spelling, pinned separately); a sign-symmetry check on the separator path
  duplicated humansize/2.
