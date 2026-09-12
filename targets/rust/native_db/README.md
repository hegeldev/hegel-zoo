# native_db

[vincent-herlemont/native_db](https://github.com/vincent-herlemont/native_db).

## What is tested

**`tests/query/auto_update_sk.rs`**
- `pbt_db_matches_model_machine`: (no doc comment)

**`tests/query/insert_get_pk.rs`**
- `pbt_insert_get_roundtrip`: (no doc comment)
- `pbt_insert_duplicate_pk_rejected_db_unchanged`: (no doc comment)

**`tests/query/insert_get_sk.rs`**
- `pbt_unique_secondary_key_enforced`: (no doc comment)

**`tests/scan.rs`**
- `pbt_primary_range_scan_matches_model`: (no doc comment)
- `pbt_primary_range_to_inclusive_includes_boundary`: (no doc comment)
- `pbt_secondary_start_with_matches_model`: (no doc comment)

**`tests/signed_integer_ordering.rs`**
- `pbt_i64_secondary_scan_sorted`: (no doc comment)
- `pbt_f64_secondary_scan_sorted`: (no doc comment)

**`tests/transaction.rs`**
- `pbt_commit_abort_atomicity`: (no doc comment)

**`tests/util.rs`**
- `pbt_reopen_persistence`: (no doc comment)

## Oracles

## Not tested

## History

- 2025-10-10: predecessor base commit `b9554fdabbdd` (chore(deps): update rust crate cc to 1.2.41).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/native_db.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
