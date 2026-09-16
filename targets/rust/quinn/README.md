# quinn

[quinn-rs/quinn](https://github.com/quinn-rs/quinn).

## What is tested

**`src/cid_queue.rs`**
- `cid_queue_retires_each_sequence_at_most_once`: (no doc comment)

**`src/frame.rs`**
- `ack_roundtrip`: Roundtrip: any non-empty set of packet-number ranges, any delay, and any ECN counts encode to a single ACK frame that decodes to exactly the same ranges, delay, and counts. Generalizes the `ack_coding` unit test above.
- `frame_iter_never_panics`: Parse robustness: the frame iterator must never panic on arbitrary payload bytes — frame payloads come straight off the network after decryption.

**`src/packet.rs`**
- `pn_wire_roundtrip`: Any encoded packet number of any width survives a wire roundtrip, its encoding is exactly `len()` bytes, and the wire tag agrees with `len()` via `decode_len`. Generalizes `roundtrip_packet_numbers` above.
- `pn_new_expand_recovers_original`: RFC 9000 Appendix A: a packet number truncated relative to `largest_acked` is recovered exactly by `expand(expected)` for any decoder reference point `expected` between `largest_acked` and the packet number itself. Generalizes the exhaustive small-range `pn_expand_roundtrip` above to the full packet number space (packet numbers are < 2^62, RFC 9000 §12.3).
- `partial_decode_accounts_for_every_byte`: Port of `fuzz/fuzz_targets/packet.rs`: `PartialDecode::new` never panics on arbitrary input, and on success every input byte is accounted for exactly once between the decoded packet and the returned trailing datagram bytes.

**`src/range_set/btree_range_set.rs`**
- `replace_empty_range_corrupts_set`: FAILING (documents a real bug): `RangeSet::replace` does not treat an empty input range as a no-op the way `insert`/`remove` do (both guard `if x.is_empty() { return false; }`). Instead its `Replace` iterator's `Drop` unconditionally inserts `range.start..range.end`, so `replace(x..x)` stores a degenerate `x -> x` entry. Afterwards the set contains no elements yet `is_empty()` reports `false` and `peek_min()`/`min()` report a phantom `x..x` range — corrupting the invariant that a `RangeSet` never holds empty ranges. Reachable in production: `Assembler::insert` (assembler.rs) calls `recvd.replace(offset..offset + bytes.len())` while in unordered-read mode; an empty STREAM frame makes `bytes.len() == 0` and passes an empty range. The property below is grounded in the `insert`/`remove` empty-range guards and the documented `RangeSet` invariant.

**`src/range_set/tests.rs`**
- `range_sets_match_element_model`: (no doc comment)

**`src/tests/mod.rs`**
- `stream_id_roundtrip`: Port of `fuzz/fuzz_targets/streamid.rs`, extended per `StreamId`'s accessor docs: a stream ID built from (initiator, direction, index) returns exactly those three components, and survives the `VarInt` wire conversion. Indexes are bounded by `MAX_STREAM_COUNT` = 2^60 (RFC 9000 §4.6).
- `stream_data_integrity_across_simulated_link`: Data integrity over the simulated network: any payload, written in arbitrary chunks with arbitrary interleaved link-driving, over a link with arbitrary MTU (>= QUIC's required 1200) and latency, is delivered exactly and in order. Built on the same `Pair` harness and stream API as `finish_stream_simple`.

**`src/transport_parameters.rs`**
- `params_write_read_roundtrip`: Roundtrip: any valid parameter set, serialized in any parameter order and with any grease parameter, is decoded back identically by a client. Generalizes the `coding` unit test above; `fuzz/fuzz_targets/params.rs` shows the maintainers consider `read` worth fuzzing.
- `params_read_never_panics`: Port of `fuzz/fuzz_targets/params.rs`: `read` must never panic, whether fed arbitrary garbage or a mutation of a valid encoding.

**`src/varint.rs`**
- `varint_encode_decode_roundtrip`: Roundtrip: `decode(encode(x)) == x` for every representable `VarInt`, and the encoding occupies exactly `size()` bytes. Grounded in the `Codec` contract ("Infallible encoding and decoding of QUIC primitives") and RFC 9000 §16.
- `varint_decode_arbitrary_bytes`: Parse robustness: `decode` never panics on arbitrary bytes, and any successfully decoded value is in bounds (< 2^62, the documented invariant of the type) and value-roundtrips through encode/decode. Grounded in `VarInt`'s "integer less than 2^62" doc contract; varints are parsed from untrusted network data.

## Oracles

## Not tested

## History

- 2026-07-20: predecessor base commit `fec2f8960df4` (build(deps): bump rustls from 0.23.41 to 0.23.42).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/quinn.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped fec2f8960df4 → 621e38abbccd (2026-09-10, "proto: reject transport parameters with a mismatched length"; 0.12.0); 1 bug(s) still reproduce. 332 tests pass.
- 2026-09-14: base bumped 621e38abbccd → a28cf43a1711 (2026-09-14, "build(deps): bump rustls from 0.23.43 to 0.23.44"; 0.12.0); 1 bug(s) still reproduce. 332 tests pass.
- 2026-09-14: base bumped a28cf43a1711 → 769ef759a35d (2026-09-14, "build(deps): bump aws-lc-rs from 1.18.0 to 1.18.1"; 0.12.0); 1 bug(s) still reproduce. 332 tests pass.
- 2026-09-16: base bumped 769ef759a35d → 5358e3463ab5 (2026-09-16, "fix: cleanup state if transmit failed"; 0.12.0); 0 bug(s) still reproduce; fixed upstream: quinn/1. 335 tests pass.
