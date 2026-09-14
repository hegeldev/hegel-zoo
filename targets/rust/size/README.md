# size

[size](https://github.com/neosmart/prettysize-rs) (PrettySize) is a strongly-typed file-size
crate: `Size` wraps an `i64` byte count built from any numeric type in any unit
(`Size::from_kib(2.5)`), prints itself in base-2 or base-10 units with a "heuristically chosen
precision" (`"1.28 MiB"`; `format()` sets base, style and scale), parses text back
(`Size::from_str("12.34 KB")`), supports `+ - * /` and `Sum`, and serialises as the bare byte
count with the optional `serde` feature. Written in the zoo at 0.5.0 (upstream HEAD `0bf9db2`,
2025-03-27); tests in `tests/hegel.rs`, run with `--features serde` (half a minute to build).

## The oracles

A model of the documented table written in the test: the largest unit the byte count reaches,
two decimals below ten units / one below a hundred / none above (or the requested scale), the
unit spelled per style (default = full lowercase name for bytes, abbreviation otherwise; full
names take a plural `s` except for one byte). The parser is checked against exact integer
arithmetic (`i128` decimal × multiplier) and against the formatter's own output; the operators
against `i64` arithmetic; the serde form against the `i64` itself through `serde_json`.

## Properties

- **Formatting** (`formatting_matches_the_model`): random base, style and scale, byte counts
  across bytes…pebi (both signs, 0–3 bytes for the singular) format to the model's text through
  `Display`, `format()` and a standalone `SizeFormatter`; `Debug` is `"<n> bytes"`. The
  generator keeps to counts whose rounding does not cross a unit or a step of the precision
  ladder (size/2) and below an exabyte (size/3).
- **Round trip** (`formatting_and_parsing_round_trip`): `from_str(format(x))` is within half a
  unit of the last printed decimal (plus one byte of truncation) in every base, style and scale;
  `Size::from_str` and `str::parse` agree.
- **Parsing** (`parsing_reads_number_times_multiplier`): `<integer><ws><unit>` with any
  spelling (abbreviation, full name, any case, plural `s` on full names, or no unit) and any
  surrounding whitespace parses to `integer × multiplier` exactly (below 2^53);
  `parsing_never_panics` on random text over the grammar's alphabet.
- **Arithmetic** (`arithmetic_is_exact_within_2_53`): within 2^53, `from_bytes`, the integer
  `from_<unit>` constructors (and exact halves), `+`, `-`, `Sum`, `*`/`/` by integer scalars
  (truncating toward zero), the assign forms and `Ord`/`Eq` follow the `i64` byte counts.
- **Serde** (`serde_is_the_transparent_byte_count`): every `i64` round-trips through JSON as
  the bare number (also as a struct field), JSON strings go through the parser, and numbers
  beyond `i64` are refused with "out of range".

## Bugs (6)

- **size/1** (wrong-result, medium; `sizes_are_exact_in_the_i64_range`): `from_bytes`, `+`,
  `-`, `*`, `/` and `Sum` go through `f64`; above 2^53 (8 PiB) the count changes —
  `Size::from_bytes(9007199254740993).bytes()` is `…992`, `x + ZERO != x`. Hegel shrank the
  failing case to 2^53 + 1.
- **size/2** (wrong-result, medium; `unit_is_chosen_after_rounding`): the unit and precision are
  chosen before rounding: `1_048_575` → `1024 KiB`, `999_999` → `1000 KB`, `10_239` →
  `10.00 KiB` next to `10_240` → `10.0 KiB`.
- **size/3** (wrong-result, low; `exabytes_keep_the_decimal_ladder`): the exabyte rule never
  prints decimals: `1.5e18` bytes → `2 EB`, `1.30 EiB` → `1 EiB`.
- **size/4** (wrong-result, medium; `parsing_decimals_is_exact`,
  `parsing_decimals_is_within_the_byte`): `from_str` multiplies in `f64` and truncates:
  `32.3KB` → 32 299 bytes, `1.005 KB` → 1004, `9007199254740993` → `…992` — the crate's own
  test says `12.34 kIloByte` is exactly 12 KB + 340 bytes.
- **size/5** (contract, low; `parsing_rejects_out_of_range_numbers`): `inf`, `infinity`,
  `1e400`, `10 EB` parse as `i64::MAX` and `nan` as 0 instead of `ParseSizeError`.
- **size/6** (contract, low; `unit_suffixes_take_at_most_one_plural_s`): any number of trailing
  `s` is stripped from the unit: `12 kbs`, `12 bytess`, `12 s`, `0 Bss` are accepted.

## Not bugs

- The float constructors truncate (`Size::from_kb(1.005)` = 1004 bytes): the caller's `f64` is
  already below 1.005 — noted under size/4, not counted separately.
- `size / 0` is `i64::MAX` bytes and `0 / 0` is `0`; `Size::from_bytes(7) * 0.1` is `0`; `u64`
  and `f64` inputs beyond `i64` saturate (`from_kib(f64::INFINITY)` = `8 EiB`): the crate's own
  tests pin these and the `ops` docs declare results beyond `i64` undefined.
- The scale is ignored for whole bytes (`with_scale(Some(2)).format(123)` = `"123 bytes"`) —
  documented. `Debug` prints `"1 bytes"`. `Deserialize` uses `deserialize_any`, so `Size` cannot
  be read from non-self-describing formats (bincode, postcard) — outside the documented JSON-style
  payloads, not counted.
