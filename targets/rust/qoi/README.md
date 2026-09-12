# qoi

[aldanor/qoi-rust](https://github.com/aldanor/qoi-rust).

## What is tested

**`tests/test_gen.rs`**
- `prop_encode_decode_roundtrip`: QOI is lossless: encode -> decode is the identity on the pixel buffer, and the header roundtrips the full configuration (dimensions, both channel counts, both colorspaces).
- `prop_c_reference_decodes_our_encoding`: The reference C implementation (qoi.h) decodes qoi-rust's output back to the original pixels: our encoder emits spec-conformant streams.
- `prop_decode_arbitrary_streams_matches_c_reference`: Differential test of the decoder against the reference C decoder on arbitrary valid chunk streams (not just encoder outputs).
- `prop_decode_3ch_uninit_index_diverges_from_c_reference`: KNOWN FAILURE (real bug, do not "fix" the test): on a valid 3-channel stream, qoi-rust's decoder diverges from the reference C decoder (qoi.h) once a QOI_OP_INDEX chunk references an uninitialized index slot. The spec zero-initializes the table, so such a reference is well-defined and yields {0,0,0,0} -- alpha 0. qoi.h carries that alpha into subsequent index-hash computations, but qoi-rust's 3-channel decoder (`decode_impl_slice::<3, false>`, src/decode.rs) tracks pixels as `Pixel<3>` and hashes via `as_rgba(0xff)`, so later QOI_OP_INDEX chunks resolve to different slots than the spec prescribes. Same root cause as `prop_decode_rgba_as_rgb_drops_alpha` in tests/test_misc.rs: the 3-channel decode paths discard alpha state. The op stream [INDEX(i), DIFF(d), INDEX(hash(px, alpha=0))] is built directly so the test fails deterministically on every case.
- `prop_decode_uninit_index_slot_diverges_from_c_reference`: KNOWN FAILURE (real bug, do not "fix" the test): the alpha-independent half of the uninitialized-index divergence, on a 4-channel stream. The reference decoder re-registers every decoded pixel in the color index, *including* pixels produced by QOI_OP_INDEX chunks. That write is a no-op when the referenced slot was previously written (table entries sit at their own hash position), but a reference to an uninitialized slot yields {0,0,0,0}, whose hash position is slot 0 -- qoi.h then stores {0,0,0,0} into slot 0, clobbering whatever was there. qoi-rust's decoders never write the index on QOI_OP_INDEX chunks (`decode_impl_slice`'s INDEX arm `continue`s), so a later QOI_OP_INDEX(0) chunk reads different values. Ops: [RGBA(0,0,0,a) with hash 0, INDEX(j) uninitialized, INDEX(0)]; constructed directly so the test fails deterministically on every case.

**`tests/test_misc.rs`**
- `prop_header_encode_decode_roundtrip`: Header::decode is the inverse of Header::encode over the full domain of valid headers (dimensions up to the documented 400Mp limit, both channel counts, both colorspaces).
- `prop_header_decode_rejects_corrupt_fields`: Corrupting any single semantic field of a valid header makes Header::decode return the matching error (validation/rejection check).
- `prop_decode_garbage_body_never_panics`: Decoding a valid (bounded-size) header followed by arbitrary garbage never panics; when it succeeds, the output length matches the header.
- `prop_decode_truncated_encoding_errors`: A truncated valid encoding (any strict prefix) always errors and never panics: the declared pixel count can no longer be satisfied.
- `prop_decode_rejects_header_larger_than_data`: Inflating the declared dimensions of a valid encoding (header promises more pixels than the chunk stream provides) makes decoding error.
- `prop_decode_bit_flipped_encoding_never_panics`: Flipping any single bit of a valid encoding past the dimension fields never panics the decoder. (Bytes 4..12 are skipped only to keep the test from allocating multi-hundred-MB buffers for legally-huge dimensions -- this protects the test's memory, not the library's contract; header-field corruption is covered by prop_header_decode_rejects_corrupt_fields.)
- `prop_encode_vec_buf_stream_agree`: The three encoding APIs (to_vec, to_buf, to_stream) produce identical bytes, and the result never exceeds encode_max_len.
- `prop_decode_slice_vs_stream_agree`: The slice decoder and the (independently implemented) stream decoder agree, for every (source channels, requested channels) combination. For the (Rgba -> Rgb) combination, alpha values are restricted to the hash-preserving set {63, 127, 191, 255}: outside it the two decoders genuinely disagree -- pinned as a known bug by `test_decode_slice_vs_stream_divergence` below.
- `prop_decode_rgb_as_rgba_adds_opaque_alpha`: Decoding an RGB image with `with_channels(Rgba)` equals the native RGB decode with an opaque alpha byte appended to each pixel (documented: "the alpha channel will be set to 255").
- `prop_decode_rgba_as_rgb_drops_alpha`: KNOWN FAILURE (real bug, do not "fix" the test): decoding an RGBA image with `with_channels(Rgb)` does NOT equal the native RGBA decode with the alpha byte dropped, contradicting the documented behavior ("the alpha channel will be ignored"). Root cause: `decode_impl_slice::<3, true>` (src/decode.rs) tracks pixels as `Pixel<3>` and rebuilds the color index via `px.as_rgba(0xff)`, i.e. it hashes with alpha=255. The encoder indexed the same pixels with their *true* alpha, so a `QOI_OP_INDEX` chunk referencing a pixel whose alpha is not hash-equivalent to 255 (alpha not in {63, 127, 191, 255}, since the hash is 3r+5g+7b+11a mod 64) looks up a slot the decoder never wrote, producing wrong RGB values. The stream decoder (`decode_impl_stream::<_, 3, true>`) has the same flaw (index of `Pixel<3>`), and on top of it diverges from the slice decoder -- see `test_decode_slice_vs_stream_divergence` below. The generator below constructs the counterexample family [A, B, A] directly so the test fails deterministically on every case: the encoder emits QOI_OP_INDEX for the third pixel, and the decoder's alpha-255 index cannot resolve it to A's RGB values.
- `prop_decode_rgba_as_rgb_drops_alpha_hash_preserving`: Green sibling of prop_decode_rgba_as_rgb_drops_alpha (see the KNOWN FAILURE comment there): the RGBA -> RGB conversion property does hold when every alpha value is hash-equivalent to 255 (a in {63, 127, 191, 255}), because then the decoder's alpha-255 index lands on the same slots the encoder used. Restricting alpha this way keeps QOI_OP_RGBA chunks and index reuse in play while excluding the known-buggy inputs.

## Oracles

## Not tested

## History

- 2025-07-28: predecessor base commit `81c14c4b637c` (Merge pull request #22 from aldanor/fuzz-fix).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/qoi.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
