# petgraph

[petgraph/petgraph](https://github.com/petgraph/petgraph).

## What is tested

**`tests/graph.rs`**
- `prop_dijkstra_matches_naive_shortest_paths`: Property: `dijkstra` returns exactly the shortest-path distances to every reachable node (docs: "Compute the length of the shortest path from `start` to every reachable node"), compared against a naive O(V*E) relaxation. The node bound protects the cubic-ish reference oracle's runtime, not the library's contract.
- `prop_astar_zero_heuristic_returns_valid_shortest_path`: Property: `astar` with the trivial heuristic behaves like dijkstra (per its docs) and its returned path is a valid witness: it starts at `start`, ends at the goal, walks only existing edges, and the per-hop minimum edge weights sum to exactly the claimed cost.
- `prop_tarjan_scc_matches_mutual_reachability`: Property: `tarjan_scc` returns exactly the equivalence classes of mutual reachability (the definition of strongly connected components), with every node in exactly one component.
- `prop_kosaraju_and_tarjan_scc_agree`: Property: `kosaraju_scc` and `tarjan_scc` (two independent implementations) produce the same partition of the nodes.
- `prop_connected_components_matches_dfs_reference`: Property: `connected_components` (union-find based) matches the component count of a naive DFS over the undirected view of the graph.
- `prop_toposort_ok_iff_acyclic`: Property: `toposort` succeeds if and only if the graph is acyclic (docs: "`toposort` returns `Err` on graphs with cycles", self loops included).
- `prop_toposort_order_respects_edges`: Property: when `toposort` succeeds, the order is a permutation of all nodes in which every node comes before its successors (docs: "each node is ordered before its successors").
- `prop_graph_mutations_match_model`: Property (stateful): a `Graph` under add/remove of nodes and edges agrees with a simple vec-based model, including the documented swap-remove index semantics of `remove_node`/`remove_edge`.

**`tests/graph6.rs`**
- `prop_graph6_roundtrip`: Property: encoding a simple undirected graph to graph6 and decoding it back preserves the node count and the edge set (round-trip). Grounded in the module docs (graph6 encoder/decoder for undirected graphs) and the paired `ToGraph6`/`FromGraph6` traits.

**`tests/min_spanning_tree.rs`**
- `prop_min_spanning_tree_is_spanning_forest`: Property: `min_spanning_tree` (Kruskal) produces a spanning forest of the input: same node set, exactly `|V| - c` edges where `c` is the number of connected components, the same components, and every output edge exists in the input with the same weight (witness check). Grounded in the docs ("minimum spanning forest") and the doc example's count assertions.
- `prop_kruskal_and_prim_agree_on_total_weight`: Property: Kruskal (`min_spanning_tree`) and Prim (`min_spanning_tree_prim`) agree on the total weight of the minimum spanning tree of a connected graph (all MSTs of a graph have the same total weight). Prim documents it only supports a single component, so the generator builds connected graphs by construction.

## Oracles

## Not tested

## History

- 2026-03-08: predecessor base commit `ed714652ab45` (chore: Bump hashbrown to ^0.16 (#967)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/petgraph.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped ed714652ab45 → e7fc31536a40 (2026-09-06, "ci: Fix clippy (#1037)"; 0.8.3); 0 bug(s) still reproduce. 406 tests pass.
