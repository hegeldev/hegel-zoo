# bigdecimal

[akubera/bigdecimal-rs](https://github.com/akubera/bigdecimal-rs).

## What is tested

**`src/impl_cmp.rs`**
- `cmp_agrees_with_rational_oracle`: Property: `Ord::cmp` orders decimals the same way exact rational arithmetic does. Evidence: Ord doc-comment example ("Complete ordering implementation for BigDecimal") — comparisons are by numeric value, independent of representation.
- `eq_agrees_with_rational_oracle`: Property: `PartialEq` (a separate implementation from Ord) agrees with exact rational equality. Evidence: unit tests `test_eq` / `test_hash_equal` compare different representations of the same value as equal. Half of the generated pairs are made value-equal (scale padding) so equality is exercised, not just inequality.
- `cmp_matches_f64`: Property: comparison of float-derived decimals matches f64's own ordering (floats convert exactly via from_f64). Ported from the (property_tests-gated) proptest `cmp_matches_f64`.

**`src/impl_fmt.rs`**
- `display_then_parse_roundtrips`: Property: `Display` output re-parses to an equal value. Evidence: existing unit test `test_parse_roundtrip` and the (property_tests-gated) proptest `roudtrip_to_str_and_back_*`.
- `lower_exp_then_parse_roundtrips`: Property: `{:e}` (LowerExp) output re-parses to an equal value. Evidence: LowerExp is implemented via the same exponential formatter used by Display for extreme values; parser accepts `e` exponents (impl_num::from_str_radix).
- `scientific_notation_then_parse_roundtrips`: Property: `to_scientific_notation()` output re-parses to an equal value. Evidence: existing (property_tests-gated) proptest `scientific_notation_roundtrip`, broadened beyond f64 values.
- `engineering_notation_then_parse_roundtrips`: Property: `to_engineering_notation()` output re-parses to an equal value. Evidence: existing (property_tests-gated) proptest `engineering_notation_roundtrip`, broadened beyond f64 values.
- `plain_string_then_parse_roundtrips`: Property: `to_plain_string()` output re-parses to an equal value. Evidence: doc examples for `to_plain_string`. The scale is bounded because the docs warn the plain representation of very large exponents "may cause out-of-memory errors".
- `float_formatting_with_precision_matches_f64`: Property: formatting a float-derived BigDecimal with a requested precision matches std's float formatting exactly. Evidence: existing (property_tests-gated) proptest `float_formatting`; BigDecimal::from_f64 is exact, and std formats the exact decimal expansion of the double. Zero is excluded because f64 has a signed zero ("-0.0") which BigDecimal cannot represent.

**`src/impl_trait_from_str.rs`**
- `parsing_arbitrary_strings_never_panics`: Property: parsing never panics — bad input must produce an `Err`, never a crash. Evidence: `FromStr::from_str` returns `Result<BigDecimal, ParseBigDecimalError>`, and the unit tests above expect specific errors for malformed strings. Inputs mix arbitrary unicode with "almost numeric" strings that reach deeper into the parser (signs, underscores, dots, oversized exponents).

**`src/lib.tests.rs`**
- `normalized_preserves_value`: Property: `normalized()` does not change the value of the decimal. Evidence: doc-comment on `normalized` ("Return a new BigDecimal after removing trailing zeros") and the `normalize` unit tests, all of which preserve the numeric value. The generator deliberately emphasizes the two ingredients of the boundary case: coefficients with trailing zeros (multiply by a small power of ten) and scales at/near i64::MIN (normalizing *subtracts* the trailing-zero count from the scale).
- `normalized_is_canonical`: Property: `normalized()` produces the canonical representation: no trailing zeros in the coefficient (zero becomes 0e0), so normalizing twice gives the identical representation. Evidence: `normalize` unit tests assert exact (int_val, scale) pairs with trailing zeros stripped, e.g. (10, 2) => (1, 1), (0, -3) => (0, 0).
- `addition_commutes`: Property: addition is commutative: a + b == b + a. Evidence: BigDecimal models exact decimal arithmetic (README: "Allows storing any real number to arbitrary precision; avoids storing errors of binary floating-point").
- `add_then_sub_roundtrips`: Property: subtraction undoes addition exactly: (a + b) - b == a. Evidence: addition/subtraction of decimals is exact (no rounding occurs in add/sub; scales are aligned), see impl_ops_add/impl_ops_sub.
- `multiplication_agrees_with_rational_oracle`: Property: multiplication agrees with exact rational arithmetic. Evidence: multiplication is documented/implemented as exact (scales add, coefficients multiply — impl_ops_mul.rs).
- `square_equals_self_times_self`: Property: `square()` equals multiplying the value by itself. Evidence: doc-comment on `square`: "No rounding or truncating of digits; this is the full result of the squaring operation", plus the existing proptest `square` (which only exercised f32-derived values). Scale is limited to i64::MAX/2 because the result's scale (2×scale) must itself fit in an i64.
- `cube_equals_self_times_self_times_self`: Property: `cube()` equals multiplying the value by itself twice. Evidence: doc-comment on `cube` ("full result of the cubing operation") and the `test_cube` unit tests. Scale is limited to i64::MAX/3 because the result's scale (3×scale) must itself fit in an i64.
- `double_and_half_are_inverses`: Property: `half()` is the inverse of `double()` (and vice versa). Evidence: doc-comments "Multiply decimal by 2 (efficiently)" / "Divide decimal by 2 (efficiently)". Scale is kept below i64::MAX because halving an odd coefficient increases the scale by one (documented in `half`), which must not overflow.
- `is_integer_agrees_with_truncation`: Property: `is_integer()` is true exactly when truncating all fractional digits does not change the value. Evidence: doc-comment "Return true if this number has zero fractional part (is equal to an integer)"; RoundingMode::Down is documented as truncation ("Always round towards zero").
- `sqrt_of_negative_is_none`: Property: sqrt of a negative number is None. Evidence: doc-comment on `sqrt`: "If the value is < 0, None is returned".
- `sqrt_squared_is_close_to_original`: Property: sqrt(x)² is within the documented precision of x. Evidence: `sqrt` docs say it computes with default precision (100 significant digits). A half-ulp error on the 100-digit root yields a relative error in the square well below 1e-95.
- `equal_values_have_equal_hashes`: Property: values that are equal must have equal hashes. Evidence: the Hash impl (lib.rs) canonicalizes trailing zeros, and unit tests test_hash_equal/test_hash_equal_scale check specific pairs; padding the scale with `with_scale` preserves the value.
- `add_overloads_agree`: Property: all `+` overloads (val/ref/assign, either side) agree. Ported from proptest `add_ref_*`.
- `sub_overloads_agree`: Property: subtraction overloads are consistent and anti-commute: n - d == -(d - n). Ported from proptest `sub_*`.
- `mul_overloads_agree`: Property: all `*` overloads agree and multiplication commutes with negation. Ported from proptest `mul_*`.
- `div_overloads_agree_and_multiply_back`: Property: integer / decimal division overloads agree, and the quotient multiplied back differs from the numerator by less than 1e-60 (the quotient carries 100 significant digits and |n| < 2^127 ≈ 1.7e38, so the error is bounded by ~1.7e-62). The decimal divisor is non-zero because `Div` explicitly panics with "Division by zero". Ported from proptest `div_*`.
- `div_assign_agrees_with_div_for_any_divisor`: Property: `d /= n` behaves exactly like `d = d / n` for *every* integer divisor, including zero — same value, or both panic. Evidence: Rust's operator convention (`DivAssign` is "the division assignment operator /=") and the crate's own gated proptests, which assert Div/DivAssign agreement for the other operators without excluding any divisor.
- `float_div_overloads_agree`: Property: float / decimal division overloads agree (including non-normal floats, which the impl short-circuits to zero for all overloads alike). Ported from proptest `div_f64`.
- `bigdecimal_agrees_with_rational_model`: (no doc comment)

**`src/lib.tests.with_scale_round.rs`**
- `floor_and_ceiling_bracket_the_value`: Property: Floor and Ceiling rounding bracket the original value, and differ by at most one unit in the last place of the new scale. Evidence: RoundingMode doc-comments — Ceiling "Towards +∞", Floor "Towards -∞".
- `rounding_error_is_less_than_one_ulp`: Property: for every rounding mode, `with_scale_round` returns a value with exactly the requested scale, and the rounding error is strictly less than one unit in the last place of that scale. Evidence: with_scale_round doc-comment ("Return a new BigDecimal after shortening the digits and rounding") and its doc examples; all seven RoundingMode variants round to a neighboring multiple of 10^-new_scale (rounding.rs doc-comments).
- `rounding_to_larger_scale_is_exact`: Property: rounding to a larger scale (more fractional digits) is exact — it never changes the value, whatever the rounding mode. Evidence: with_scale doc-comment ("If the new_scale is lower than the current value ... digits will be dropped" — implying higher scale only pads) and the Ordering::Greater branch of with_scale_round, which only multiplies by a power of ten.

## Oracles

## Not tested

## History

- 2025-12-27: predecessor base commit `7f0243e73702` (Begin v0.4.11 development).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/bigdecimal.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: 10× budget run (`--test-cases 1000`) found two failures the default budget had
  missed: `normalized_is_canonical` hits the known bigdecimal/1 overflow (scale i64::MIN), and
  `engineering_notation_then_parse_roundtrips` is a new bug, **bigdecimal/4** — at scale i64::MAX
  `to_engineering_notation()` prints `100e-9223372036854775809`, which the crate's `FromStr`
  rejects with "Exponent overflow". Both pinned as intermittent expected failures.
- 2026-09-20: base bumped 7f0243e73702 → 120166b6faaa (2026-09-20, "use the dep: syntax, in order to remove a duplicate feature name"; 0.5.0+dev); 2 bug(s) still reproduce; intermittent, not seen this run: bigdecimal/4; 1 ignored reproducer(s) not run. 1346 tests pass.
