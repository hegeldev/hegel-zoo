# base64

[marshallpierce/rust-base64](https://github.com/marshallpierce/rust-base64): the `base64` crate
(0.23: `GeneralPurpose` engine, the new runtime-dispatched `Simd`/`Avx2`/`Neon` engines, six
built-in alphabets plus custom ones, streaming reader/writer).

Written in the zoo (not imported from the predecessor).

## What is tested

**`tests/hegel.rs`**
- `encoding_agrees_with_reference_and_across_apis`: Every engine encodes identically and `data-encoding` agrees; `encoded_len`, `encode_string`, `encode_slice` (including `OutputSliceTooSmall`), `Base64Display` and `EncoderWriter`/`EncoderStringWriter` all produce that encoding.
- `canonical_decoding_round_trips`: Decoding a canonical encoding round-trips (or is rejected exactly as the padding mode says), identically for every engine; `decode_vec`, `decode_slice` (with `OutputSliceTooSmall`) and `decode_slice_unchecked` agree with `decode`.
- `arbitrary_input_decodes_alike`: Under the strict padding modes, `GeneralPurpose` accepts exactly the inputs `data-encoding` accepts and decodes them to the same bytes; the `Simd`/`Avx2` engines give exactly the same `Result` as `GeneralPurpose` — same bytes, or the same `DecodeError` with the same offsets — on any input, valid or not.
- `single_corruption_gives_documented_error`: A single corruption of a canonical encoding produces the documented error: a byte outside the alphabet (and not `=`) replacing a symbol → `InvalidByte(offset, byte)`; a symbol whose discarded low bits are nonzero as the last symbol → `InvalidLastSymbol` at its offset, or with `decode_allow_trailing_bits` the same bytes as the canonical encoding decodes to; one symbol dropped so that a lone symbol ends the input → `InvalidLength`; a `=` replacing a symbol before the end → `InvalidByte` at the `=`.
- `streaming_decoder_matches_decode`: `DecoderReader`, read in arbitrary chunk sizes from a reader that also returns arbitrary short reads, yields exactly `decode`'s bytes for valid input and an error for input `decode` rejects.
- `custom_alphabets_round_trip`: `Alphabet::new` accepts exactly 64 unique printable ASCII bytes without `=` (and reports the documented error otherwise), and an engine built on any such alphabet encodes like `data-encoding` with the same symbols, round-trips, and — under the strict padding modes — accepts exactly what `data-encoding` accepts.

Configurations are drawn in full: alphabet (STANDARD, URL_SAFE, CRYPT, BCRYPT, IMAP_MUTF7,
BIN_HEX, or a random permutation of 64 printable bytes), `encode_padding`,
`decode_allow_trailing_bits`, `DecodePaddingMode`; inputs go up to 160 bytes so the AVX2 bulk
loops run several iterations plus a tail.

## Oracles

`data-encoding` (an independent RFC 4648 implementation, itself a zoo target), configured through
its `Specification` with the same symbols, padding and trailing-bit check as the config under test
— the encoding oracle for every alphabet and the acceptance/bytes oracle for the strict padding
modes (`Indifferent` has no counterpart there). One documented semantic difference is accounted
for: `base64` rejects `=` anywhere but in the final quad, `data-encoding` decodes concatenated
padded blocks (`AA==AA==`). The crate's `Simd`/`Avx2` engines are compared with `GeneralPurpose`
result for result (the `Naive` reference engine is `#[cfg(test)]`-only and not reachable).

## Not tested

`Neon` (aarch64), the `no_std`/`alloc`-only build, `prelude` re-exports, `Base64Display`
formatting flags, the `chunked_encoder`, error `Display` text.

## History

- 2026-09-13: written in the zoo against `5b98ee180cc7` (2026-08-18, "Merge pull request #311
  from marshallpierce/mp/test-arch-without-simd"; 0.23.1) with hegeltest 0.44.1. 3 × 10 000
  cases: **no bug found** — a target with no `bugs.toml`, like polars and quorum-set.
