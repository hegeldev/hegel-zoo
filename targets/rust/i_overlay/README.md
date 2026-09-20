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
- 2026-09-13: base bumped eeb4a9acfd1a → 1e33a352ee3d (2026-09-06, "int range"; 8.1.1); 3 bug(s) still reproduce; fixed upstream: i_overlay/2. 699 tests pass. i_overlay/2 (Frag solver region disagreement) no longer reproduces after upstream's fragment-solver rework; /1 and /3 still do. New zoo finding i_overlay/4: `simplify` with `FillRule::Negative` returns a clockwise outer contour (documented as counterclockwise) — found by `hegel_simplify_is_idempotent` on this bump, pinned by `hegel_pin_simplify_negative_returns_clockwise_outer`.
- 2026-09-15: base bumped 1e33a352ee3d → 340bd5d1eaa2 (2026-09-15, "Merge pull request #92 from iShape-Rust/bug/fix_shape_binding"; 8.1.2); 3 bug(s) still reproduce. 736 tests pass.
- 2026-09-20: base bumped 340bd5d1eaa2 → 26782e3b93f9 (2026-09-19, "Merge pull request #93 from iShape-Rust/feature/int_offset"; 9.0.0); 2 bug(s) still reproduce; fixed upstream: i_overlay/4 (`contour_direction` rewritten in #93: fill decided by the input winding, then reversed to the output direction, so `simplify` under `Negative` returns a counterclockwise outer). 9.0.0 moves to i_float 5.0.0, whose float API has a documented coordinate contract (finite, |x| <= 2^500 for f64; beyond it the adapter panics with `CoordinatesOutOfRange` by design): `hegel_float_overlay_extremes_no_panic_finite_output` now tops out at 1e150 instead of 1e300, a harness adjustment to the new contract, not a bug. 874 tests pass.
