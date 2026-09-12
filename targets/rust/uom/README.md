# uom

[iliekturtles/uom](https://github.com/iliekturtles/uom).

## What is tested

**`src/si/angle.rs`**
- `hegel_atan2_matches_underlying_float`: Property: `Quantity::atan2` agrees exactly with `f64::atan2` on the underlying values. Evidence: the `atan2` quickcheck test below; this is the hegel port with the full `f64` range (including NaN and infinities).
- `hegel_sin_cos_consistent_with_sin_and_cos`: Property: `Angle::sin_cos` is consistent with calling `Angle::sin` and `Angle::cos` separately. Evidence: the `sin_cos` documentation ("Computes the value of both the sine and cosine of the angle") and its delegation to `Float::sin_cos`.

**`src/tests/quantity.rs`**
- `hegel_new_get_same_unit_roundtrip`: Property: converting a value into a quantity and retrieving it in the same (non-base) unit round-trips. Evidence: the `get` unit test above and the `from_base`/`change_base` quickcheck tests in `tests/system.rs`. The `assume` mirrors the self-consistency guard used by the `change_base` quickcheck test: it rejects values where the conversion arithmetic itself overflows/loses precision in plain `f64`, which is a property of floating point rather than of `uom`.
- `hegel_get_base_unit_scales_by_coefficient`: Property: retrieving a quantity in the base unit scales the stored value by the unit's conversion coefficient. Evidence: the `new`/`get` unit tests above and the `to_base` quickcheck test in `tests/system.rs`.
- `hegel_from_str_never_panics`: Property: `FromStr` handles arbitrary input without panicking; it must return `Ok` or `Err`, never crash. Evidence: the `from_str` unit test above exercises the error variants, and the `FromStr` implementation in `src/quantity.rs` documents the error cases via `ParseQuantityError`.
- `hegel_display_parse_roundtrip`: Property: formatting a quantity with `into_format_args` and parsing the result back recovers the original quantity exactly (`f64`'s `Display` produces a shortest round-trippable representation). Evidence: the `round_trip` unit test above, which checks the single value `1.0`; this generalizes it to arbitrary values and both display styles.
- `hegel_from_str_accepts_all_unit_name_forms`: Property: `FromStr` accepts all three documented unit name forms (abbreviation, singular and plural) for every unit, producing the quantity in that unit. Evidence: the `FromStr` implementation in `src/quantity.rs` matches `$abbreviation | $singular | $plural`, and the `from_str` unit test above checks a few concrete instances.

**`src/tests/system.rs`**
- `hegel_add_homomorphism`: Property: quantity addition is a homomorphism over the underlying storage type — wrapping two values in the same unit and adding the quantities gives exactly the same result as adding the raw values first. Evidence: the `add` quickcheck test above.
- `hegel_affine_unit_roundtrip`: Property: conversion through a unit with an affine (non-zero constant) conversion round-trips: storing a temperature in degrees Fahrenheit and reading it back in degrees Fahrenheit recovers the value up to floating point tolerance. Evidence: the `from_base`/`to_base` quickcheck tests above exercise the kelvin <-> fahrenheit conversions in each direction; this composes them. The tolerance is *absolute*, proportional to `epsilon * (|v| + constant)`: the round-trip computes `((v + c) * k) / k - c`, so each rounding step contributes error relative to `|v + c|`, not to `|v|`. Near `v = 0` the result is off by ~`c * epsilon` (e.g. `-5.7e-14` for `v = 0`), which is inherent to the affine conversion, not a `uom` bug — a ulps-relative comparison is an unsound property here (the crate's own fahrenheit round-trip quickcheck cases are commented out).
- `hegel_length_behaves_like_f64_model`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-04-04: predecessor base commit `a465bcc2b3bf` (Merge pull request #543 from SombkeMaximilian/gyromagnetic_ratio).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/uom.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
