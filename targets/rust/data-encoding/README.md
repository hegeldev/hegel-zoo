# data-encoding

[ia0/data-encoding](https://github.com/ia0/data-encoding).

## What is tested

**`tests/lib.rs`**
- `prop_encode_decode_roundtrip_predefined`: (no doc comment)
- `prop_encode_decode_roundtrip_custom_spec`: (no doc comment)
- `prop_encode_output_is_ascii`: (no doc comment)
- `prop_decode_arbitrary_input_error_position`: (no doc comment)
- `prop_decode_mut_partial_contract`: (no doc comment)
- `prop_encode_len_matches_encode`: (no doc comment)
- `prop_decode_len_accepts_encode_output`: (no doc comment)
- `prop_specification_roundtrip`: (no doc comment)
- `prop_encode_append_appends`: (no doc comment)
- `prop_encode_write_buffer_matches_encode`: (no doc comment)
- `prop_encode_display_matches_encode`: (no doc comment)
- `prop_padded_concatenation_decodes`: (no doc comment)
- `prop_interpret_byte_consistent_with_specification`: (no doc comment)
- `prop_encode_len_documented_domain_no_panic`: (no doc comment)
- `prop_decode_len_documented_domain_no_panic`: (no doc comment)
- `prop_encoder_stateful_matches_batch_encode`: (no doc comment)
- `prop_decode_encode_canonical_roundtrip`: (no doc comment)
- `prop_trailing_bits_noncanonical_spellings_rejected`: (no doc comment)
- `prop_corrupt_one_char_rejected`: (no doc comment)
- `prop_truncated_padded_rejected`: (no doc comment)
- `prop_encode_padding_shape`: (no doc comment)
- `prop_encode_mut_matches_encode`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-07-19: predecessor base commit `a57da53784fd` (Remove deprecated authors field from Cargo.toml (#158)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/data-encoding.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1. One upstream `assert_eq!(x, [])` on a `Vec<u8>` in `tests/lib.rs` (and its `v3/` copy) rewritten as `assert!(x.is_empty())`: hegeltest 0.44 pulls in `serde_json`, whose `PartialEq` impls make the literal ambiguous (E0282/E0283).
- 2026-09-12: base bumped a57da53784fd → 65862b9234e2 (2026-09-01, "Fix redundant explicit links in v3 doc (#165)"; 2.11.2-git); 0 bug(s) still reproduce. 97 tests pass.
