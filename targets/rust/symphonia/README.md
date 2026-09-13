# symphonia

[pdeljanov/Symphonia](https://github.com/pdeljanov/Symphonia).

## What is tested

**`src/audio/conv.rs`**
- `hegel_widening_roundtrip_is_identity`: (no doc comment)
- `hegel_signed_unsigned_same_width_roundtrip`: (no doc comment)
- `hegel_float_conversion_is_path_independent`: (no doc comment)

**`src/io/bit.rs`**
- `hegel_ltr_read_bit_matches_byte_oracle`: (no doc comment)
- `hegel_rtl_read_bit_matches_byte_oracle`: (no doc comment)
- `hegel_ltr_read_bits_matches_bit_oracle`: (no doc comment)
- `hegel_rtl_read_bits_matches_bit_oracle`: (no doc comment)
- `hegel_ignore_bits_equals_reading_bits`: (no doc comment)
- `hegel_read_unary_zeros_matches_oracle`: (no doc comment)
- `hegel_read_unary_ones_matches_oracle`: (no doc comment)
- `hegel_read_unary_capped_matches_oracle`: (no doc comment)
- `hegel_arbitrary_ops_never_panic`: (no doc comment)
- `hegel_codebook_roundtrip`: (no doc comment)
- `hegel_read_codebook_arbitrary_data_consumes_all_bytes`: (no doc comment)

**`src/io/buf_reader.rs`**
- `hegel_buf_reader_matches_slice_oracle`: (no doc comment)

**`src/util.rs`**
- `hegel_sign_extend_matches_arithmetic_oracle`: (no doc comment)
- `hegel_masks_match_bit_loop_oracle`: (no doc comment)
- `hegel_contains_ones_byte_matches_oracle`: (no doc comment)
- `hegel_clamp_matches_std_clamp`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-07-23: predecessor base commit `5f26f020b3a1` (core (io): Clamp scan_bytes_aligned_ref to scan_len to prevent over...).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/symphonia.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
