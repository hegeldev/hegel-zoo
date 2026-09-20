# simplefeatures

[peterstace/simplefeatures](https://github.com/peterstace/simplefeatures)
(`github.com/peterstace/simplefeatures/geom`), a pure Go implementation of the OGC Simple
Features (WKT, WKB, GeoJSON, TWKB, DE-9IM, overlays, buffer, measures), against shapely 2 over
GEOS on the same generated geometries.

## What is tested

Geometries are generated as WKT: points, lines, polygons (rectangles with rectangular holes,
convex hulls of random points, random rings that may self-intersect or repeat a vertex),
multi-geometries with `EMPTY` members and nested collections, with XY, XYZ, XYM and XYZM
coordinates on a small grid (integers, halves, two decimals, and a few extreme values for the
serialisations). Validity is itself a differential; the geometry properties run on what both
sides hold valid.

**`hegel/hegel_serial_test.go`**
- `TestHegelWKTValidityMatchesGEOS`: what parses and what is valid agree.
- `TestHegelSerialisationMatchesGEOS`: `AsText` (up to spacing and number formatting),
  `AsBinary` (byte for byte, NaN payloads aside) and `MarshalJSON` give what GEOS gives; each
  side reads the other's WKB and GeoJSON as the same geometry; the GeoJSON round trip closes.

**`hegel/hegel_unary_test.go`**
- `TestHegelUnaryMatchesGEOS`: `IsEmpty`, `Dimension`, `Area`, `Length` (non-areal), the
  coordinate count, `Envelope`, `Centroid`, `ConvexHull`, `Boundary`, `IsSimple`, `IsRing`,
  `PointOnSurface` (on the geometry, inside a polygon: by GEOS's predicates),
  `RotatedMinimumAreaBoundingRectangle` (same area, covers the geometry), `UnaryUnion`,
  `Reverse`.
- `TestHegelDensifySimplifyMatchesGEOS`: `Densify` against `segmentize`, `Simplify` against
  Douglas-Peucker simplification.
- `TestHegelSimplifyStaysClose`: every vertex of the input lies within the threshold of
  `Simplify`'s result.

**`hegel/hegel_binary_test.go`**
- `TestHegelPredicatesMatchGEOS`: `Intersects`, `ExactEquals`, `Distance`, `Relate` (the DE-9IM
  string) and the nine named predicates.
- `TestHegelOverlaysMatchGEOS`: `Intersection`, `Union`, `Difference`, `SymmetricDifference`
  give GEOS's result (exactly up to normalisation and 1e-9, or topologically equal, or the same
  point set).

**`hegel/hegel_orient_test.go`**: `ForceCW`/`ForceCCW` orient every ring as GEOS reads it and
give what shapely's `orient_polygons` gives.

**`hegel/hegel_more_test.go`**
- `TestHegelBufferMatchesGEOS`: `Buffer` with quadrant segments, end cap and join styles and the
  single-sided mode gives GEOS's buffer (within 1e-9 of the area).
- `TestHegelUnionManyMatchesGEOS`: `UnionMany` gives `union_all` and `UnaryUnion` of the
  collection.
- `TestHegelTWKBRoundTrip`: `UnmarshalTWKB(MarshalTWKB(g, precision))` is `g.SnapToGrid`; the
  size and bounding box headers say what they should.
- `TestHegelPreparedAgrees`: a `PreparedGeometry` answers as the plain predicates;
  `ContainsProperly` is the DE-9IM pattern `T**FF*FF*`.

**`hegel/hegel_pins_test.go`**: one deterministic reproducer per recorded bug.

## Oracle and normalisations

shapely 2.1.2 with its bundled GEOS 3.13.1 in the CI venv (`pip install shapely==2.1.2`), as one
persistent `python3` child (`hegel/oracle.go`: hex-encoded arguments in, one JSON object out per
request); geometries travel as ISO WKB. When the child dies (GEOS crashes) it is restarted and the
request reported. Constructions are compared in XY (simplefeatures drops Z/M from hulls,
centroids and polygon boundaries, GEOS keeps Z); tolerances are 1e-9 relative. Both erroring
counts as agreement. Not judged (GEOS's own quirks or spec grey zones): an empty multi or
collection's Z/M in WKT and WKB (GEOS has no coordinate to carry them and writes a Z collection's
empty member without Z, which simplefeatures cannot read); `[[]]` for an empty polygon's GeoJSON
coordinates (read as `[]`); a MultiPoint's empty point in the GeoJSON round trip; `Length` of
areal geometries (PostGIS's 0 against GEOS's perimeter); `PointOnSurface` and the minimum
rotated rectangle's exact position (many are equally good); overlays and unions of a
GeometryCollection or of inputs with a repeated vertex or collinear overlapping segments (GEOS
loses parts and segments, and merges the overlaps its own way); a
union GEOS gives as a Z collection with a 2D member; `segmentize` of collections with empty
parts and `relate` of an empty geometry with a collection holding an empty lineal part (GEOS
3.13.1 segfaults); GEOS's densifier dropping repeated points and unwrapping single-member multis,
its simplifier dropping collapsed polygons and keeping collapsed lines as two equal points;
single-sided buffers of closed or self-intersecting lines, of lines turning by more than a right
angle, or with non-default caps and joins (the two JTS ports fill a sharp turn's far side
differently); `ExactEquals` compared in XY (GEOS's `equals_exact` ignores Z, M and the
coordinate type); `Crosses` and `Overlaps` of a collection whose empty member has a higher
dimension than its non-empty parts (GEOS 3.13's RelateNG takes the non-empty parts' dimension,
simplefeatures the declared one, as GEOS did before, while both report the same DE-9IM and
`Dimension`); buffers of closed
self-intersecting lines (GEOS 3.13 loses a lobe: the union of the segments' buffers agrees with
simplefeatures); overlays with an empty operand compared to the other operand itself (GEOS
nodes a self-intersecting line and then misjudges the two equal); TWKB of a ring whose closing
coordinate has other Z/M (the format omits it) and of a snap that merges vertices. Not
generated: lower-case WKT keywords and a MultiPoint mixing parenthesised and bare points (GEOS
and simplefeatures differ in leniency).

## Known bugs (gated)

Eight bugs (`bugs.toml`): `Simplify` is not Ramer-Douglas-Peucker and drops vertices farther
than the threshold from its result; TWKB of an empty geometry carries size and bounding box bytes
its header does not declare; a GeometryCollection's TWKB bounding box is all zeros; an empty
Point in a MultiPoint reads back from TWKB as `POINT (0 0)`; a MultiPolygon or collection with
an empty member loses Z and M through TWKB; a prepared polygon's `Contains` and `Covers` fail
with a recovered panic on a puntal geometry holding an empty point or a nested MultiPoint; the
prepared predicates misjudge a collection whose members overlap (a point inside a polygon member
and at a line member's end touches rather than lies within; two overlapping areal members give a
recovered `side location conflict` panic); point-point overlays compare Z and M (the intersection
of `POINT (1 1)` and `POINT Z (1 1 5)` is empty, their union two equal points). `hegel/known.go`
gates them by generated shape or by the shape of the one disagreement; `HEGEL_NO_KNOWN=1` lifts
the gates.

## Not tested

The `geos` and `rawgeos` packages (cgo bindings), `proj`, `carto`, `rtree`, GeoJSON feature
collections, `Transform`/`TransformXY`, `SnapToGrid` against `set_precision`, `Envelope`'s own
methods, `ExactEquals` options, TWKB ID lists and per-dimension precisions, the SQL
`Scan`/`Value` interface, `Validate`'s error messages, `Summary`.

## History

- 2026-09-20: written against 896784c3b5d5bee03a3a71f76bfa27028ebd1af1 (2026-08-21, v0.59.0+17)
  with hegel.dev/go/hegel v0.6.33; 8 bugs.
