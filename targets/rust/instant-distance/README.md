# instant-distance

[InstantDomain/instant-distance](https://github.com/InstantDomain/instant-distance).

## What is tested

**`tests/all.rs`**
- `hegel_search_results_valid_consistent_sorted_unique`: Every search result is valid and self-consistent: the pid refers to a real point of the index, the returned point is bit-identical to the input point that got that pid, the reported distance equals an independent recomputation of the metric, results are sorted by ascending distance, and no pid appears twice.
- `hegel_search_result_count_bounds`: Result-count bounds that hold for *any* build configuration: `len <= min(n, ef_search)`, empty iff the index is empty. Exact `len == min(n, ef_search)` is NOT guaranteed in general: hegel found a 255-point cloud with `select_heuristic(None)` where only 98 of the requested 161 results come back. That is inherent to the algorithm — `ZeroNode::insert` documents that a new node's id may not be inserted into a full neighbor list, so a node can end up with no in-links and become unreachable from the entry point.
- `hegel_search_count_exact_for_small_index`: For small indices the count is exact: with `n <= M * 2` (64) every node's zero-layer neighbor list can hold all other nodes, so every point stays reachable and search returns exactly `min(n, ef_search)` results. Evidence: the existing `randomized` test asserts `results.len() >= 100` (i.e. == ef_search). This holds for simple selection (`select_heuristic(None)`), where links are only ever *added*, with any `ef_construction`. For heuristic selection it additionally needs `keep_pruned = true` (dropping pruned candidates can drop links) and `ef_construction > n`: the heuristic path *rewrites* a neighbor's whole link list via a search capped at `ef = ef_construction`, so a small `ef_construction` strips links — hegel found 4 duplicate points with `ef_construction = 1` returning only 3 of 4 requested results.
- `hegel_indexed_point_found_at_distance_zero`: Querying with a point that is in the index finds a result at distance exactly 0.0 in first position. Evidence: the existing `map` unit test asserts this for a 5-point index. Kept to n <= 64 (M * 2), where every point is guaranteed reachable (see the small-index count test), so the exact duplicate cannot be missed. Note we deliberately do NOT assert the returned coordinates equal the query: hegel found that two *different* points can be at computed distance 0.0 (e.g. (0.0, 0.0) vs (0.0, 2.6e-23): the squared difference underflows f32 to zero), and returning either is correct.
- `hegel_same_seed_same_points_reproduce_identical_index`: Building twice from the same points, seed, and configuration produces an identical index: same PointId assignment and identical search results (ids and distance bits) for arbitrary queries — even though construction inserts points in parallel.
- `hegel_map_agrees_with_hnsw_and_maps_values_correctly`: `HnswMap` search agrees with a raw `Hnsw` built from the same builder (same pids and distances), and its value reordering is correct: using the original input index as the value, each result's value points back at exactly the input point that was returned.
- `hegel_pids_are_permutation_mapping_inputs`: `build_hnsw` returns one PointId per input point, forming a permutation of 0..n, and indexing the Hnsw with the id returned for input i yields exactly input point i. `iter()` walks ids 0..n in order and agrees with indexing.
- `hegel_search_handle_reuse_equivalent_to_fresh`: Reusing one `Search` handle across many queries (and across two different indices) returns exactly the same results as a fresh `Search` per query. 260 iterations force the `Visited` generation counter (u8, reset at 249) through its wraparound path.
- `hegel_no_panic_on_arbitrary_float_coordinates`: Building and searching never panics for arbitrary f32 coordinates, including NaN and infinities, under arbitrary build configurations. Only weak result checks here — with NaN coordinates the distance is not a metric, so ordering/recall guarantees don't apply.
- `hegel_serde_roundtrip_preserves_search_results`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-07-21: predecessor base commit `13ea89ac1ca0` (Bump actions/setup-python from 6 to 7).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/instant-distance.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
