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

## Not tested

## History

- 2026-03-20: predecessor base commit `7afb5bf760e7` (version 1.31.0).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/fixed.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-17: base bumped 7afb5bf760e7 → 78d4346c78cf (2026-09-17, "Merge branch 'fix-wrapping-cast-warning' into 'master'"; 1.31.0); 1 bug(s) still reproduce. 3851 tests pass.
