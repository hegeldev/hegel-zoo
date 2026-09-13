# brotli

[dropbox/rust-brotli](https://github.com/dropbox/rust-brotli).

## What is tested

**`src/enc/test.rs`**
- `test_hegel_oneshot_roundtrip`: (no doc comment)
- `test_hegel_compressor_writer_streaming_roundtrip`: (no doc comment)
- `test_hegel_compressor_reader_streaming_roundtrip`: (no doc comment)
- `test_hegel_decompressor_reader_matches_oneshot`: (no doc comment)
- `test_hegel_decompressor_writer_streaming_roundtrip`: (no doc comment)
- `test_hegel_decompress_arbitrary_bytes_never_panics`: (no doc comment)
- `test_hegel_truncated_stream_errors`: (no doc comment)
- `test_hegel_bitflip_never_panics`: (no doc comment)
- `test_hegel_custom_dictionary_roundtrip`: (no doc comment)
- `test_hegel_brocatli_concat_roundtrip`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-06-14: predecessor base commit `9651aa3ebfd2` (Fix version bump).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/brotli.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
