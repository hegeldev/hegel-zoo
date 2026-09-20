# graphology

[graphology](https://github.com/graphology/graphology) is a graph data structure for JavaScript
(mixed, directed or undirected; simple or multi; with or without self loops) with a standard library
of algorithms in the same monorepo. Pinned at 0.26.0 of the core, 65e278f (2026-09-02), MIT. Tested
here: the core `Graph`, `graphology-shortest-path`, `-components`, `-dag`, `-simple-path`,
`-traversal`, `-operators`, `-metrics` (graph, node and centrality metrics), `-cores` and
`-bipartite`, all at the pinned commit.

The core is ESM source and the library packages are CommonJS that `require` each other by package
name, so the setup bundles them with esbuild from `hegel/entry.mjs` into `hegel/graphology.mjs`,
aliasing the intra-repo names to their directories; the four external runtime dependencies
(`events`, `mnemonist`, `@yomguithereal/helpers`, `pandemonium`) go under `.hegel/`. Tests:
`hegel/hegel.test.mjs`, run with `node --test`. `ZOO_FULL=1` opens the gates around the known bugs;
`ZOO_COLLECT=1` prints mismatch statistics.

## Oracle

`hegel/model.mjs` is a naive model: a graph is its option set, a node list and an edge list
(`{key, source, target, undirected, attributes}`), and every algorithm is written the obvious way on
it: neighbour sets by scanning the edges (outbound = out + undirected, as graphology documents),
BFS distances, Bellman-Ford for weights, components by reachability, DFS cycle detection,
exhaustive simple-path enumeration, Brandes' accumulation for betweenness over ordered pairs (with
graphology's documented normalisation), networkx's closeness (inbound distances, optional
Wasserman-Faust factor), k-core peeling by multiplicity. `hegel/gen.mjs` builds the same random
graph in both (0-7 nodes, 0-10 edges with integer weights, random type/multi/self-loop options,
skipping edges the options forbid).

## Properties

| Test | Checks |
| --- | --- |
| `TestHegelGraphReadsAgreeWithTheModel` | After random edge/node drops: order, sizes, self-loop count, every degree and neighbour variant, `edges(node)`, `hasEdge`/`outEdges`/`undirectedEdges` between two nodes, export/import round trip, `copy()` |
| `TestHegelEdgeAdditionIsRefusedExactlyWhenTheModelSaysSo` | `addDirectedEdge`/`addUndirectedEdge` throw exactly for duplicates in simple graphs, self loops when disallowed, and edges of the wrong type |
| `TestHegelUnweightedShortestPathsAgreeWithBfs` | `singleSourceLength`, `undirectedSingleSourceLength`, `singleSource`, `bidirectional`, `edgePathFromNodePath` against BFS |
| `TestHegelDijkstraFindsMinimalWeightPaths` | `dijkstra.singleSource` / `bidirectional` paths are valid and of minimal weight |
| `TestHegelConnectedComponentsPartitionTheGraph` | Weakly and strongly connected components, counts, orders, largest component and its subgraph |
| `TestHegelDagFunctionsAgreeWithCycleDetection` | `hasCycle`, `topologicalSort` (valid order or throws), `topologicalGenerations` (one after the latest predecessor), `forEachNodeInTopologicalOrder`, `willCreateCycle` |
| `TestHegelSimplePathsAreEnumeratedExhaustively` | `allSimplePaths` and `allSimpleEdgePaths` (with and without `maxDepth`) equal the brute-force enumeration |
| `TestHegelTraversalsVisitReachableNodesOnce` | `bfsFromNode` (depths), `dfsFromNode`, `bfs`, `dfs`, inbound mode |
| `TestHegelOperatorsMatchTheModel` | `reverse`, `toUndirected`, `toDirected`, `toSimple`, `simpleSize`, `subgraph`, `disjointUnion` |
| `TestHegelMetricsAgreeWithTheModel` | `density`, `eccentricity`, `diameter`, degree centrality, closeness (both normalisations), betweenness (weighted and unweighted, normalised or not), pagerank sums to 1, `isBipartiteBy` |
| `TestHegelCoreNumbersMatchPeeling` | `coreNumber` on simple graphs without self loops |

In the default run the shapes of the recorded bugs are counted and skipped: the two-argument
`edges`/`directedEdges`, `toDirected` on coinciding directed/undirected edges, path and
power-iteration centralities of an empty graph, eccentricity and degree centrality of a one-node
graph, `simpleSize` with an undirected self loop in a multi graph, and closeness/betweenness/pagerank
on graphs where the neighbourhood index is shorter than its upper bound (multi graphs, undirected
self loops, a directed edge beside an undirected one). `edgePathFromNodePath` of a one-node path is
not judged (it returns a self loop when there is one, by design), nor is `allSimplePaths` with
`maxDepth: 0` (it behaves like 1). Pins (`TestHegelPin*`) reproduce the bugs in `bugs.toml` and are
listed as expected failures.

## Not tested

- Attribute methods and events of the core beyond what export/import covers; `mergeEdge`/`updateEdge`
  semantics; typed-key edge cases (numbers as keys).
- `astar`, `brandes` directly, the Louvain/Leiden communities, layouts, generators, GEXF/GraphML,
  `kTruss`/`onionLayers`/`kCore` subgraphs, modularity, HITS and eigenvector values (only their
  behaviour on an empty graph), edge betweenness values, disparity/chi-square/g-square, `union`.
- Error messages.

## History

- 2026-09-20: created (turn 322); 8 bugs recorded.
