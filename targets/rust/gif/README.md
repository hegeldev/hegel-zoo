# gif

[image-rs/image-gif](https://github.com/image-rs/image-gif).

## What is tested

**`tests/decode.rs`**
- `arbitrary_bytes_decode_never_panics`: Decoding arbitrary bytes (optionally with a valid GIF magic prefix so the fuzzer reaches deeper block-parsing paths) must never panic. It returns `Ok` or `Err`; under a bounded memory limit it must not OOM, and being finite input it must terminate. We vary the decoder configuration to cover paths the crate's single fuzz target (default options only) misses: RGBA output, frame-consistency checks, unknown-block tolerance, and the LZW end-code requirement. `skip_frame_decoding` is deliberately NOT exercised here: it reserves `width*height/4` bytes ignoring the memory limit (see `skip_frame_decoding_ignores_memory_limit_KNOWN_FAILURE`), which would let a crafted dimension reserve gigabytes and is pinned separately.
- `valid_then_corrupt_never_panics`: Build a valid single-frame GIF, then corrupt it (flip a byte or truncate) and confirm decoding degrades gracefully — an `Ok` or `Err`, never a panic. Oracle-independent robustness.
- `memory_limit_enforced_on_pixel_path`: Craft a tiny file that declares a huge frame but carries only a few bytes of LZW data, then decode it through the normal (pixel) path with a memory limit far below width*height. The decoder must reject it with an error rather than allocating the full frame — i.e. `set_memory_limit` is honored on the pixel path.
- `?`: KNOWN FAILURE — pins a real memory-limit bypass. With `skip_frame_decoding` enabled, `Decoder::read_next_frame` (src/reader/mod.rs, the `FrameDataType::Lzw` branch) pre-reserves `width * height / 4` bytes for the output buffer using the raw, attacker-controlled frame dimensions and WITHOUT consulting the configured `MemoryLimit`. A ~45-byte crafted GIF that declares a 65535x65535 frame therefore makes the decoder reserve ~1 GiB even though a 1 KiB memory limit was explicitly set. This is a decompression-bomb / memory-limit-bypass vector. The reservation is a `try_reserve` (virtual, not committed), so it does not abort the process — this fails as a normal assertion, deterministically. It stays failing until the crate clamps the skip-path reservation to the memory limit. Remove the `should_panic`/pin once fixed.

**`tests/roundtrip.rs`**
- `encode_decode_indexed_roundtrip`: Encode a drawn frame with a global palette, decode it back in Indexed mode, and assert the index buffer and dimensions recover exactly. LZW is lossless, so this is an oracle-independent round trip.
- `decoded_buffer_length_matches_dimensions`: A decoded frame's buffer length must equal width*height (Indexed) or width*height*4 (RGBA). This holds for any encodable image and needs no external oracle.
- `lzw_pre_encoded_roundtrip`: Compressing a frame with `make_lzw_pre_encoded` and writing it via `write_lzw_pre_encoded_frame` must round-trip back to the original indices when decoded normally. Exercises the parallel-compression LZW path (crate `lzw_encode` -> weezl decode).
- `multi_frame_with_extensions_roundtrip`: Encode a multi-frame animation with a NETSCAPE repeat extension and a comment extension, then decode it. Frame count, per-frame control metadata, buffers and the repeat count must all round-trip, and the extension blocks must be handled without panicking.

## Oracles

## Not tested

## History

- 2026-05-31: predecessor base commit `a5f89ddc2b29` (Merge pull request #236 from lilith/bump-weezl-0.2).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/gif.patch`).
- 2026-09-11: imported into the zoo; ported to hegeltest 0.44.1.
