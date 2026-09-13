# ciborium

[enarx/ciborium](https://github.com/enarx/ciborium).

## What is tested

**`tests/canonical.rs`**
- `canonical_ordering_matches_serialized_bytes`: `CanonicalValue`'s ordering (i.e. `cmp_value`) matches the documented rule: compare the serialized bytes, shorter first, then lexicographic. The serialized bytes themselves are the independent oracle. Tag-vs-tag comparisons are excluded here: they violate this rule and are pinned by `known_failure_cmp_value_tag_pairs_ignore_length` below.
- `known_failure_cmp_value_tag_pairs_ignore_length`: KNOWN FAILURE: when both values are tags, `cmp_value` compares the tag *numbers* numerically (`Value::from(t).partial_cmp(...)`) instead of following its documented rule that shorter serializations sort first. A 1-byte tag header with long content then sorts before a 2-byte tag header with short content. Besides contradicting the documentation, this makes `CanonicalValue`'s `Ord` intransitive when tags are mixed with other types, e.g.:   A = Tag(0, Bytes(vec![0; 10]))  (12 bytes), B = Tag(24, Null) (3 bytes),   C = Text("abc") (4 bytes)  =>  A < B (tag rule), B < C, C < A (byte rule). Code path: `ciborium/src/value/canonical.rs`, `cmp_value`, `(Tag, Tag)` arm. The generator is pinned to the failing region (1-byte tag + long content vs 2-byte tag + `Null`) so this fails deterministically.
- `canonical_value_is_idempotent`: `canonical_value` is idempotent: canonicalizing an already-canonical value changes nothing. Tag map keys are excluded because of the `cmp_value` tag-ordering bug pinned above.
- `canonical_encoding_is_map_order_independent`: RFC 8949 deterministic encoding: two values that differ only in map entry order produce identical canonical encodings. Map keys are unique (duplicate keys have no canonical order) and exclude tags (bug pinned above).
- `canonical_bytes_decode_to_canonical_value`: Canonical encoding preserves the value: decoding the canonical bytes yields exactly `canonical_value(v)`. Bignum tags excluded (they collapse on decode); tag map keys excluded (cmp_value bug pinned above).

**`tests/codec.rs`**
- `value_bytes_roundtrip`: Encoding any `Value` to CBOR bytes and decoding it back yields the same `Value` (the crate-level roundtrip promise; see the rstest cases above). Tags 2/3 are excluded because ciborium intentionally decodes bignum tags into `Value::Integer`/normalized bignums (the "Not In RFC" cases).
- `value_serializer_is_identity`: `Value::serialized` and `Value::deserialized` act as the identity on `Value` itself, including bignum tags (which only collapse on the byte path). Evidence: the codec rstest above checks `Value::serialized(&input)` against the expected `Value` for every case.
- `derived_types_roundtrip`: Serde-derived types roundtrip through both the byte path (`into_writer`/`from_reader`) and the dynamic path (`Value::serialized`/`Value::deserialized`).
- `i128_bytes_roundtrip`: Any `i128` roundtrips through CBOR: values within the 64-bit wire range use plain (major type 0/1) encoding, larger magnitudes use bignum tags (evidence: the 18446744073709551616i128 / -18446744073709551617i128 rstest cases above).
- `u128_bytes_roundtrip`: Any `u128` roundtrips through CBOR (bignum tag 2 above `u64::MAX`).
- `integer_encoding_is_smallest`: Integers are always serialized to the smallest lossless width (crate-level "Always Serialize Numeric Values to the Smallest Size" design promise), with major type 0 for non-negative and 1 for negative.
- `float_encoding_is_lossless_and_small`: Floats are encoded at a smaller width only when lossless, and always decode back to the exact same bits (crate-level design promise: "This coercion is **always** lossless ... only ... if coercion back to the original size has the same raw bits").

**`tests/error.rs`**
- `decoding_arbitrary_bytes_never_panics`: Decoding arbitrary bytes never panics, whatever the target type (parse robustness; same property as the fork-based fuzz test in tests/fuzz.rs, but with shrinking).
- `strict_prefix_of_valid_encoding_is_an_error`: CBOR is self-delimiting, so no strict prefix of a valid encoding is a valid encoding: decoding a truncation must fail (and not panic). Evidence: all the truncated-input rstest cases above expect errors.
- `trailing_bytes_after_one_item_are_ignored`: `from_reader` consumes exactly one item from the reader: bytes after a complete encoding do not affect the decoded value.

## Oracles

## Not tested

## History

- 2026-06-18: predecessor base commit `00279e48e75e` (build(deps): bump actions/checkout from 6 to 7).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/ciborium.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
