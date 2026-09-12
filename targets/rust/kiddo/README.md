# kiddo

[sdd/kiddo](https://github.com/sdd/kiddo).

## What is tested

**`src/kd_tree/mod.rs`**
- `?`: (no doc comment)
- `hegel_nearest_n_matches_brute_force`: (no doc comment)
- `hegel_within_inclusive_matches_brute_force`: (no doc comment)
- `hegel_within_exclusive_matches_brute_force`: (no doc comment)
- `hegel_within_unsorted_matches_brute_force`: (no doc comment)
- `hegel_nearest_n_within_matches_brute_force`: (no doc comment)
- `hegel_best_n_within_matches_brute_force`: (no doc comment)
- `hegel_approx_nearest_one_never_better_than_exact`: (no doc comment)
- `hegel_fixed_point_nearest_one_agrees_with_f64_oracle`: (no doc comment)
- `hegel_nearest_one_overflowed_distance_fabricates_default_item_known_bug`: (no doc comment)
- `hegel_mutable_add_split_scrambles_items_known_bug`: (no doc comment)
- `hegel_mutable_tree_agrees_with_vec_model`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-07-22: predecessor base commit `39cbbaf99876` (ci: cap benchmark trees at 2^25).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/kiddo.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
