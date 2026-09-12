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
