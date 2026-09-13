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
