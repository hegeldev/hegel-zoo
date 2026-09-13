# itoa

[dtolnay/itoa](https://github.com/dtolnay/itoa): the `itoa` crate (1.0, master), integer
primitives to decimal text without `core::fmt::Formatter` — the integer printer behind
`serde_json`. `Buffer::format` for every integer type (`i8`–`i128`, `u8`–`u128`, `isize`,
`usize`), `Integer::MAX_STR_LEN`.

Written in the zoo (not imported from the predecessor).

## What is tested

**`tests/hegel.rs`** — the oracle is `std`'s `Display`/`ToString` (the crate's code was lifted
from `core::fmt::num`, but the `u128` path is its own: two Granlund–Montgomery multiply-shift
divisions by 10^16 and a 16-digit block encoder) plus `str::parse`.
- `<type>_prints_like_std` (ten tests, one per fixed-width type): for uniform bit patterns, the
  values around every power of ten (10^k − 2 … 10^k + 2, both signs), around every power of two,
  the type's `MIN`/`MAX`/0/1/9/10/99/100 and small values, `Buffer::format` prints exactly
  `to_string()`, at most `MAX_STR_LEN` bytes, reads back with `parse`, is ASCII digits with an
  optional `-` and no leading zero, and prints the same into a fresh or a reused buffer; the
  type's longest value fills `MAX_STR_LEN` exactly.
- `usize_and_isize_print_like_their_fixed_width_twins`: the pointer-sized types print as `u64`/
  `i64` and share their `MAX_STR_LEN`.
- `wider_types_and_the_16_digit_split_agree`: for a `u128`, the text of `hi × 10^16 + lo` is the
  text of `hi` followed by `lo` zero-padded to 16 digits; the same value as `u8`/`u16`/`u32`/
  `u64`/`i64`/`i128` (where it fits) prints the same text, and its negation prints `-` + text.
- `text_order_follows_numeric_order`: for two `u64`s the text ordered by (length, bytes) orders
  like the numbers; for two `i64`s likewise, reversed for negatives, sign first across signs.
- `buffers_are_reusable_and_independent`: a `Buffer` (`Default`, `Copy`, `Clone`) reused across
  `i128`, `u8`, `i16` values, copies formatting independently, and is at least `MAX_STR_LEN` of
  `i128` bytes.

## Oracles

`std`: `Display`/`ToString`, `str::parse`, integer arithmetic for the 10^16 split.

## Not tested

The `no-panic` feature (a link-time assertion, not a behaviour), 16- and 32-bit targets (where
`usize`/`isize` map to `u16`/`i16` and `u32`/`i32`), Miri.

## History

- 2026-09-13: written in the zoo against `1577ed901354` (2026-06-23, "Update
  actions/upload-artifact@v6 -> v7"; 1.0.18) with hegeltest 0.44.1. 100 + 3 × 1 000 + 1 × 10 000
  cases per property: **no bug found** — every value prints exactly as `std` does — a target
  with no `bugs.toml` like polars, quorum-set, base64, crc, crc32fast, ryu and adler2.
