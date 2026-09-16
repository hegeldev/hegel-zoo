# redb

[cberner/redb](https://github.com/cberner/redb).

## What is tested

**`tests/basic_tests.rs`**
- `hegel_value_roundtrip_nested_composite`: (no doc comment)
- `hegel_key_compare_matches_rust_ordering`: (no doc comment)
- `hegel_fixed_width_matches_serialized_len`: (no doc comment)
- `hegel_str_range_matches_btreemap`: (no doc comment)
- `hegel_reopen_preserves_contents`: (no doc comment)
- `hegel_compact_preserves_contents`: (no doc comment)

**`tests/integration_tests.rs`**
- `hegel_model_matches_btreemap_across_transactions_and_savepoints`: (no doc comment)

**`tests/multimap_tests.rs`**
- `hegel_multimap_matches_model`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-07-17: predecessor base commit `fe0141159c73` (Sandbox just bench target).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/redb.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped fe0141159c73 → 8f08680d3d40 (2026-09-12, "Update changelog"; 4.2.0); 0 bug(s) still reproduce. 450 tests pass. The patch's `use redb::backends::InMemoryBackend;` was dropped because upstream's test file now imports it at the top.
- 2026-09-15: base bumped 8f08680d3d40 → 2de02fa48d1b (2026-09-14, "Bump version to 4.3.0"; 4.3.0); 0 bug(s) still reproduce. 450 tests pass.
- 2026-09-16: base bumped 2de02fa48d1b → 5677e5d90f7f (2026-09-16, "Shrink database files when write transactions abort"; 4.3.0); 0 bug(s) still reproduce. 459 tests pass.
