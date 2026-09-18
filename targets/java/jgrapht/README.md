# jgrapht

[JGraphT](https://github.com/jgrapht/jgrapht) (EPL-2.0 or LGPL-2.1), pinned at `7580075f`
(1.6.0-SNAPSHOT, 2026-08-03): the `jgrapht-core` graph algorithms - shortest paths, k shortest and
disjoint paths, maximum flows and cuts, matchings, spanning trees and spanners, connectivity and
biconnectivity, cycles and cycle bases, Eulerian cycles, colourings, cliques, vertex covers,
travelling-salesman tours, lowest common ancestors, planarity, isomorphism, the `GraphTests`
predicates, `DirectedAcyclicGraph`, the traversals, and some generators and `Graphs` utilities.

The patch adds a Maven module `hegel/` that depends on `jgrapht-core` at its pom version (installed
by the setup step with `mvn -pl jgrapht-core -am install -DskipTests`), on `dev.hegel:hegel` 0.6.0
and JUnit 5. The properties are JUnit tests driven by `Hegel.test`; `Zoo.java` is the small harness
shared by the Java targets (case counts from `HEGEL_TEST_CASES`, a collect mode under
`ZOO_COLLECT=1`) and `ZooListener` prints one `ZOO ok|FAILED <method>` line per test for the judge.
Surefire runs with assertions enabled (its default), which is how jgrapht/27 shows.

## Oracles

`GraphGen` draws graphs of at most nine vertices and sixteen edges - directed or undirected,
simple or with parallel edges and self loops, with small integral weights so every sum is exact -
and prints a failing graph as `directed multi V=[...] E=[0->1:3, ...]`. `Brute` answers the
questions by force: Floyd-Warshall for distances, DFS enumeration of simple paths and simple
cycles, subset enumeration for cuts, cliques, independent sets, vertex covers and colourings,
bitmask dynamic programs for matchings and Held-Karp for tours, Kruskal on the sorted edge list
for spanning forests, reachability matrices for components, strong components, cut vertices,
bridges and topological orders, and a walk up the tree for ancestors.

## What is tested

- `PathsTest` - every shortest-path algorithm (Dijkstra and its bidirectional, integer-vertex,
  radius-bounded and many-to-many forms, A* with the zero heuristic, delta-stepping, contraction
  hierarchies with transit-node routing, Bellman-Ford, Johnson, Floyd-Warshall with its hop
  tables and path counts, BFS on the unweighted view) against Floyd-Warshall; Johnson and
  Bellman-Ford must throw on reachable negative cycles; Yen, bounded-pruned Yen, Eppstein (exact
  when no cycle lies on an s-t walk, else sorted valid walks no heavier than the simple paths of
  the same rank) and `AllDirectedPaths` against the enumeration of simple paths; Suurballe and
  Bhandari disjoint paths (as many as the unit min cut allows, disjoint, the first one shortest,
  the pair optimal); `GraphWalk`'s contract (verify, derived lists, equals, reverse, concat).
- `FlowMatchingTest` - Edmonds-Karp, Dinic, push-relabel and Boykov-Kolmogorov flows equal the
  brute-force minimum cut, respect capacities and conservation, and their cuts are consistent;
  Gomory-Hu and equivalent-flow trees answer every pair, Stoer-Wagner and the k-connectivity
  algorithm match global cuts and connectivities; the Edmonds, greedy, Kolmogorov (max, min,
  perfect), path-growing, Hopcroft-Karp, maximum-weight bipartite and Kuhn-Munkres matchings
  against the bitmask dynamic program (exact or within the documented approximation factors, with
  certificates); Kruskal, Prim and Boruvka against Kruskal on the edge list (negative weights
  included), greedy spanners within their stretch, Kou-Markowsky-Berman Steiner trees (compared
  by endpoints) connecting the terminals, acyclic, between the optimum and twice it.
- `StructureTest` - connected sets, path existence, strong components and their condensation,
  `CycleDetector`, cut points, bridges and blocks against reachability; transitive closure and
  reduction (of DAGs) against reachability; Eulerian graphs and Hierholzer's cycle; the five
  simple-cycle enumerators against the enumeration and the three cycle bases (dimension m-n+c,
  independence over GF(2), closed walks, weights); the greedy colourings proper, Brown exact, the
  chordal algorithms exact on chordal graphs and null otherwise, `ChordalityInspector`'s
  elimination orders and holes; the three Bron-Kerbosch finders against the maximal cliques;
  exact and 2-approximate vertex covers, weighted too; Held-Karp exact, Christofides within 3/2
  and the tree approximation within 2 on metric graphs, the heuristics valid, two-opt never
  worse, Palmer on Ore graphs; the LCA finders on trees and forests; the `GraphTests`
  predicates against their definitions (planarity against a Kuratowski search on at most seven
  vertices, embeddings and Kuratowski subdivisions checked); `DirectedAcyclicGraph` rejects
  exactly the cycle-closing edges and iterates topologically, ancestors and descendants;
  breadth-first depths and parents, depth-first coverage.
- `JGraphtPinsTest` - one plain JUnit test per recorded bug (two for jgrapht/11 and /45),
  asserting the correct behaviour so that it fails while the bug exists. The Howard pin runs the
  hanging call in a child JVM with a small heap (`HowardProbe`) because the thread cannot be
  stopped.

## Known bugs (50, see bugs.toml)

Wrong results: `TransitiveReduction` empties cyclic graphs (5), the Kou-Markowsky-Berman Steiner
tree returns edge objects foreign to the graph (49) and, on multigraphs, weighs more than its
bound (50), `BinaryLiftingLCAFinder` cannot
climb past 2^floor(log2 n) - 1 (9), `ColorRefinementIsomorphismInspector` returns invalid mappings
(8) and throws for directed graphs (17), `KConnectivityFlowAlgorithm` looks one way on directed
graphs (3), `isBiconnected` on disconnected graphs (1), antiparallel arcs as bridges (2),
`BipartitePartitioning` on multigraphs (6), Boyer-Myrvold on loops and parallel edges (11),
Kuratowski predicates on disconnected graphs (10), VF2 subgraph isomorphism and self loops (12),
Held-Karp on multigraphs (19), the unweighted greedy spanner's DFS distances (20), capacitated
spanning trees on incomplete graphs (24), Prim and infinite weights (25), Johnson and vertex
supplier collisions (33), Kolmogorov and supplier collisions (30), Yen and bounded Yen on parallel
arcs (38, 39), `GraphWalk.verify` and direction (36), BFS path weights (37), Kleinberg's
wrap-around (43), G(n,p) loops sampled twice (46), `Graphs.addGraph`/`addAllEdges` weights (45),
`removeVertexAndPreserveConnectivity` on undirected graphs (48), colour counts (7), cardinality
matchings' weights (28), path-growing and self loops (29), lazy getters that never compute (13),
`simpleCycleToGraphPath` without its promised exception (26), and the ignored epsilons of
Bellman-Ford (35) and push-relabel (31). Crashes: Johnson's reweighting round-off (32), A*
reopening (34), Suurballe on decimal weights (40), the line graph with weights (16), Brown on tiny
graphs (14), `isOverfull` on the null graph (15), Edmonds matchings on the null graph (27),
spanners of edgeless graphs (21), `SpannerImpl.toString` (22), `ChordalityInspector` on directed
graphs (23), `TreeDynamicConnectivity.cut` (4), `RingGraphGenerator(1)` / `WheelGraphGenerator(2)`
(42), `RandomRegularGraphGenerator` on multigraphs (44). Hangs: Howard's minimum mean cycle on
tied means (18), G(n,m) with too many edges (47). `AsUndirectedGraph` declares no multiple edges it
has (41).

The properties skip a known-bug shape only when the mismatch actually occurs (`known jgrapht/N`
in the collect output); the pins assert the correct behaviour and are listed as expected failures.

## Conventions followed, not recorded

The null graph is not Eulerian and not a split graph (explicit in the code); an edgeless graph
with vertices is Eulerian and its cycle is the empty walk. `CycleDetector.findCyclesContainingVertex`
is documented as incomplete, so only a subset of the strong component is required. On the null
graph `PivotBronKerboschCliqueFinder` lists the empty clique and the other two finders list nothing;
both are accepted. Eppstein's
"k shortest paths" are walks. `BergeGraphInspector` reads directed graphs with directed semantics
unlike its siblings; the TSP heuristics crash on infinite edge weights; `PushRelabelMFImpl`
accepts source == sink; `BoykovKolmogorovMFImpl` is reported wrong on directed multigraphs but no
deterministic reproduction was found - none of these is recorded.
