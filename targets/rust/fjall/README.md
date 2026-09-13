# fjall

[fjall-rs/fjall](https://github.com/fjall-rs/fjall).

## What is tested

**`tests/batch.rs`**
- `batch_commit_matches_sequential_model`: (no doc comment)

**`tests/blob_kv_simple.rs`**
- `blob_roundtrip_matches_model`: (no doc comment)

**`tests/db_open.rs`**
- `accepted_keyspace_names_survive_reopen`: (no doc comment)

**`tests/journal_large_value.rs`**
- `insert_within_documented_key_limit_does_not_panic`: (no doc comment)

**`tests/keyspace_recover.rs`**
- `recover_matches_model`: (no doc comment)

**`tests/keyspace_snapshot.rs`**
- `snapshot_repeatable_read_matches_model`: (no doc comment)

**`tests/model.rs`**
- `database_matches_btreemap_model`: (no doc comment)

**`tests/prefix_complex.rs`**
- `prefix_matches_model`: (no doc comment)
- `prefix_agrees_with_prefix_to_range`: (no doc comment)
- `range_matches_model`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-07-18: predecessor base commit `6debe706dbc5` (3.1.8).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/fjall.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped 6debe706dbc5 → 3adaa50261c9 (2026-08-30, "3.1.10"; 3.1.10); 1 bug(s) still reproduce. 215 tests pass.
