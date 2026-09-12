# radix_trie

[michaelsproul/rust_radix_trie](https://github.com/michaelsproul/rust_radix_trie).

## What is tested

**`src/qc_test.rs`**
- `hegel_stateful_model_vs_btreemap`: (no doc comment)
- `hegel_insert_get_remove_consistency`: (no doc comment)
- `hegel_get_ancestor_is_longest_stored_prefix`: (no doc comment)
- `hegel_get_raw_ancestor_is_deepest_node_prefix`: (no doc comment)
- `hegel_get_raw_descendant_is_the_prefix_filter`: (no doc comment)
- `hegel_subtrie_of_stored_key_is_the_prefix_filter`: (no doc comment)
- `hegel_iteration_matches_oracle`: (no doc comment)
- `hegel_len_counts_distinct_keys`: (no doc comment)
- `hegel_prefix_chain_and_near_collision_edge_cases`: (no doc comment)

## Oracles

## Not tested

## History

- 2025-09-16: predecessor base commit `a89f789e1267` (Release v0.3.0 (#79)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/radix_trie.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
