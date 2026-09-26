# jts

The [JTS Topology Suite](https://github.com/locationtech/jts) (`org.locationtech.jts:jts-core`, 1.21.0-SNAPSHOT at
the pinned commit, 2026-09-14) is the reference implementation of planar geometry for the Java world (and, through
GEOS, for much of the rest): geometry model, robust predicates, DE-9IM relate, overlay, buffer, triangulation,
spatial indexes, WKT/WKB readers and writers; `jts-io-common` adds GeoJSON.

The tests are a Maven module `hegel/` added by the patch; `[run] setup` installs `jts-core` and `jts-io-common` from
the pinned tree into the local Maven repository (tests, javadoc, sources, signing and the enforcer skipped).

## The oracles

- **Exact rational arithmetic** (`Exact`): every double is converted exactly (`new BigDecimal(double)`) to a
  `BigInteger` rational, so orientation, segment intersection (classification and point), point-in-ring by crossing
  count, signed area, centroid, squared distances, convex hull (monotone chain), the in-circle test and ring/line
  simplicity are computed without rounding. Lengths and distances become doubles only at the final square root.
- **JTS against itself**: `RelateOp` (the default) against `RelateNG` and `RelateNG.prepare`, plain predicates against
  `PreparedGeometry`, `OverlayOp` (the default) against `OverlayNGRobust`, unary against iterated union, list against
  visitor queries, `Geometry.isSimple`/`isValid` against `IsSimpleOp`/`IsValidOp`.
- **Laws and invariants**: DE-9IM transposition and the predicate definitions, area identities of the four overlay
  operations, brute force for the spatial indexes, Euler's formula and the empty-circumcircle property for Delaunay,
  reader ∘ writer = identity.

`GeoGen` draws coordinates on an integer grid (range 3 to 1000), on eighths, or with three decimals — all exact in
`Exact` — and builds simple rings (random points sorted by angle, kept only when exactly simple, else their convex
hull), valid polygons with up to two holes (hole vertices strictly inside, rings exactly disjoint), multipolygons of
exactly disjoint parts, lines that may self-intersect or repeat points, empties and collections. `nearRing` builds a
ring from another's vertices, edge midpoints and slightly shifted vertices, so holes and neighbours touch, cross and
nest in every way.

## Properties (`JtsTest`)

- **robustAlgorithmsAreExact** — `Orientation.index`/`isCCW`/`isCCWArea`, `RobustLineIntersector` (has/number/proper/
  points), `Intersection.intersection`, `Envelope.intersects`, `Distance.pointToSegment`/`segmentToSegment`,
  `PointLocation.isOnSegment`/`locateInRing`/`isInRing`, `Area.ofRing[Signed]`, `Length.ofLine`, `LineSegment`
  (orientation, distances, closest points, intersection, projection, reflection), `Triangle` (orientation, areas,
  centroid, circumcentre in both precisions, circumradius, incentre, acuteness, containment) against `Exact`.
- **measuresAreExact** — polygon area, length, centroid (exact rational), interior point strictly inside, validity
  and simplicity of the generated (valid) polygons, envelope, point location three ways (`SimplePointInAreaLocator`,
  `IndexedPointInAreaLocator`, `PointLocator`) and `contains`/`covers`/`intersects`/`touches`/`distance` of a point;
  validity and simplicity of arbitrary rings and lines against exact simplicity; convex hull against the exact hull;
  `MinimumBoundingCircle` (covers all points, touches two, radius between half the diameter and diameter/√3).
- **validityIsExact** — `IsValidOp` on a polygon with a hole built near its shell (touching, crossing, nested,
  outside) and on two-part multipolygons of near rings, against the SFS rules computed exactly: simple rings, no
  proper crossings or collinear overlaps, no piece of one boundary inside the other's interior (edges split at their
  meeting points), holes inside the shell; configurations whose interior connectivity the model does not decide (a
  hole touching the shell at two or more points) are skipped. Valid multipolygons also check area, `union()` and
  `relate` of the parts.
- **predicatesAgree** — `RelateOp` = `RelateNG` = `RelateNG.prepare`, `relate(b, a)` = transpose, every boolean
  predicate equals its matrix definition, `contains`/`within` and `covers`/`coveredBy` symmetry, prepared predicates,
  `containsProperly` = `T**FF*FF*`, exact `intersects` (vertex in area or edges meeting) and exact `distance`
  (`Geometry.distance`, `DistanceOp.nearestPoints`, `IndexedFacetDistance`, `isWithinDistance`), `relate(a, a)` =
  `T*F**FFF*`, `equalsTopo` with the reverse and the norm.
- **overlayIsConsistent** — for polygonal or lineal pairs (copies, translations by a few grid steps, random):
  `OverlayNGRobust` and `OverlayOp` give valid results of equal area/length whose symmetric difference has area 0
  (polygonal parts, since OverlayNG refuses mixed collections), area(∩) + area(∪) = area(A) + area(B), area(−) +
  area(∩) = area(A), area(⊕) + 2 area(∩) = area(A) + area(B), bounds, union covers the inputs' vertices and the
  intersection's vertices lie in both, `intersects` ⇔ non-empty intersection, A ∪ A, A ∪ ∅, unary and cascaded unions
  of disjoint parts, snapped `OverlayNG` with `PrecisionModel(1)` (valid, on the grid); length identities for simple
  lines and line ∩/− polygon.
- **readersInvertWriters** — WKT (`toText`, `WKTWriter`, formatted), WKB (both byte orders, with and without SRID,
  hex) and GeoJSON round trips are `equalsExact` with the same types, empties included; `copy`, `norm` idempotent,
  `equalsNorm` with the reverse, `reverse` twice, `equals`/`hashCode`, `compareTo` antisymmetric and 0 iff
  `equalsExact`, `getEnvelope`, boundary of the boundary empty, a polygon's boundary has its points.
- **indexesMatchBruteForce** — `STRtree`, `HPRtree` (exact), `Quadtree` (superset, list = visitor), `STRtree`
  nearest neighbour (item and pair, with an anti-reflexive distance as documented), removal, `KdTree` (query, counts,
  size, point lookup), `SortedPackedIntervalRTree`.
- **constructionsKeepInvariants** — buffers (valid, contain the input's vertices, boundary vertices at distance d
  within the chord approximation of `quadrantSegments` and the 1 % input simplification, monotone, `buffer(0)` and
  `bufferByZero` keep valid polygons, negative buffers inside, cap styles ordered by area); `DouglasPeucker`, `VW` and
  `TopologyPreserving` simplifiers (valid, no new points, DP keeps endpoints and stays within tolerance);
  `Densifier` (segments ≤ tolerance, same length/area, vertices on the input); `GeometryPrecisionReducer` (on grid,
  valid, vertices within half a cell of the input); Delaunay (vertices are sites, non-degenerate, exact empty
  circumcircles, triangles tile the hull exactly, Euler count 2n − 2 − h), Voronoi (one cell per site, site inside,
  vertices no closer to another site), `MaximumInscribedCircle`, minimum rectangles, `ConcaveHull`,
  `LargestEmptyCircle`; `GeometryFixer` (valid, keeps valid input), `buffer(0)` of invalid rings, validation error
  location on the geometry; `Polygonizer` of a boundary gives the polygons back, `LineMerger` reassembles a shuffled
  split line; `LengthIndexedLine` (vertices, sub-lines, projection); `AffineTransformation` (determinant, area
  scaling by |det| on the grid, inverse, translation, rotation, reflection).
- **newerOperationsKeepInvariants** — `OffsetCurve` (vertices at distance d within the approximation, joined and
  raw variants); coverage operations on a polygon split by a vertical line (`CoverageValidator`, `CoverageUnion`
  area, `CoverageSimplifier` keeps a valid coverage without new vertices, `CoverageGapFinder`, an overlapping copy
  is invalid); `GeometryNoder` snap-rounding (on grid, fully noded — checked exactly — vertices within half a
  cell); WKT text variants (whitespace, case, `+`, exponents, leading/trailing zeros, `.5`); n-ary unions of
  overlapping polygons (`UnaryUnionOp`, `CascadedPolygonUnion`, `OverlayNGRobust.union`, `GeometryCollection.union`)
  against the iterated binary union; normal form (shell CW, holes CCW, idempotent, reverse-invariant);
  `isRectangle`.

## Known shapes (`JtsShapesTest`)

The generators draw the shape of every recorded bug by default (STYLE.md rule 11): `GeoGen.line` repeats an
interior vertex in one line in ten (half the time next to the original), one point set in ten has all its points
coincide, and the strange-ordinate pool mixed into a tenth of the points and lines holds 1/7, 1/3000, 1e-17 and
5e-324 beside the extremes; `predicatesAgree` judges every pair, including lines whose segments cross each other on a
polygon's boundary or along another line. The wide properties fail on those shapes when they draw them - a few percent of cases each, so
they pass some runs at the default count and are mapped as intermittent (`readersInvertWriters` to jts/1,
`measuresAreExact` to jts/3, which it shrinks to in every run, `predicatesAgree` to jts/4, the first of the two
relate shapes it meets - jts/5 is the other). Beside them
`JtsShapesTest` has one narrow property per bug, drawing only the bug's shape region with random contents and judged
by the same check as the wide property (`checkWktRoundTrip`, `checkRingSimple`/`checkLineSimple`,
`checkBoundingCircle`, `checkRelateAgree`): ordinates below one through WKT, a repeated interior vertex in a simple
line or ring, 2..8 coincident points under `MinimumBoundingCircle`, a line crossing itself at the midpoint of a
polygon's edge, and a self-crossing line with a line along its last segment, under `RelateOp` and `RelateNG`. They fail every run; `JtsPinsTest` keeps the regression examples.
`HEGEL_NO_KNOWN=1`, read once into `Zoo.NO_KNOWN`, switches the shapes off: the generators stop planting them, the
narrow properties draw the neighbouring region (short decimals, a repeated end point, a second distinct point, a
crossing off the boundary, the middle segment) and every property passes; the skips this adds are 0.9 % of `readersInvertWriters`
(hole vertices on the thousandths grid that need 17 digits), 2.2 % of `measuresAreExact` and below 0.1 % elsewhere.

`HEGEL_TEST_CASES=2000` × 14 properties runs in about 25 s.

## What the properties allow for

Zero-length lines (all points equal) are invalid in JTS (`isValid` false) and relate inconsistently, so predicates
leave them out (`assume`), and the simplifiers, densifier and precision reducer are checked on valid lines only.
`GeometryNoder` drops a line whose vertices all snap to one grid point, `DouglasPeucker` and `VW` may collapse a
closed line to a zero-length one (validity is promised for polygonal results only), and `OffsetCurve.rawOffset`
gives a single point when the inside offset distance is at least every segment's length (`LINESTRING (3 0, 2 0,
2 1)` at -1) - tolerated for those cases only. The quirks the properties allow for, all documented or inherent: `Area.ofRingSigned` and
`Triangle.signedArea` are positive for *clockwise* rings; `IntersectionMatrix.transpose()` mutates in place;
`GeometryCollection.getBoundary` throws; `RobustLineIntersector` reports a two-point collinear intersection when a
zero-length segment lies on the other; the `Quadtree` may return a superset; `STRtree.nearestNeighbour(ItemDistance)`
pairs an item with itself unless the distance is anti-reflexive; simplifiers and the densifier return a single
component for a one-part multi-geometry; `GeometryPrecisionReducer` nodes segments at hot pixels and removes
collapsed parts; buffers approximate circles by chords (one fillet chord spans up to 1.5 × π/(2·quadrantSegments))
and simplify their input by 1 % of the distance; the offset curve is not compared with the buffer boundary; the
coverage validator demands vertex-matched shared edges, so a copy touching along part of an edge is invalid, and a
narrow hole of an input polygon is a coverage gap.

## Not tested

Z/M ordinates and `CoordinateSequence` implementations other than the default, `PrecisionModel` FIXED geometries as
inputs (only OverlayNG with a fixed model), `BoundaryNodeRule`s other than Mod-2, GML/KML readers, the `app`, `lab`
and `tests` modules, `SnapIfNeededOverlayOp` and other legacy overlay entry points beyond `OverlayOp.overlayOp`,
`ConformingDelaunayTriangulationBuilder`, `LineSequencer`, `Densifier.setValidate`, performance.

## Bugs found

See `bugs.toml` (5, all open at the pinned commit, each with a narrow property in `JtsShapesTest` and a pin in
`JtsPinsTest`): `WKTWriter` prints at most 16
fraction digits under the floating precision model, so ordinates below 1 needing 17 significant digits (1/7, 1/3000)
and anything below 1e-16 do not round-trip (1); `IsSimpleOp` reports a line or ring with a repeated interior vertex
as non-simple while trimming repeated end points (2); `MinimumBoundingCircle` of two or more coincident points has a
null centre — the convex hull is a single point and the "duplicate final point" strip removes it (3); `RelateOp`
reports the boundary of a polygon meeting the interior of a line in a one-dimensional set when two segments of the
line cross each other at a point inside one of the polygon's edges (`1021F1102` where `RelateNG` and the boundary's
intersection, two points, say `1020F1102`) (4); `RelateOp` relates a line collinear with a segment of a self-crossing
line as mostly outside it when the crossing point is not exactly representable (`001F001F2` for
`LINESTRING (0 0, 1 -1, 0 -1, 1 1)` and its own segment `LINESTRING (0 -1, 1 1)`, `RelateNG` `101F00FF2`, so
`covers` is false) (5). Both found on 2026-09-26 by `predicatesAgree` once the shapes were drawn.

## Observed, not recorded

- `Geometry.relate` and `Geometry.intersection` use the original `RelateOp`/`OverlayOp` unless the system properties
  `jts.relate=ng`/`jts.overlay=ng` are set; the overlay pair agreed on every case (2000 per run), the relate pair
  except for bugs 4 and 5.
- `OverlayNG` intersection may return a mixed-dimension collection (polygon plus the touching line/point), which it
  then refuses as input ("Overlay input is mixed-dimension").
- `GeometryPrecisionReducer(1)` changes an on-grid polygon whose hole vertex lies within half a cell of the shell
  (snap-rounding nodes the shell at the hole's vertex) — inherent in snap-rounding.

## History

- 2026-09-16: created (turn 176) at 9c995e538329 (1.21.0-SNAPSHOT); 3 bugs.
- 2026-09-26: the known shapes drawn by default, one narrow property per bug in `JtsShapesTest`, `Zoo.NO_KNOWN`;
  bugs 4 and 5 found by the freed `predicatesAgree`; `Zoo.chance` now shrinks to false; four tolerances for zero-length
  and closed lines from `GeoGen.line` (above).
