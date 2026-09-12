# postcard

[jamesmunns/postcard](https://github.com/jamesmunns/postcard).

## What is tested

**`tests/accumulator.rs`**
- `prop_accumulator_reassembles_arbitrarily_chunked_stream`: Feeding a well-formed COBS stream to `CobsAccumulator` in arbitrary chunks reassembles exactly the original sequence of messages, regardless of where the chunk boundaries fall (mid-frame, on frame boundaries, multiple frames per chunk, ...).

**`tests/loopback.rs`**
- `prop_rich_message_roundtrip`: (no doc comment)
- `$name` (macro `varint_roundtrip_props!`, instances `prop_varint_roundtrip_u8`, `prop_varint_roundtrip_u16`, `prop_varint_roundtrip_u32`): (no doc comment)
- `prop_unsigned_varint_encoding_matches_leb128_reference`: Spec conformance: unsigned integers encode as canonical LEB128 (independent reference implementation as the oracle).
- `prop_signed_varint_encoding_matches_zigzag_leb128_reference`: Spec conformance: signed integers are zigzag-encoded, then encoded as canonical LEB128 (independent reference implementation).
- `prop_varint_noncanonical_padding_accepted_within_max_len`: Spec "Canonicalization" table: non-canonical encodings (excess `0x80` continuation bytes) are accepted while the total length stays within the type's maximum encoded length (5 for u32), and rejected once it exceeds it.
- `prop_serialized_size_matches_to_slice`: (no doc comment)
- `prop_to_slice_exact_buffer_ok_undersized_errors`: (no doc comment)
- `prop_take_from_bytes_returns_exact_remainder`: (no doc comment)
- `prop_from_bytes_rejects_truncated_input`: (no doc comment)
- `prop_decoders_never_panic_on_arbitrary_input`: (no doc comment)
- `prop_cobs_roundtrip_and_zero_free_framing`: (no doc comment)
- `prop_float_bitpattern_roundtrip`: Spec: f32/f64 are encoded as their little-endian bit patterns, and round-trip bit-exactly (including NaN payloads and infinities).
- `prop_fixint_layout_and_roundtrip`: `fixint` opt-out: fields are laid out as fixed-size LE/BE byte arrays (documented in src/fixint.rs) and round-trip.

## Oracles

## Not tested

## History

- 2026-07-20: predecessor base commit `118d274cf46e` (Merge pull request #300 from sugar700/enum-map-v2_0).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/postcard.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
