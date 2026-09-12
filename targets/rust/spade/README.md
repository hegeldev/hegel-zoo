# spade

[Stoeoef/spade](https://github.com/Stoeoef/spade).

## What is tested

**`src/cdt.rs`**
- `hegel_cdt_try_add_constraint_chain`: `try_add_constraint` behaves as documented:  - it returns an empty list exactly if `from == to` or the constraint would cross an    existing constraint edge (which `can_add_constraint` reports),  - otherwise it returns a chain of constraint edges leading from `from` to `to`,  - `num_constraints` always equals the number of edges flagged as constraint edges,  - the CDT stays structurally valid (`cdt_sanity_check`).

**`src/delaunay_core/math.rs`**
- `hegel_insert_agrees_with_validate_vertex`: `Triangulation::insert` accepts a vertex exactly if `validate_vertex` does (documented on `bulk_load`/`insert`), returns the same error, never panics - and leaves the triangulation unchanged when it fails (documented on `insert`).
- `hegel_mitigate_underflow_never_too_small`: A position returned by `mitigate_underflow` never causes `InsertionError::TooSmall` (documented on `mitigate_underflow`), and the function only ever flushes too-small coordinates to zero - all other coordinates pass through unchanged.

**`src/delaunay_core/triangulation_ext.rs`**
- `hegel_delaunay_empty_circumcircle`: The defining global Delaunay property: no vertex lies strictly inside the circumcircle of any inner face. Checked with the exact predicates of the `robust` crate as an oracle. `robust::incircle(a, b, c, q)` is positive exactly if `q` lies strictly inside the circle through the counterclockwise-ordered points `a`, `b`, `c`. Spade stores all inner faces in counterclockwise order.
- `hegel_insertion_order_invariance`: The triangulation of a point set does not depend on how it is built: `bulk_load` and incremental insertion in an arbitrary drawn order must produce the same vertex set, the same convex hull and the same number of edges and faces. (Edge *sets* can legitimately differ for cocircular point sets, but the counts are uniquely determined by the number of vertices and the convex hull.)
- `hegel_euler_formula_after_insertions_and_removals`: Euler's formula `V - E + F = 2` (`F` including the outer face) holds after any sequence of insertions and removals, as long as not all vertices lie on a single line. For fully degenerate (collinear) triangulations the documented invariants are `F = 1` and `E = V - 1` (or 0 for empty triangulations).
- `hegel_locate_agrees_with_exact_predicates`: `locate` returns a position description that is consistent with exact geometric predicates: `OnVertex` queries match the vertex position exactly, `OnEdge` queries lie exactly on the edge's segment, `OnFace` queries lie strictly inside the face and `OutsideOfConvexHull` queries are contained in no face at all.
- `hegel_delaunay_matches_point_set_model`: (no doc comment)

**`src/flood_fill_iterator.rs`**
- `hegel_vertices_in_rectangle_match_brute_force`: `get_vertices_in_rectangle` returns exactly the vertices inside the rectangle, boundary included, and yields the empty iterator for unordered corners (all documented behavior). Oracle: brute force filtering of all vertices.
- `hegel_inverted_rectangle_yields_empty_iterator`: KNOWN FAILURE - this test pins a real bug and fails deterministically. `get_vertices_in_rectangle` documents: "Yields an empty iterator if `lower.x > upper.x || lower.y > upper.y`". This is violated when a vertex lies exactly on the inverted rectangle's edge frame. Root cause: `VerticesInShapeIterator` checks containment through the `DistanceMetric` *trait's* default `is_point_inside` (`distance_to_point(p) <= 0`), and `RectangleMetric::distance_to_point` returns the distance to the rectangle's four frame edges - which is 0 for a point on the frame, even when the rectangle is inverted and therefore empty. `RectangleMetric`'s *inherent* `is_point_inside` (component-wise comparison) correctly reports "outside", but it does not override the trait method and is not the one called here. Minimal counterexample found by hegel: a single vertex at (0, 0), queried with `lower = (0, 0)`, `upper = (0, -1)` - returns the vertex instead of nothing.
- `hegel_vertices_in_circle_match_brute_force`: `get_vertices_in_circle` returns exactly the vertices whose squared distance to the center is at most `radius_2`, boundary included (documented behavior). Oracle: brute force filtering of all vertices.
- `hegel_rectangle_query_includes_vertex_left_of_extreme_rectangle`: KNOWN FAILURE - this test pins a real bug and fails deterministically. `get_vertices_in_rectangle` returns a vertex lying strictly *outside* the rectangle when the rectangle's coordinates are on a vastly larger scale than the vertex. For a vertex at `(0, y)` and the rectangle `[1, 2^k] x {y}` (k >= 54), the vertex has `x = 0 < 1` and must not be returned. But the trait-default `DistanceMetric::is_point_inside` computes `distance_to_point(p) <= 0`, and computing the distance to the frame edge from `(2^k, y)` to `(1, y)` suffers catastrophic cancellation: `fl(1 - 2^k) = -2^k`, so the projection foot rounds to exactly `(0, y)` - the query point itself - and the computed distance is 0 instead of 1. Same underlying weakness as `hegel_inverted_rectangle_yields_empty_iterator` (distance-based instead of exact component-wise containment), but triggered by precision loss instead of corner inversion, so it is pinned separately. Original hegel counterexample: vertex `(0, -15)`, `lower = (1, -15)`, `upper = (2.9802323204351658e60, -15)`.

## Oracles

## Not tested

## History

- 2026-03-24: predecessor base commit `c8befc96bbbc` (chore: Release).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/spade.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
