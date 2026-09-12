# num-complex

[rust-num/num-complex](https://github.com/rust-num/num-complex).

## What is tested

**`src/lib.rs`**
- `prop_add_commutative`: (no doc comment)
- `prop_additive_inverse_exact`: (no doc comment)
- `prop_add_associative`: (no doc comment)
- `prop_mul_commutative`: (no doc comment)
- `prop_mul_distributive`: (no doc comment)
- `prop_mul_div_roundtrip`: (no doc comment)
- `prop_mul_inv_is_one`: (no doc comment)
- `prop_conj_involution_exact`: (no doc comment)
- `prop_conj_multiplicative_exact`: (no doc comment)
- `prop_mul_conj_is_norm_sqr`: (no doc comment)
- `prop_norm_squared_matches_norm_sqr`: (no doc comment)
- `prop_norm_bounds`: (no doc comment)
- `prop_norm_multiplicative`: (no doc comment)
- `prop_polar_roundtrip`: (no doc comment)
- `prop_exp_ln_roundtrip`: (no doc comment)
- `prop_ln_exp_roundtrip`: (no doc comment)
- `prop_sqrt_squares_to_input`: (no doc comment)
- `prop_sqrt_of_nonzero_is_nonzero`: (no doc comment)
- `prop_sqrt_principal_branch`: (no doc comment)
- `prop_powu2_is_mul`: (no doc comment)
- `prop_powf_half_matches_sqrt`: (no doc comment)
- `prop_display_fromstr_roundtrip`: (no doc comment)
- `prop_fromstr_never_panics`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-07-07: predecessor base commit `fb5dca6f915c` (Merge pull request #161 from cuviper/rename-head).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/num-complex.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
