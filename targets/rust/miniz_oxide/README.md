# miniz_oxide

[Frommi/miniz_oxide](https://github.com/Frommi/miniz_oxide).

## What is tested

**`tests/flush.rs`**
- `hegel_streaming_deflate_flush_points_roundtrip`: Compressing via the streaming `deflate::stream::deflate` API with arbitrary chunk splits, a drawn flush type at every split, and a small output buffer must still produce a stream that decompresses back to the original data.

**`tests/test.rs`**
- `hegel_roundtrip_any_level_window_strategy`: Compress -> decompress is the identity for every compression level, window setting and strategy accepted by `create_comp_flags_from_zip_params`.
- `hegel_streaming_inflate_tiny_buffers_matches_oneshot`: Streaming inflate with tiny drawn input/output buffers agrees with the one-shot decompression functions.
- `hegel_inflate_state_reset_reuse`: An `InflateState` can be reused for a fresh stream after any reset policy.
- `hegel_decompress_arbitrary_bytes_no_panic`: Decompressing arbitrary bytes must return, never panic.
- `hegel_decompress_truncated_stream_errors`: A strict prefix of a valid compressed stream must fail to decompress (the end-of-stream marker is always cut off), and must never panic.
- `hegel_decompress_bitflip_no_panic`: Flipping any single bit of a valid compressed stream must never cause a panic when decompressing (it may or may not decode successfully).
- `hegel_decompress_limit_respected`: `decompress_to_vec_*_with_limit` succeeds iff the limit is at least the decompressed size, and failure reports `HasMoreOutput` with a partial output no larger than the limit.
- `hegel_zlib_wrapper_structure`: The zlib wrapper written by `compress_to_vec_zlib` is structurally valid: correct header check bits, a deflate body that raw-decompresses to the input, and a big-endian adler32 trailer matching the input checksum.
- `hegel_decompress_slice_iter_chunked`: `decompress_slice_iter_to_slice` over drawn chunkings of the compressed input agrees with one-shot decompression.

## Oracles

## Not tested

## History

- 2026-07-20: predecessor base commit `fed739a8c7fe` (try fuzz again).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/miniz_oxide.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
