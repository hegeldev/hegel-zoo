# palette

[Ogeon/palette](https://github.com/Ogeon/palette).

## What is tested

**`src/encoding/srgb.rs`**
- `lin_to_enc_to_lin_prop`: Property version of `lin_to_enc_to_lin`: the sRGB transfer function decodes back to the original linear value over the whole [0, 1] domain, not just 101 fixed points.
- `enc_to_lin_to_enc_prop`: Property version of `enc_to_lin_to_enc`: encoding a decoded value returns the original encoded value over the whole [0, 1] domain.

**`src/hsl.rs`**
- `from_in_gamut_srgb_is_within_bounds`: Bounds: converting an in-gamut sRGB color to HSL with the clamping `FromColor` keeps saturation and lightness within their documented [0, 1] ranges (exact — this is `from_color`'s documented clamping promise). The unclamped conversion keeps lightness exactly in [0, 1] and saturation non-negative, but its saturation is only *approximately* bounded by 1. `FromColorUnclamped` makes no bounds promise, and indeed cannot: saturation is `d / (2 - sum)` for light colors, and `sum` rounds before the subtraction, so the error grows without bound as lightness approaches 1. Examples found while writing this test: rgb(0.5986116890844827, 1.0, 1.0) gives saturation 1.0000000000000002 and rgb(0.9999999999999999, 1.0, 1.0) gives saturation +infinity (2 - sum rounds to exactly 0). The clamping conversion absorbs both. Saturation is therefore only asserted `<= 1 + 1e-6` where lightness <= 1 - 1e-9, which bounds the cancellation error to ~1.1e-7.
- `grey_has_zero_saturation`: Achromatic edge case: greys have exactly zero saturation and a lightness equal to the component value. The hue of a grey is undefined (the implementation picks zero), so it is deliberately not asserted.

**`src/hues.rs`**
- `hue_normalization_equivalence`: `into_positive_degrees` and `into_degrees` return angles that are equivalent to the input modulo 360 degrees, within their documented ranges. The input magnitude is capped at 1e9 degrees: beyond that, one f64 ulp of the input approaches the size of a whole turn and "equivalent modulo 360" stops being numerically meaningful. The 1e-6 tolerance covers the ulp-scale error of subtracting the whole turns back out at magnitude 1e9.
- `into_positive_degrees_range_known_failure`: KNOWN FAILURE: `into_positive_degrees` documents the range `[0, 360)`, but tiny negative hues violate it in two ways in `normalize_unsigned_angle` (`self - floor(self / 360) * 360`): - for e.g. `-1e-30`, it computes `-1e-30 + 360.0`, which rounds   to exactly `360.0`, violating the exclusive upper bound; - for `-5e-324` (the smallest subnormal), `self / 360` underflows   to `-0.0`, so the input is returned unchanged: a *negative*   result. Every input drawn here reproduces the failure, so this test fails deterministically until the bug is fixed.

**`src/lab.rs`**
- `mix_endpoints`: Mix endpoints: `mix(a, b, 0.0) == a` and `mix(a, b, 1.0) == b`, as documented on the `Mix` trait. Factor 0.0 is exact in float arithmetic; factor 1.0 has one rounding step (`a + (b - a)`), hence the 1e-9 absolute tolerance on components up to +/-128.

**`src/rgb/rgb.rs`**
- `u8_f32_u8_format_roundtrip`: Round-trip: converting u8 components to f32 with `into_format` and back is lossless (tolerance: exact). Every 8-bit value is exactly representable in f32, lands in [0, 1], and must round back to the same integer.

## Oracles

## Not tested

## History

- 2026-05-15: predecessor base commit `9aa1ac21a7da` (Merge pull request #469 from Ogeon/phf_0.13).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/palette.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
