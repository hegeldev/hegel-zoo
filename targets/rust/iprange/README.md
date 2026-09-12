# iprange

[sticnarf/iprange-rs](https://github.com/sticnarf/iprange-rs).

## What is tested

**`src/ipnet.rs`**
- `merge_matches_membership_union`: (no doc comment)
- `intersect_matches_membership_intersection`: (no doc comment)
- `intersect_commutes`: (no doc comment)
- `exclude_matches_membership_difference`: (no doc comment)
- `exclude_then_merge_restores_universe_v4`: (no doc comment)
- `merge_self_is_identity`: (no doc comment)
- `exclude_self_is_empty`: (no doc comment)
- `simplify_preserves_membership`: (no doc comment)
- `simplify_is_idempotent`: (no doc comment)
- `iter_yields_disjoint_minimal_exact_cover`: (no doc comment)
- `supernet_agrees_with_ipnet_contains`: (no doc comment)
- `window_model_agrees`: (no doc comment)
- `ipv6_merge_matches_membership_union`: (no doc comment)
- `ipv6_exclude_matches_membership_difference`: (no doc comment)
- `exclude_then_merge_restores_universe_v6`: (no doc comment)
- `serde_bincode_roundtrip_v4`: (no doc comment)
- `serde_bincode_roundtrip_v6`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-04-20: predecessor base commit `0f36df090902` (Merge pull request #31 from pronebird/rust-edition-2024).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/iprange.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
