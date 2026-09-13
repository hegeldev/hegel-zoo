# iso8601

[badboy/iso8601](https://github.com/badboy/iso8601): a nom parser for ISO 8601 dates (calendar,
ISO week and ordinal forms), times, datetimes and durations, with `Display`, optional `serde`
and optional `chrono` conversions. It documents that it does not check calendar validity
(`2015-02-29` parses) and that the top-level functions discard leftover input.

Written in the zoo (not imported from the predecessor). Built with `--all-features` (`std`,
`chrono`, `serde`). The crate's own unit, integration and doc tests run alongside
`tests/hegel.rs`.

## What is tested

**`tests/hegel.rs`** — every text is *generated from* known components, so the expected parse
is exact; `jiff` is the second reading.
- `dates_parse_in_every_form_and_print_back`: a valid date (years −9998..=9998, biased to
  1890–2110 and to leap/edge days) in the calendar, ISO-week and ordinal forms — the week and
  ordinal numbers from `jiff` — in extended, basic and mixed spellings; the low-level
  `parsers::parse_date` leaves a suffix untouched; `Display` is the extended form and re-parses;
  serde round trip; `into_naive()`/`TryFrom` for the calendar and ordinal forms give the day.
- `out_of_range_date_fields_are_rejected`: month 0/13+, day 0/32+, week 0/54+, week-day 0/8/9,
  ordinal 0/367+, 3- or 5-digit years and a 1-digit day are parse errors (and serde errors).
- `times_parse_in_every_form_and_print_back`: hour 0..=24, optional seconds (incl. 60), a 1–9
  digit fraction with `.` or `,` (the crate keeps the first three digits as milliseconds), `Z`
  or `±hh[[:]mm]`, extended or basic; suffix untouched; `Display` (`HH:MM:SS.mmm±hh:mm`)
  re-parses; serde; `into_naive()` is `Some` exactly when hour < 24 and second < 60 and equals
  chrono's `from_hms_milli_opt`; `set_tz`.
- `out_of_range_time_fields_stop_the_parser`: hour 25+ / minute 60+ are errors; an out-of-range
  optional part (`:61`, `+25:00`) is left as the remainder by `parsers::parse_time`.
- `datetimes_are_the_instant_jiff_computes`: `<date>T<time>` in every form parses to the pair;
  `Display`/serde round trips; `into_fixed_offset()` is `Some` exactly for representable times
  and its `timestamp_millis()`/offset equal `jiff`'s for the same civil datetime and offset;
  for RFC 3339 texts `jiff::Timestamp::from_str` gives the same millisecond.
- `durations_parse_like_jiff_and_print_back`: `P[nY][nM][nD][T[nH][nM][n[.f]S]]` with any
  subset of components (values up to `u32::MAX`), the seconds fraction truncated to
  milliseconds; the same components from `jiff::Span` (within its unit limits); the
  `From<Duration> for core::time::Duration` 365-day-year/30-day-month model; `is_zero`;
  `Display` re-parses (`P0D` for zero); serde; `P` alone is rejected.
- `week_and_datetime_form_durations`: `PnW` is `Weeks(n)` (7-day weeks in the model);
  `P<date>T<time>` in the calendar form is the `YMDHMS` duration with those fields.
- Pinned: `week_dates_convert_to_the_day_jiff_names` (iso8601/1),
  `a_bare_time_designator_is_rejected` (iso8601/2).

## Oracles

The generating components; `jiff` 0.2 (`ISOWeekDate`, `day_of_year`, fixed-offset `Zoned`
timestamps, RFC 3339 `Timestamp` parsing, `Span` parsing); `chrono` 0.4 through the crate's own
conversions; the RFC 3339 appendix-A duration grammar quoted in the crate's docs.

## Not tested

Calendar validity (by design not checked: `2015-02-30` parses), leftover-input semantics beyond
"the suffix is returned" (e.g. `time("12:30:61")` is `12:30:00` with `:61` discarded, as
documented), `no_std`, fractional minutes (`12:30.5` is accepted, undocumented), offsets with
hour 24, `Display` of field values that no parse produces (e.g. `millisecond: 1500`, mixed-sign
offsets from `set_tz`).

## Bugs

- **iso8601/1** (medium): `Date::Week → chrono::NaiveDate` is one day late and fails for
  Sundays — the ISO week-day 1..=7 is passed to chrono's 0-based `Weekday::from_u32`; the
  crate's own tests expect `2023-W06-2` (a Tuesday) to be 8 February.
- **iso8601/2** (low): `PT` and `P1YT` parse as durations with an empty time part, and
  `parse_duration` swallows a trailing `T`; the quoted grammar requires a unit after `T`
  (`jiff` rejects them).

## History

- 2026-09-13: written in the zoo against `65e10440fed6` (2026-09-10, 0.6.6) with hegeltest
  0.44.1 and jiff 0.2. The whole crate (about 1 000 lines outside its tests) was read first:
  iso8601/1 was found by eye (chrono's weekday numbering) and confirmed by the pinned test's
  first run; iso8601/2 surfaced as a leftover mismatch (`P0D` + `T12:00`) in the first run and
  at 1 000 cases. Clean otherwise at 100 + 3 × 1 000 + 10 000 cases. Test defects on the way:
  a "5-digit year" case that spelled a valid mixed-separator date, and jiff keeping
  sub-millisecond digits (truncating toward zero on negative instants) where the crate keeps
  three — the RFC 3339 comparison is limited to ≤ 3 fraction digits.
