# tiff

[image-rs/image-tiff](https://github.com/image-rs/image-tiff).

## What is tested

**`tests/decode_images.rs`**
- `byte_order_ii_vs_mm_decode_identically`: Property: the same logical image serialized in little-endian (`II`) and big-endian (`MM`) byte order — by a spec-transcribed writer independent of the crate's encoder — decodes to identical samples, which are exactly the source pixels.

**`tests/encode_images.rs`**
- `roundtrip_arbitrary_image_and_config`: Property: encoding any image (drawn dimensions, color type, bit depth, compression, predictor, TIFF vs BigTIFF, strip size) and decoding it back recovers exactly the pixels that were written. Floats are compared bit-for-bit (NaN payloads included) since nothing in the pipeline may alter sample bytes.
- `multipage_roundtrip`: Property: a multi-page file roundtrips — every page is recovered in order by `next_image`, `more_images` reports exactly the encoded number of pages, and `seek_to_image` random access agrees with the sequential walk.
- `strip_chunks_reassemble_to_image`: Property: reading an image strip by strip (`read_chunk`) and concatenating the strips yields exactly the same samples as `read_image`, and both equal the encoded pixels; per-strip data dimensions tile the image height exactly.
- `rows_per_strip_returns_err_instead_of_panicking`: KNOWN FAILURE: `ImageEncoder::rows_per_strip` returns `TiffResult`, but calling it with `0` panics with an unchecked divide-by-zero (`height.div_ceil(value)` at src/encoder/mod.rs:895) instead of returning `Err`. The `just(0)` branch makes the failure deterministic.

**`tests/fuzz_tests.rs`**
- `decode_arbitrary_bytes_never_panics`: Property 1: arbitrary bytes — with or without a valid TIFF/BigTIFF magic prefix — never panic, hang, or blow past the decoding limits.
- `crafted_ifd_fields_never_panic_or_oom`: Property 2: a syntactically well-formed IFD whose *fields* are adversarial (huge dimensions, huge strip byte counts, out-of-range offsets, absurd sample counts, giant entry counts) must be handled gracefully: `Err` is fine, panicking / OOM (pre-allocating from attacker-controlled sizes before checking `Limits`) / hanging is not. Each field is independently either sane or adversarial. A quarter of the cases are fully sane (a valid Gray8 image), so the decode-success path — strip reading and the dimension-sanity assertion — is exercised on every run, and single-field attacks against otherwise-valid images are common.
- `corrupted_valid_tiff_never_panics`: Property 3: take a *valid* encoder-produced TIFF and corrupt it — truncation at any point, or arbitrary byte edits anywhere (header, IFD entries, strip offsets, pixel data). Decoding the result must not panic; if it still succeeds, the dimension-sanity invariant must hold.

## Oracles

## Not tested

## History

- 2026-07-20: predecessor base commit `f3f9ff1244e5` (Merge pull request #398 from Shnatsel/safe-rust-zstd-2).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/tiff.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped f3f9ff1244e5 → 3302936b08e2 (2026-09-06, "Merge pull request #415 from paolobarbolini/zstd-0.14"; 0.11.3); 1 bug(s) still reproduce; add/add conflicts in tests/decode_images.rs resolved by keeping both sides. 259 tests pass.
