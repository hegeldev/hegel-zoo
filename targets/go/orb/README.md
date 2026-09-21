# go/orb

[paulmach/orb](https://github.com/paulmach/orb) — 2D geometry types for Go (Point, MultiPoint,
LineString, MultiLineString, Ring, Polygon, MultiPolygon, Collection, Bound) with WKT, WKB/EWKB
and GeoJSON codecs, planar and geodesic measures, clipping, three simplifiers, resampling, web
mercator tiles and tile cover, a quadtree and projections. Pinned at `a12a48e` (v0.13.0,
2026-03-30). MIT, no contribution policy on AI.

## Build

The tests live in a new package directory `hegel/` of the module (the run command is
`go test ... ./hegel`), with `hegel.dev/go/hegel` added to go.mod. The codecs, planar measures,
Douglas-Peucker and clipping are checked against **shapely 2.1.2 (GEOS 3.13.1)** through a
Python child process (`python3`, or `HEGEL_PYTHON`) that answers one JSON line per request;
geometries travel as ISO WKB. `HEGEL_TEST_CASES=500` for the whole package takes about a
second.

## Oracles

- shapely: `from_wkt`/`from_wkb`/`from_geojson` and their writers for the codecs; `area`,
  `length`, `centroid`, `bounds`, `covers`, `distance` (to the boundary for polygons, which is
  orb's `DistanceFrom` contract) for the planar package; `simplify(preserve_topology=False)` for
  Douglas-Peucker; `intersection` with a box (its area and length) for clipping.
- Models from the doc comments: the box of the coordinates and the Bound methods; the radial
  simplifier; Visvalingam's point counts; resampling positions along the path (arc length);
  the web-mercator formulas, quadkeys and tile arithmetic; brute force over the same points for
  the quadtree; the haversine formula and geometric contracts for the geo package (bearing and
  distance round trip, midpoints, bounds around points, the area of small polygons against the
  scaled planar area); the spherical Mercator formulas.

## Properties

- `TestHegelWKT`, `TestHegelWKB`, `TestHegelGeoJSON`: round trips through each codec (typed
  helpers, streams, hex, EWKB with SRID, features and feature collections, BBox), shapely
  reading orb's output and orb reading shapely's, whitespace variants of WKT, proper prefixes
  rejected.
- `TestHegelBounds`: `Bound()` of every type against the coordinate box (shapely agreeing) and
  the Bound methods; `clip.Bound`.
- `TestHegelPlanar`: area, length, centroid, distances, `DistanceFrom`, point in ring and
  polygon (boundary points included), orientation.
- `TestHegelClip`: clipped geometries within the box, on the original, measuring what shapely's
  intersection measures; `clip.Geometry`'s dispatch.
- `TestHegelSimplify`: Douglas-Peucker against shapely (ties at the threshold excluded),
  Radial against its model, Visvalingam's contracts, subsequence and end-point invariants, the
  type rules of `Simplify`.
- `TestHegelResample`: `Resample` and `ToInterval` counts, ends and spacing.
- `TestHegelMaptile`: `Fraction`, `At`, `Bound`, `Center`, quadkeys, parents, children,
  siblings, `Contains`, `SharedParent`, `Range`, `ChildrenInZoomRange`, `tilecover` of points
  and bounds.
- `TestHegelQuadtree`: `Find`, `KNearest` (filters, maximum distance), `InBound`, `Remove`
  against brute force.
- `TestHegelGeo`, `TestHegelProject`: the geo formulas and the Mercator/WGS84 projections.
- `TestHegelRoundCloneEqual`: `Round`, `Clone` independence, `Equal`, dimensions and types,
  `Reverse`.

## Bugs

Fourteen, in bugs.toml. Parsers and encoders: the WKT collection splitter fails on ", " between
members, nested collections and EMPTY members (1); two spaces between coordinates are rejected
(2); `Marshal` writes `()` for an empty part (8); an empty Collection marshals to JSON `null` and
a null member panics the reader (9); a GeoJSON position of fewer than two numbers is accepted
(10). Geometry: `Union`/`Extend` on an empty bound leak its placeholder coordinates, so the
`Bound()` of a collection or multi-geometry whose first part is empty is wrong (3); `IsEmpty`'s
comment promises zero-area emptiness (4); `maptile.At` at longitude 180 is an invalid tile (5);
a point on a hole's boundary is not "in" (6); the centroid of a zero-area ring is its first
point (11) and the centroid of a collection of points or lines is the origin (12). Panics:
`resample.ToInterval` on an empty line (7), `VisvalingamKeep(1)` on any line of three points
(13), `KNearest` with k = 0 (14).

Modelled as recorded, not counted: `clip.Bound` returns the other bound when one is empty
(upstream's tests want it); `ToInterval` spaces at `total / (int(total/dist))`, up to twice the
interval ("about the given distance"); `Collection{}.Dimensions()` is -1; a `Polygon{Ring{}}`
in WKB is a ring of zero points, which shapely reads
as POLYGON EMPTY (skipped in the WKB property; the WKT side is bug 8); `Fraction` at the
southern limit returns the last tile row as documented.
