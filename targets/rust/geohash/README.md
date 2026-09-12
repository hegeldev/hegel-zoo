# geohash

[georust/geohash.rs](https://github.com/georust/geohash.rs).

## What is tested

**`tests/base.rs`**
- `prop_encode_decode_containment`: (no doc comment)
- `prop_encode_lat90_containment`: (no doc comment)
- `prop_decode_encode_roundtrip`: (no doc comment)
- `prop_encode_prefix_monotone`: (no doc comment)
- `prop_decode_bbox_prefix_nesting`: (no doc comment)
- `prop_error_shrinks_with_length`: (no doc comment)
- `prop_neighbor_is_one_cell_away`: (no doc comment)
- `prop_neighbor_opposite_roundtrip`: (no doc comment)
- `prop_decode_rejects_invalid_characters`: (no doc comment)
- `prop_decode_never_panics`: (no doc comment)
- `prop_decode_nonempty_never_panics`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-06-14: predecessor base commit `50a4b2a35ee0` (Add encode_iter variant of encode to enable avoiding allocations (#62)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/geohash.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-12: base bumped 50a4b2a35ee0 → 7d4c402de15b (2026-08-19, "Return an error instead of panicking when decoding an empty geohash (#65)"; 0.13.2); 1 bug(s) still reproduce; fixed upstream: geohash/2. 22 tests pass. geohash/2 (decode("") shift overflow) is fixed upstream by PR #65; geohash/1 (north pole) still reproduces.
