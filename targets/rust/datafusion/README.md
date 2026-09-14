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
