# lzma-rs

[gendx/lzma-rs](https://github.com/gendx/lzma-rs).

## What is tested

**`tests/lzma.rs`**
- `prop_lzma_round_trip_structured`: Compress followed by decompress (default options) is the identity.
- `prop_lzma_compress_interops_with_liblzma`: liblzma (independent implementation, via the `lzma` crate) decodes our compressed output back to the original data.
- `prop_lzma_round_trip_generated_unpacked_size_configs`: Round-trip holds for every compatible (encode, decode) unpacked-size configuration pair, not just the default. The valid pairs follow the crate's own `unpacked_size_*` unit tests above.
- `prop_lzma_decompress_arbitrary_bytes_no_panic`: Decompressing arbitrary bytes returns a Result; it never panics.
- `prop_lzma_decompress_corrupted_stream_no_panic`: Decompressing a corrupted (bit-flipped, truncated, or byte-overwritten) valid stream returns a Result; it never panics.
- `prop_lzma_memlimit_zero_rejects_nonempty_output`: With `memlimit: Some(0)`, decompressing any stream that produces at least one output byte fails with a memory-limit error instead of allocating.
- `prop_lzma_stream_chunked_matches_one_shot`: (no doc comment)
- `prop_lzma_stream_arbitrary_bytes_no_panic`: (no doc comment)
- `prop_lzma_stream_allow_incomplete_truncated_yields_prefix`: (no doc comment)
- `prop_lzma_provided_size_takes_prefix_or_errors`: Decoding with `ReadHeaderButUseProvided(Some(m))`: - if `m` is at most the real unpacked length, decoding succeeds and yields   exactly the first `m` bytes of the original data; - if `m` is larger, decoding fails with an error (never panics). The encoder docs note that a provided size is written unchecked, so the decoder must cope with sizes that disagree with the stream.

**`tests/lzma2.rs`**
- `prop_lzma2_round_trip_structured`: LZMA2 compress followed by decompress is the identity.
- `prop_lzma2_decompress_arbitrary_bytes_no_panic`: Decompressing arbitrary bytes as LZMA2 returns a Result; it never panics.
- `prop_lzma2_decompress_corrupted_stream_no_panic`: Decompressing a corrupted valid LZMA2 stream returns a Result; it never panics.

**`tests/xz.rs`**
- `prop_xz_round_trip_structured`: XZ compress followed by decompress is the identity.
- `prop_xz_decompress_arbitrary_bytes_no_panic`: Decompressing arbitrary bytes as XZ returns a Result; it never panics.
- `prop_xz_decompress_corrupted_stream_no_panic`: Decompressing a corrupted valid XZ stream returns a Result (the format is checksummed, so corruption is typically detected); it never panics.

## Oracles

## Not tested

## History

- 2024-05-06: predecessor base commit `1f14478def43` (Remove CARGO_UNSTABLE_SPARSE_REGISTRY from GitHub actions.).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/lzma-rs.patch`).
- 2026-09-11: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: `[run] command` gained `--features stream`: the three `prop_lzma_stream_*` properties are `#[cfg(feature = "stream")]` and had never run in the zoo (the judge reported them NOTRUN in a re-run; the target had never been bumped or re-run since import because upstream has not moved). With the feature on, 74 tests pass, no bug found.
