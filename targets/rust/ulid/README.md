# ulid

[dylanhart/ulid-rs](https://github.com/dylanhart/ulid-rs).

## What is tested

**`src/generator.rs`**
- `prop_generator_monotonic`: The generator's documented guarantee: "Each call is guaranteed to provide a Ulid with a larger value than the last call", for arbitrary timestamp sequences — including repeated and backwards clocks.

**`src/lib.rs`**
- `prop_string_roundtrip`: Crown roundtrip: any u128 encodes to a 26-char string which parses back to the same Ulid via every parsing entry point, including the lowercase form (Crockford base32 decoding is case-insensitive).
- `prop_integer_conversions_roundtrip`: u128, big-endian bytes, and (u64, u64) conversions are all bijective views of the same 128 bits (std's to_be_bytes/shifts as the oracle).
- `prop_from_parts_roundtrip`: `from_parts` keeps exactly the low 48 timestamp bits and low 80 random bits ("Any overflow bits in the given args are discarded"), and `timestamp_ms`/`random` recover them. For in-width inputs the masks are identities, so this subsumes the exact roundtrip.
- `prop_from_string_rejects_wrong_length`: Strings whose length is not exactly 26 are rejected with InvalidLength, even when every character is valid Crockford base32.
- `prop_from_string_rejects_invalid_char`: Corrupting one character of a valid encoding with a non-Crockford ASCII byte (boosting the deliberately excluded letters I, L, O, U) is rejected with InvalidChar.
- `prop_from_string_never_panics`: `from_string` returns (never panics) on arbitrary text.
- `prop_valid_string_canonical_roundtrip`: Any in-range 26-char Crockford string (first char '0'..='7', mixed case) decodes, and re-encoding yields its uppercase canonical form — i.e. decode is injective on in-range strings modulo case.
- `prop_from_string_rejects_out_of_range`: 26 Crockford base32 chars encode 130 bits, but a Ulid has only 128: the ULID spec caps ULIDs at "7ZZZZZZZZZZZZZZZZZZZZZZZZZ" (which is Ulid::max()), so any string whose first char encodes 8..=31 denotes a value >= 2^128 and must be rejected rather than silently truncated. KNOWN FAILURE — real bug, deliberately left failing: `base32::decode` never checks the two overflow bits, so every out-of-range string is accepted and its top two bits are silently discarded. Minimal counterexample: "80000000000000000000000000" decodes to Ok(Ulid(0)), i.e. it collides with "00000000000000000000000000". This violates the ULID spec ("Any attempt to decode or encode a ULID larger than [7ZZZZZZZZZZZZZZZZZZZZZZZZZ] should be rejected ... to prevent overflow bugs") and makes from_string non-injective. The failure is deterministic: every input this generator draws is out of range, so the property fails on the first case of every run.
- `prop_string_order_matches_value_order`: "Lexicographically sortable": comparing two Ulids as strings gives the same ordering as comparing their 128-bit values.
- `prop_timestamp_order_implies_string_order`: A Ulid with a strictly larger timestamp sorts strictly later as a string, regardless of the random parts (the documented reason the timestamp occupies the high bits).
- `prop_increment`: `increment` bumps the random part and keeps the timestamp; when the random part is maxed it returns the overflowed (next-millisecond) Ulid in Err, saturating at Ulid::max.

**`src/time.rs`**
- `prop_datetime_roundtrip`: For any representable millisecond instant (48 bits), a Ulid created at that instant reports exactly that instant back through both timestamp_ms() and datetime(), regardless of the random bits.

## Oracles

## Not tested

## History

- 2026-07-15: predecessor base commit `6018cb8d158a` (Add changelog).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/ulid.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
