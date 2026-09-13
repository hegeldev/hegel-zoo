# crc

[mrhooray/crc-rs](https://github.com/mrhooray/crc-rs): the `crc` crate (3.4: `Crc<W, I>` for
`u8`…`u128` registers with the `NoTable`, `Table<1>` and `Table<16>` implementations, the 113
parametrised algorithms of `crc-catalog`, custom algorithms, `Digest` with `digest_with_initial`).

Written in the zoo (not imported from the predecessor).

## What is tested

**`tests/hegel.rs`**
- `reference_reproduces_every_catalogue_check_value` (plain test): the oracle is right — the
  bit-by-bit model reproduces the catalogue's `check` value (the CRC of `"123456789"`) for all
  113 algorithms, and so does the crate; the catalogue's `residue` holds for every whole-byte,
  `refin == refout` algorithm when the crate's own checksum is appended to the message.
- `catalogue_u{8,16,32,64,128}_matches_the_bitwise_model`: Every catalogue algorithm of that
  register type, on arbitrary data split into arbitrary chunks: `NoTable`, `Table<1>` and
  `Table<16>` all equal the bit-by-bit model, one-shot (`checksum`) and through a `Digest` (which
  is cloned half way; both continuations must agree), and the `residue` holds where defined.
- `custom_u{8,16,32,64,128}_matches_the_bitwise_model`: A random algorithm of that register type
  — any width from 1 to the register's bits, any polynomial, init and xorout within the width,
  all four reflection settings — with the algorithm's `init` or a custom one through
  `digest_with_initial` ("the effects of the algorithm's properties `refin` and `width` are
  applied to the custom initial value"): all three implementations equal the bit-by-bit model.

Inputs are up to five chunks of up to 70 bytes, so `Table<16>`'s 16-byte loop runs several
times with every tail length and chunk boundaries fall anywhere.

## Oracles

A bit-by-bit implementation of the Rocksoft / reveng parametrised CRC model — the register is
shifted one message bit at a time with the feedback taken from the top bit, which is the
*definition* of the catalogue's `width`/`poly`/`init`/`refin`/`refout`/`xorout` and shares nothing
with the crate's byte tables. It is itself validated against all 113 catalogue `check` values.
The crate's three implementations are also compared with each other through the same expected
value.

## Not tested

`Crc::table()` (the raw lookup tables; their layout is not documented), `Debug` for `Digest`,
the `crc-catalog` `poly` module re-exports.

## History

- 2026-09-13: written in the zoo against `1894aa9f184d` (2026-01-02, "Remove unnececessary
  \"as usize\""; 3.4.0) with hegeltest 0.44.1. 3 × 10 000 cases (1000 per property):
  **no bug found** — a target with no `bugs.toml`, like polars, quorum-set and base64.
