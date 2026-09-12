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
