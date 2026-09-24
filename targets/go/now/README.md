# now

[jinzhu/now](https://github.com/jinzhu/now) is the time toolkit by GORM's author (4.7k stars):
`BeginningOf`/`EndOf` minute, hour, day, week (configurable `WeekStartDay`), month, quarter,
half year and year; `Monday`, `Sunday`, `EndOfSunday`, `Quarter`; a lenient `Parse` that tries a
list of layouts (`TimeFormats`) and fills the fields a string does not carry from "now" —
`"2017"` is 2017-01-01, `"10-13"` is this year's October 13th, `"12:20"` is today at 12:20 — with
`MustParse`, `Between` and a `Config` carrying the week start, location and layouts. About 450
lines without tests. The pinned commit is the June 2025 head, four commits past v1.1.5. MIT.
No CONTRIBUTING or AI policy in the repository (the README points at gorm.io/contribute);
not archived. Checked 2026-09-14.

## Oracle

Go's own `time` package and the calendar in the time's location. The beginning of a unit is the
first instant whose wall clock lies in that unit and the end is the last one — so `EndOfX` is
the next beginning minus a nanosecond, the package's own definition for weeks, months, quarters
and years. Weeks start on `WeekStartDay`; `Monday()` is the Monday on or before the date, with a
Sunday belonging to the week of the Monday six days earlier ("Last Monday if today is Sunday"),
`Sunday()` the Sunday on or after it, and `EndOfSunday` the end of that day — the README's
definitions. `Parse` follows the README's examples and the upstream tests: a date-only string is
midnight of that date (missing month and day are the 1st), a month-day string takes the current
year, a time-only string takes today's date, a date-time string carries its fields with the
missing clock parts zero, a string with a numeric offset keeps that offset, and a time-only
string followed by a date-only string combines them (asserted upstream). Strings no layout
accepts — hour 24+, minute or second 60+, month 13+, day 32+, February 30th, words, leading or
trailing blanks — are errors with the zero time, and `MustParse` panics. `Between` is strict at
both ends. The model is a few lines of calendar arithmetic done in UTC (where there are no
transitions) plus the date's first instant in the location (its midnight when that exists,
else the first instant after the gap); `BeginningOfHour` is the top of the time's own hour
(its own occurrence when the hour is repeated) and `EndOfHour` the last instant of the wall
hour, and a date-only string parses to the day's first instant.

## Properties

- `TestHegelCalendarUnitsBeginAndEndOnTheCalendar` — for a random instant in one of twenty IANA
  zones (New York, London, Berlin, Kolkata, Kathmandu, Lord Howe, Chatham, Havana, São Paulo,
  Apia, Tehran, Casablanca, Santiago, Sydney, Cairo, Asunción, Beirut, Auckland, St John's, UTC)
  or a fixed zone with a whole-minute offset, years 1975–2060, and a random `WeekStartDay`:
  `BeginningOf`/`EndOf` day, week, month, quarter, half and year equal the model's first and last
  instant, are idempotent, `BeginningOfX(EndOfX(t))` is `BeginningOfX(t)`, the package-level
  `WeekStartDay` path agrees with the `Config` path, and `Quarter()` is right.
- `TestHegelClockUnitsBeginAndEndOnTheClock` — `BeginningOf`/`EndOf` minute and hour against
  `time.Date` of the wall clock, with idempotence.
- `TestHegelParseFillsFromNow` — a time rendered in one of the twenty-one default layouts the
  oracle covers (eight date-only, nine date-time including RFC 3339 and `Z0700`, three time-only,
  and `1-2`), optionally with a 3-, 6- or 9-digit fraction, against a random "now": `Parse`,
  `MustParse`, `Config.With(...).Parse` with a `TimeLocation`, a `Config` restricted to that one
  layout (accepts) and to an unrelated layout (refuses); and the two-string form
  `Parse(timeOnly, date)`.
- `TestHegelMalformedStringsAreRefused` — nine shapes of unparseable strings: error, zero time,
  `MustParse` panics.
- `TestHegelMondaySundayAndBetween` — `Monday()`, `Sunday()`, `EndOfSunday()` against the
  model; `Monday(timeOnly)`/`Sunday(timeOnly)` keep the clock; `Between` with two rendered
  strings is strict.

Twenty thousand cases per property before saving. The generators draw the recorded shapes at
their natural rates: fixed-zone offsets in seconds (now/1, about 15% of the clock cases),
instants anywhere, transition hours and the days without a midnight or with a repeated last
hour included (now/2-6; 1-2% of the calendar and week cases, one in a million for Apia's
skipped date), Kitchen among the time-only layouts (now/8, one parse case in sixteen),
fractions of one to nine digits (now/7), the month-day string as the second string (now/9) and
both orders of the two-string form (now/10). The wide properties fail when they meet a shape
and are the expected failures mapped to the bug each usually shrinks to (`target.toml`: the
clock property to /1, `ParseFillsFromNow` to /7 with /8 and /10 as other basins, the calendar
and week properties to /3 as intermittent, since their shapes are in a few cases per hundred).
Each bug also has a narrow property over its shape region with random contents
(`TestHegelSubMinuteOffsetsBeginAndEndOnTheClock`, `TestHegelHoursAroundATransitionBeginAndEndOnTheClock`,
`TestHegelDaysWithoutAMidnightBeginOnTheCalendar`, `TestHegelMonthsWithoutAMidnightOnTheFirstBeginOnTheCalendar`,
`TestHegelDaysWithARepeatedLastHourEndOnTheCalendar`, `TestHegelWeeksAcrossASkippedDateBeginOnTheCalendar`,
`TestHegelFractionsOfAnyLengthParse`, `TestHegelKitchenTimesAreToday`,
`TestHegelMonthDayAfterATimeKeepsTheClock`, `TestHegelDateThenTimeKeepsTheDate`,
`TestHegelDatesWithoutAMidnightParse`); the zones' transitions and the dates with a shape (no
midnight, a repeated last hour, a skipped date) are computed from tzdata at start-up
(1974-2062), so each narrow property draws a zone, one of its shape dates and a random instant
or string on it. The pins are the regression examples beside them. `HEGEL_NO_KNOWN=1` switches
the shapes off (the wide case generators are filtered by the same shape tests, under 2% of
draws; the narrow properties draw the neighbouring region instead, and the two-string order is
fixed) for a run past the known bugs, under which the sixteen properties pass at 3000 cases.
Zone abbreviations are not compared for zoned strings, because `ParseInLocation`
reuses the location's zone when the offset matches (documented Go behaviour).

## Bugs (11; details in bugs.toml)

| id | severity | shape |
|----|----------|-------|
| now/1 | low | `BeginningOfMinute` is `Truncate(time.Minute)` on the absolute time: LMT +00:19:32 gets 12:34:32 |
| now/2 | medium | `BeginningOfHour`/`EndOfHour` in a repeated hour pick the earlier occurrence, so `EndOfHour(t) < t`; `EndOfHour` assumes 60-minute hours (Lord Howe: 03:29:59.999) |
| now/3 | medium | a missing midnight (DST starting at 00:00: Cuba, Chile, Paraguay, Lebanon, Egypt, …) puts `BeginningOfDay` on the previous day at 23:00; `BeginningOfWeek`, `EndOfWeek`, `Monday`, `Sunday`, `EndOfSunday` follow |
| now/4 | medium | the same on the 1st of a month: `BeginningOfMonth` in the previous month, `EndOfQuarter` of a September time is 31 October (Asunción 2002), `BeginningOfHalf` an hour late (Beirut 1990) |
| now/5 | medium | `EndOfDay` in a repeated 23rd hour (DST ending at midnight) returns the earlier 23:59:59.999, before `t` |
| now/6 | low | `BeginningOfWeek` across Samoa's skipped 30 December 2011 lands on Thursday, before the week's Friday start |
| now/7 | medium | fractions of other than 3/6/9 digits defeat the has-time regex: `"12:20:13.5"` is January 1st, `"… 12:00:21.5"` gets the current minute |
| now/8 | low | `"12:20PM"` (Kitchen) parses but lands on January 1st |
| now/9 | low | `"10-13"` matches the has-time regex via its hyphen, so `Parse("12:20", "10-13")` is 00:00 |
| now/10 | medium | `Parse("2017-10-13", "12:20")` is 2017-01-01 12:20 — `onlyTimeInStr` is ANDed across strings; the upstream test passes only because its date is 2011-1-1 |
| now/11 | medium | a date-only string for a day without a midnight parses to the previous day 23:00 (Havana, Santiago; Beirut gives 01:00), and `Parse("12:20", "2025-03-09")` has its clock overwritten: 2025-03-08 23:20 |

now/2–now/5 and now/11 share one root: wall clocks are rebuilt with `time.Date`, which, for a nonexistent
or repeated wall time, "returns a time that is correct in one of the two zones" (Go's own words;
it is not guaranteed which), and the arithmetic after it assumes days are 24 hours and hours 60
minutes. They are recorded separately because they hit different functions with different
magnitudes (an hour, a day, a week, a month).

## Not bugs (documented or design)

- `Parse("1013")` is the year 1013 (`"2006"` is the first layout); `Parse("0000-01-02")` is
  this year's January 2nd (a zero year is "replaced with current time"); `Parse("2017-10-13T12:20:21")`
  without an offset has no layout and is an error while `…Z` and `…+08:00` parse; a leading or
  trailing blank is an error (the layouts have none, though the regexes tolerate it);
  `Parse("1-2")` is a month and day, never a day and month.
- `Parse()` with no strings returns the zero time and a nil error, and `MustParse()` does not
  panic — a quirk of the variadic signature, not recorded.
- `Config.Parse` (as opposed to `Config.With(t).Parse`) uses the real `time.Now()`; the
  properties use the `With` form so that "now" is under the generator's control.
- A `Parse` result for a wall clock that is itself ambiguous or missing (today's 02:30 on the
  day the clocks go forward) is whatever `time.Date` returns; the model makes the same call.
- Transitions *inside* a unit are handled correctly everywhere: `EndOfWeek`, `EndOfMonth`,
  `EndOfYear` on a 23- or 25-hour day at the boundary are right when the midnight itself exists
  once (`AddDate` renormalises the wall clock), and `BeginningOfMinute` is right for every
  whole-minute offset including +05:45 and +12:45.

## History

- 2026-09-14: created at 2367773 (v1.1.5+4); 11 bugs, each with a pin, the properties redrawing
  the pinned shapes.
- 2026-09-24: the redraws went (STYLE.md rule 11): the properties draw the shapes and fail, one
  narrow property per bug was added, `HEGEL_NO_KNOWN=1` switches the shapes off. Removing the
  filters exposed three places where the oracle shared the library's assumptions: the clock
  model rebuilt the hour with `time.Date` (wrong in a repeated hour, as now/2 is) and now takes
  the top of the time's own occurrence and the last instant of the wall hour; the calendar and
  parse models used `time.Date` for midnight (wrong on a day without one, as now/3-5 and now/11
  are) and now use the date's first instant; and the clean-transition window was two hours,
  which missed St John's two-hour setback of 1988 (now three).
