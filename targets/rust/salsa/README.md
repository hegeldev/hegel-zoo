# salsa

[salsa-rs/salsa](https://github.com/salsa-rs/salsa).

## What is tested

**`tests/accumulate.rs`**
- `accumulated_logs_match_current_inputs`: (no doc comment)

**`tests/cycle.rs`**
- `default_cycle_handling_panics_iff_cycle_reachable`: (no doc comment)

**`tests/dataflow.rs`**
- `incremental_dataflow_matches_fresh_db`: (no doc comment)

**`tests/durability.rs`**
- `add3_matches_sum_across_durability_changes`: (no doc comment)

**`tests/hello_world.rs`**
- `incremental_computation_matches_fresh_db`: (no doc comment)

**`tests/interned-structs.rs`**
- `interned_data_roundtrips`: Interning round-trips: reading the field back returns exactly the data that was interned.
- `interned_identity_iff_equal_data`: Interned handles are equal exactly when the interned data is equal (within one database). Multi-field version also checks that the field *boundary* matters, generalizing `interning_returns_equal_keys_for_equal_data_multi_field`'s ("Hello, World", "") vs ("Hello, ", "World") example.

**`tests/lru.rs`**
- `lru_eviction_never_changes_results`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-07-22: predecessor base commit `dcbcc7082c3b` (chore: release v0.28.1 (#1248)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/salsa.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped dcbcc7082c3b → e021c01d4939 (2026-09-07, "chore: Update taiki-e/install-action action to v2.87.2 (#1309)"; 0.28.2); 1 bug(s) still reproduce; add/add conflicts in Cargo.toml resolved by keeping both sides. 223 tests pass.
- 2026-09-14: base bumped e021c01d4939 → c6ae3973824d (2026-09-14, "Remove assemble support from interneds (#1314)"; 0.28.2); 1 bug(s) still reproduce. 223 tests pass.
