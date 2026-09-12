# euclid

[servo/euclid](https://github.com/servo/euclid).

## What is tested

**`src/angle.rs`**
- `hegel_positive_is_in_zero_two_pi`: (no doc comment)
- `hegel_signed_is_in_neg_pi_pi`: (no doc comment)
- `hegel_angle_to_is_finite_for_finite_angles`: (no doc comment)
- `hegel_angle_to_magnitude_is_at_most_pi`: (no doc comment)

**`src/box2d.rs`**
- `hegel_box_rect_box_roundtrip_is_identity`: (no doc comment)
- `hegel_intersects_iff_intersection_is_some`: (no doc comment)
- `hegel_intersection_is_contained_in_both`: (no doc comment)
- `hegel_union_contains_both_operands`: (no doc comment)
- `hegel_from_points_contains_all_points_inclusive`: (no doc comment)

**`src/point.rs`**
- `hegel_lerp_is_exact_at_endpoints`: (no doc comment)

**`src/rotation.rs`**
- `hegel_rotation2d_preserves_vector_length`: (no doc comment)
- `hegel_rotation3d_inverse_roundtrip`: (no doc comment)

**`src/transform2d.rs`**
- `hegel_then_inverse_approximates_identity`: (no doc comment)
- `hegel_transform_point_inverse_roundtrip`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-03-17: predecessor base commit `60f2bd96deec` (Avoid NaNs in Rotation::get_angle (#552)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/euclid.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
