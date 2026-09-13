# ryu

[dtolnay/ryu](https://github.com/dtolnay/ryu): the `ryu` crate (1.0, master), Ulf Adams' Ryū
float-to-shortest-decimal algorithm ported to Rust; the float printer behind `serde_json`.
`Buffer::format`/`format_finite` (the safe "pretty" layout) and `raw::format32`/`format64`.

Written in the zoo (not imported from the predecessor).

## What is tested

**`tests/hegel.rs`**
- `f64_prints_the_shortest_digits_in_the_pretty_layout` / `f32_…`: for any float — uniform bit
  patterns (every exponent, subnormals, both zeros, NaN payloads), hegel's floats, integers,
  short decimals m × 10^k, 1–17 (1–9) digit decimals at any exponent, and the corners of the
  layout rules (1e15/1e16/1e17, 1e-4/1e-5/1e-6, 2^53 ± 2, MIN_POSITIVE, MAX, 5e-324, …) — the
  printed text reads back bit for bit with `str::parse`; NaN/±inf print as `NaN`/`inf`/`-inf`
  and `format_finite` agrees with `format` on everything finite; **the digits are exactly the
  ones the standard library's `{:e}` chooses** (its own shortest-round-trip implementation,
  Grisu with a Dragon fallback) laid out by the crate's pretty rules modelled from those digits
  (plain decimal with `.0` for integers up to 16 (13) integer digits, `0.000…` down to 5 (6)
  leading zeros, otherwise `d.ddde±N` with no `+`); at most 24 (16) bytes, no `+`, never a bare
  integer; and `raw::format64`/`format32` write exactly the bytes they report — the same text —
  into a canary-filled buffer without touching anything past them.
- `buffers_are_reusable_and_independent`: one `Buffer` reused across f64s and f32s, `Copy`,
  `Clone`, `Default`, a short value after the longest leaves no tail.
- `ordering_of_the_text_follows_the_numbers_within_a_layout`: for positive numbers printed in
  plain decimal the text (fraction zero-padded) orders like the numbers — a consequence of
  shortest digits and the fixed layout.

## Oracles

`str::parse` (round trip), `format!("{:e}")` from `std` for the shortest digits and the decimal
exponent — an independent implementation of the same specification — and the crate's own
layout thresholds read from `src/pretty/mod.rs`.

## Not tested

The `small` feature (a 10× smaller power-of-5 table with the intermediate powers computed by
multiplication; the same algorithm on another table — upstream's `d2s_table_test` checks the
table computation itself), the `no-panic` feature, the Miri/exhaustive upstream runs (the ignored
`test_exhaustive` walks every f32; `cargo test --release -- --ignored` runs it).

## History

- 2026-09-13: written in the zoo against `75f9e707e77c` (2026-08-05, "Resolve deprecated f64
  constants warning"; 1.0.23) with hegeltest 0.44.1. 100 + 3 × 1 000 + 1 × 10 000 cases per
  property: **no bug found** — the digits agree with `std` on every draw (so `ryu` and `std` break
  shortest-representation ties the same way), a target with no `bugs.toml` like polars,
  quorum-set, base64, crc and crc32fast.
