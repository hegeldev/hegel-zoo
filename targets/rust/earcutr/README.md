# earcutr

[frewsxcv/earcutr/](https://github.com/frewsxcv/earcutr/).

## What is tested

**`tests/integration_test.rs`**
- `earcut_arbitrary_input_no_panic_and_output_well_formed`: (no doc comment)
- `convex_polygon_triangle_count_is_n_minus_2`: Property 2: a strictly convex polygon with n vertices triangulates into exactly n - 2 triangles.
- `convex_polygon_triangle_areas_sum_to_polygon_area`: Property 3: the triangles of a convex polygon partition it — their total area equals the polygon's shoelace area.
- `star_polygon_triangle_areas_sum_to_polygon_area`: Property 4: same area-partition oracle for concave simple polygons.
- `holed_polygon_triangle_count_is_v_plus_2h_minus_2`: Property 5: a polygon with V total vertices and one hole in general position triangulates into exactly V + 2*1 - 2 triangles (the hole bridge duplicates two vertices; a ring of k vertices yields k - 2 triangles). Restricted to a single hole: with several holes, a later hole's bridge can route through an earlier bridge's zero-width channel, and `filter_points` then removes an immediately-degenerate duplicate node — a correct triangulation (the exact-area property 6 and deviation property 7 still pass on such inputs, with up to 4 holes) with fewer than V + 2H - 2 triangles. Verified against a concrete 3-hole counterexample producing 19 instead of 20 triangles with all 16 vertices used and deviation exactly 0.
- `holed_polygon_triangle_areas_sum_exactly`: Property 6: the triangulation of a holed polygon covers exactly the outer area minus the hole areas. Integer coordinates make every shoelace term exact in f64, so this equality is exact.
- `deviation_is_zero_for_valid_triangulation`: Property 7: the crate's own `deviation` helper (documented: "used to verify correctness of triangulation") reports ~0 for the triangulation of a valid holed polygon — this also exercises deviation's own hole-subtraction logic.
- `earcut_invariant_under_ring_representation`: Property 8: earcut is invariant under ring re-representation — the same polygon given with reversed winding, or as a GeoJSON-style closed ring (first vertex repeated at the end), triangulates to the same triangle count and the same total area. Evidence: `add_contour` normalizes winding and drops a duplicated final vertex.
- `collinear_polygon_yields_no_triangles`: Property 9 (degenerate edge case, evidence: the `degenerate` fixture expects 0 triangles): a "polygon" whose vertices are all exactly collinear (constructed on an integer lattice, so collinearity is exact in f64) triangulates to nothing.

## Oracles

## Not tested

## History

- 2026-05-04: predecessor base commit `a201db6b6ec1` (Update README with deprecation and new repository link).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/earcutr.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
