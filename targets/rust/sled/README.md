# sled

[spacejam/sled](https://github.com/spacejam/sled).

## What is tested

**`tests/test_tree.rs`**
- `hegel_tree_matches_btreemap_model`: (no doc comment)
- `hegel_apply_batch_matches_model`: (no doc comment)
- `hegel_range_matches_model`: (no doc comment)
- `hegel_double_ended_iteration_matches_model`: (no doc comment)
- `hegel_compare_and_swap_semantics`: (no doc comment)
- `hegel_reopen_preserves_contents`: (no doc comment)
- `hegel_scan_prefix_matches_model`: (no doc comment)
- `hegel_pop_in_range_drains_range_in_order`: (no doc comment)
- `hegel_checksum_is_history_independent`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-04-04: predecessor base commit `e449d17111f4` (Add benchmark for memory and throughput of a fanout=3 data set for ...).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/sled.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
