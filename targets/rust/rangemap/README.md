# rangemap

[jeffparsons/rangemap](https://github.com/jeffparsons/rangemap).

## What is tested

**`src/inclusive_map.rs`**
- `hegel_inclusive_map_matches_point_model`: (no doc comment)
- `hegel_inclusive_gaps_match_point_model`: (no doc comment)
- `hegel_inclusive_backwards_range_ops_panic`: (no doc comment)

**`src/inclusive_set.rs`**
- `hegel_union_matches_point_membership`: (no doc comment)
- `hegel_intersection_matches_point_membership`: (no doc comment)

**`src/map.rs`**
- `hegel_map_matches_point_model`: (no doc comment)
- `hegel_gaps_match_point_model`: (no doc comment)
- `hegel_overlapping_matches_iter_filter`: (no doc comment)
- `hegel_empty_range_ops_panic`: (no doc comment)
- `hegel_full_i32_domain_invariants`: (no doc comment)

## Oracles

## Not tested

## History

- 2025-12-19: predecessor base commit `414e9c7c10af` (Merge pull request #117 from jeffparsons/prepare_v1.7.1).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/rangemap.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-12: base bumped 414e9c7c10af → fbd1575a8629 (2026-08-14, "Merge pull request #122 from jeffparsons/check_formatting"; 1.8.0); 0 bug(s) still reproduce; add/add conflicts in Cargo.toml resolved by keeping both sides. 178 tests pass.
