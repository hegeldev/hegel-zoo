# num-bigint

[rust-num/num-bigint](https://github.com/rust-num/num-bigint).

## What is tested

**`tests/bigint.rs`**
- `hegel_add_sub_mul_neg_match_i128`: (no doc comment)
- `hegel_div_rem_match_i128`: (no doc comment)
- `hegel_cmp_matches_i128`: (no doc comment)
- `hegel_to_str_radix_roundtrip`: (no doc comment)
- `hegel_display_parse_roundtrip`: (no doc comment)
- `hegel_format_impls_match_to_str_radix`: (no doc comment)
- `hegel_signed_bytes_roundtrip`: (no doc comment)
- `hegel_bytes_sign_roundtrip`: (no doc comment)
- `hegel_radix_digits_roundtrip`: (no doc comment)
- `hegel_div_rem_contract`: (no doc comment)
- `hegel_div_mod_floor_contract`: (no doc comment)
- `hegel_gcd_lcm_contract`: (no doc comment)
- `hegel_pow_matches_repeated_mul`: (no doc comment)
- `hegel_parse_rejects_invalid_char`: (no doc comment)
- `hegel_parse_never_panics`: (no doc comment)

**`tests/bigint_bitwise.rs`**
- `hegel_bitwise_ops_match_i128`: (no doc comment)
- `hegel_shifts_match_i128`: (no doc comment)
- `hegel_bit_matches_i128`: (no doc comment)
- `hegel_set_bit_bit_consistency`: (no doc comment)
- `hegel_trailing_zeros_contract`: (no doc comment)

**`tests/biguint.rs`**
- `hegel_biguint_bit_queries_match_u128`: (no doc comment)

**`tests/modpow.rs`**
- `hegel_modpow_matches_naive`: (no doc comment)
- `hegel_modinv_contract`: (no doc comment)
- `hegel_modinv_unit_modulus_interval`: (no doc comment)

**`tests/roots.rs`**
- `hegel_biguint_nth_root_contract`: (no doc comment)
- `hegel_bigint_negative_nth_root_contract`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-07-07: predecessor base commit `9ec740f8c162` (Merge pull request #351 from cuviper/rename-head).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/num-bigint.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
