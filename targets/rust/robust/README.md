# robust

[georust/robust](https://github.com/georust/robust).

## What is tested

**`src/tests.rs`**
- `prop_orient2d_sign_matches_exact_oracle`: (no doc comment)
- `prop_orient3d_sign_matches_exact_oracle`: (no doc comment)
- `prop_incircle_sign_matches_exact_oracle`: (no doc comment)
- `prop_insphere_sign_matches_exact_oracle`: (no doc comment)
- `prop_orient2d_swap_antisymmetry`: (no doc comment)
- `prop_orient2d_cyclic_invariance`: (no doc comment)
- `prop_incircle_swap_antisymmetry`: (no doc comment)
- `prop_orient2d_orient3d_embedding_consistency`: (no doc comment)
- `prop_orient2d_exactly_collinear_is_zero`: (no doc comment)
- `prop_orient3d_exactly_coplanar_is_zero`: (no doc comment)
- `prop_incircle_exactly_cocircular_is_zero`: (no doc comment)
- `prop_insphere_exactly_cospherical_is_zero`: (no doc comment)
- `prop_predicates_never_panic_on_any_floats`: (no doc comment)
- `prop_orient2d_exactly_collinear_is_zero_subnormal_scale`: (no doc comment)
- `prop_orient2d_oracle_subnormal_scale`: (no doc comment)

## Oracles

## Not tested

## History

- 2025-05-09: predecessor base commit `654f34cb8cdb` (Prepare for 1.2.0 release).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/robust.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
