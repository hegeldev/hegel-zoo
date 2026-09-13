# pathfinding

[evenfurther/pathfinding](https://github.com/evenfurther/pathfinding).

## What is tested

**`tests/connected-components.rs`**
- `components_agree_with_union_find`: (no doc comment)

**`tests/kuhn_munkres.rs`**
- `kuhn_munkres_matches_brute_force_maximum`: (no doc comment)
- `kuhn_munkres_min_matches_brute_force_minimum`: (no doc comment)

**`tests/pathfinding.rs`**
- `dijkstra_astar_fringe_agree_with_bellman_ford_oracle`: (no doc comment)
- `idastar_agrees_with_dijkstra`: (no doc comment)
- `dijkstra_path_is_a_valid_witness`: (no doc comment)
- `astar_with_consistent_heuristic_finds_optimal_cost`: (no doc comment)
- `bfs_returns_a_valid_minimum_hop_path`: (no doc comment)
- `dijkstra_all_matches_oracle_distances`: (no doc comment)

**`tests/strongly_connected_components.rs`**
- `sccs_partition_nodes_by_mutual_reachability`: (no doc comment)

**`tests/topological_sort.rs`**
- `topological_sort_orders_edges_or_reports_a_cycle_node`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-07-21: predecessor base commit `16ce0bc5d60b` (chore(deps): update actions/checkout action to v7).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/pathfinding.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1. One upstream `assert_eq!(assignments, vec![])` in `tests/kuhn_munkres.rs` rewritten as `assert!(assignments.is_empty())`: hegeltest 0.44 pulls in `serde_json`, whose `PartialEq` impls make the empty literal ambiguous (E0282/E0283).
- 2026-09-13: base bumped 16ce0bc5d60b → 2f02dc94b5a5 (2026-09-11, "perf(grid): fill a fixed buffer of neighbours instead of a vector per vertex"; 4.16.0); 0 bug(s) still reproduce; add/add conflicts in tests/strongly_connected_components.rs, tests/topological_sort.rs resolved by keeping both sides. 295 tests pass.
