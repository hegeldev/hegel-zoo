# i_overlay

[iShape-Rust/iOverlay](https://github.com/iShape-Rust/iOverlay).

## What is tested

**`tests/float_overlay_tests.rs`**
- `hegel_float_overlay_extremes_no_panic_finite_output`: (no doc comment)

**`tests/overlay_tests.rs`**
- `hegel_area_union_intersect_additivity`: (no doc comment)
- `hegel_area_xor_difference_decomposition`: (no doc comment)
- `hegel_commutativity`: (no doc comment)
- `hegel_membership_matches_winding_oracle`: (no doc comment)
- `hegel_output_boundary_has_no_proper_crossings`: (no doc comment)
- `hegel_output_orientation`: (no doc comment)
- `hegel_result_is_fixed_point`: (no doc comment)
- `hegel_empty_clip_identities`: (no doc comment)
- `hegel_solver_equivalence`: (no doc comment)
- `hegel_int_engine_equivalence`: (no doc comment)

**`tests/simplify_tests.rs`**
- `hegel_simplify_is_idempotent`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-07-05: predecessor base commit `eeb4a9acfd1a` (update contribution rules).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/i_overlay.patch`).
- 2026-09-11: imported into the zoo; ported to hegeltest 0.44.1.
