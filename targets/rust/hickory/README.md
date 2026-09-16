# hickory

[hickory-dns/hickory-dns](https://github.com/hickory-dns/hickory-dns).

## What is tested

**`src/op/message.rs`**
- `hegel_message_roundtrip`: Property: a structurally valid Message encodes and decodes back to itself. Evidence: `test_emit_and_read_*` above check this for fixed messages, and the repository's `fuzz/fuzz_targets/message.rs` asserts the same round-trip starting from arbitrary decodable bytes.
- `hegel_message_from_vec_never_panics`: Property: `Message::from_vec` never panics — neither on arbitrary bytes nor on corruptions/truncations of a valid encoded message. Evidence: both fuzz targets in `fuzz/fuzz_targets/` feed arbitrary bytes to message decoding; `rdata_zero_roundtrip` and `nsec_deserialization` above are fixed regression cases for hostile inputs.

**`src/rr/domain/label.rs`**
- `hegel_label_constructors_never_panic`: Property: none of the `Label` constructors panic, whatever input they are fed. Evidence: all three constructors return `ProtoResult` (their docs describe returning errors for invalid input); `from_utf8` feeds arbitrary user text through the `idna` crate (see `IntoLabel for &str`).

**`src/rr/domain/name.rs`**
- `hegel_name_wire_roundtrip`: Property: a Name emitted to wire format reads back as the same name. Evidence: `test_read`/`test_write_to` above check this for four fixed examples; `Name::encoded_len` documents that `is_fqdn` is ignored on the wire (every wire name is terminated by the root label), so the decoded name is always an FQDN.
- `hegel_name_compression_roundtrip`: Property: emitting many (frequently suffix-sharing) names through one encoder — which exercises name compression, on by default — and decoding them in order returns the original names, byte-for-byte including ASCII case. Evidence: `test_pointer` and `test_pointer_with_pointer_ending_labels` above; `BinEncoder::get_label_pointer` matches candidate labels byte-exactly, so compression must preserve case.
- `hegel_name_read_never_panics`: Property: `Name::read` never panics, whatever bytes it is fed. Evidence: the repository's fuzz targets decode messages from arbitrary bytes; `test_recursive_pointer`/`test_bin_overlap_enforced` above show hostile inputs are expected to produce `Err`, not panics.
- `hegel_name_to_ascii_from_ascii_roundtrip`: Property: `Name::from_ascii` parses `Name::to_ascii` output back to the same name (case-sensitively, preserving the FQDN flag). Evidence: `to_ascii` escapes exactly so the name can be represented as a safe string (`test_ascii_escape` above), `from_ascii`'s doc examples parse escaped labels (`bad\056char`), and `to_utf8` documents that the output "could be used with parse".
- `hegel_name_to_ascii_from_ascii_roundtrip_safe_labels`: Weaker version of the property above, restricted to labels made of characters that `Label::from_ascii` accepts unescaped (`is_safe_ascii`), plus embedded dots, which exercise the `\.` escape. This pins down the subset of the presentation-format round-trip that does hold.
- `hegel_name_cmp_matches_rfc4034_reference`: Property: `Name::cmp` agrees with an independently written RFC 4034 §6.1 reference comparison. Evidence: the RFC text quoted on `Ord for Name`, and `test_partial_cmp` above.
- `hegel_name_case_insensitive_eq_implies_hash_eq`: (no doc comment)
- `hegel_name_trim_to_is_zone_of`: Property: any trailing part of a name (as produced by `trim_to`) is a zone of the name, even when its ASCII case differs. Evidence: `zone_of` docs ("returns true if the name components of self are all present at the end of name") and its use of `eq_ignore_ascii_case`; `trim_to` docs show it keeps the trailing labels.
- `hegel_ip_to_arpa_name_parses_back`: Property: converting an IP address to its reverse-DNS name parses back to the same address with a full-length prefix. Evidence: `From<Ipv4Addr>/From<Ipv6Addr> for Name` and `parse_arpa_name` are documented as a conversion pair; `test_from_ipv4`/`test_from_ipv6` and `test_parse_arpa_name` above check fixed examples.
- `hegel_name_from_str_relaxed_never_panics`: Property: `Name::from_str_relaxed` (the `FromStr` impl) never panics on arbitrary text. Evidence: `FromStr` is the crate's user-facing string entry point (used by `IntoName for &str`); parsers returning `Result` promise Err, not panics.

**`src/rr/serial_number.rs`**
- `hegel_serial_addition_orders_correctly`: Property: RFC 1982 §3.1 — adding n with 0 < n < 2^31 to a serial number yields a serial number greater than the original, across the u32 wrap-around. Evidence: the `Add` impl above cites "Serial Number Addition, see RFC 1982, section 3.1" and `PartialOrd` cites section 3.2.
- `hegel_serial_cmp_antisymmetric`: Property: RFC 1982 §3.2 comparison is antisymmetric, and is undefined exactly when the two serial numbers are 2^31 apart. Evidence: RFC 1982 §3.2 ("the order of two numbers differing by 2^(SERIAL_BITS-1) is undefined"), cited by the `PartialOrd` impl above.

## Oracles

## Not tested

## History

- 2026-07-22: predecessor base commit `1b78772fcad0` (Include CNAME records when calculating minimum TTL for caching purp...).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/hickory.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1. Thirteen upstream `assert_eq!(Nu8, x.into())` in `#[cfg(test)]` code of `rr/rdata/sshfp.rs` rewritten as `u8::from(x)`: hegeltest 0.44 pulls in `serde_json`, whose `PartialEq<Value> for u8` makes the `.into()` target ambiguous (E0282/E0283). The failing round-trip test was already failing for the predecessor (its report calls it a suspected bug); recorded as `hickory/1`.
- 2026-09-13: base bumped 1b78772fcad0 → 254f95d3a021 (2026-09-11, "proto: preserve the OPT record when truncating responses"; 0.27.0-alpha.1); 1 bug(s) still reproduce. 290 tests pass. The patch's test module in `crates/proto/src/rr/serial_number.rs` was renamed `hegel_tests` because upstream added its own `mod tests` there.
- 2026-09-14: base bumped 254f95d3a021 → b78ac510a14d (2026-09-14, "proto: truncate encoding after rollback"; 0.27.0-alpha.1); 1 bug(s) still reproduce. 291 tests pass.
- 2026-09-14: base bumped b78ac510a14d → e640429a586b (2026-09-14, "bin: refuse to treat empty zone as root"; 0.27.0-alpha.1); 1 bug(s) still reproduce. 291 tests pass.
- 2026-09-14: base bumped e640429a586b → 5276716c9f4b (2026-09-14, "Change default group setting"; 0.27.0-alpha.1); 1 bug(s) still reproduce. 291 tests pass.
- 2026-09-14: base bumped 5276716c9f4b → 1b1084e2a0b4 (2026-09-14, "Update rustls"; 0.27.0-alpha.1); 1 bug(s) still reproduce. 291 tests pass.
- 2026-09-14: base bumped 1b1084e2a0b4 → 96469219f3a3 (2026-09-14, "SVCB: Reject extra data in SvcParamValue"; 0.27.0-alpha.1); 1 bug(s) still reproduce. 292 tests pass.
- 2026-09-15: base bumped 96469219f3a3 → 0a67a39db05f (2026-09-15, "Fix disabling optional server timeouts"; 0.27.0-alpha.1); 1 bug(s) still reproduce. 292 tests pass.
- 2026-09-16: base bumped 0a67a39db05f → a0b6fecbdf09 (2026-09-16, "`NoConnections` error no longer hides useful io errors"; 0.27.0-alpha.1); 1 bug(s) still reproduce. 292 tests pass.
