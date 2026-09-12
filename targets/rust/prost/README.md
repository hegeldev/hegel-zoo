# prost

[tokio-rs/prost](https://github.com/tokio-rs/prost).

## What is tested

**`src/encoding/varint.rs`**
- `hegel_encode_varint_matches_leb128_reference`: Property: `encode_varint` produces exactly the bytes the LEB128 spec prescribes, and `encoded_len_varint` agrees with the actual encoded length.
- `hegel_varint_decode_paths_roundtrip`: Property: all three decoding paths (`decode_varint`, the unrolled `decode_varint_slice`, and the fallback `decode_varint_slow`) round-trip every encoded varint back to the original value and consume exactly its bytes.
- `hegel_varint_decoders_agree_on_arbitrary_bytes`: Property: on *arbitrary* bytes the optimized decoder (`decode_varint`, which dispatches to the unrolled slice decoder) and the simple loop decoder (`decode_varint_slow`) agree — same Ok/Err outcome, same value, same number of bytes consumed on success — and neither panics.
- `hegel_varint_split_buffer_decode`: Property: decoding a varint split across two non-contiguous `Buf` chunks (via `Buf::chain`) yields the same value as contiguous decoding, for every value and every split point. Generalizes the hand-picked cases in `encoding::test::split_varint_decoding`, which is kept as a cheap pin.

**`tests/derived_message_properties.rs`**
- `hegel_derived_message_roundtrip`: Property: `decode(encode(m)) == m` for a message covering every derived field kind, and `encoded_len` reports exactly the number of bytes `encode` produces. NaN is excluded because the property is `==`-based; NaN payloads are covered by `hegel_reencode_of_decoded_message_is_identical`.
- `hegel_reencode_of_decoded_message_is_identical`: Property: re-encoding a decoded message reproduces the original bytes (`encode(decode(encode(m))) == encode(m)`). Holds bit-for-bit even for NaN floats, so the generator keeps them.
- `hegel_decode_arbitrary_bytes_never_panics`: Property: `decode` returns `Ok` or `Err` but never panics, both on completely arbitrary bytes and on valid encodings corrupted at a single position (which reach much deeper into the decoding paths than uniform garbage).
- `hegel_unknown_fields_are_skipped`: Property: unknown fields of every wire type are skipped per the spec (<https://protobuf.dev/programming-guides/encoding/#structure>): decoding a valid encoding with unknown fields prepended and/or appended yields the same message.
- `hegel_concatenated_encodings_merge_per_spec`: Property: decoding the concatenation of two encodings merges the messages per the protobuf spec, checked against an independently written merge oracle.
- `hegel_length_delimited_stream_roundtrip`: Property: a stream of length-delimited messages written with `encode_length_delimited` reads back, in order, via `decode_length_delimited` — the framing determines every message boundary.

## Oracles

## Not tested

## History

- 2026-07-05: predecessor base commit `aed74ad0e844` (fix: Prevent panic for service generator in empty module (#1442)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/prost.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
