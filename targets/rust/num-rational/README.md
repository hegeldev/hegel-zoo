# num-rational

[rust-num/num-rational](https://github.com/rust-num/num-rational).

## What is tested

**`src/tests/arith.rs`**
- `hegel_add_commutes`: (no doc comment)
- `hegel_mul_commutes`: (no doc comment)
- `hegel_add_associates`: (no doc comment)
- `hegel_mul_associates`: (no doc comment)
- `hegel_mul_distributes_over_add`: (no doc comment)
- `hegel_additive_inverse`: (no doc comment)
- `hegel_multiplicative_inverse`: (no doc comment)
- `hegel_ops_preserve_reduced_invariant`: (no doc comment)
- `hegel_op_assign_matches_binop`: (no doc comment)
- `hegel_rem_is_truncated_division_remainder`: (no doc comment)
- `hegel_trunc_fract_identity`: (no doc comment)
- `hegel_floor_ceil_round_bounds`: (no doc comment)
- `hegel_pow_matches_repeated_multiplication`: (no doc comment)
- `hegel_checked_ops_agree_with_bigint_oracle`: (no doc comment)

**`src/tests.rs`**
- `hegel_new_produces_reduced_form`: (no doc comment)
- `hegel_pin_new_negation_overflow`: (no doc comment)
- `hegel_cmp_matches_i128_cross_multiplication`: (no doc comment)
- `hegel_pin_cmp_equal_numerator_mixed_sign_denominators`: (no doc comment)
- `hegel_pin_cmp_div_mod_floor_overflow`: (no doc comment)
- `hegel_hash_agrees_with_eq_for_unreduced_fractions`: (no doc comment)
- `hegel_display_from_str_roundtrip_i64`: (no doc comment)
- `hegel_display_from_str_roundtrip_big`: (no doc comment)
- `hegel_from_str_never_panics`: (no doc comment)
- `hegel_from_float_to_f64_roundtrip`: (no doc comment)
- `hegel_i64_to_f64_is_correctly_rounded`: (no doc comment)
- `hegel_big_to_f64_is_correctly_rounded`: (no doc comment)
- `hegel_approximate_float_never_panics_and_stays_close`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-07-07: predecessor base commit `cf95d6719c58` (Merge pull request #154 from cuviper/modules).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/num-rational.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
