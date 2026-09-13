# bs58

[Nullus157/bs58-rs](https://github.com/Nullus157/bs58-rs).

## What is tested

**`src/alphabet.rs`**
- `hegel_new_validates_alphabets`: Property: `Alphabet::new` accepts exactly the arrays of 58 unique ASCII bytes, and reports the correct error (kind, character, indexes) for the first offending byte otherwise.

**`tests/decode.rs`**
- `hegel_decode_error_characterization`: Property: decode over arbitrary byte strings never panics and returns exactly the documented error for the *first* offending byte (`NonAsciiCharacter` for bytes > 127, `InvalidCharacter` for ASCII bytes outside the alphabet), and succeeds when every byte is valid.
- `hegel_decode_arbitrary_text_never_panics`: Property: decode (in all check modes) never panics on arbitrary Unicode strings — it returns an error or a value, but must not crash.
- `hegel_decode_then_encode_identity`: Property: for any string over the alphabet (arbitrary alphabets included), decode succeeds and re-encoding reproduces the exact string — i.e. Base58 is a bijection between byte strings and alphabet strings.
- `hegel_decode_const_matches_runtime`: Property: the `const` decoder (`into_array_const`) agrees with the runtime decoder (`into_vec`) — same bytes on success (zero-padded), same error on failure.
- `hegel_decode_onto_buffer_boundaries`: Property: decoding onto an exactly-sized buffer succeeds and yields the original bytes; onto a one-byte-undersized buffer it returns `BufferTooSmall` (and never panics).

**`tests/encode.rs`**
- `hegel_encode_decode_roundtrip`: Property: decode(encode(x)) == x for arbitrary bytes and arbitrary valid alphabets.
- `hegel_encode_structure`: Property: structural invariants of the encoded form — every character is from the alphabet, the number of leading "zero digit" characters equals the number of leading zero bytes, and the length is within the documented bounds (between input length and ~1.5x input length).
- `hegel_encode_onto_buffer_boundaries`: Property: encoding onto an exactly-sized buffer succeeds and matches `into_string`; onto a one-byte-undersized buffer it returns `BufferTooSmall` (and never panics).
- `hegel_check_roundtrip`: (no doc comment)
- `hegel_check_version_roundtrip`: (no doc comment)
- `hegel_check_detects_single_char_corruption`: (no doc comment)
- `hegel_cb58_roundtrip`: (no doc comment)

## Oracles

## Not tested

## History

- 2024-03-19: predecessor base commit `e4a65a9ec641` (Merge pull request #118 from Nemo157/nightly-update).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/bs58.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
