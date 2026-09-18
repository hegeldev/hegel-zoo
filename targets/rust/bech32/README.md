# bech32

[rust-bitcoin/rust-bech32](https://github.com/rust-bitcoin/rust-bech32).

## What is tested

**`src/lib.rs`**
- `prop_encode_decode_roundtrip`: The crown roundtrip: for any valid HRP and any data, `encode` (either checksum algorithm) followed by `decode` recovers the HRP and the data exactly.
- `prop_upper_and_lower_encodings_agree`: Case consistency: `encode_upper` is exactly the uppercase of `encode_lower`, and both decode to the same HRP and data (bech32 is case-insensitive for non-mixed input).
- `prop_decode_rejects_every_single_char_substitution_in_data_part`: The whole point of the checksum: substituting any single data-part character with any other charset character must be rejected, at every position (exhaustively probed).
- `prop_decode_rejects_every_single_char_substitution_in_hrp`: The checksum also covers the HRP: corrupting any single HRP character (with another valid, non-'1', non-uppercase HRP character) must be rejected, at every position.
- `prop_decode_rejects_mixed_case`: BIP-173: mixed-case strings must be rejected even when the checksum is otherwise valid.
- `prop_decode_rejects_invalid_data_char`: Characters outside the 32-character charset (e.g. the excluded '1', 'b', 'i', 'o' confusion characters, punctuation) in the data part are rejected with a parse error.
- `prop_bech32_and_bech32m_are_mutually_exclusive`: A string with a valid Bech32 checksum is never a valid Bech32m string and vice versa (the two algorithms differ only in target residue, so validity is mutually exclusive).
- `prop_encode_enforces_code_length_limit`: Length limit: the crate enforces `Checksum::CODE_LENGTH` (1023 for Bech32/Bech32m, not the segwit 90-char limit). `encode` succeeds iff the encoded length (computed with an independently transcribed formula) is <= 1023, and on success the string has exactly that length and `encoded_length` agrees.
- `prop_decode_arbitrary_input_never_panics`: Robustness: no decoding entry point may panic on arbitrary input.

**`src/primitives/hrp.rs`**
- `prop_parse_accepts_valid_hrp_and_preserves_it`: Every BIP-173-valid HRP (1..=83 chars of ASCII 33..=126, non-mixed-case) parses, preserving content, length and case.
- `prop_parse_display_agrees_with_parse`: `parse_display` is documented as semantically equivalent to `parse` — differential test over arbitrary strings (both accepted content and all rejection classes).
- `prop_parse_rejects_out_of_range_char`: Characters outside ASCII 33..=126 (controls, space, DEL, non-ASCII) anywhere in an otherwise valid HRP cause rejection.
- `prop_parse_rejects_too_long`: HRPs longer than 83 characters are rejected with `Error::TooLong` reporting the length.
- `prop_parse_rejects_mixed_case`: Mixed-case HRPs are rejected (BIP-173) even though each character is individually valid.

**`src/segwit.rs`**
- `prop_segwit_encode_decode_roundtrip`: Segwit roundtrip: encode a valid (hrp, version, program) triple, decode it back and recover all three exactly; the address respects the 90-character limit.
- `prop_segwit_encode_validity_matches_spec`: `segwit::encode` accepts exactly the BIP-173/BIP-350 valid inputs: witness version 0..=16 (guaranteed by construction), program length in 2..=40 (v0: exactly 20 or 32), and total encoded length <= 90. The oracle re-states the spec rules independently.
- `prop_segwit_decode_rejects_over_90_chars`: The 90-character limit is enforced on the decode side too: a string with a perfectly valid checksum that is longer than 90 characters must be rejected by `segwit::decode`.

## Oracles

## Not tested

## History

- 2026-07-22: predecessor base commit `162cff91760a` (Merge rust-bitcoin/rust-bech32#283: Automated daily update to rustc...).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/bech32.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-12: base bumped 162cff91760a → db709c498f86 (2026-09-11, "Merge rust-bitcoin/rust-bech32#301: Automated daily update to rustc (to nightly-2026-09-04)"; 0.12.0); 0 bug(s) still reproduce. 265 tests pass.
- 2026-09-16: base bumped db709c498f86 → 69ec69951358 (2026-09-16, "Merge rust-bitcoin/rust-bech32#305: hrp: add Panics doc to Hrp::parse_unchecked"; 0.12.0); 0 bug(s) still reproduce. 265 tests pass.
- 2026-09-17: base bumped 69ec69951358 → 0e12a9c76a65 (2026-09-17, "Merge rust-bitcoin/rust-bech32#306: field: add a "large odd field" unit test and fix a pile of bugs it exhibits"; 0.12.0); 0 bug(s) still reproduce. 284 tests pass.
- 2026-09-18: base bumped 0e12a9c76a65 → 2ea19ee776de (2026-09-18, "Merge rust-bitcoin/rust-bech32#308: correction and lfsr: fix a bunch of limits, mostly no-alloc ones"; 0.12.0); 0 bug(s) still reproduce. 294 tests pass.
