# indexmap

[indexmap-rs/indexmap](https://github.com/indexmap-rs/indexmap).

## What is tested

**`tests/quick.rs`**
- `map_model`: (no doc comment)
- `set_model`: (no doc comment)
- `insert_only_iteration_matches_insertion_order`: For an insert-only sequence, iteration order is first-occurrence insertion order and each key holds the last value inserted for it. Full-range i64 keys (the quickcheck version only uses u32 keys with unit values).
- `swap_remove_vs_shift_remove`: swap_remove and shift_remove agree on the returned value and on the remaining key-value *set*; they differ only in order, each matching its exact Vec counterpart (Vec::swap_remove / Vec::remove).
- `insert_existing_key_keeps_position`: Inserting an existing key updates the value in place: same length, same index for the key, iteration order completely unchanged, and the old value is returned.
- `split_off_partitions_in_order`: split_off partitions the entries at the given index: the head keeps [0, at) and the tail gets [at, len), both in the original order, and hash lookups work on both halves.
- `binary_search_keys_agrees_with_get_index_of`: After sorting by keys, binary_search_keys agrees with get_index_of for present keys and returns a correct insertion point for absent keys.
- `set_union_order`: union yields self's values in order, then other's unique values in order; as a set it equals the HashSet union.
- `set_intersection_order`: intersection yields values in self's order; as a set it equals the HashSet intersection.
- `set_difference_order`: difference yields values in self's order; as a set it equals the HashSet difference.
- `set_symmetric_difference_order`: symmetric_difference yields self-only values in self's order, then other-only values in other's order; as a set it equals the HashSet symmetric difference.

## Oracles

## Not tested

## History

- 2026-07-10: predecessor base commit `571943c5b3ec` (Merge pull request #445 from maxtaran2010/fix/typos).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/indexmap.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-12: base bumped 571943c5b3ec → 41a870887c4c (2026-09-05, "Merge pull request #450 from cuviper/macros"; 2.14.2); 0 bug(s) still reproduce. 235 tests pass.
