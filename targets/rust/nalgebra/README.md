# nalgebra

[dimforge/nalgebra](https://github.com/dimforge/nalgebra).

## What is tested

**`tests/core/matrix.rs`**
- `transpose_involution_dyn`: (no doc comment)
- `product_transpose_is_reversed_transpose_product`: (no doc comment)

**`tests/linalg/cholesky.rs`**
- `cholesky_reconstructs_spd_matrix`: (no doc comment)

**`tests/linalg/eigen.rs`**
- `symmetric_eigen_pairs_satisfy_eigen_equation`: (no doc comment)

**`tests/linalg/inverse.rs`**
- `inverse_composes_to_identity`: (no doc comment)
- `inverse_composes_to_identity_static4`: (no doc comment)

**`tests/linalg/lu.rs`**
- `lu_reconstructs_permuted_matrix`: (no doc comment)
- `lu_solve_residual_is_small`: (no doc comment)
- `determinant_product_rule`: (no doc comment)
- `determinant_of_transpose_matches`: (no doc comment)

**`tests/linalg/qr.rs`**
- `qr_reconstructs_matrix`: (no doc comment)
- `qr_q_is_orthonormal`: (no doc comment)

**`tests/linalg/svd.rs`**
- `svd_reconstructs_matrix`: (no doc comment)
- `svd_singular_values_nonnegative_and_descending`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-06-30: predecessor base commit `3320ecca21dc` (fix: Cholesky::new returns None non-positive-definite complex matri...).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/nalgebra.patch`).
- 2026-09-11: imported into the zoo; ported to hegeltest 0.44.1.
