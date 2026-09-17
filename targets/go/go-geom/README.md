# go-geom — Hegel properties for `github.com/twpayne/go-geom`

[twpayne/go-geom](https://github.com/twpayne/go-geom) is a Go geometry
library: Point, LineString, LinearRing, Polygon, MultiPoint,
MultiLineString, MultiPolygon and GeometryCollection in the XY, XYZ, XYM and
XYZM layouts over flat coordinate arrays, with WKT, WKB, EWKB (and hex) and
GeoJSON codecs and an `xy` package of planar algorithms. Pinned at
`158e26b` (after v1.6.1, 2026-08-19).

## Build

The patch adds `go.mod` changes and four test files: `hegel_test.go`
(plumbing, the `Known` gates), `hegel_gen_test.go` (random geometries,
structural equality bit for bit, model encoders for WKT, WKB, EWKB and
GeoJSON, exact-arithmetic helpers), `hegel_props_test.go` (nine
properties) and `hegel_pins_test.go` (six pins). No external tool is
needed. The whole run takes well under a second at the default case count;
`HEGEL_TEST_CASES=2000` about 3 s.

## Oracles

- **Model encoders** written from the specifications: WKT text byte for
  byte (`POINT Z (1 2 3)`, `EMPTY` members, `, ` separators, shortest
  round-trip decimals), WKB bytes in both byte orders with ISO type codes
  (1000/2000/3000 offsets) and EWKB bytes with the Z/M/SRID flags, GeoJSON
  as RFC 7946 objects compared as JSON values.
- **Round trips** through every codec, with text variants for the WKT
  parser (lower and mixed case, `POINTZ`, tabs and newlines, exponents,
  trailing zeros), streams of two EWKB geometries, hex forms, the
  `EmptyPointHandlingNaN` option, `EncodeGeometryWithBBox` against
  `Bounds`, `MaxDecimalDigits` as a rounding within half a unit, and the
  three codecs against each other.
- **Malformed input**: every proper prefix of a WKT or (E)WKB encoding is
  rejected, single-character and single-bit corruptions never panic, and
  whatever is accepted re-encodes and re-decodes to the same geometry.
- **Exact arithmetic** (`math/big.Rat`): signed areas by the shoelace
  formula, orientation, point location by exact ray crossing, centroids by
  the exact formulas, Andrew's monotone chain for the convex hull — on
  small-integer coordinates, so `Area`, `SignedArea`,
  `IsRingCounterClockwise`, `IsPointInRing`, `LocatePointInRing`,
  `PolygonsCentroid`, `LinesCentroid`, `PointsCentroidFlat`, `ConvexHull`,
  `DistanceFromPointToLine` and `SimplifyFlatCoords` are checked against
  ground truth (lengths and centroids to 1e-9).
- **Structural identities**: `Coords`/`SetCoords`, `Clone` independence,
  `Reverse` twice, `Bounds` of the whole as the union of the parts',
  `Bounds.IsEmpty` against `Empty`, and a collection's layout as the union
  of its members'.

## Properties

| Test | Checks |
|---|---|
| `TestHegelWKTRoundTripsAndMatchesModel` | `wkt.Marshal` equals the model text; `Unmarshal` of it and of its variants gives the same geometry |
| `TestHegelWKTRejectsMalformedText` | prefixes and one-character damage of WKT are rejected or parse to something self-consistent |
| `TestHegelWKBMatchesModelAndRoundTrips` | WKB/EWKB bytes equal the model in both byte orders; Unmarshal, Read, hex and the NaN empty-point option round-trip |
| `TestHegelWKBRejectsMalformedBytes` | prefixes of (E)WKB are errors; bit flips never panic and what decodes re-encodes consistently |
| `TestHegelGeoJSONMatchesModelAndRoundTrips` | GeoJSON equals the model object; Geometry and Feature round-trip; bbox = Bounds; digits option rounds |
| `TestHegelCodecsAgree` | WKT, EWKB and GeoJSON readings agree and re-encode identically |
| `TestHegelMeasuresAreExact` | `Area`, `Length`, `Bounds`, `xy.SignedArea`, `IsRingCounterClockwise` against exact arithmetic |
| `TestHegelAlgorithmsMatchModels` | convex hull, point in ring, centroids, point-segment distance, Douglas-Peucker against exact models |
| `TestHegelStructuralIdentities` | Coords/SetCoords, Clone, Reverse, Bounds union, collection layout |

## Bugs

| Id | Pin | Summary |
|---|---|---|
| go-geom/1 | `TestHegelPinNestedCollectionBounds` | `Bounds.Extend` panics on a GeometryCollection: `Bounds()` and the GeoJSON bbox option panic on a nested collection |
| go-geom/2 | `TestHegelPinGeoJSONEmptyFirstMultiPoint` | an empty MultiPoint member is written as a `null` position, unreadable when first |
| go-geom/3 | `TestHegelPinGeoJSONEmptyFirstLineString` | GeoJSON layout is guessed from the first part: empty first line/polygon/ring plus Z or M fails to decode |
| go-geom/4 | `TestHegelPinWKTMixedLayoutCollection` | a mixed-layout collection marshals to WKT that `wkt.Unmarshal` rejects |
| go-geom/5 | `TestHegelPinConvexHullFewDistinctPoints` | `ConvexHull` of 3+ points with fewer than 3 distinct returns the origin among its coordinates |
| go-geom/6 | `TestHegelPinConvexHullDropsExtremePoints` | `ConvexHull` of more than 50 points misses extreme points (unclosed octant ring in the reduction) |

## Not bugs

- An empty geometry without a layout (`NoLayout`, only a bare
  `NewGeometryCollection()` has one) reads back with a layout: XY from WKB,
  EWKB and GeoJSON, the enclosing collection's layout from WKT (a bare
  `EMPTY` member takes the collection's dimension). The properties expect
  that.
- `wkt.Marshal` writes NaN and infinite coordinates as `NaN`/`+Inf`, which
  no WKT parser reads; GeoJSON refuses them. The codec properties keep to
  finite coordinates.
- `wkb.Unmarshal`/`ewkb.Unmarshal` ignore trailing bytes after a complete
  geometry, as JTS and GEOS do; an SRID flag with SRID 0 and SRIDs on the
  members of a multi-geometry are dropped on reading. The corruption
  property checks decode/encode/decode consistency rather than the bytes.
- `MaxDecimalDigits` rounds half to even (`strconv`), so `2.5` at 0 digits
  is `2`; the property checks for half a unit, not a direction.
- A Polygon with an empty ring (constructible, and produced by
  `geojson.Unmarshal` of `[[...],[]]`) marshals to `POLYGON ((...), EMPTY)`,
  which the WKT parser rejects; an empty ring is not a valid polygon
  component and is not generated for WKT.
- `xy.ConvexHull` returns the extreme points only (collinear boundary points
  removed), a LineString for two distinct or collinear points; the model
  does the same. While go-geom/5 and /6 are open the hull is checked for 3
  to 50 input points with at least 3 distinct.
- `Bounds.IsEmpty` is true for a collection of mixed layouts whose extra
  dimension no member fills (a `FIXME` in `GeometryCollection.Bounds`);
  checked only for collections of one layout.
