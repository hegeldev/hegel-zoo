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

## Known bugs (drawn by default)

Fifteen bugs (`bugs.toml`): `Simplify` is not Ramer-Douglas-Peucker and drops vertices farther
than the threshold from its result; TWKB of an empty geometry carries size and bounding box bytes
its header does not declare; a GeometryCollection's TWKB bounding box is all zeros; an empty
Point in a MultiPoint reads back from TWKB as `POINT (0 0)`; a MultiPolygon or collection with
an empty member loses Z and M through TWKB; a prepared polygon's `Contains` and `Covers` fail
with a recovered panic on a puntal geometry holding an empty point or a nested MultiPoint; the
prepared predicates misjudge a collection whose members overlap (a point inside a polygon member
and at a line member's end touches rather than lies within; two overlapping areal members give a
recovered `side location conflict` panic); point-point overlays compare Z and M (the intersection
of `POINT (1 1)` and `POINT Z (1 1 5)` is empty, their union two equal points); line overlays
lose a vertex shared with an operand that carries Z (9); a point on the boundary of a
MultiPolygon nested in a collection is prepared-within rather than touching (10); an empty areal
member raises a collection's prepared dimension so `Within`/`CoveredBy`/`Contains` against a
point go false (11); prepared `Overlaps` is false for two lines sharing a segment that one of
them crosses at a non-representable point (12); `Buffer` of a closed line whose inside the
distance erodes keeps the hole-side offset curve that JTS 1.20 and GEOS 3.13 drop: under a
mitre join its spike at a sharp notch pokes past the outer curve, and a tiny triangle gets a
spurious hole (13); `Relate` of a closed line
against a collection holding a point at its closing vertex beside another member puts none of
the line outside it, so `CoveredBy`, `Within`, `Covers` and `Contains` are true (14);
`Intersects` of a point an ulp off a segment is true, the plain float64 cross product absorbing
the nudge, while `Relate` says disjoint and `Disjoint` is true at the same time (15). Bugs 10 to
12 and 14 are in JTS 1.20 too, inherited through the port.

The wide properties draw these shapes by default and fail naming them ("the shape of
simplefeatures/N" on the mismatch), and `target.toml` maps each to the bug it meets most often,
measured over thirty rounds at a hundred cases: `TestHegelTWKBRoundTrip` on 2 every run (an empty
geometry with a size header comes first in its choice at a fifth, so the property cannot miss it;
STYLE.md rule 3's exception), `TestHegelDensifySimplifyMatchesGEOS` on 1 every run (plain),
`TestHegelSimplifyStaysClose` on 1 in nearly every run (intermittent), `TestHegelPreparedAgrees`
on 7 most often (five rounds of thirty fail: 12 twice, 7 twice, 6 once; intermittent),
`TestHegelOverlaysMatchGEOS` on 8 (one round of thirty; intermittent).
`TestHegelUnionManyMatchesGEOS` draws the shapes of 8 and 9 too but has not met them in sixty
rounds at a hundred cases nor at three thousand, so it is not mapped; nor are
`TestHegelBufferMatchesGEOS` (13: it met the tiny-triangle hole twice in thirty rounds at a
hundred cases before the shape was named, none in the thirty after) and
`TestHegelPredicatesMatchGEOS` (14: the shape is a point at a ring's closing vertex, which the
oracle misjudges the same way for all but a line doubling back on itself; no hit in seventy
rounds; 15: a point an ulp off a segment, which only a wild coordinate reaches, once in some
six thousand cases). The densify-simplify property fails on 1 in forty of forty rounds at a hundred cases
but only a third of its rounds at twenty. Each bug also has a narrow
property over its shape region in `hegel/hegel_shapes_test.go` that fails deterministically beside
its pin. `HEGEL_NO_KNOWN=1` switches the shapes off (`hegel/known.go` names the shape of a drawn
case or of the one disagreement regardless, and under `HEGEL_NO_KNOWN=1` the case is counted and
skipped), and then every property passes.

Accepted differences with GEOS 3.13.1, not bugs: buffer offsets at turns shallower than three
degrees, where GEOS places the segments differently from JTS 1.20 (which simplefeatures matches
to the last digit); GEOS collapsing a ring whose start vertex lies within the tolerance of the
simplifying chord; overlays of near-degenerate inputs (coordinates within 1e-9 of coincidence);
a union whose lineal result differs only by noding; a buffer input with a vertex about a
hundredth of the distance from the chord between its neighbours, which JTS's input
simplification drops in one port and keeps in the other; two non-adjacent segments nearly parallel
at twice the buffer distance apart, whose offset curves touch at a tiny angle and GEOS loses the
lobe between them (a union of the segments' buffers agrees with simplefeatures); and WKT
coordinates differing by 1e-16.

## Not tested

The `geos` and `rawgeos` packages (cgo bindings), `proj`, `carto`, `rtree`, GeoJSON feature
collections, `Transform`/`TransformXY`, `SnapToGrid` against `set_precision`, `Envelope`'s own
methods, `ExactEquals` options, TWKB ID lists and per-dimension precisions, the SQL
`Scan`/`Value` interface, `Validate`'s error messages, `Summary`.

## History

- 2026-09-20: written against 896784c3b5d5bee03a3a71f76bfa27028ebd1af1 (2026-08-21, v0.59.0+17)
  with hegel.dev/go/hegel v0.6.33; 8 bugs.
- 2026-09-28: the weekly 1000-case run failed the overlay and prepared properties; bugs 9-12 recorded, the
  known shapes drawn by default with narrow properties, four oracle tolerances added; 12 bugs.
- 2026-10-08: generators rewritten in combinator style (geometries as records rendered to WKT
  by pure functions from a depth-indexed tower; per-property case records); the mismatch names
  the shape; a densify budget (200 000 vertices), `union_all` artifacts, buffers of tiny
  segments and near-reversals and a GEOS `relate` crash on nested empty areal parts tolerated;
  the TWKB shape first in its choice; mappings re-measured; two candidates counted.
- 2026-10-08: the two candidates reproduced standalone and recorded as bugs 13 and 14, with
  pins and narrow properties; 14 bugs.
- 2026-10-08: the `Intersects` ulp candidate, met by the predicate property once the shapes of
  13 and 14 were named, probed over every integer segment in a 21 by 21 grid and recorded as
  bug 15 (its narrow property filters the drawn nudges by the library's own float64 test);
  15 bugs.
