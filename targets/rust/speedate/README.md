# speedate

[pydantic/speedate/](https://github.com/pydantic/speedate/).

## What is tested

**`tests/main.rs`**
- `prop_date_display_parse_roundtrip`: Format -> parse roundtrip for `Date`: any valid calendar date survives Display and re-parsing unchanged, and the string form is a fixpoint.
- `prop_time_display_parse_roundtrip`: Format -> parse roundtrip for `Time`, including microseconds and timezone offsets (`Z` and `+HH:MM`/`-HH:MM` forms).
- `prop_datetime_display_parse_roundtrip`: Format -> parse roundtrip for `DateTime` (the crown roundtrip).
- `prop_parse_never_panics`: All four parsers must return an error rather than panic, on both arbitrary text and near-miss input (a canonical datetime string with one byte corrupted).
- `prop_date_rejects_out_of_range_components`: Date strings with any component pushed just outside the calendar are rejected: month 0/13+, day 0, day beyond the month's length (which covers Feb 29 in non-leap years, Feb 30, Apr 31, ...).
- `prop_time_rejects_out_of_range_components`: Time strings with any component pushed out of range are rejected: hour 24+, minute 60+, second 60+ (i.e. leap seconds are not accepted), timezone offsets of 24h or more, and timezone minutes of 60+.
- `prop_datetime_timestamp_roundtrip`: `DateTime::from_timestamp(ts, micro).timestamp()` recovers `ts` for the whole documented "interpreted as seconds" range (|ts| <= 2e10).
- `prop_date_timestamp_roundtrip_second_unit`: With the timestamp unit pinned to seconds (no watershed inference), `Date -> timestamp -> Date` is the identity for every valid date, including dates beyond the 2e10 inference watershed (year > 2603).
- `prop_duration_display_parse_roundtrip`: Format -> parse roundtrip for `Duration` in ISO 8601 form, including the year/day split in Display and fractional-second trimming.
- `prop_duration_sign_symmetry`: Sign handling: `-X` parses to the same magnitude as `X` and `+X`, with `positive` flipped and all signed totals exactly negated.
- `prop_datetime_agrees_with_chrono`: Differential against chrono: the canonical string of any tz-aware DateTime parses as RFC 3339 in chrono and denotes the same instant.
- `prop_datetime_ordering_matches_chrono`: Ordering consistency: comparing two tz-aware DateTimes agrees with chrono's instant-based ordering of the same values.

## Oracles

## Not tested

## History

- 2026-04-15: predecessor base commit `6fafc2c60b5c` (Bump codecov/codecov-action from 5 to 6 in the actions group (#99)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/speedate.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-12: base bumped 6fafc2c60b5c → a68ce8660d04 (2026-09-05, "Fix integer parsing with out-of-range inputs (#106)"; 0.17.0); 0 bug(s) still reproduce. 548 tests pass.
