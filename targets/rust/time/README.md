# time

[time-rs/time](https://github.com/time-rs/time): the `time` crate (0.3, main), the other widely
used Rust date-time library — `Date`/`Time`/`PlainDateTime` (`PrimitiveDateTime`),
`OffsetDateTime`/`UtcDateTime`/`Timestamp`, `UtcOffset`, `SignedDuration` (`Duration`),
format descriptions (`[year]-[month]-[day]`), the well-known RFC 3339/RFC 2822/ISO 8601 formats.

Written in the zoo (not imported from the predecessor). Built with `--all-features` (the crate's
own integration tests need `rstest`, which only compiles that way; this also turns on
`large-dates`, so years span ±999 999); the crate's unit, doc and integration tests run alongside
`tests/hegel.rs`.

## What is tested

**`tests/hegel.rs`** — two oracles: a small calendar model for the whole range (Hinnant's
`days_from_civil`/`civil_from_days`, the ISO week rules, `%U`/`%W` week numbering, Julian day
numbers, i128 nanosecond arithmetic) and the `jiff` crate for −9999..=9999 — an independent
library with its own calendar arithmetic, `strftime`, RFC 2822/3339 codecs — with `time`'s
format-description components mapped onto `strftime` specifiers.
- `dates_match_the_calendar_model`: for a date anywhere in ±999 999 (uniform day counts,
  −9999..=9999, 1890–2110, first/last days of years, the corners): day count both ways, Julian day
  both ways (`to_julian_day` = days since 1970-01-01 + 2 440 588), `ordinal`, `weekday` (all four
  numberings), ISO week date, `sunday_based_week`/`monday_based_week`, `Month::length`,
  `util::{days_in_month, is_leap_year, days_in_year, weeks_in_year}`; every constructor rebuilds
  it and refuses day 0/one past the month, ordinal 0/367, week 0/one past the year;
  `next_day`/`previous_day` (`None` at the ends), `next_occurrence`/`prev_occurrence` (strictly
  after/before), `nth_next_occurrence`/`nth_prev_occurrence`; `replace_year/month/day/ordinal`
  equal the constructors; `Display` (four-digit year, signed outside 0..=9999); the descriptions
  `[year]-[month]-[day]`, `[year]-[ordinal]`, `[year base:iso_week]-W[week_number]-[weekday
  repr:monday]`, `[weekday], [month repr:long] [day padding:none], [year]` and the Monday-based
  week description round-trip.
- `date_arithmetic_matches_the_model`: `checked_add`/`checked_sub` of a `SignedDuration` (its
  whole days), `checked_add_std`/`checked_sub_std`, `saturating_add`/`saturating_sub`, `Sub`
  (`SignedDuration::days`), `Ord`, the Julian-day bounds, `MIN`/`MAX`.
- `dates_agree_with_jiff`: weekday, day of year, leap year, days in month, ISO week date both
  ways, tomorrow/yesterday, ±4 000 000 days, differences in days, the n-th weekday
  before/after, first/last of month, `Month::next/previous`.
- `times_match_the_model`: `Time` accessors and constructors (`from_hms*`, the refusals at 24/60/
  1e9), `replace_*`/`truncate_to_*`, `Ord`, `Sub` (signed, same day), `duration_since`/
  `duration_until` (forward around the clock), `Add`/`Sub` of `SignedDuration` and
  `std::time::Duration` wrapping at midnight; `[hour]:[minute]:[second].[subsecond digits:9]`,
  `[subsecond]` (shortest, at least one digit), `[subsecond digits:3]` truncating, the 12-hour
  clock with `[period]`/`[period case:lower]`, `Display`.
- `offset_date_times_agree_with_jiff_and_the_model`: `UtcOffset` accessors, `from_hms` and the
  ±25:59:59 bounds; `unix_timestamp`/`unix_timestamp_nanos` (floor), `from_unix_timestamp*`,
  `UtcDateTime`, `Timestamp` (`as_seconds/milliseconds/microseconds/nanoseconds`, civil
  accessors); the same instant in jiff has the same civil fields in UTC and in the offset;
  `to_offset`/`checked_to_offset`/`to_utc`/`replace_offset` keep the instant, equality and
  ordering follow the instant, jiff's `with_time_zone` agrees on the converted wall clock; RFC 3339
  round trip in `time` and jiff (both directions), `Z` only for UTC, `UtcDateTime::parse`;
  `Iso8601::DEFAULT` round trip and shape; RFC 2822 round trip (fractions dropped) parsed back by
  `time` and jiff, jiff's RFC 2822 text parsed by `time`.
- `datetime_arithmetic_matches_the_model`: `PlainDateTime` `checked_add`/`checked_sub`/
  `saturating_add` and the operators over the whole range against i128 nanoseconds (`None` beyond
  `MIN`/`MAX`), differences, `Ord`, `replace_time`/`replace_date`/`truncate_to_day`,
  `to_julian_day`, the same through `assume_utc`/`as_utc`/`assume_offset`.
- `format_descriptions_agree_with_jiff`: 29 components (year, two-digit year, numeric/short/long
  month, padded/space/unpadded day, ordinal, long/short/Sunday/Monday weekday, ISO/Sunday/Monday
  week numbers, ISO week year, 24-/12-hour hours with each padding, minute, second, period,
  `±hhmm`/`±hh:mm` offsets) formatted one by one and in drawn combinations with drawn
  separators equal jiff's `strtime::format` character for character; `[unix_timestamp]` is the
  floor timestamp (jiff's `%s` truncates, compared on whole seconds); a complete description with
  offset parses back in `time` and jiff.
- `format_descriptions_round_trip`: thirteen complete descriptions (calendar, ordinal, ISO week,
  Monday-based week, 12-hour clock, month/weekday names, no separators, `[unix_timestamp]` and
  `[unix_timestamp precision:nanosecond]`) read back the value over the whole range; `[subsecond]`
  fractions; `[offset_hour sign:mandatory]:[offset_minute]:[offset_second]` and `±hhmm` with
  offsets; trailing input is an error.
- `signed_durations_match_i128_nanoseconds`: `SignedDuration` rebuilt from its nanoseconds, the
  sign invariant of the two fields, every `whole_*`/`subsec_*` accessor (truncating toward zero),
  `checked_add`/`sub`/`mul`/`div`/`neg` (`None` beyond `MIN`..=`MAX`, division exact), the
  `saturating_*` versions, `abs`/`unsigned_abs`, `Ord`, constructors, nanosecond carry in `new`,
  `std::time::Duration` conversions, `seconds_f64`/`checked_seconds_f64` round trip, `Display`
  shape.
- KNOWN FAILURES, one pinned test each: `sunday_based_week_numbers_parse_back` (time/1),
  `saturating_subtraction_saturates_toward_the_result` (time/2),
  `rfc2822_negative_offsets_below_an_hour_parse_back` (time/3).

## Oracles

The proleptic Gregorian calendar (Hinnant's algorithms, ISO 8601 week rules, Julian day numbers),
i128 nanosecond arithmetic, `jiff` 0.2 (`civil::Date`/`DateTime`, `Timestamp`,
`tz::TimeZone::fixed`, `fmt::strtime`, `fmt::rfc2822`), and the crate's own documentation
(format-description modifiers, `duration_until`, `UtcOffset::from_hms` sign rule, the
`SignedDuration` range).

## Not tested

`OffsetDateTime::now_local` and the local-offset code (system dependent), `serde`/`rand`/`quickcheck`
integrations, `parse_owned` (`[first]`/`[optional]`), `Ignore`, `[year repr:century]` and
`[subsecond]` in the jiff differential (jiff pads `%C` and spells fractions differently — checked
against `time`'s own rules instead), the RFC 2822 obsolete syntax, `Iso8601` configurations other
than `DEFAULT`, `Timestamp` beyond the `OffsetDateTime` range, the `time::macros`, the weekday of a
parsed `[weekday], [year]-[month]-[day]` (not cross-checked against the date; the documentation
doesn't say it should be — chrono and jiff reject a mismatch), `[year][month][day]` without
separators outside 0..=9999 (a signed extended-range year reads up to six digits).

## History

- 2026-09-13: written in the zoo against `4784b0a65b36` (2026-09-07; 0.3.55) with hegeltest
  0.44.1 and jiff 0.2.37. Test defects fixed on the way: `duration_until` is the forward distance
  around the clock, `Display` signs years beyond 9999 with `+`, jiff's `%s` truncates, a signed
  year swallows unseparated month digits, the model's own overflows at `SignedDuration::MIN`/`MAX`.
  **Three bugs**: time/1 (Sunday-based week numbers parse to the wrong date — the Monday
  adjustment is used for both), time/2 (`saturating_sub` saturates the wrong way for a zero
  seconds field), time/3 (RFC 2822 `-00mm` offsets lose their sign — the fix for #522 in 0.3.18
  never reached the RFC 2822 parser).
