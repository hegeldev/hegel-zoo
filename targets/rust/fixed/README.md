# fixed

[https://gitlab.com/tspiteri/fixed](https://gitlab.com/tspiteri/fixed).

## What is tested

**`src/arith.rs`**
- `hegel_add_agrees_with_wide_integer_oracle`: (no doc comment)
- `hegel_sub_agrees_with_wide_integer_oracle`: (no doc comment)
- `hegel_mul_agrees_with_floored_wide_oracle`: (no doc comment)
- `hegel_div_agrees_with_truncated_wide_oracle`: (no doc comment)
- `hegel_neg_overflows_exactly_at_boundary`: (no doc comment)
- `hegel_abs_overflows_exactly_at_min`: (no doc comment)

**`src/convert.rs`**
- `hegel_f64_roundtrip_exact_for_32bit_and_narrower`: (no doc comment)
- `hegel_f32_roundtrip_exact_for_16bit_and_narrower`: (no doc comment)
- `hegel_lossless_int_conversions_roundtrip`: (no doc comment)

**`src/display.rs`**
- `hegel_display_explicit_precision_matches_exact_rounding`: (no doc comment)
- `hegel_known_failure_display_explicit_precision_wrong_digits`: (no doc comment)

**`src/from_str.rs`**
- `hegel_display_from_str_roundtrips_exactly`: (no doc comment)
- `hegel_known_failure_display_to_string_not_roundtrippable`: (no doc comment)
- `hegel_radix_display_from_str_roundtrips_exactly`: (no doc comment)
- `hegel_from_str_never_panics`: (no doc comment)
- `hegel_parse_variants_agree`: (no doc comment)

**`src/sqrt.rs`**
- `hegel_sqrt_rounded_down_within_delta`: (no doc comment)
- `hegel_sqrt_all_frac_signed_overflows_at_quarter`: (no doc comment)

## Oracles

## Bugs

- **fixed/1** (medium): `Display` with an explicit precision prints wrong digits (`{:.16}` of the exact value `0.0999908447265625` gives `0.1000000000000000`), and the default `Display` output does not round-trip through `FromStr` for some values. Pins: `hegel_known_failure_display_explicit_precision_wrong_digits`, `hegel_known_failure_display_to_string_not_roundtrippable`.
- **fixed/2** (high, found 2026-09-17 at `95fe9d1db509`): `to_num::<f64>()` is wrong for types with 31 or 32 fractional bits. The new fast path (`fast_to_float` in `src/float_helper.rs`) computes the scale as `(1 << frac_bits) as f64` with an `i32` literal: `I1F31::from_bits(1).to_num::<f64>()` is `-2^-31` (wrong sign), and `U0F32::from_bits(1).to_num::<f64>()` panics with "attempt to shift left with overflow" in debug builds and returns `1.0` (2^32 too large) in release builds. `f32` is unaffected (its fast path stops at 24 bits). `hegel_f64_roundtrip_exact_for_32bit_and_narrower` leaves 31/32 fractional bits out while the bug is open; pin `hegel_known_failure_to_f64_wrong_for_31_and_32_frac_bits`.

## Not tested

## History

- 2026-03-20: predecessor base commit `7afb5bf760e7` (version 1.31.0).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/fixed.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-17: base bumped 7afb5bf760e7 → 78d4346c78cf (2026-09-17, "Merge branch 'fix-wrapping-cast-warning' into 'master'"; 1.31.0); 1 bug(s) still reproduce. 3851 tests pass.
- 2026-09-17: base bumped 78d4346c78cf → c3a503b48a82 (2026-09-17, "`f64::EPSILON` -> `<f64>::EPSILON` to avoid using core::f64::EPSILON"; 1.31.0); 1 bug(s) still reproduce. 3851 tests pass.
- 2026-09-17: base bumped c3a503b48a82 → 95fe9d1db509 (2026-09-17, "Merge branch 'fast-float-conversion' into 'master'"; 1.31.0); 2 bug(s) still reproduce. 3851 tests pass.
