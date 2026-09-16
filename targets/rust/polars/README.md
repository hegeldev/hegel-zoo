# polars

[pola-rs/polars](https://github.com/pola-rs/polars).

## What is tested

**`src/encode.rs`**
- `row_encode_i64_is_order_preserving`: (no doc comment)
- `row_encode_f64_is_order_preserving`: (no doc comment)
- `row_encode_str_is_order_preserving`: (no doc comment)
- `row_encode_multi_column_is_lexicographic`: Multi-column rows must sort like the tuple (col0, col1) where each column uses its own sort options. The variable-length string column is put first so that the property also checks that its encoding is self-delimiting (no ordering leak across the column boundary).
- `row_encode_decode_roundtrip_i64`: (no doc comment)
- `row_encode_decode_roundtrip_f64_canonical`: The float encoding canonicalizes -0.0 to 0.0 and all NaNs to the canonical quiet NaN, so decode must return exactly the canonical form of the input (compared bit-for-bit).
- `row_encode_decode_roundtrip_str`: (no doc comment)
- `row_encode_decode_roundtrip_list_i64`: (no doc comment)
- `row_encode_no_order_keeps_uniqueness_str`: NO_ORDER drops order preservation but is documented to keep uniqueness: two rows encode to the same bytes iff the values are equal.

## Oracles

## Not tested

## History

- 2026-07-23: predecessor base commit `1f6362635a59` (fix: Do not CSE non-column height expr on streaming engine (#28480)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/polars.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped 1f6362635a59 → ccff55e4f507 (2026-09-12, "perf: Improve cache-removal and join-order cost estimates (#29263)"; 0.55.1); 0 bug(s) still reproduce. 10 tests pass.
- 2026-09-13: base bumped ccff55e4f507 → a8811c306720 (2026-09-13, "perf: Use stats to decide cross join buffering side (#29270)"; 0.55.1); 0 bug(s) still reproduce. 10 tests pass.
- 2026-09-13: base bumped a8811c306720 → d84c1d4f28b0 (2026-09-13, "feat: Fix tpch SQL issues  (#29269)"; 0.55.1); 0 bug(s) still reproduce. 10 tests pass.
- 2026-09-14: base bumped d84c1d4f28b0 → effe7e05942f (2026-09-14, "perf: Push inner joins before outer joins and rewrite left-join-is-null to anti join (#29277)"; 0.55.1); 0 bug(s) still reproduce. 10 tests pass.
- 2026-09-14: base bumped effe7e05942f → abba65f36c11 (2026-09-14, "fix: Don't panic on an empty or null quantile expression input (#29240)"; 0.55.1); 0 bug(s) still reproduce. 10 tests pass.
- 2026-09-14: base bumped abba65f36c11 → efbfd1f38072 (2026-09-14, "chore: More obvious `MapChunked` storage handling (#29248)"; 0.55.1); 0 bug(s) still reproduce. 10 tests pass.
- 2026-09-14: base bumped efbfd1f38072 → 85ee8753973a (2026-09-14, "perf: Don't clone the full frame per arm in when/then/otherwise (#29258)"; 0.55.1); 0 bug(s) still reproduce. 10 tests pass.
- 2026-09-14: base bumped 85ee8753973a → 7d80fdf9bb7b (2026-09-14, "fix(python): Fix comparison expression method comment (#29257)"; 0.55.1); 0 bug(s) still reproduce. 10 tests pass.
- 2026-09-14: base bumped 7d80fdf9bb7b → 6a00e2197edd (2026-09-14, "perf: Lower uncorrelated subqueries to semi joins and push semi/anti joins below inner joins (#29289)"; 0.55.1); 0 bug(s) still reproduce. 10 tests pass.
- 2026-09-15: base bumped 6a00e2197edd → a30671c1f938 (2026-09-15, "test(python): Fix the stalling `test_fused_many_morsels_and_skew` test (#29290)"; 0.55.1); 0 bug(s) still reproduce. 10 tests pass.
- 2026-09-15: base bumped a30671c1f938 → 1d87e9509eea (2026-09-15, "ci: Bump build deps used in ARM64 Windows release pipeline (#29280)"; 0.55.1); 0 bug(s) still reproduce. 10 tests pass.
- 2026-09-15: base bumped 1d87e9509eea → 4fff6cc4676e (2026-09-15, "feat: Binning functions (#28888)"; 0.55.1); 0 bug(s) still reproduce. 10 tests pass.
- 2026-09-15: base bumped 4fff6cc4676e → 5267819479ed (2026-09-15, "chore(rust): Update rustls dependency to version `0.23.45` (#29303)"; 0.55.1); 0 bug(s) still reproduce. 10 tests pass.
- 2026-09-15: base bumped 5267819479ed → 1bcbd4fef4ff (2026-09-15, "fix: Resolve arithmetic `Struct` supertypes per-field (#29261)"; 0.55.1); 0 bug(s) still reproduce. 10 tests pass.
- 2026-09-15: base bumped 1bcbd4fef4ff → d68e93010fed (2026-09-15, "fix(rust): Fix musl Python build (#29306)"; 0.55.1); 0 bug(s) still reproduce. 10 tests pass.
- 2026-09-15: base bumped d68e93010fed → 07988fc518f2 (2026-09-15, "perf: Use HTTP suffix range for Parquet size and footer (#29308)"; 0.55.1); 0 bug(s) still reproduce. 10 tests pass.
- 2026-09-15: base bumped 07988fc518f2 → 5dcf491ab638 (2026-09-15, "fix(python): Fix panic in scan_iceberg for snapshot_id before a schema change (#28895)"; 0.55.1); 0 bug(s) still reproduce. 10 tests pass.
- 2026-09-15: base bumped 5dcf491ab638 → 2dacb0d42f9a (2026-09-15, "chore(rust): Remove unused `utf8_to_timestamp_scalar` (#29264)"; 0.55.1); 0 bug(s) still reproduce. 10 tests pass.
- 2026-09-15: base bumped 2dacb0d42f9a → f0551e00194a (2026-09-15, "chore: Bump object_store crate to 0.14.2 (#29317)"; 0.55.1); 0 bug(s) still reproduce. 10 tests pass.
- 2026-09-16: base bumped f0551e00194a → b3e18daed873 (2026-09-16, "fix: Incorrect height in multi-input GroupBy (#29332)"; 0.55.1); 0 bug(s) still reproduce. 10 tests pass.
- 2026-09-16: base bumped b3e18daed873 → 77cc5fac18b0 (2026-09-16, "chore: Mark test as slow (#29336)"; 0.55.1); 0 bug(s) still reproduce. 10 tests pass.
- 2026-09-16: base bumped 77cc5fac18b0 → 9c4d5e09e694 (2026-09-16, "chore!: Deprecate cut/qcut (#29329)"; 0.55.1); 0 bug(s) still reproduce. 10 tests pass.
