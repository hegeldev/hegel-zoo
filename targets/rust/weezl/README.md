# weezl

[image-rs/weezl](https://github.com/image-rs/weezl).

## What is tested

**`tests/fuzz_panic_regression.rs`**
- `hegel_decode_arbitrary_bytes_never_panics`: Property: the decoder handles completely arbitrary input bytes, for every configuration (order × size 0..=12 × tiff × yield_on_full), by returning `Ok` or `Err` — it must never panic. Generalizes the crate's `decode0` fuzz target across all configurations.
- `hegel_bitflip_corrupted_stream_never_panics`: Property: flipping a single bit in a *valid* encoded stream must not panic the decoder (wrong output or `InvalidCode` are both fine). Near-valid streams reach much deeper decode paths than random bytes; this generalizes the fixed single-bit-flip finding pinned by `corrupt_input_does_not_panic_in_derive_burst` above.

**`tests/roundtrip.rs`**
- `hegel_stream_encode_matches_vec_encode`: Property: encoding through `into_stream` — with a drawn intermediate buffer size and a writer that accepts only tiny writes — produces byte-identical output to the one-shot `encode` (both append an end marker), i.e. the stream and buffer APIs agree.
- `hegel_stream_decode_roundtrips_with_drawn_buffers`: Property: decoding through `into_stream` — with a drawn intermediate buffer size and tiny reader chunks — reproduces the original payload, i.e. the stream decode agrees with the buffer APIs for any buffer sizing choices.

**`tests/roundtrip_vec.rs`**
- `hegel_roundtrip_generated_config`: Property: encode→decode is the identity for every generated configuration (bit order × min code size × TIFF flavor) and every payload whose symbols fit the alphabet, per the crate docs: "you must use the same arguments to `Encoder` and `Decoder`".
- `hegel_chunked_encode_bytes_matches_oneshot`: Property: driving the sans-IO `encode_bytes` with arbitrary small input-chunk and output-buffer sizes produces exactly the same encoded bytes as the one-shot `encode` convenience method. The `Encoder` docs promise the same state machine works with "streams as well as your own buffers and driver logic".
- `hegel_chunked_decode_bytes_matches_oneshot`: Property: driving the sans-IO `decode_bytes` with arbitrary small input-chunk and output-buffer sizes reproduces the original payload, like the one-shot `decode`. Mirrors `hegel_chunked_encode_bytes_...` on the decode side.
- `hegel_truncated_stream_decodes_to_prefix`: Property: decoding a truncated prefix of a valid stream is not an error (with the non-finishing `IntoVec::decode`) and yields a prefix of the original payload — LZW decoding is deterministic and prefix-preserving, and truncation at a byte boundary can only lose codes, not corrupt them.
- `hegel_trailing_garbage_after_end_marker_is_ignored`: Property: `decode` stops at the end marker, so arbitrary trailing garbage after a complete stream does not change the result. Evidence: `Decoder::has_ended` docs ("No more output is produced beyond the end code ... excess bytes provided") and `IntoVec::decode_all` ("read data until the slice is empty or an end marker is reached").
- `hegel_encoder_rejects_out_of_alphabet_byte`: Property: a byte that is "not smaller than `1 << size`" makes encoding fail, and (per the `encode_bytes` docs) "all bytes up to but not including the offending byte have been consumed".
- `hegel_encoder_reset_matches_fresh`: Property: `Encoder::reset` produces "an encoder as if just constructed with `new`" — encoding A on a fresh encoder equals encoding B, resetting, then encoding A on a reused encoder.
- `hegel_decoder_reset_matches_fresh`: Property: `Decoder::reset` produces "a decoder as if just constructed with `new`" — decoding a stream after decoding another stream plus `reset` equals decoding it fresh.

**`tests/yield_on_full_regression.rs`**
- `hegel_yield_on_full_matches_straight_decode`: Property: for any configuration, payload and output-buffer size, a `yield_on_full_buffer(true)` decoder driven with a fixed-size output buffer produces exactly what a straight decode produces (which in turn round-trips the payload). Generalizes the fuzz-minimized regressions above via the same helpers.

## Oracles

## Not tested

## History

- 2026-05-15: predecessor base commit `606f9c79b054` (Merge pull request #82 from image-rs/release-0.2.1).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/weezl.patch`).
- 2026-09-11: imported into the zoo; ported to hegeltest 0.44.1.
