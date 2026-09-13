# lz4_flex

[pseitz/lz4_flex](https://github.com/pseitz/lz4_flex).

## What is tested

**`src/fastcpy.rs`**
- `test_fast_short_slice_copy`: (no doc comment)

**`src/fastcpy_unsafe.rs`**
- `test_fast_short_slice_copy`: (no doc comment)

**`tests/tests.rs`**
- `hegel_roundtrip_block_and_frame`: Port of the old `proptest_roundtrip` test to hegel. Property: compress ∘ decompress is the identity, for the raw block format, the size-prepended block format, the frame format (both block modes), and cross-checked against the C++ lz4 implementation (see `test_roundtrip`).
- `hegel_prepend_size_consistency`: Property: `compress_prepend_size` output is documented to be the uncompressed size as a little-endian u32 followed by the regular compressed data, and `uncompressed_size` is documented to read that size back and return the rest.
- `hegel_roundtrip_with_dict`: Property: dictionary roundtrip. `compress_prepend_size_with_dict` is documented to be usable in conjunction with `decompress_size_prepended_with_dict` (with the same dictionary on both sides).
- `hegel_compress_into_max_output_size_is_sufficient`: Property: a buffer of exactly `get_maximum_output_size(input.len())` bytes is documented to be large enough for `compress_into` ("output should be preallocated with a size of `get_maximum_output_size`"), so compression into such a buffer must succeed and report a length within the buffer.
- `hegel_compress_table_reuse_roundtrips`: Property: a `CompressTable` is documented to be reusable across many inputs ("Create one table and pass it to `compress_into_with_table` repeatedly"), including a transparent Small -> Large upgrade for inputs >= 64KB. Every compression in such a sequence must still roundtrip; stale table state from a previous input must never leak into the next compression.
- `hegel_decompress_accepts_larger_size_hint`: Property: `decompress` documents that `min_uncompressed_size` "needs to be equal or larger than the uncompressed size" — so any larger size hint must give the same result as the exact one.
- `hegel_frame_roundtrip_any_config`: Property: the frame roundtrip must hold for every configuration expressible through the public `FrameInfo` API — every `BlockSize` variant (all are public and accepted by the encoder), both `BlockMode`s, both checksum options, the optional content size, and the `legacy_frame` flag.
- `hegel_frame_write_chunking_invariance`: Property: `FrameEncoder` documents that "writes are buffered automatically", so splitting the input across arbitrary `write` calls (with arbitrary intermediate flushes) must still decompress to the same data as a single `write_all`. `Max8MB` is excluded here only because it already fails the roundtrip on its own (see `hegel_frame_roundtrip_any_config`); including it would make this test fail for the same, already-covered reason.
- `hegel_frame_read_chunking_invariance`: Property: the `io::Read` contract — decompressing with arbitrary (small) read buffer sizes must produce exactly the same bytes as `read_to_end`.
- `hegel_frame_concatenated_frames`: Property: several frames written through one encoder via `try_finish` are read back one frame per `read_to_end` call, in order. Generalization of the `concatenated` unit test above.
- `hegel_frame_corruption_never_panics_or_misdecodes`: Property: with block and content checksums enabled, flipping a single byte anywhere in the compressed frame must never panic the decoder, and must never be silently accepted with different output (evidence: the `checksums` unit test above checks specific corrupted byte positions).

## Oracles

## Not tested

## History

- 2026-07-14: predecessor base commit `f4f624772f13` (stricter lints).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/lz4_flex.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped f4f624772f13 → f6251928e30a (2026-08-11, "Merge pull request #234 from teddytennant/fix-max8mb-frame-header"; 0.14.0); 1 bug(s) still reproduce; fixed upstream: lz4_flex/1. 83 tests pass. lz4_flex/1 was fixed by making `BlockSize::Max8MB` `#[non_exhaustive]` (legacy frames only, unconstructible from outside), so the `frame_config` generator no longer draws it and `hegel_frame_roundtrip_any_config` now passes.
