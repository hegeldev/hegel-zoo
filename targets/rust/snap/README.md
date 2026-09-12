# snap

[BurntSushi/rust-snappy](https://github.com/BurntSushi/rust-snappy).

## What is tested

**`tests.rs`**
- `hegel_roundtrip_raw`: Property: raw compress -> decompress is the identity. Port of `qc_roundtrip` (which ran 1000 cases; count carried over), with structured rather than purely arbitrary payloads.
- `hegel_roundtrip_frame_chunked_writes`: Property: write::FrameEncoder followed by read::FrameDecoder is the identity, no matter how the input is split across write calls and regardless of intervening flushes. Port of `qc_roundtrip_stream` (1000 cases carried over), strengthened: the original used a single write_all and discarded empty inputs.
- `hegel_read_write_frame_encoders_agree`: Property: read::FrameEncoder and write::FrameEncoder produce identical compressed bytes for the same input (when written in one shot). Generalizes the per-corpus `read_and_write_frame_encoder_match` tests.
- `hegel_frame_decoder_small_buffers`: Property: reading a frame stream through read::FrameDecoder with a small caller buffer yields the same bytes as reading it whole.
- `hegel_read_frame_encoder_small_buffers`: Property: reading compressed bytes from read::FrameEncoder with a small caller buffer yields the same bytes as reading it whole. Generalizes `read_frame_encoder_big_and_little_buffers` (which tested sizes 5 and 1_000_000 on one corpus file).
- `hegel_raw_decompress_never_panics`: Property: the raw decoder never panics, whatever the input: arbitrary bytes, or a valid compression with one bit flipped. It may return an error or (for lucky corruptions) different data, but must not crash.
- `hegel_frame_decoder_never_panics`: Property: read::FrameDecoder never panics, whatever the input: arbitrary bytes, arbitrary bytes behind a valid stream header, or a valid stream with one bit flipped.
- `hegel_frame_truncation_prefix_or_error`: Property: decoding a truncated frame stream either fails or yields a prefix of the original data (truncation at a chunk boundary legally yields the leading chunks; truncation mid-chunk must error).
- `hegel_decompress_len_matches_original`: Property: decompress_len reports exactly the original input length for any valid compression (documented: "Returns the decompressed size (in bytes) of the compressed bytes given").
- `hegel_max_compress_len_bound`: Property: compressed output never exceeds max_compress_len, the bound compress() documents callers must allocate.
- `hegel_concatenated_frames`: Property: concatenated frame streams decode to the concatenated data (the framing format allows a new stream identifier mid-stream, and FrameDecoder accepts it after the first chunk).
- `hegel_encoder_reuse_deterministic`: Property: reusing an Encoder across inputs produces the same bytes as a fresh Encoder ("It is beneficial to reuse an Encoder when possible" implies reuse must not change the output).

## Oracles

## Not tested

## History

- 2026-07-15: predecessor base commit `29fcab53647b` (1.1.2).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/snap.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
