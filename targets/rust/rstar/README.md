# rstar

[georust/rstar](https://github.com/georust/rstar).

## What is tested

**`src/aabb.rs`**
- `hegel_min_max_dist_2_bounds`: `min_max_dist_2` is used by the nearest neighbor search as an upper bound for the distance to the closest object inside the envelope (see `algorithm/nearest_neighbor.rs`); pruning is only correct if it lies between the distance to the box itself and the distance to the box's farthest corner.

**`src/algorithm/intersection_iterator.rs`**
- `hegel_intersection_candidates_match_brute_force`: (no doc comment)

**`src/algorithm/iterators.rs`**
- `hegel_locate_in_envelope_matches_naive_filter`: (no doc comment)
- `hegel_locate_within_distance_matches_naive_filter`: (no doc comment)

**`src/algorithm/nearest_neighbor.rs`**
- `hegel_nearest_neighbor_matches_brute_force`: (no doc comment)
- `hegel_nearest_neighbor_iter_is_sorted_permutation`: (no doc comment)
- `hegel_nearest_neighbors_returns_all_ties`: (no doc comment)

**`src/algorithm/removal.rs`**
- `hegel_drain_in_envelope_partitions_elements`: (no doc comment)

**`src/rtree.rs`**
- `hegel_insert_supports_full_finite_coordinate_range`: KNOWN FAILURE: `RTree::insert` panics with "called `Option::unwrap()` on a `None` value" (algorithm/rstar.rs, `get_nodes_for_reinsertion`) once a node overflows while its envelope has corners with magnitude above `f64::MAX / 2`: * `AABB::center` computes `(lower + upper) / 2`, which overflows to   infinity for such corners (e.g. `lower == upper == -f64::MAX`). * The reinsertion heuristic then sorts children by the squared   distance between the child center and the node center; with both   centers infinite this is `inf - inf == NaN`, and   `partial_cmp(..).unwrap()` panics. All inserted coordinates are finite, i.e. ordinary valid input, so this is a library bug rather than a test artifact. The minimal reproducer is inserting `MAX_SIZE + 1` copies of `[0.0, -f64::MAX]`. The generator is boosted to the failing region so the failure reproduces deterministically on every run.
- `hegel_bulk_load_produces_uniform_leaf_depth`: KNOWN FAILURE: `RTree::bulk_load` produces trees whose leaves sit at different depths, violating the R-tree balance invariant that the crate's own `ParentNode::sanity_check` asserts (uniform leaf height). The OMT partitioning is driven purely by the element *count*: for 25 elements with the default `MAX_SIZE` of 6, the clusters have sizes 7/6/6/6, and only the 7-element cluster gets an extra tree level, so *any* 25 points reproduce this. Queries still return correct results (nothing in the query code assumes balance), so the impact is on tree quality/performance and on the crate's own stated invariant. The element count is drawn from a boosted region so the failure reproduces deterministically on every run.
- `hegel_model_test`: (no doc comment)
- `hegel_bulk_load_matches_incremental_insertion`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-06-22: predecessor base commit `05e6d58c5e03` (Bump actions/checkout from 6 to 7 (#234)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/rstar.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
