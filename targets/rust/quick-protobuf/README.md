# quick-protobuf

[tafia/quick-protobuf](https://github.com/tafia/quick-protobuf).

## What is tested

**`src/reader.rs`**
- `prop_read_varint_arbitrary_bytes`: Reading varints from arbitrary bytes never panics, consumes at most 10 bytes, and never moves the cursor past the buffer.
- `prop_overlong_varint_errors`: Over-long varints (10 continuation bytes with their high bit set, i.e. >10 bytes total) are rejected with Error::Varint by both read_varint32 and read_varint64 — no panic, no unbounded scan.
- `prop_huge_length_prefix_errors`: A length-delimited field claiming a huge length backed by a short buffer must fail with UnexpectedEndOfBuffer — quickly, without allocating anything proportional to the claimed length.
- `prop_scan_unknown_fields_arbitrary_bytes`: Scanning arbitrary bytes as a stream of unknown fields (next_tag + read_unknown, exactly what generated from_reader impls do for unknown tags) terminates, never panics, and never moves the cursor past the end of the buffer.
- `prop_read_bytes_position_accounting`: Position accounting: a successful read_bytes advances the cursor by exactly sizeof_len(returned.len()) — the length prefix plus the data — and never past the buffer.

**`tests/write_read.rs`**
- `prop_varint_u64_roundtrip`: write_varint/read_varint64 round-trip over the full u64 range, and the encoded length matches sizeof_varint.
- `prop_varint_scalar_roundtrip`: The varint-coded scalar write/read pairs (int32/int64/uint32/uint64/ bool/enum) round-trip over their full ranges, consuming exactly the bytes written (sizeof_* agreement included where a sizeof exists).
- `prop_zigzag_roundtrip`: Zigzag-coded sint32/sint64 round-trip over the full range including MIN/MAX, and the encoded length matches sizeof_sint32/sizeof_sint64.
- `prop_fixed_width_roundtrip`: Fixed-width scalars (fixed32/fixed64/sfixed32/sfixed64/float/double) round-trip exactly. Floats are drawn as raw bit patterns so the whole domain (NaNs, infinities, subnormals) is covered, and compared by bits.
- `prop_bytes_roundtrip`: write_bytes/read_bytes round-trip for arbitrary contents including empty, and the encoding is exactly sizeof_len(len) bytes.
- `prop_string_roundtrip`: write_string/read_string round-trip for arbitrary unicode including empty strings.
- `prop_packed_varint_roundtrip`: write_packed/read_packed round-trip for varint-coded elements; an empty slice writes nothing at all (documented early-return).
- `prop_packed_fixed_roundtrip`: write_packed_fixed/read_packed_fixed round-trip (including empty, which unlike write_packed does write a zero length prefix).
- `prop_wire_sequence_roundtrip`: The crown: any sequence of (field_number, wire value) written through Writer (tag + value) is read back exactly by a BytesReader loop dispatching on next_tag, covering wire types 0/1/2/5 and the full field-number range.
- `prop_message_roundtrip_and_get_size`: Messages round-trip through serialize_into_vec/deserialize_from_slice and serialize_into_slice, and get_size agrees with the bytes actually produced (hegel version of the quickcheck property `test_get_size` in tests/rust_protobuf/v2/test_basic.rs).
- `prop_deserialize_arbitrary_bytes_no_panic`: Untrusted-decoder robustness: deserializing arbitrary bytes as a message returns Ok or Err but never panics, OOMs, or hangs.
- `prop_deserialize_corrupted_message_no_panic`: Corrupted-valid robustness: take a valid encoded message, corrupt it (flip a byte, overwrite a byte, or truncate), and decoding must return Ok or Err — never panic.
- `prop_nested_message_moderate_depth_roundtrip`: Nested length-delimited messages decode correctly at any moderate depth: the recovered structure has exactly the crafted nesting depth.

## Oracles

## Not tested

## History

- 2024-02-14: predecessor base commit `54e7d6c5d981` (Merge pull request #259 from ghpr-asia/mr-config-msrv-re).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/quick-protobuf.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
