# crc32fast

[srijs/rust-crc32fast](https://github.com/srijs/rust-crc32fast): the `crc32fast` crate (1.5:
CRC-32/ISO-HDLC with a slicing-by-16 baseline and `pclmulqdq` / `vpclmulqdq` (AVX2, AVX-512)
implementations selected at runtime; `Hasher` with initial state, byte count and `combine`).

Written in the zoo (not imported from the predecessor).

## What is tested

**`tests/hegel.rs`** — every property draws the implementation: the runtime-selected one
(`Hasher::new` and friends) or the baseline, reached through the `#[doc(hidden)]`
`internal_new_baseline` the crate's own tests use (on this machine `new` selects the AVX-512
`vpclmulqdq` variant, so the baseline would otherwise go untested).
- `checksum_matches_the_bitwise_definition`: `hash`, a fresh `Hasher` fed all at once, a `Hasher`
  fed in arbitrary chunks (cloned half way, both continuations agreeing), `Default`, and
  `std::hash::Hasher::write`/`finish` all give the bit-by-bit CRC-32/ISO-HDLC of the
  concatenation; `finish` does not consume the state.
- `initial_state_continues_a_checksum`: `new_with_initial(crc(a))` continued with `b` gives
  `crc(a ‖ b)` (the documented meaning of the initial state); a fresh hasher's checksum is the
  CRC of the empty message; `reset` gives a fresh hasher whatever was fed or configured,
  including the byte count `combine` relies on.
- `combine_concatenates_checksums`: `crc(a ‖ b)` from a hasher over `a` — or from
  `new_with_initial_len(crc(a), len(a))` — and a hasher over `b`, for any split including empty
  parts; chained over three pieces with the combined hasher used both as receiver and as
  argument (so the byte counts must be kept right); updating after a combine; combining with or
  into an empty hasher; and the argument is left unchanged.

Inputs are up to six chunks of up to 300 bytes, so the widest SIMD path (256 bytes per
iteration) runs several iterations with every tail length and chunk boundaries fall anywhere.

## Oracles

The definition of CRC-32/ISO-HDLC one message bit at a time (reflected polynomial `0xEDB88320`,
init and xorout `0xFFFFFFFF`), which shares nothing with the crate's tables or carry-less
multiplication, and the crate's own stated identities for `new_with_initial`,
`new_with_initial_len` and `combine`, checked against that definition on the concatenated data.

## Not tested

`combine` with byte counts beyond the data actually hashed (lengths ≥ 2³², where the
power-of-two table wraps), the `aarch64` implementation, the `no_std` build, the runtime
selection itself (which variant `new` picks is not observable).

## History

- 2026-09-13: written in the zoo against `92c03d6315fd` (2026-09-13, "bench: switch from
  bencher to criterion (#66)"; 1.5.2) with hegeltest 0.44.1. 3 × 3 000 cases: **no bug found**
  — a target with no `bugs.toml`, like polars, quorum-set, base64 and crc.
