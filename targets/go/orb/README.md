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
geometries travel as ISO WKB. `HEGEL_TEST_CASES=500` for the whole package takes about two
seconds (the zoo run about fifteen with the build and the shapely check).

The codec and bounds properties (part 1 of the rewrite, 2026-10-10) follow the repository's
standard for known bugs (DESIGN.md decision 3): `hegel_test.go` holds the harness - `known`,
fourteen switches in bug order, off by default; the judge `hzCaseJudge`; the collector; the
classifier `shapeBy` that runs a family's model per switch before the library is called - and
`hegel_idioms_test.go` the shared idioms; `hegel_geometries_test.go` draws the geometries as
records from package-level generators in two families, `shapedGeometries` (the default
population) and `plainGeometries` (the same with every recorded shape filtered out, drawn under
`HEGEL_NO_KNOWN=1`), the realised rate written beside every weight; `hegel_codec_test.go` and
`hegel_bounds_test.go` state every checked value in a model `expected(c, k)` - a pure WKT
writer `wktOf` and reader `readWKT` with the library's collection splitter, point parser and
`()` empty part transcribed under their switches, a pure GeoJSON renderer `geoJSONOf`, and
`libBound`/`libUnion`/`libExtend`/`libIsEmpty` from bound.go - and the shapes files hold one
narrow property per bug. The other nine properties still run through the old generators and
the `Known` struct until part 2.

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
  reading orb's output and orb reading shapely's, whitespace variants of WKT (an ordered list),
  proper prefixes rejected; the WKT text and the GeoJSON document are modelled byte for byte.
  The WKT property draws the shapes of orb/1 (a collection: 12 % of its cases), orb/2 (any
  text with coordinates through the double-space variant: 85 %) and orb/8 (an empty inner
  part: 0.8 %) and shrinks to orb/8's `Ring{}` in 39 rounds of 40; the GeoJSON property draws
  orb/9 (an empty collection: 4 %) and orb/10 (a document with a short position, 10 %) and
  shrinks to orb/9 in 25 rounds of 40; WKB has no known shape.
- `TestHegelBounds`: `Bound()` of every type against the coordinate box (shapely agreeing) and
  the Bound methods, the receiver the empty bound one time in twenty (its `Union` and `Extend`
  are where orb/3 is checked; its other methods are unspecified); `clip.Bound`. Draws orb/3
  (a multi-part whose first part is empty, 4 %) and orb/4 (a zero-area receiver, 17 %) and
  shrinks to orb/4's `{0 0}-{0 0}`, the engine's first case, in 35 rounds of 40.
- Narrow properties, one per bug of part 1, each failing every run by default and passing
  under `HEGEL_NO_KNOWN=1`: `TestHegelWKTCollectionsReadBackWithSpaces` (1),
  `TestHegelWKTAllowsRunsOfWhitespace` (2), `TestHegelBoundOfAnEmptyFirstPart` (3, the parts
  beyond the unit square: the leak needs them), `TestHegelZeroAreaBoundIsEmpty` (4),
  `TestHegelEmptyPartsAreWrittenEmpty` (8), `TestHegelEmptyCollectionIsAGeometryObject` (9),
  `TestHegelShortPositionsAreRejected` (10).
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

The shapes of the codec and bounds bugs are drawn by the wide properties at their natural rates
and found by them (mapped in target.toml to the basin of forty rounds at a hundred cases), the
narrow properties fail on them every run, and the pins keep the regression examples; under
`HEGEL_NO_KNOWN=1` the shapes are off (filtered from the geometries, the drawn alternatives
off, the whitespace and shapely-text checks of a collection dropped) and every property passes.
The classifier names every shaped case before the library is called, and the replicas agree
with the library on every one of them over 3000 cases; the rewrite found the note of orb/3
overstated (the leak needs the later parts beyond the unit square: `MultiLineString{{},
{{-10 -1} {1 -2}}}.Bound()` is the right box) and orb/10's wording inexact (orb.Point has no
`UnmarshalJSON`; encoding/json fills the array), both corrected. The old `empty.Union(a)`
check on every case is gone: it named orb/3 on nearly every case; the drawn empty receiver
carries it.

Modelled as recorded, not counted: `clip.Bound` returns the other bound when one is empty
(upstream's tests want it); `ToInterval` spaces at `total / (int(total/dist))`, up to twice the
interval ("about the given distance"); `Collection{}.Dimensions()` is -1; a `Polygon{Ring{}}`
in WKB is a ring of zero points, which shapely reads
as POLYGON EMPTY (skipped in the WKB property; the WKT side is bug 8); `Fraction` at the
southern limit returns the last tile row as documented.
