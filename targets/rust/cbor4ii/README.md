# cbor4ii

[quininer/cbor4ii](https://github.com/quininer/cbor4ii).

## What is tested

**`tests/decode.rs`**
- `prop_core_value_roundtrip`: Round-trip: decode(encode(v)) == v (bit-exact for floats), and re-encoding the decoded value is a byte-for-byte fixpoint.
- `prop_raw_value_and_ignored_any_consume_exactly_one_item`: `RawValue` and `IgnoredAny` consume exactly one item, and `RawValue` captures exactly the encoded bytes of that item.
- `prop_core_decode_arbitrary_bytes_never_panics`: Decoding arbitrary untrusted bytes as any type returns Ok/Err but never panics, aborts, over-allocates or hangs. (Supplements fuzz_targets/decode.rs.)
- `prop_crafted_length_prefix_rejected_without_oom`: A definite-length header claiming a huge length (or an unterminated indefinite-length item) must fail with a normal error -- quickly and without pre-allocating the claimed length.
- `prop_deeply_nested_input_no_stack_overflow`: Deeply nested input must either decode or fail with a depth error -- never overflow the stack. SliceReader's documented recursion limit is 256.
- `prop_corrupted_encoding_never_panics`: Corrupting a valid encoding (bit flip, truncation, insertion) never panics.
- `prop_string_decode_validates_utf8`: Decoding a text string validates UTF-8: a definite-length string item decodes to exactly its payload iff the payload is valid UTF-8, and is rejected otherwise.
- `prop_int_header_shortest_form`: Spec (RFC 8949 4.2.1-style shortest form): the encoder emits the smallest possible integer header, for both unsigned and negative integers.
- `prop_narrowing_decode_matches_try_from`: Narrowing decodes agree with `try_from`: bytes encoded from a wide integer decode as a narrower type exactly when the value fits.

**`tests/serde.rs`**
- `prop_serde_roundtrip_rich_model`: The crown: from_slice(to_vec(v)) == v over a rich serde model, through both the zero-copy slice reader and the buffered io reader.
- `prop_serde_encoding_deterministic_and_fixpoint`: Encoding is deterministic, and decode-then-encode is a byte fixpoint.
- `prop_serde_value_roundtrip`: Round-trip of dynamic `Value` trees through the serde mod, including bignum (tag 2/3) integers beyond the u64 range.
- `prop_serde_value_roundtrip_big_negative_int_known_bug`: KNOWN FAILURE (real bug): CBOR negative integers in [-2^64, i64::MIN - 1] -- valid RFC 8949 major type 1, and exactly what `to_vec` itself emits for `Value::Integer` in that range -- fail to decode as `Value` with `CastOverflow { name: "-i64" }`. `deserialize_any` routes all of major type 1 to `deserialize_i64` (src/serde/de.rs) with no i128 fallback, so the serde-mod Value round-trip is broken for these values. serde_cbor decodes the same bytes successfully (`Integer(-9223372036854775809)`). Minimal reproducer: to_vec(Value::Integer(i64::MIN as i128 - 1)).
- `prop_from_slice_arbitrary_bytes_never_panics`: Decoding arbitrary untrusted bytes never panics, over-allocates or hangs. (Supplements fuzz_targets/de.rs.)
- `prop_from_slice_cross_type_never_panics`: Bytes valid for one type decoded as any other type never panic.
- `prop_serde_deeply_nested_no_stack_overflow`: Deeply nested input through the serde deserializer is depth-limited: graceful error, never a stack overflow.

**`tests/serde_cbor.rs`**
- `prop_serde_cbor_decodes_cbor4ii_encoding`: serde_cbor decodes what cbor4ii encodes.
- `prop_cbor4ii_decodes_serde_cbor_float_known_bug`: KNOWN FAILURE (compatibility bug): serde_cbor encodes every f64 in the shortest lossless float width (0.0 -> 0xf9 0x00 0x00, an f16), which RFC 8949 treats as an equivalent representation. cbor4ii's typed `deserialize_f64` (src/serde/de.rs -> f64::decode in src/core/dec.rs) accepts only the F64 (0xfb) marker, so cbor4ii fails to decode most serde_cbor-encoded floats with `Mismatch { name: "f64", found: 249 }`, despite the README's serde_cbor-compatibility claim (float width is not one of the documented intentional differences). Minimal reproducer: `cbor4ii::serde::from_slice::<f64>(&serde_cbor::to_vec(&0.0f64)?)`.
- `prop_cbor4ii_decodes_serde_cbor_encoding`: cbor4ii decodes what serde_cbor encodes.

## Oracles

## Not tested

## History

- 2025-11-30: predecessor base commit `7a496cb5186d` (release 1.2.2).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/cbor4ii.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
