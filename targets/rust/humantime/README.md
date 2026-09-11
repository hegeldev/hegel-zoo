# humantime

Human-friendly duration and RFC 3339 timestamp parsing/formatting
([chronotope/humantime](https://github.com/chronotope/humantime)). Tests live in the existing
`src/date.rs` and `src/duration.rs` test modules.

## What is tested

Durations (`duration.rs`):
- `format_duration` → `parse_duration` round-trip on arbitrary `Duration`s.
- Fractional seconds parse to the exact nanosecond value.
- A single integer with a unit equals the documented multiplier for that unit.
- `parse_duration` never panics on arbitrary strings built from duration-like fragments;
  reported error positions lie inside the input.

Timestamps (`date.rs`):
- `format_rfc3339*` → `parse_rfc3339` round-trip; fixed-precision formatters truncate rather than round.
- `parse_rfc3339` agrees with the `time` crate on the same input; nanosecond output parses with `time`.
- Strict and weak parsers never panic; everything strict accepts, weak accepts.
- Strict rejects trailing garbage (**fails: humantime/1**); weak rejects non-UTC offsets
  (**fails: humantime/2**, upstream #67).

## Oracles

The `time` crate for RFC 3339 parsing/formatting; documented unit multipliers.

## Not tested

Locale or leap-second behaviour beyond what the crate documents.

## History

- 2026-07-22: written against `76c8929` with hegeltest 0.28.2 (predecessor, `humantime.patch`).
- 2026-09-11: imported; ported to hegeltest 0.44.1 (`#[hegel::composite]` now takes `&TestCase`).
  Upstream HEAD is still `76c8929`.
