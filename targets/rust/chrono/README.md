# chrono

[chronotope/chrono](https://github.com/chronotope/chrono): the `chrono` crate (0.4, main), Rust's
most used date-time library — `NaiveDate`/`NaiveTime`/`NaiveDateTime`, `DateTime<Utc|FixedOffset>`,
`TimeDelta`, `strftime` formatting and parsing, RFC 3339/2822, `DurationRound`/`SubsecRound`.

Written in the zoo (not imported from the predecessor). Default features (`clock`, `std`, …); the
crate's own unit and doc tests run alongside `tests/hegel.rs`.

## What is tested

**`tests/hegel.rs`** — two oracles: a small calendar model for chrono's whole range (years
−262 144..=262 142: Hinnant's `days_from_civil`/`civil_from_days`, the ISO week rules, `%U`/`%W`
week numbering, i128 nanosecond arithmetic) and the `jiff` crate for −9999..=9999 — an
independent library with its own calendar arithmetic, `strftime`, RFC 2822/3339 codecs and
`Span` parser.
- `dates_match_the_calendar_model`: for a date anywhere in the range (uniform day counts,
  −9999..=9999, 1890–2110, first/last days of years, the corners): day count both ways,
  `ordinal`/`weekday`/`leap_year`/`quarter`/ISO week against the model; every constructor
  rebuilds it (`from_ymd_opt`, `from_yo_opt`, `from_isoywd_opt`, `from_weekday_of_month_opt`) and
  refuses the day after the month, ordinal 0/367, month 13, the weekday after the last of the
  month; `succ_opt`/`pred_opt`; every `with_*` setter equals the constructor with one component
  replaced; `Display`/`Debug`/`FromStr`/`%F` (`+`/`-` sign outside 0..=9999) round trip; `%U`,
  `%W`, `%j`, `%u`, `%w`, `%V`, `%G`, `%C%y` against the model; parsing back `%G-W%V-%u`, `%Y-%j`,
  `%A, %B %e, %Y`, `%a %b %d %Y`, `%v`, `%Y%m%d`; a wrong `%a` is rejected.
- `date_arithmetic_matches_the_model`: `checked_add_days`/`checked_sub_days` (0..2^64),
  `checked_add_signed`/`checked_sub_signed`, `signed_duration_since`/`Sub`/`Add`, `Ord`,
  `checked_add_months`/`checked_sub_months` (month index moves, day clamped, `None` beyond the
  range), `iter_days`/`iter_weeks` forwards and reversed, the day-count bounds.
- `dates_agree_with_jiff`: weekday, day of year, leap year, ISO week date both ways, first/last of
  month, tomorrow/yesterday, ±4 000 000 days, ±120 000 months (both clamp the day), differences in
  days, the n-th weekday of the month for n = 1..=5.
- `times_match_the_model`: `NaiveTime` constructors and their validity rules (leap seconds as
  `nanosecond ≥ 1e9` only after `:59`, `with_nanosecond` after any second as documented),
  `Ord`, `signed_duration_since` with the crate's leap-second rule (the leap second seen is the
  only one), `overflowing_add_signed`/`overflowing_sub_signed` (wrapped seconds in whole days),
  `%H:%M:%S%.f` with `:60` and 0/3/6/9 fraction digits, `%.3f`/`%.6f`/`%.9f`/`%3f`/`%6f`/`%9f`,
  12-hour clock (`%I %p`, `%l %P`, `hour12`), `%k`, `%-H`, `%R`, `Display`/`FromStr`.
- `timestamps_agree_with_jiff_and_the_model`: `timestamp`, `_millis`, `_micros`,
  `_nanos_opt` (floor semantics), `from_timestamp*` round trips, leap-second nanos in
  `from_timestamp`; the same instant in jiff has the same civil fields, in UTC and in a fixed
  offset; `with_timezone`, `naive_utc`/`naive_local`, `from_local_datetime`/`from_utc_datetime`,
  `east_opt`/`west_opt` bounds; `Display`/`Debug` of offsets (`+hh:mm[:ss]`) and of date-times
  (round trips for whole-minute offsets); `%z`/`%:z` round the seconds to the nearest minute
  (never `24:00`), `%::z` prints them, `%:::z` truncates to hours, `%s` is the floor timestamp;
  ordering across offsets follows the instant.
- `datetime_arithmetic_matches_the_model`: `checked_add_signed`/`checked_sub_signed` and the
  operators over the whole range against i128 nanoseconds (`None` beyond `MIN`/`MAX`),
  `signed_duration_since`, `Ord`, whole days/months via the date, `std::time::Duration`.
- `strftime_agrees_with_jiff`: 50 specifiers (with `-`/`_`/`0` padding flags) formatted one by
  one and in drawn combinations with drawn separators, for a `DateTime<FixedOffset>` (whole
  minutes) and its naive value, equal jiff's `strtime::format` character for character.
- `strftime_round_trips`: fourteen complete formats (`%F %T`, `%Y-%j %T`, `%G-W%V-%u %T`, 12-hour
  clocks, month/weekday names, `%s`, …) read back the value in chrono *and* in jiff's `strptime`;
  `%.f` and `.%f` fractions; `%z`, `%:z`, `%+` with offsets (rounded minutes); `Z`/`z`/`UTC`/
  `+00:00` spellings of `%+`; `parse_and_remainder` vs trailing input.
- `rfc3339_and_rfc2822_agree_with_jiff`: `to_rfc3339` = `%+`, parsed back by chrono and by jiff
  to the same instant; jiff's RFC 3339 text parsed by chrono to the same value and offset;
  `to_rfc3339_opts` with every `SecondsFormat` and `use_z`; `to_rfc2822` (fractions dropped)
  parsed back by both, jiff's RFC 2822 text parsed by chrono.
- `rounding_matches_the_model`: `round_subsecs`/`trunc_subsecs` for 0–12 digits (halfway up),
  `duration_trunc`/`duration_round`/`duration_round_up` by nanoseconds to hundreds of days on
  `NaiveDateTime`, `DateTime<Utc>` and `DateTime<FixedOffset>` (on the local wall clock) against
  floor/nearest-half-up/ceil of the nanoseconds since the epoch, the error cases
  (`DurationExceedsLimit` for zero, negative or unrepresentable spans, `TimestampExceedsLimit`),
  idempotence.
- `time_delta_matches_i128_nanoseconds`: `TimeDelta` rebuilt from its nanoseconds, every
  `num_*` accessor (truncating toward zero, `subsec_nanos` signed), `checked_add`/`sub`
  (`None` beyond `MIN`..=`MAX`), `checked_mul` within the range, `checked_div` within 1 ns,
  `abs`, `Neg`, `Ord`, constructors, `to_std`/`from_std`, `Display` (`P0D` / `[-]PT<s>[.<f>]S`)
  parsed back by jiff's `Span`.
- KNOWN FAILURES, one pinned test each: `offset_specifiers_with_seconds_or_hours_only_parse_back`
  (chrono/1), `negative_unix_timestamps_parse` (chrono/2),
  `nanosecond_count_is_printed_as_documented` (chrono/3), `iterators_start_from_the_date_itself`
  (chrono/4), `division_is_exact_to_the_nanosecond` (chrono/5),
  `multiplication_beyond_the_range_is_none` (chrono/6).

## Oracles

The proleptic Gregorian calendar (Hinnant's algorithms, ISO 8601 week rules), i128 nanosecond
arithmetic, `jiff` 0.2 (`civil::Date`/`DateTime`, `Timestamp`, `tz::TimeZone::fixed`,
`fmt::strtime`, `fmt::rfc2822`, `Span`), and the crate's own documentation (`strftime` table,
leap-second handling, `DurationRound`, `TimeDelta` range).

## Not tested

`Local` and the TZif/`iana-time-zone` code (system dependent), `serde`/`rkyv`/`arbitrary`
integrations, `unstable-locales` and the locale specifiers (`%c`, `%x`, `%X`, `%r`), `%Z`
(documented to print the offset and to skip a word when parsing), `%v`/`%C`/`%:::z`/`%s`/`%.f`
in the jiff differential (jiff pads or rounds those differently — checked against chrono's own
rules instead), offsets with seconds in RFC 3339/2822 (not representable), two leap seconds in one
subtraction (outside the documented contract), `Display` of a `NaiveDateTime` (space) parsed by
`FromStr` (documented as the `Debug` format with `T`), `Months`/`Days` beyond `u32`/`u64` draws,
`Parsed` directly, `no_std`, `wasmbind`.

## History

- 2026-09-13: written in the zoo against `6adaa5240c26` (2026-08-03, "Return None from
  from_isoywd_opt for out-of-range years"; 0.4.45) with hegeltest 0.44.1 and jiff 0.2.37. Test
  defects fixed on the way: jiff's `Timestamp` splits negative instants with a negative fraction,
  `%C`/`%:::z`/`%z`-with-seconds/`%s`-with-fraction conventions differ, the leap-second model,
  `overflowing_add_signed` returns seconds not days, `%z` rounds the offset to the minute,
  `TimeDelta::try_milliseconds(i64::MIN)` is `None`, jiff refuses `P0D` as a `SignedDuration`.
  **Six bugs**: chrono/1 (`%::z`/`%:::z` don't parse their own output — upstream #1228/#1629,
  found independently), chrono/2 (negative `%s` never parses), chrono/3 (`%f` is padded, the
  docs say it isn't), chrono/4 (`MAX.iter_days()` is empty and `iter_weeks` drops the last representable week — new in
  0.4.45's iterator rework), chrono/5 (`checked_div` off by a
  nanosecond), chrono/6 (`checked_mul` beyond `MAX`, then `num_milliseconds` panics).
