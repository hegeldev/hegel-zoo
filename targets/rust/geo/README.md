# geo

[georust/geo](https://github.com/georust/geo).

## What is tested

**`src/algorithm/area.rs`**
- `pbt_signed_area_translation_invariant`: (no doc comment)
- `pbt_signed_area_negates_when_ring_reversed`: (no doc comment)

**`src/algorithm/bool_ops/tests.rs`**
- `pbt_union_with_self_preserves_area`: (no doc comment)
- `pbt_union_intersection_inclusion_exclusion`: (no doc comment)
- `pbt_difference_and_intersection_partition_union`: (no doc comment)

**`src/algorithm/centroid.rs`**
- `pbt_centroid_translation_equivariant`: (no doc comment)

**`src/algorithm/contains/mod.rs`**
- `pbt_contains_implies_intersects`: (no doc comment)

**`src/algorithm/convex_hull/test.rs`**
- `pbt_convex_hull_contains_all_input_points`: (no doc comment)
- `pbt_convex_hull_is_convex_and_ccw`: (no doc comment)
- `pbt_convex_hull_no_panic_on_any_finite_coords`: (no doc comment)

**`src/algorithm/simplify.rs`**
- `pbt_simplify_matches_simplify_idx`: (no doc comment)
- `pbt_simplify_never_increases_length`: (no doc comment)

**`src/algorithm/validation/tests.rs`**
- `pbt_star_polygons_are_valid`: (no doc comment)

## Oracles

## Not tested

Note: geo commits no `Cargo.lock`, so dependencies resolve fresh; a dozen of upstream's own tests
(geodesic distances at 1e-13, earcut triangle order, related doc-tests) fail under current dependency
versions. `tools/zoo` reports those as UPSTREAM and does not judge them.

## History

- 2026-07-22: predecessor base commit `6b2127d9ad99` (Use total_cmp in sweep line interval ordering (#1554)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/geo.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped 6b2127d9ad99 → 4b31f1409a56 (2026-09-01, "Fix unsound prefix pruning in the separable distance fast path (#1603)"; 0.33.1); 3 bug(s) still reproduce; add/add conflicts in geo/src/algorithm/convex_hull/test.rs resolved by keeping both sides. 1438 tests pass.
- 2026-09-20: base bumped 4b31f1409a56 → c12769fdf745 (2026-09-19, "Make the point-to-segment distance scale-invariant (#1613)"; 0.33.1); 2 bug(s) still reproduce; fixed upstream: geo/3. 1441 tests pass.
