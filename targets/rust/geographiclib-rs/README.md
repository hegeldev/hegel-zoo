# geographiclib-rs

[georust/geographiclib-rs](https://github.com/georust/geographiclib-rs).

## What is tested

**`src/geodesic.rs`**
- `test_hegel_direct_inverse_roundtrip`: The crown roundtrip: direct(lat1, lon1, azi1, s12) -> (lat2, lon2), then inverse(lat1, lon1, lat2, lon2) must recover s12 and azi1. s12 is capped at MINIMAL_CAP_M so the direct segment is the unique shortest path, which is what inverse returns.
- `test_hegel_inverse_direct_lands_on_target`: Inverse-direct roundtrip: solving inverse(A, B) and then shooting from A with the returned azi1 for the returned s12 must land on B.
- `test_hegel_inverse_symmetry_under_point_exchange`: Exchanging the two points must give the same distance, and the azimuths of the reversed solution must be the originals rotated by 180 degrees (the same path walked backwards).
- `test_hegel_inverse_mirror_isometries`: The WGS84 ellipsoid is symmetric under reflection across the equator and across any meridian, so both reflections are isometries: they must preserve the geodesic distance.
- `test_hegel_coincident_points_zero_distance`: The distance from a point to itself is zero.
- `test_hegel_inverse_output_ranges`: Documented output contract of inverse(): s12 is a shortest-path distance, so 0 <= s12 <= the antipodal distance; azimuths are normalized to [-180, 180]; the arc length a12 is in [0, 180]. Input longitudes may be any finite value.
- `test_hegel_direct_output_ranges`: Documented output contract of direct(): lat2 in [-90, 90], lon2 in [-180, 180], azi2 in [-180, 180], for any finite s12 (including negative distances and distances wrapping the ellipsoid many times).
- `test_hegel_equatorial_distance_oracle`: Closed-form oracle: the geodesic between two points on the equator (with longitude difference below the equatorial cut at ~179.397 deg) runs along the equator, so its length is exactly a * |dlon in radians|.
- `test_hegel_near_antipodal_inverse_consistency`: The documented hard case for the inverse solve: nearly antipodal points. The solution must stay within global bounds and be self-consistent: shooting from point 1 with the returned azimuth and distance must land on point 2.
- `test_hegel_direct_additivity`: Direct is a flow along a geodesic line: walking s_a then continuing (with the forward azimuth) for s_b lands at the same point as walking s_a + s_b in one step.

**`src/polygon_area.rs`**
- `test_hegel_polygon_reversal_negates_signed_area`: Reversing the vertex order of a polygon negates its signed area (computed with sign=true) and preserves its perimeter.

## Oracles

## Not tested

## History

- 2026-02-17: predecessor base commit `c5e906d94a46` (return result rather than panic).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/geographiclib-rs.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
