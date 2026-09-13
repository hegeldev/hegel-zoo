# asn1

[alex/rust-asn1](https://github.com/alex/rust-asn1).

## What is tested

**`tests/derive_test.rs`**
- `test_derive_struct_roundtrip_property`: Property: write→parse is the identity for a derived SEQUENCE exercising OPTIONAL, CHOICE, IMPLICIT/EXPLICIT tagging, and OPTIONAL DEFAULT fields.
- `test_parse_reserialize_identity_property`: Property (from the crate's own fuzz target): DER is canonical — any input that parses successfully must re-serialize to exactly the input bytes.

**`tests/oid_tests.rs`**
- `test_oid_string_roundtrip_property`: Property: `from_string` → `to_string` is the identity for any valid dotted OID string.
- `test_oid_der_roundtrip_property`: Property: DER write→parse is the identity for any valid OID.

**`tests/roundtrip_tests.rs`**
- `test_i64_roundtrip_property`: Property: write→parse is the identity for `i64` over the full range.
- `test_u64_roundtrip_property`: Property: write→parse is the identity for `u64` over the full range (covers the 0x00 pad byte for values with the high bit set).
- `test_octet_string_length_boundaries`: Property: OCTET STRING write→parse is the identity for content lengths across the length-encoding boundaries (127/128/255/256/65535/65536/...), and the writer emits the spec-mandated minimal length encoding.
- `test_padded_integer_rejected`: Property (validation/rejection): an INTEGER whose contents are padded with a redundant leading 0x00/0xff byte is not minimally encoded and must be rejected by the parser.
- `test_negative_integer_rejected_for_unsigned`: Property (validation/rejection): a negative INTEGER must be rejected when parsed as an unsigned type.
- `test_non_minimal_length_rejected`: Property (validation/rejection): DER requires the definite length to be encoded in the minimal number of octets. Re-encoding a valid TLV's length with more octets than necessary must be rejected.
- `test_bit_string_roundtrip_property`: Property: write→parse is the identity for BIT STRINGs over arbitrary contents and padding-bit counts.
- `test_utctime_roundtrip_property`: Property: write→parse is the identity for `UtcTime` over its whole documented domain (years 1950-2049), including the 1999/2000 pivot.
- `test_x509_generalized_time_roundtrip_property`: Property: write→parse is the identity for `X509GeneralizedTime` for any representable date (years 0-9999).
- `test_generalized_time_roundtrip_property`: Property: write→parse is the identity for `GeneralizedTime`, including arbitrary sub-second precision (nanoseconds in [1, 999_999_999]).
- `test_owned_bigint_roundtrip_property`: Property: write→parse is the identity for `OwnedBigInt` over values wider than any machine type the crate parses directly.
- `test_owned_biguint_roundtrip_property`: Property: write→parse is the identity for `OwnedBigUint`.
- `test_bigint_bit_length_oracle`: Property (oracle): `BigInt::bit_length` and `BigInt::is_negative` agree with values computed directly from an `i128` (bit length of the magnitude; 0 for 0), for the full `i128` range including MIN/MAX and powers of two.
- `test_set_of_roundtrip_property`: Property: `SetOfWriter` write→`SetOf` parse yields the same multiset of values, and the parsed iteration order is sorted by DER encoding (the SET OF canonical order).
- `test_set_of_unordered_rejected`: Property (validation/rejection): a SET OF whose elements are not in ascending DER-encoding order must be rejected by the parser.
- `test_set_writer_rejects_unordered_writes`: Property (write-side ordering enforcement): `SetWriter`/`SetElementWriter` must refuse to write SET elements in descending DER-encoding order.

## Oracles

## Not tested

## History

- 2026-07-20: predecessor base commit `851dc2e18e90` (Upgrade to syn 3 (#622)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/asn1.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
