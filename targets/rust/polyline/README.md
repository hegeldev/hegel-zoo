# polyline

[georust/polyline](https://github.com/georust/polyline).

## What is tested

**`src/lib.rs`**
- `prop_encode_decode_roundtrip_within_tolerance`: Crown roundtrip: encoding is lossy (grid rounding), but every decoded coordinate must be within half a grid step of the original — checked per coordinate, so delta-encoding drift on long lines would fail it.
- `prop_higher_precision_loses_less`: Precision monotonicity: for the same input, precision 6 must recover each coordinate at least as accurately as precision 5 (the 1e-5 grid is a subset of the 1e-6 grid; epsilon covers f64 tie-rounding noise).
- `prop_decode_encode_fixpoint`: Canonical roundtrip: decode(encode(line)) is on the grid, so re-encoding must reproduce the exact same string, and decoding that string must be a fixpoint (no further value drift).
- `prop_rounding_boundary_roundtrip`: Boundary hunting: coordinates sitting exactly on grid points and at the round-half tie boundaries (including clamped ±90/±180) must still encode successfully and decode within tolerance.
- `prop_out_of_range_coordinates_rejected`: Validation: a line with one out-of-range coordinate anywhere in it is rejected with the right error variant, index, and offending value.
- `prop_decode_never_panics_on_arbitrary_strings`: Parse robustness: decoding arbitrary (full Unicode) strings must return Ok/Err, never panic.
- `prop_decode_polyline_alphabet_no_panic_and_in_range`: Parse robustness on polyline-shaped input: strings drawn from the polyline alphabet (bytes 63..=126) exercise the varint-chunk decoder deeply. Must never panic, and (per the docs) any Ok result contains only in-range coordinates.
- `prop_decode_corrupted_polyline_never_panics`: Robustness against corruption of a *valid* polyline: truncating it at any byte, overwriting any byte with arbitrary ASCII, or inserting an ASCII byte must be handled gracefully (no panic; Ok results in range).
- `prop_empty_and_single_point_roundtrip`: Degenerate line shapes: the empty line encodes to the empty string (and back), and a single-point line roundtrips within tolerance.
- `prop_any_precision_no_panic`: The precision parameter is an unrestricted `u32` with no documented upper bound; encode/decode should return Ok/Err for any value, not panic. KNOWN FAILURE: any `precision >= 10` panics with "attempt to multiply with overflow" — both `encode_coordinates` and `decode_polyline` compute `10_i32.pow(precision)`, which overflows `i32` for precision >= 10 (debug builds panic; release builds would silently wrap). The `sampled_from` branch below pins the failure so it reproduces deterministically on every run (shrinks to precision = 10).

## Oracles

## Not tested

## History

- 2025-07-26: predecessor base commit `7fc654d463a0` (make PolylineError clonable (#54)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/polyline.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
