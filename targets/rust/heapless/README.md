# heapless

[rust-embedded/heapless](https://github.com/rust-embedded/heapless).

## What is tested

**`src/binary_heap.rs`**
- `hegel_binary_heap_max_model`: (no doc comment)
- `hegel_binary_heap_min_pop_order`: Heap-sort differential: pushing arbitrary values into a `Min` heap and popping them all must yield exactly the input sorted ascending (`std`'s sort is the oracle).

**`src/deque.rs`**
- `hegel_deque_model`: (no doc comment)

**`src/history_buf.rs`**
- `hegel_history_buf_model`: (no doc comment)

**`src/index_map.rs`**
- `hegel_index_map_model`: (no doc comment)

**`src/index_set.rs`**
- `hegel_index_set_insertion_order`: Insertion-order and membership property: iteration yields exactly the first occurrences of accepted values, in order; membership and len agree with a `HashSet` oracle; len never exceeds the capacity.
- `hegel_index_set_algebra_matches_std`: Set-algebra differential: `union`, `intersection`, `difference`, `symmetric_difference`, `is_subset`, `is_superset` and `is_disjoint` must agree with `std::collections::HashSet` on the same elements.

**`src/linear_map.rs`**
- `hegel_linear_map_model`: (no doc comment)

**`src/string/mod.rs`**
- `hegel_string_model`: (no doc comment)

**`src/vec/mod.rs`**
- `hegel_vec_model`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-07-19: predecessor base commit `fbe9aeb4db17` (Merge pull request #652 from sgued/rem-perf).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/heapless.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1. Four upstream `assert_eq!(x, [])` on byte slices in `#[cfg(test)]` code (`src/c_string.rs`, `src/history_buf.rs`) rewritten as `assert!(x.is_empty())`: hegeltest 0.44 pulls in `serde_json`, whose `PartialEq` impls make the literal ambiguous (E0282/E0283).
- 2026-09-12: base bumped fbe9aeb4db17 → f008da8b34aa (2026-08-08, "Merge pull request #668 from Conaclos/binaryheap_retain"; 0.9.3); 0 bug(s) still reproduce; fixed upstream: heapless/1. 462 tests pass. heapless/1 is fixed upstream (`make_contiguous` no longer sets `back = N` on a full wrapped deque; regression test added there).
