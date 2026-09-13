# ruzstd

[KillingSpark/zstd-rs](https://github.com/KillingSpark/zstd-rs).

## What is tested

**`src/tests/mod.rs`**
- `prop_reference_encode_ruzstd_decode_roundtrip`: Property 1 (crown roundtrip): anything the reference C encoder produces, ruzstd's StreamingDecoder must decode back to the original bytes exactly, at any compression level.
- `prop_bulk_frame_content_size_and_decode_all`: Property 2: frames with a pinned content size (the bulk API always writes Frame_Content_Size) must report that size through `content_size()` and decode losslessly through `decode_all`.
- `prop_arbitrary_bytes_never_panic`: Property 3 (robustness, oracle-independent): arbitrary bytes -- pure garbage, magic-prefixed garbage, or a truncated valid frame with a garbage tail -- must never panic the decoder. Errors are fine. Output reading is capped so a decompression bomb becomes a bounded read, not an OOM abort.
- `prop_corrupted_frame_graceful_and_agrees_with_c`: Property 4 (corruption + differential): take a valid frame, flip bytes or truncate it. ruzstd must handle it gracefully (Err or Ok, no panic/hang), and whenever both ruzstd and the C decoder accept the whole corrupted input, they must produce identical output (the format fully determines decoding). Accept/reject is deliberately NOT compared: ruzstd defaults to a 100 MiB window cap (libzstd: 128 MiB), does not verify checksums, and stops after the first frame, so acceptance can legitimately differ.
- `prop_skippable_frames_are_skipped`: Property 5 (skippable frames per spec): skippable frames (magic 0x184D2A50..=0x184D2A5F + LE length + payload) interleaved with real frames contribute nothing to the output; `decode_all` must return exactly the concatenation of the real frames' content. The C decoder is run as a second witness.
- `prop_chunked_source_reads_equal_oneshot`: Property 6 (source chunking is invisible): decoding the same frame through a reader that returns arbitrarily small chunks, into arbitrarily sized output buffers, must give the same bytes as a one-shot decode. Exercises the short-read/resume paths.
- `prop_decode_from_to_resumable`: Property 7 (decode_from_to is resumable): feeding a valid frame to the old-style push API in arbitrary source increments and draining into an arbitrarily small target must reproduce the original content, making progress at every step.
- `prop_frame_header_magic_classification`: Property 8 (frame header / magic number classification): `read_frame_header` must never panic on arbitrary bytes; skippable magics must be reported as SkipFrame with the exact declared length, and any other non-zstd magic as BadMagicNumber.
- `prop_declared_window_gate`: Property 9 (anti-bomb window gate, oracle-independent): a frame header declaring a window (window descriptor, or Frame_Content_Size in single-segment mode) larger than the decoder's limit must be rejected at init -- before any decompression -- and one within the limit must be accepted. The expected window size is transcribed from the spec's formula as an independent oracle.

## Oracles

## Not tested

## History

- 2026-07-22: predecessor base commit `e7cc3b92895f` (Remove `compiler-builtins` from `rustc-dep-of-std` dependencies (#113)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/ruzstd.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped e7cc3b92895f → 1f76b371c69d (2026-09-04, "Decrease memory usage"; 0.9.1); 0 bug(s) still reproduce. 88 tests pass.
- 2026-09-13: base bumped 1f76b371c69d → fe37617b53d6 (2026-09-13, "avoid allocating bigger buffers by adding the sentinel after rounding up"; 0.9.1); 0 bug(s) still reproduce. 88 tests pass.
