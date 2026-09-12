# lodepng

[kornelski/lodepng-rust.git](https://github.com/kornelski/lodepng-rust.git).

## What is tested

**`tests/roundtrip/roundtrip_test.rs`**
- `roundtrip_generated_color_config`: (no doc comment)
- `roundtrip_generated_palette`: (no doc comment)

**`tests/tests.rs`**
- `grey_decode32_matches_sample_scaling`: (no doc comment)
- `auto_convert_encode_is_lossless`: (no doc comment)
- `decode_arbitrary_bytes_never_panics`: (no doc comment)
- `decode_corrupted_png_never_panics`: (no doc comment)
- `decode_truncated_png_errors`: (no doc comment)
- `inspect_reports_encoder_metadata`: (no doc comment)
- `file_and_memory_apis_agree`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-02-16: predecessor base commit `cc5d7c6feb89` (Drop cf-zlib).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/lodepng.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1. Two `.into()` calls in upstream's own `test_low_bpp` were made explicit (`u32::from`, `u8::from`): ambiguous under current rustc.
