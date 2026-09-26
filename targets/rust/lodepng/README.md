# lodepng

[kornelski/lodepng-rust.git](https://github.com/kornelski/lodepng-rust.git).

## What is tested

The cases are records drawn from hegeltest's combinators and rendered by pure functions: a
colour `Mode` (type and bit depth, GREY 8 first), a `Picture` (width, height and a `Pixels`
structure - constant, tiled, gradient or runs - rendered to any byte length, so the pixel
structure is independent of the dimensions), a `Filters` choice (a strategy, or a tape of
predefined filter types recycled over the scanlines), a list of `Poke`s applied modulo the PNG
length, a `cut` taken modulo the length, `Junk` (an empty, signature or signature-and-IHDR prefix
and a tail of a drawn length) and a `PaletteImage` (depth, then entries and indices that fit it).
No recorded bugs: nothing is gated, and every property passes at 20000 cases.

**`tests/roundtrip/roundtrip_test.rs`**
- `roundtrip_generated_color_config`: encode then decode with auto_convert off, in every
  non-palette colour mode (1/2/4-bit GREY included), either interlacing and any filter choice,
  reproduces the raw pixel buffer exactly.
- `roundtrip_generated_palette`: palette images round-trip exactly - packed indices and palette
  survive encode + decode with `color_convert(false)`, and decoding to RGBA maps every index
  through the palette.

**`tests/tests.rs`**
- `grey_decode32_matches_sample_scaling`: decoding a GREY PNG of any bit depth to RGBA puts each
  sample scaled by 255/(2^depth-1) (the MSB for 16-bit) into all three channels with opaque alpha.
- `auto_convert_encode_is_lossless`: encoding RGBA with auto_convert is lossless whatever output
  mode the encoder picks (grey, palette, colour key, RGB, grey+alpha).
- `decode_arbitrary_bytes_never_panics`: the decoder returns an error, never panics or aborts, on
  arbitrary bytes, also behind a valid signature or signature+IHDR.
- `decode_corrupted_png_never_panics`: overwriting bytes of a valid PNG never makes the default
  decoder panic or abort.
- `decode_truncated_png_errors`: every strict prefix of a valid PNG is rejected with an error (IEND
  can never be complete).
- `inspect_reports_encoder_metadata`: `Decoder::inspect` reports the encoded width/height and
  exactly the configured colour type, bit depth and interlace method.
- `file_and_memory_apis_agree`: `encode_file` + `decode_file` through a real file give the same
  image as `encode_memory` + `decode_memory`, both reproducing the raw pixels (convertible modes
  only).
- `decode_ignore_crc_oversized_header_ooms` (`#[ignore]`d): the reproducer of an out-of-memory on
  an oversized header with CRC checking off, kept as documentation.

## Oracles

## Not tested

## History

- 2026-02-16: predecessor base commit `cc5d7c6feb89` (Drop cf-zlib).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/lodepng.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1. Two `.into()` calls in upstream's own `test_low_bpp` were made explicit (`u32::from`, `u8::from`): ambiguous under current rustc.
- 2026-09-26: generators rewritten in combinator style (records rendered by pure functions,
  plainest alternatives first, edits and cuts applied modulo the live size); a `binary()` tail
  that never reached 50 of its 300 bytes became a drawn length with a fixed-size fill; the
  properties gained doc comments.
