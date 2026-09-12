# rpds

[orium/rpds](https://github.com/orium/rpds).

## What is tested

**`src/list/test.rs`**
- `hegel_list_model_matches_vec_deque`: (no doc comment)
- `hegel_list_reverse_matches_vec_reverse`: (no doc comment)

**`src/map/hash_trie_map/test.rs`**
- `hegel_hash_trie_map_model_matches_hash_map`: (no doc comment)
- `hegel_hash_trie_map_collisions_model_matches_hash_map`: (no doc comment)
- `hegel_hash_trie_map_persistence`: (no doc comment)

**`src/map/red_black_tree_map/test.rs`**
- `hegel_insert_remove_keeps_tree_consistent`: (no doc comment)
- `hegel_rbt_map_model_matches_btree_map`: (no doc comment)
- `hegel_rbt_map_range_matches_btree_map`: (no doc comment)
- `hegel_rbt_map_persistence`: (no doc comment)

**`src/queue/test.rs`**
- `hegel_queue_model_matches_vec_deque`: (no doc comment)
- `hegel_queue_persistence`: (no doc comment)
- `hegel_queue_eq_and_hash_ignore_internal_structure`: (no doc comment)

**`src/set/hash_trie_set/test.rs`**
- `hegel_hash_trie_set_relations_match_hash_set`: (no doc comment)

**`src/set/red_black_tree_set/test.rs`**
- `hegel_rbt_set_relations_match_btree_set`: (no doc comment)

**`src/stack/test.rs`**
- `hegel_stack_model_matches_vec`: (no doc comment)

**`src/vector/test.rs`**
- `hegel_vector_model_matches_vec`: (no doc comment)
- `hegel_vector_persistence`: (no doc comment)
- `hegel_vector_new_with_bits_no_panic`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-07-19: predecessor base commit `d7c1205c81f1` (Fix new clippy warnings.).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/rpds.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1. The model tests sampled keys from a `std::collections::HashMap` in iteration order, which varies per run; hegeltest 0.44 detects non-deterministic generation and fails the test, so `model_key_or_any` now sorts the keys before sampling (same distribution, deterministic).
