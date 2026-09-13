# byte-unit

[magiclen/byte-unit](https://github.com/magiclen/byte-unit).

## What is tested

**`tests/byte.rs`**
- `byte_parse_str_never_panics`: `Byte::parse_str` must never panic, for arbitrary garbage and for near-miss numeric strings.
- `display_reparses_to_same_byte`: Plain `Display` output (a bare integer) must re-parse to the same `Byte`, over the full representable range.
- `alternate_display_reparses_to_same_byte`: Alternate (`{:#}`) `Display` output uses `get_recoverable_unit`, which is documented to be precise, so it must re-parse to the same `Byte` for every documented format style and precision.
- `recoverable_unit_recovers_byte_exactly`: `get_recoverable_unit` is documented to "find the appropriate unit and value that can be used to recover back to this `Byte` precisely".
- `exact_unit_recovers_byte_exactly`: `get_exact_unit` returns a unit that is a factor of the byte count and a value that multiplies back to exactly the original `Byte`.
- `from_u64_with_unit_matches_u128_arithmetic`: `from_u64_with_unit` must agree with independent u128 arithmetic: `size * unit` bytes for byte-based units, `ceil(size / 8)` for `Bit`, and `None` exactly when the result exceeds the representable maximum.
- `parse_str_matches_decimal_oracle`: Parsing a constructed `"<number><spaces><unit>"` string must agree with `rust_decimal`'s own string parser combined with `from_decimal_with_unit` (the hand-rolled digit loop in `Byte::parse_str` is independent code).
- `appropriate_unit_selects_largest_fitting_unit`: `get_appropriate_unit` must pick the largest unit of the requested unit type that does not exceed the byte count (and `B` otherwise).
- `appropriate_unit_get_byte_is_close`: Recovering a `Byte` from its appropriate-unit representation is documented to be inexact ("may not be logically equal ... due to the accuracy of floating-point numbers"), but the error must be bounded by f64 rounding: a couple of ULPs plus the round-up of `ceil`.
- `known_bug_adjusted_byte_get_byte_panics_near_max`: (no doc comment)
- `adjusted_byte_ordering_is_monotone`: `AdjustedByte`'s `Ord` (defined via `get_byte`) must order two values adjusted to the same unit consistently with their byte counts.

**`tests/unit.rs`**
- `unit_as_str_parse_roundtrip`: Every unit's canonical string (`as_str`) must parse back to the same unit with `ignore_case = false`, regardless of `prefer_byte` (the canonical strings are all explicit about bit vs byte).
- `unit_parse_str_never_panics`: `Unit::parse_str` must never panic on arbitrary input.

## Oracles

## Not tested

## History

- 2026-06-28: predecessor base commit `8acd4c0cd85e` (update docs cfg).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/byte-unit.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped 8acd4c0cd85e → 3f2dcb8c0f3f (2026-09-13, "bump version"; 5.2.6); 0 bug(s) still reproduce; fixed upstream: byte-unit/1. 83 tests pass. byte-unit/1: `AdjustedByte::get_byte` now saturates at `Byte::MAX` instead of unwrapping `None` (docs: "Values rounded above the supported range return the maximum value"); `known_bug_adjusted_byte_get_byte_panics_near_max` stays as a regression test and the sibling properties (`appropriate_unit_get_byte_is_close`, `adjusted_byte_ordering_is_monotone`) no longer exclude the near-maximum region.
