# plist

[ebarnard/rust-plist/](https://github.com/ebarnard/rust-plist/).

## What is tested

**`src/value.rs`**
- `xml_roundtrip_recovers_value`: Property: writing a `Value` as XML and reading it back yields an equal `Value`, and re-serializing yields byte-identical XML (round-trip is a fixpoint).
- `binary_roundtrip_recovers_value`: Property: writing a `Value` as a binary plist and reading it back yields a bit-exact equal `Value`, and re-serializing yields identical bytes.
- `xml_and_binary_encodings_agree`: Property: a `Value` written as XML and as binary reads back to the same value from both encodings.
- `integer_boundary_values_roundtrip_both_formats`: Property: boundary integers (i64::MIN/MAX, u64::MAX, 0, ±1, ...) round-trip exactly through both encodings.
- `real_boundary_values_roundtrip_both_formats`: Property: every `f64` bit pattern round-trips bit-exactly through the binary encoding, and through the XML encoding up to NaN canonicalization.
- `date_with_nanoseconds_roundtrips_xml_exactly`: Property: dates with nanosecond precision round-trip exactly through the XML encoding (RFC 3339 carries up to 9 subsecond digits).
- `date_binary_roundtrip_within_f64_precision`: Property: dates round-trip through the binary encoding to within the precision of the format. The binary format stores dates as an `f64` of seconds since the year 2001, so sub-second precision inherently degrades with distance from that epoch (~4µs per ULP at 545 years away, found by a high-count run of this test); the round-trip error must never exceed ~2 ULPs of that representation.
- `string_edge_codepoints_roundtrip_both_formats`: Property: strings built from arbitrary codepoints — deliberately including ASCII controls, C1 controls, unicode line separators and non-characters, which sit just outside the XML writer's escape set and on the boundary between the binary format's ASCII and UTF-16 representations — round-trip through both encodings.

**`tests/fuzzer.rs`**
- `arbitrary_bytes_decode_never_panics`: Property: decoding arbitrary bytes returns `Ok` or `Err` but never panics, hangs or makes an unbounded allocation. This supplements the libFuzzer targets in fuzz/fuzz_targets with an always-on version, and additionally boosts inputs that start with the binary plist magic so the binary reader (offset table, trailer parsing) is exercised, not just format detection.
- `corrupted_binary_trailer_never_panics`: Property: a valid binary plist whose trailer fields (offset size, ref size, object count, root object ref, offset table offset — all attacker-controlled) are overwritten with arbitrary values must be handled gracefully: `Ok` or `Err`, never a panic or an allocation driven by the corrupted field.
- `inflated_object_count_is_rejected`: Property: inflating the trailer's object count beyond the real one is always rejected with an error (the offset table cannot contain that many entries), and in particular a huge count must not cause a huge up-front allocation.
- `corrupted_valid_plist_never_panics`: Property: flipping or truncating bytes of a valid plist (either encoding) is handled gracefully — `Ok` or `Err`, never a panic.
- `deeply_nested_xml_parses_without_stack_overflow`: Property: deeply nested XML plists (arrays or dicts) parse without stack overflow — `Ok` when well formed, `Err` when unclosed — at depths into the tens of thousands.

## Oracles

## Not tested

## History

- 2026-07-04: predecessor base commit `2881e175b61f` (Release v1.10.0).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/plist.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped 2881e175b61f → 10ba3e3b44ad (2026-09-06, "Release v1.10.1 (#201)"; 1.10.1); 1 bug(s) still reproduce; 1 ignored reproducer(s) not run. 109 tests pass.
