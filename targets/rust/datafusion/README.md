# datafusion

[apache/datafusion](https://github.com/apache/datafusion).

## What is tested

**`src/rounding.rs`**
- `prop_next_up_next_down_match_std`: Property: `next_up`/`next_down` agree bit-for-bit with the std library `f64::next_up`/`f64::next_down` (and the f32 versions), except at ±0.0, where this implementation deliberately steps through the signed zeros one at a time (`-0.0 -> +0.0 -> TINY`, mirrored for `next_down`), which the unit tests above pin.
- `prop_next_up_next_down_are_inverses`: Property: on non-NaN input, `next_up` is the strict successor in the IEEE total order (`total_cmp`) and `next_down` its exact inverse, and vice versa — so `next_down(next_up(x))` returns `x` bit-for-bit.

**`src/scalar/mod.rs`**
- `prop_scalar_eq_ord_hash_consistency`: Property: `ScalarValue`'s manual `PartialEq`, `PartialOrd` and `Hash` implementations are mutually consistent: `eq` is reflexive (bitwise for floats, so this includes NaN), `partial_cmp` is antisymmetric, `a == b` implies both `partial_cmp == Some(Equal)` and equal hashes, and within a single data type `Some(Equal)` implies `eq`.
- `prop_scalar_to_array_of_size_roundtrip`: Property: `to_array_of_size` produces an array with the scalar's data type where every index round-trips back to the original scalar via `try_from_array`.
- `prop_scalar_iter_to_array_roundtrip`: Property: `iter_to_array` over same-typed scalars concatenates them in order — reading back every index with `try_from_array` returns the original scalar.
- `prop_scalar_add_checked_matches_native_checked_add`: Property: `add_checked` on integer scalars matches native `checked_add` — same value on success, an error exactly when the native operation overflows, and null propagation when either side is null.
- `prop_scalar_sub_checked_matches_native_checked_sub`: Property: `sub_checked` on integer scalars matches native `checked_sub`, with error on overflow and null propagation.
- `prop_scalar_add_wrapping_matches_native_wrapping_add`: Property: the wrapping `add` on integer scalars matches native `wrapping_add` (this exercises the in-place fast path against the arrow kernel fallback), with null propagation.

**`src/stats.rs`**
- `prop_precision_usize_add_oracle`: Property: `Precision::<usize>::add` is commutative, computes the saturating sum, is `Exact` exactly when both inputs are exact and the native addition does not overflow, and is `Absent` when either input is absent.
- `prop_precision_usize_sub_oracle`: Property: `Precision::<usize>::sub` computes the saturating difference, is `Exact` exactly when both inputs are exact and the native subtraction does not underflow, and is `Absent` when either input is absent.
- `prop_precision_usize_multiply_oracle`: Property: `Precision::<usize>::multiply` is commutative, computes the saturating product, is `Exact` exactly when both inputs are exact and the native multiplication does not overflow, and is `Absent` when either input is absent.
- `prop_precision_usize_min_max_consistency`: Property: `Precision::min`/`Precision::max` agree with `std::cmp` on the wrapped values, are commutative, propagate exactness only when both inputs are exact, are `Absent` when either input is absent, and satisfy `min <= max`.

**`src/table_reference.rs`**
- `prop_table_reference_quoted_string_roundtrip`: Property: a `TableReference` built from arbitrary non-empty parts round-trips through `to_quoted_string` and `parse_str`: quoting escapes everything (including embedded `"` and `.`) such that parsing recovers the identical reference. Empty parts are excluded: they cannot round-trip (see the KNOWN FAILURE test `prop_table_reference_empty_table_part_roundtrip` below).
- `prop_table_reference_empty_table_part_roundtrip`: KNOWN FAILURE (bug): `quote_identifier("")` leaves the empty string unquoted, so a reference with an empty table part serializes to e.g. `"schema."`, which does not parse back: without the `sql` feature the trailing empty identifier is dropped (`Partial { schema, table: "" }` becomes `Bare { table: "schema" }`), and with the `sql` feature the string fails to parse and falls back to `Bare { table: "schema." }`. An empty identifier would need to be quoted as `""` to survive the round-trip. This test pins the bug deterministically; the general round-trip property above excludes empty parts for this reason.

## Oracles

## Not tested

## History

- 2026-07-23: predecessor base commit `1c8295c992c5` (feat: Support Union type in approx_distinct (#23714)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/datafusion.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped 1c8295c992c5 → a407990b4443 (2026-09-12, "fix: out-of-bounds read in ArrowBytesMap on a short/long hash collision (#25218)"; 55.0.0); 1 bug(s) still reproduce; add/add conflicts in datafusion/common/src/scalar/mod.rs, datafusion/common/src/stats.rs resolved by keeping both sides. 623 tests pass.
- 2026-09-13: base bumped a407990b4443 → 82335b426d88 (2026-09-13, "feat: serialize ASOF join plans (#23832)"; 55.0.0); 1 bug(s) still reproduce. 623 tests pass.
- 2026-09-13: base bumped 82335b426d88 → 9082d6b10c29 (2026-09-13, "fix: discard parquet bounds when row group statistics are missing (#25228)"; 55.0.0); 1 bug(s) still reproduce. 623 tests pass.
- 2026-09-13: base bumped 9082d6b10c29 → 681705e6fdc4 (2026-09-13, "fix: reject groups accumulator for bit_xor(DISTINCT) (#24989)"; 55.0.0); 1 bug(s) still reproduce. 623 tests pass.
- 2026-09-13: base bumped 681705e6fdc4 → d9646f49fb6f (2026-09-13, "ci: share extended test commands through xtask (#25256)"; 55.0.0); 1 bug(s) still reproduce. 623 tests pass.
- 2026-09-13: base bumped d9646f49fb6f → e4c4fa43d29d (2026-09-13, "Fix `Numeric` signature coercion to properly handle null types (#24988)"; 55.0.0); 1 bug(s) still reproduce. 623 tests pass.
- 2026-09-13: base bumped e4c4fa43d29d → c5257f0540b9 (2026-09-13, "fix: preserve computed projections in unions_to_filter (#25074)"; 55.0.0); 1 bug(s) still reproduce. 623 tests pass.
- 2026-09-13: base bumped c5257f0540b9 → f2b2ffd400cc (2026-09-13, "chore: update version 55.1.0 (#25070) (#25200)"; 55.1.0); 1 bug(s) still reproduce. 623 tests pass.
- 2026-09-13: base bumped f2b2ffd400cc → 15f32dd7ac75 (2026-09-13, "Reduce binary size of `ScalarUDFImpl` default impls (#24966)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-14: base bumped 15f32dd7ac75 → 38d58ed09db2 (2026-09-14, "fix(physical-plan): honor distinct soft limits in SingleHashAggregateStream (#25158)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-14: base bumped 38d58ed09db2 → c2cf28940b1e (2026-09-14, "Reduce repetitive string formatting in push_projection_dedupl (#25236)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-14: base bumped c2cf28940b1e → 17c6d74deb11 (2026-09-14, "fix: preserve target extension metadata in INSERT (#24971)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-14: base bumped 17c6d74deb11 → 7b00b63e048b (2026-09-14, "fix: stabilize grouped correlation with centered moments (#24953)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-14: base bumped 7b00b63e048b → 85d4cbb0a9a8 (2026-09-14, "Support ORDER BY ALL for projected expressions (#25243)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-14: base bumped 85d4cbb0a9a8 → c14976481ea5 (2026-09-14, "fix: preserve missing Parquet null counts (#25242)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-14: base bumped c14976481ea5 → 6bbd3f42c3e8 (2026-09-14, "chore: Update Rust toolchain to 1.98.1 (#25295)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-15: base bumped 6bbd3f42c3e8 → a7305f1cd5c1 (2026-09-15, "minor: Remove empty public module `datafusion::physical_plan::joins::chain (#25286)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-15: base bumped a7305f1cd5c1 → add66e424fa1 (2026-09-15, "refactor: clean up aggregation planning (#25104)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-15: base bumped add66e424fa1 → cee7bae63ba1 (2026-09-15, "Support predicate subqueries in projections (#24972)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-15: base bumped cee7bae63ba1 → 745b1ec218d4 (2026-09-15, "fix: update rustls to address RUSTSEC-2026-0285 (#25309)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-15: base bumped 745b1ec218d4 → 133111f43a57 (2026-09-15, "fix: report a negative array_resize size as a user error (#25179)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-15: base bumped 133111f43a57 → 2178f275ed51 (2026-09-15, "perf: Optimize prefix-group processing in `PartialSortExec` (#24979)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-15: base bumped 2178f275ed51 → ec97d1c902bf (2026-09-15, "Push down topk through join (#21621)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-15: base bumped ec97d1c902bf → b376290aad68 (2026-09-15, "fix: map pushed-down filter columns by position instead of by name (#25259)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-15: base bumped b376290aad68 → 7917a9a65a03 (2026-09-15, "bench: cover dictionary group keys with a shared values array (#25198)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-15: base bumped 7917a9a65a03 → a0631edb7748 (2026-09-15, "perf: reuse cached dictionary value hashes in vectorized_append (#25185)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-15: base bumped a0631edb7748 → 22651d24cc81 (2026-09-15, "test: bound merge fan-in in ordered aggregate spill tests (#25252)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-15: base bumped 22651d24cc81 → 8bd6629db689 (2026-09-15, "chore(deps): bump taiki-e/install-action from 2.87.6 to 2.87.12 (#25321)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-16: base bumped 8bd6629db689 → be5a96e76df9 (2026-09-16, "fix: prune row groups when file statistics collapse the predicate to a constant (#24770)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-16: base bumped be5a96e76df9 → 62dc7ac37b31 (2026-09-16, "Support INSERT OVERWRITE for MemTable (#24969)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-16: base bumped 62dc7ac37b31 → 5a4490502d53 (2026-09-16, "dev: include ASF status checks in the local lint suite (#25313)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-16: base bumped 5a4490502d53 → 86ba5e05fccc (2026-09-16, "docs(physical-optimizer): warn that wrapper rules must forward schema_check (#25357)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-16: base bumped 86ba5e05fccc → 606ae0f69738 (2026-09-16, "dev: include security auditing in the local lint suite (#25359)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-16: base bumped 606ae0f69738 → b0b547136fbe (2026-09-16, "refactor: exhaustively destructure dynamic filter and scalar subquery proto hooks (#25178)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-16: base bumped b0b547136fbe → 140c7c5a4cbd (2026-09-16, "fix: Handle nulls correctly when extracting nested arrays from nullable struct/map (#25122)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-16: base bumped 140c7c5a4cbd → e3163d46affb (2026-09-16, "feat: Support lazy per-file Parquet Arrow schema derivation (#25343)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-16: base bumped e3163d46affb → 4e907557ad7e (2026-09-16, "perf: Unify, optimize `map[k]` and `map_extract(key)` (#25201)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-17: base bumped 4e907557ad7e → dcd385e3e177 (2026-09-17, "perf: reuse one StatisticsContext across ensure_distribution (#25098)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-17: base bumped dcd385e3e177 → 0bef032a4a42 (2026-09-17, "fix(physical-plan): CoalescePartitionsExec panic on wasm32-unknown-unknown (#24890)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-17: base bumped 0bef032a4a42 → 16ecdc9bdff1 (2026-09-17, "docs: move misplaced upgrade notes to DataFusion 55 (#25331)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-17: base bumped 16ecdc9bdff1 → b300cea226af (2026-09-17, "fix: preserve UPPER and LOWER input nullability (#25381)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-17: base bumped b300cea226af → e5469e157079 (2026-09-17, "chore(docs): Fix the documentation for TableProvider::scan()'s `limit` argument (#25397)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-17: base bumped e5469e157079 → 902ee8a67e68 (2026-09-17, "feat: push dynamic filters through nested loop joins (#25030)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-17: base bumped 902ee8a67e68 → 0f8f3b9d8bb0 (2026-09-17, "perf: optimize `levenshtein` (#23543)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-17: base bumped 0f8f3b9d8bb0 → 56361282fcf1 (2026-09-17, "docs: Add SKILL.md for designing benchmark (#25285)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-17: base bumped 56361282fcf1 → a2b809331f70 (2026-09-17, "feat: simplify contradicting and redundant predicates on a column (#25207)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-17: base bumped a2b809331f70 → c4f72bad3424 (2026-09-17, "bench: SQL benchmark suite for null-aware (NOT IN) joins (#25386)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-17: base bumped c4f72bad3424 → 22f9a921781c (2026-09-17, "perf(range): avoid eager ok_or in gen_range_timestamp (#25308)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-17: base bumped 22f9a921781c → 62f039f0d958 (2026-09-17, "dev: include dependency checks in the local lint suite (#25399)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-17: base bumped 62f039f0d958 → bf67e970ba95 (2026-09-17, "Avoid normalizing hidden values in sliced list set operations (#25300)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-17: base bumped bf67e970ba95 → 3ab72e61e382 (2026-09-17, "fix: leave memory for aggregate spill replay (#25383)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-17: base bumped 3ab72e61e382 → c4f5a9e0f202 (2026-09-17, "fix: do not push filters on volatile group keys below Aggregate (#25416)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-17: base bumped c4f5a9e0f202 → edc936f38b74 (2026-09-17, "fix: `NOT IN (subquery)` with a constant value ignores NULLs in the subquery (#25348)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
- 2026-09-18: base bumped edc936f38b74 → 3a647e49dd79 (2026-09-18, "ci: skip queue-verified Dev and Dependencies jobs on pushes to main (#25443)"; 55.1.0); 1 bug(s) still reproduce. 627 tests pass.
