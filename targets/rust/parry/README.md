# parry

[dimforge/parry](https://github.com/dimforge/parry).

## What is tested

**`tests/geometry/aabb_scale.rs`**
- `prop_aabb_from_points_contains_points`: Property: an AABB built from a set of points contains every one of those points, and its bounds are finite for finite input — including points at the extremes of the finite float range (min/max are overflow-free, so the full range is in-domain here).
- `prop_compute_aabb_contains_transformed_triangle_vertices`: Property: the world-space AABB of a transformed shape contains all of the shape's transformed vertices (within a scale-relative tolerance).

**`tests/geometry/ball_cuboid_contact.rs`**
- `prop_ball_cuboid_distance_matches_analytic_oracle`: Property: the distance between a ball and a cuboid matches the analytic oracle `max(0, |max(|c| - half_extents, 0)| - radius)`, where `c` is the ball's center expressed in the cuboid's local frame.

**`tests/geometry/ray_cast.rs`**
- `prop_raycast_hit_point_lies_on_shape`: Property: if a solid ray cast reports a hit at time `t`, then `t` is finite and non-negative, and the hit point `ray.point_at(t)` lies on the shape (its distance to the shape is ~0 relative to the coordinate scale).
- `prop_solid_raycast_from_inside_starts_at_zero`: Property: a solid ray cast whose origin is inside the shape reports a hit at exactly `t = 0` (the documented semantics of `solid = true`). The pose translation and cuboid extents are kept at scales where the inside-point construction itself cannot drift outside the cuboid through float rounding — this bound protects the test's construction, not the library's contract.

**`tests/geometry/support_map.rs`**
- `prop_support_point_maximizes_dot_product`: Property: the support point of a transformed convex shape attains the maximum dot product with the query direction over all of the shape's (transformed) vertices — checked against a brute-force scan of the vertices.

**`tests/query/point_cuboid.rs`**
- `prop_cuboid_solid_projection_matches_clamp_oracle`: Property: projecting a point onto a solid cuboid matches the independent clamp oracle — the projection is the componentwise clamp of the point to the cuboid's half-extents, and `is_inside` agrees with a componentwise containment check (points too close to the boundary for float comparisons are exempted from the flag check only).
- `prop_cuboid_distance_to_point_matches_clamp_oracle`: Property: the distance from a point to a solid cuboid matches the independent clamp oracle `|max(|pt| - half_extents, 0)|`.

**`tests/query/point_triangle.rs`**
- `prop_triangle_projection_is_idempotent`: Property: point projection onto a triangle's boundary is idempotent — the projected point already lies on the boundary, so projecting it again moves it (almost) nowhere.

**`tests/query/shape_query_consistency.rs`**
- `prop_distance_is_symmetric`: Property: `distance(a, b) == distance(b, a)` (up to the GJK termination tolerance) for arbitrary pairs of simple convex shapes at arbitrary poses.
- `prop_intersection_implies_zero_distance`: Property: if `intersection_test` reports an intersection, then the distance between the two shapes is ~0 (within the GJK termination tolerance). Also, reported distances are always non-negative and finite.

## Oracles

## Not tested

## History

- 2026-07-04: predecessor base commit `8436f7c21875` (Release v0.29.0 (#427)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/parry.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped 8436f7c21875 → 3609fcc6bffe (2026-09-03, "compound pseudo normals (2d and 3d) (#442)"; 0.30.2); 0 bug(s) still reproduce; fixed upstream: parry/1. 641 tests pass. The 0.30.1 fix to closest_points_cuboid_cuboid makes cuboid-cuboid distances exact and symmetric; the property that found parry/1 no longer excludes cuboid pairs.
