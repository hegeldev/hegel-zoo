# glam

[bitshifter/glam-rs](https://github.com/bitshifter/glam-rs).

## What is tested

**`tests/affine3.rs`**
- `hegel_affine3a_matches_mat4_transform_point`: (no doc comment)
- `hegel_affine3a_composition_matches_sequential`: (no doc comment)
- `hegel_affine3a_inverse_roundtrips_points`: (no doc comment)

**`tests/euler.rs`**
- `hegel_euler_roundtrip_preserves_rotation`: (no doc comment)

**`tests/mat3.rs`**
- `hegel_mat3_vs_mat3a_ops_agree`: (no doc comment)
- `hegel_mat3_vs_mat3a_inverse_agree`: (no doc comment)

**`tests/mat4.rs`**
- `hegel_mat4_inverse_roundtrip`: (no doc comment)
- `hegel_mat4_cols_array_roundtrip`: (no doc comment)

**`tests/quat.rs`**
- `hegel_quat_from_axis_angle_unit_and_fixes_axis`: (no doc comment)
- `hegel_quat_conjugate_is_inverse`: (no doc comment)
- `hegel_quat_rotation_preserves_length_and_matches_mat3`: (no doc comment)

**`tests/vec3.rs`**
- `hegel_vec3_vec3a_lanewise_ops_agree_exactly`: (no doc comment)
- `hegel_vec3_and_vec3a_match_f64_oracle`: (no doc comment)
- `hegel_vec3_normalize_family_contract`: (no doc comment)

**`tests/vec4.rs`**
- `hegel_vec4_lanewise_ops_match_scalar_reference`: (no doc comment)
- `hegel_vec4_dot_length_match_f64_oracle`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-07-23: predecessor base commit `6feed7d50ee7` (Consolodate some common test code into macros where possible (#756)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/glam.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped 6feed7d50ee7 → 2391a343f22b (2026-09-12, "chore: Undo most of PR #836. (#837)"; 0.33.7); 1 bug(s) still reproduce. 3459 tests pass.
- 2026-09-13: base bumped 2391a343f22b → df107d6bbfb4 (2026-09-13, "ci: run release-plz semver check on nightly (#838)"; 0.33.7); 1 bug(s) still reproduce. 3459 tests pass.
- 2026-09-14: base bumped df107d6bbfb4 → 23343fc305cf (2026-09-14, "test: fix UB in vec3a m128 store (#840)"; 0.33.7); 1 bug(s) still reproduce. 3459 tests pass.
- 2026-09-15: base bumped 23343fc305cf → 15971997d7a9 (2026-09-15, "feat(mat): add row constructors and set_row to the matrix types (#790)"; 0.33.7); 1 bug(s) still reproduce. 3466 tests pass.
- 2026-09-15: base bumped 15971997d7a9 → 104058313a3a (2026-09-16, "docs(mat): mat row and col method consistency pass (#843)"; 0.33.7); 1 bug(s) still reproduce. 3466 tests pass.
- 2026-09-16: base bumped 104058313a3a → 296329c1dd4b (2026-09-16, "docs: hide deref helper types from rustdoc (#851)"; 0.33.7); 1 bug(s) still reproduce. 3466 tests pass.
