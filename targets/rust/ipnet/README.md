# ipnet

[krisprice/ipnet](https://github.com/krisprice/ipnet).

## What is tested

**`src/ipnet.rs`**
- `hegel_ipv4net_display_parse_roundtrip`: (no doc comment)
- `hegel_ipv6net_display_parse_roundtrip`: (no doc comment)
- `hegel_ipnet_display_parse_roundtrip`: (no doc comment)
- `hegel_from_str_never_panics`: (no doc comment)
- `hegel_ipnet_parse_agrees_with_concrete_types`: (no doc comment)
- `hegel_netmask_hostmask_are_complementary`: (no doc comment)
- `hegel_ipv4_hosts_count_and_endpoints_match_docs`: (no doc comment)
- `hegel_ipv6_hosts_count_and_endpoints_match_docs`: (no doc comment)
- `hegel_contains_addr_matches_prefix_bits_oracle`: (no doc comment)
- `hegel_contains_net_iff_longer_prefix_and_network_inside`: (no doc comment)
- `hegel_supernet_is_unique_immediate_parent`: (no doc comment)
- `hegel_subnets_partition_their_network`: (no doc comment)
- `hegel_ipv4_subnets_iterator_covers_exact_range`: (no doc comment)
- `hegel_ipv6_subnets_iterator_covers_exact_range`: (no doc comment)
- `hegel_aggregate_preserves_address_membership`: (no doc comment)
- `hegel_ord_consistent_with_contains`: (no doc comment)
- `hegel_trunc_preserves_range_and_is_idempotent`: (no doc comment)

**`src/mask.rs`**
- `hegel_prefix_netmask_roundtrip`: (no doc comment)
- `hegel_mask_to_prefix_accepts_exactly_contiguous_masks`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-03-03: predecessor base commit `65c04c355668` (Update version number.).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/ipnet.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
