# borsh

[near/borsh-rs](https://github.com/near/borsh-rs).

## What is tested

**`tests/deserialization_errors/test_initial.rs`**
- `prop_bool_byte_canonical`: A bool byte deserializes to false/true for 0/1 and errors otherwise.
- `prop_option_tag_canonical`: An Option tag other than 0/1 is rejected regardless of payload.
- `prop_result_tag_canonical`: A Result tag other than 0 (Err) / 1 (Ok) is rejected.

**`tests/roundtrip/requires_derive_category/test_combined_properties.rs`**
- `prop_rich_roundtrip`: serialize -> deserialize round-trip for the rich combined type.
- `prop_rich_wire_format_matches_spec`: The encoding matches an independent transcription of the BORSH spec.
- `prop_rich_object_length_matches_serialized_len`: `object_length` agrees with the length of the actual serialization.
- `prop_rich_encoding_is_injective`: Canonicality, injectivity direction: distinct values have distinct encodings. Alongside independent pairs, single-field mutations of one value are generated to concentrate on near-collisions.
- `prop_rich_strict_prefix_rejected`: Every strict prefix of a valid encoding must fail to deserialize: the format is deterministic, so a truncated buffer either hits EOF or (via `from_slice`'s full-consumption check) leaves the parse short.
- `prop_plain_accepted_bytes_are_canonical`: Canonical-acceptance property (validation/rejection pattern): any byte string the deserializer accepts must re-serialize to exactly the same bytes. Inputs are single-byte corruptions of valid encodings (to land near the accept/reject boundary) plus arbitrary byte strings.

**`tests/roundtrip/requires_derive_category/test_enum_discriminants.rs`**
- `prop_enum_tag_is_declared_discriminant_and_roundtrips`: The first byte on the wire is the declared discriminant, and the value (with arbitrary payloads) round-trips.
- `prop_undeclared_enum_tag_rejected`: Any tag byte that is not a declared discriminant is rejected, whatever bytes follow it.

**`tests/roundtrip/test_btree_map.rs`**
- `prop_btreemap_key_order_enforcement`: Hand-encode `pairs` as a borsh map and check the ordering contract: strictly ascending keys are always accepted (and decode to exactly those entries); non-ascending keys are rejected under `de_strict_order` and accepted (last key wins) without it.
- `prop_btreeset_item_order_enforcement`: The same ordering contract for sets.

**`tests/roundtrip/test_hash_map.rs`**
- `prop_hashmap_serializes_like_btreemap`: Sibling-implementation agreement: the spec requires HashMap entries to be serialized in ascending key order, which is exactly BTreeMap's iteration order — so serializing the same entries through both types must produce identical bytes (the two impls sort independently).
- `prop_hashset_serializes_like_btreeset`: Same agreement for HashSet vs BTreeSet.
- `prop_hashmap_key_order_enforcement`: Ordering contract on deserialization for HashMap (separate impl from the BTreeMap one): strictly ascending keys always accepted; non-ascending rejected only under `de_strict_order`.

**`tests/roundtrip/test_primitives.rs`**
- `prop_f32_f64_bit_exact_roundtrip_and_le_layout`: Non-NaN floats round-trip bit-exactly (covers -0.0, infinities and subnormals), and the encoding is exactly the little-endian bytes of the IEEE-754 bit pattern (spec oracle).
- `prop_nan_rejected_on_both_sides`: Every NaN bit pattern is rejected by serialization, and its byte encoding is rejected by deserialization (validation/rejection).

**`tests/roundtrip/test_vecs.rs`**
- `prop_rotated_vecdeque_serializes_like_vec`: A VecDeque must serialize exactly like a Vec with the same element order, including when its ring buffer is wrapped around (rotation makes `as_slices()` return two non-empty slices, exercising the two-part serialization path).

## Oracles

## Not tested

## History

- 2026-07-16: predecessor base commit `7fc21fe52d39` (chore: release v1.8.0 (#375)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/borsh.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped 7fc21fe52d39 → c9a2ed489276 (2026-09-10, "test: make isize/usize snapshots pointer-width independent (#382)"; 1.8.1); 0 bug(s) still reproduce; add/add conflicts in borsh/tests/roundtrip/test_primitives.rs resolved by keeping both sides. 199 tests pass.
