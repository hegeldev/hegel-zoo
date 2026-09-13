# loro

[loro-dev/loro/](https://github.com/loro-dev/loro/).

## What is tested

**`tests/loro_rust_test.rs`**
- `prop_concurrent_replicas_converge`: (no doc comment)
- `prop_snapshot_modes_preserve_state`: (no doc comment)
- `prop_all_updates_roundtrip`: (no doc comment)
- `prop_import_is_idempotent`: (no doc comment)
- `prop_text_matches_string_model`: (no doc comment)
- `prop_list_matches_vec_model`: (no doc comment)
- `prop_movable_list_matches_vec_model`: (no doc comment)
- `prop_map_matches_hashmap_model`: (no doc comment)
- `prop_checkout_reproduces_recorded_states`: (no doc comment)
- `prop_frontiers_vv_roundtrip`: (no doc comment)
- `prop_counter_zero_sum_import_batching_diverges_known_bug`: (no doc comment)
- `prop_shallow_snapshot_of_concurrent_tips_is_importable_known_bug`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-07-22: predecessor base commit `6844fc7c9d8f` (chore: version packages (#1042)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/loro.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped 6844fc7c9d8f → d5da57dd2a91 (2026-09-10, "chore: version packages"; 1.16.0); 2 bug(s) still reproduce. 556 tests pass.
