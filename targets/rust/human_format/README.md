# human_format

[human_format](https://github.com/BobGneu/human-format-rs) formats numbers into short
human-readable strings — `Formatter::new().format(1_000_000.0)` is `"1.00 M"` — with SI,
binary and time scales or a custom base and suffix list, configurable decimals, separator,
units, a forced suffix and the micro sign, and parses such strings back (`try_parse`,
`parse_or_clamp`). Written in the zoo at 1.2.1 (upstream HEAD `9c54533`, 2026-03-23); tests in
`tests/hegel.rs` (half a minute to build).

## The oracles

A model written in the test: the scale tables (`SI`, `Binary`, the `Time` table of seconds per
unit, a custom `with_base`/`with_suffixes` scale with SI's fraction suffixes still in force),
the unit a value should be shown in (the largest whose scaled value is at least one, or the
smallest available), `{:.d}` of the scaled value, then separator, suffix and units — `NaN`,
`inf`, and a leading `-` for negatives. The formatter's inverse `try_parse` is checked against
`format` (round trip to half a unit in the last printed decimal) and against
`number × multiplier` for constructed strings.

## Properties

- **Formatting** (`formatting_matches_the_model`): random configurations (four scale kinds,
  0–4 decimals, five separators, nine units strings, micro sign) and values across each scale's
  range, plus 0/NaN/±∞, format to the model's text (any synonym accepted for the time table).
  The general generator keeps to values whose rounding does not cross a unit boundary
  (human_format/2) and to non-zero values for the time scale (human_format/1).
- **Round trip** (`formatting_and_parsing_round_trip`): `try_parse(format(x))` is within half a
  unit of the last printed decimal of `x`, for units that do not end a suffix
  (human_format/4) and separators without trailing whitespace after other characters
  (human_format/6).
- **Parsing** (`parsing_reads_number_times_multiplier`): `<number><sep><suffix><units>` for a
  generated decimal and any known suffix (including `µ` for `u`) parses to `number ×
  multiplier`, the same through `parse_or_clamp`; an unknown suffix is `UnknownSuffix`, and
  `parse_or_clamp(_, true)` reads it as the largest multiplier.
- **Determinism** (`time_formatting_is_deterministic`): eight fresh time-scale formatters give
  the same text. **Expected failure** (human_format/3).

## Bugs (6)

- **human_format/1** (crash, high; `time_scale_formats_zero`): `Scales::Time().format(0.0)`
  panics — zero skips the time table and indexes the empty positional suffix list.
- **human_format/2** (wrong-result, medium; `scaled_values_stay_below_the_base`): the unit is
  chosen before rounding: `999_999.0` → `1000.00 k`, `0.999_999_9` → `1000.00 m`, time
  `59.999` → `60.00 s`.
- **human_format/3** (wrong-result, medium; `time_formatting_is_deterministic`,
  `time_synonyms_format_consistently`): time synonyms (`y`/`yr`/`year`, `mo`/`month`, …) are
  picked in `HashMap` order — a year formats as `1.00 y`, `1.00 year` or `1.00 yr` depending
  on the formatter instance.
- **human_format/4** (wrong-result, medium; `units_are_stripped_once_when_parsing`): units are
  stripped with `trim_end_matches`: with units `m`, `1.00 mm` parses as `1.0`; `1.50 kBB`
  is accepted.
- **human_format/5** (contract, low; `formatter_output_for_infinities_parses`): `try_parse`
  rejects the formatter's own `inf`/`-inf`/`NaN`.
- **human_format/6** (contract, low; `separator_survives_trimming_when_the_suffix_is_empty`):
  the input is trimmed before the separator is removed, so with separator ` | ` the
  formatter's own `1.00 | ` (no suffix) does not parse.

## Not bugs

- Values below the base print with a trailing separator and empty suffix (`format(5.0)` =
  `"5.00 "`); `-0.0` prints as `"-0.00 "`; a forced suffix is honoured even when it makes the
  number huge (`with_suffix("k").format(5e9)` = `"5000000.00 k"`); `with_base(0)` prints
  `inf Q` — all consequences of the documented design, not counted.
- `try_parse` does not accept `+`, exponents or `inf`; only the last is counted (as /5), since
  only that is the formatter's own output.
