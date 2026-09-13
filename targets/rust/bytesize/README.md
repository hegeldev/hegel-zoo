# bytesize

[bytesize-rs/bytesize](https://github.com/bytesize-rs/bytesize): `ByteSize(u64)` with SI/IEC
constructors, six `Display` styles (`1.0 MiB`, `1.0M`, `1.0 MB`, `1.0M`, `8.0 Mib`, `8.4 Mb`)
with precision, width and alignment, `FromStr` for `"1.5 KiB"`-style texts and for `Unit`,
arithmetic, and serde (string when human-readable, `u64` otherwise).

Written in the zoo (not imported from the predecessor). Built with `--all-features` (`std`,
`serde`, `arbitrary`). The crate's own unit and quickcheck tests run alongside `tests/hegel.rs`.

## What is tested

**`tests/hegel.rs`** — byte counts are drawn over the whole `u64` range with a bias to the
1000ⁿ/1024ⁿ boundaries (± a few bytes, × common multipliers), to rounding ties in the first
decimal and to the 2⁵³ f64 edge; the oracle is exact `u128` arithmetic.
- `display_styles_pick_the_unit_and_round_the_mantissa`: in each style, below the unit
  threshold (1024 / 1000 bytes, 128 / 125 bytes for bits) the integer count is printed; above
  it the unit is the largest power that fits the (f64-rounded) value and the mantissa has
  exactly the requested decimals (1 by default, `{:.p}` otherwise) and is within half a last
  digit of the exact quotient; `{}`/`to_string` are the IEC style; `Debug` is `<display>
  (<n> bytes)`; the rendering is under 11 characters; width/fill/alignment pad by characters
  without truncating (the crate's own regression) — `{:w$.p$}`, `<`, `>`, `^`, custom fill.
- `decimal_and_unit_texts_parse_to_the_bytes_they_denote`: `<int>[.<frac>][ws]<unit>` for all
  26 accepted spellings in random case (`k`, `kb`, `kB`, `Ki`, `KiB`, …) and whitespace
  between: integer texts are exact, decimal texts are within a couple of f64 ulps of
  ⌊N × factor / 10ᵏ⌋ (the exactness of whole-byte decimals is pinned, see bytesize/1); texts
  beyond `u64` must not panic; `Unit` parsing and its `+`/`×` with `u64` and `f64`.
- `malformed_texts_are_refused`: bare integers parse (also as JSON numbers); empty text, a bare
  fraction, two dots, space-grouped digits, a leading unit, unknown units (including
  non-ASCII) and exponents are errors with the documented messages, the unit error truncating
  long spellings to three characters at a char boundary.
- `arithmetic_and_ordering_follow_the_byte_count`: constructors, module helpers and `as_*`
  accessors are the documented multiples; `+`/`-`/`*` with `ByteSize` and with `u64`/`u32`/
  `u16`/`u8` in both orders, the assigning forms, `Sum` by value and by reference; `Ord`/`Eq`/
  `Hash`/`Default`.
- `serde_forms`: JSON numbers and strings, the `Display` string as the human-readable
  serialization (round-tripping where the rendering is exact), TOML strings and integers,
  refusal of negative numbers, floats, `null` and `""`.
- Pinned: `decimal_texts_denoting_whole_bytes_parse_exactly` (bytesize/1).

## Oracles

Exact `u128` arithmetic (unit powers, quotients, the byte count a decimal text denotes), the
documented constants and spellings, `serde_json`/`toml` (dev-dependencies).

## Not tested

The `arbitrary` implementation; `no_std`; the non-human-readable serde path (no binary
serializer among the dev-dependencies); overflow behaviour of `+`/`*` (unspecified; the
`FromStr` path saturates); the lossy `Display → FromStr` round trip above a few decimals (the
crate's own quickcheck test excludes it); `iec_short` output (`953.7M`) re-parsing as decimal
megabytes — the spellings `K`/`M`/… are decimal on input but binary in the short IEC output,
which is a documented `sort -h` compatibility choice.

## Bugs

- **bytesize/1** (medium): a decimal text with an SI unit parses one byte short whenever the
  f64 product lands just below the whole number it denotes — `1.001 kB` → 1 000, `8192.3 kB`
  → 8 192 299, `2.01 GB` → 2 009 999 999 (782 of the 90 000 one-decimal `x.y kB` texts below
  10 000, 1 810 of the 99 000 `x.yz GB` texts below 1 000). Integer texts and IEC units are
  exact.

## History

- 2026-09-13: written in the zoo against `da17fdc04a3c` (2026-09-01, 2.7.0) with hegeltest
  0.44.1. The crate (1 100 lines) was read first: the `f64` decimal path was the suspect and
  the first 1 000-case run confirmed it (bytesize/1). Otherwise clean at 100 + 3 × 1 000 +
  10 000 cases. Test defects on the way: the exactness claim first covered fractions of a
  byte and values beyond 2⁵³, where truncation of an f64 cannot be exact; a `m × EiB`
  overflow in the serde generator.
