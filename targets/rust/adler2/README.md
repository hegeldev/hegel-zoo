# adler2

[oyvindln/adler2](https://github.com/oyvindln/adler2): the `adler2` crate (2.0, master), the
maintained fork of `adler` — a clean-room, `unsafe`-free Adler-32 (RFC 1950) used by
`miniz_oxide`/`flate2` for every zlib stream. `Adler32` (`new`, `from_checksum`, `write_slice`,
`checksum`, `Hasher`), `adler32_slice`, `adler32` over a `BufRead`.

Written in the zoo (not imported from the predecessor).

## What is tested

**`tests/hegel.rs`** — the oracle is the definition itself, one byte at a time
(`a = (a + byte) mod 65521`, `b = (b + a) mod 65521`, checksum `b << 16 | a`); the crate defers
the modulo over 5552-byte runs and splits the input into four interleaved lanes recombined at the
end, so the interesting inputs are the lengths where that structure changes.
- `adler32_slice_matches_the_definition`: the checksum of any input — lengths 0–64, 1–3 (the
  serial tail), multiples of 4 ± 5, around 5552 and the 22 208-byte inner chunk (× 1, 2, 3), or
  anywhere up to three chunks; contents all `0xff` (the deferred-modulo worst case), one repeated
  byte, a short repeated pattern, xorshift bytes from a drawn seed, or fully drawn bytes — equals
  the definition; both halves come back reduced below 65521; the empty checksum is 1; the low half
  is `1 + Σ bytes mod 65521`.
- `piecewise_and_resumed_checksums_match_the_whole`: the same input cut at up to six drawn
  offsets and fed through `write_slice`, `Hasher::write`, or restarted from
  `from_checksum(checksum())` after every piece gives the prefix checksum after every piece and
  the whole at the end; `Copy`/`Clone`/`Debug`; continuing a resumed state equals continuing the
  live one.
- `hashing_is_the_checksum_of_the_written_bytes`: `[u8]::hash` and `u64::hash` through the
  `Hasher` impl are the checksums of the bytes `Hash` writes (length prefix in native-endian
  `usize`, then the bytes); `finish` does not consume.
- `buf_read_matches_the_slice_and_propagates_errors`: `adler32` over a `BufReader` of any capacity
  1–9000, a bare slice, or a `Chain` of two halves equals the slice checksum; a reader failing
  after `n` bytes returns that error unchanged (kind and message), consumed up to the failure.
- `known_vectors`: RFC 1950's `"Wikipedia"`, `"abc"`, 1024 zeros, the empty input, and a single
  byte (`(b + 1) << 16 | (b + 1)`).

## Oracles

The byte-at-a-time definition (RFC 1950 §8.2 / Wikipedia), `std`'s `Hash` write protocol for
slices and integers, `std::io::Read` adapters.

## Not tested

`from_checksum` with a value whose halves are not below 65521 (not a checksum, outside the
documented contract), `no_std` (`default-features = false` — the same code minus `adler32`),
big-endian targets (the `Hash` test computes its expectation with native endianness), and the
`rustc-dep-of-std` feature.

## History

- 2026-09-13: written in the zoo against `89a031a0f42e` (2025-06-10, "update version and
  changelog, and exclude . folders/files from crate"; 2.0.1) with hegeltest 0.44.1. 100 + 3 ×
  1 000 + 1 × 10 000 cases per property: **no bug found** — a target with no `bugs.toml` like
  polars, quorum-set, base64, crc, crc32fast and ryu.
