# carbon — Hegel properties for `github.com/dromara/carbon/v2`

[dromara/carbon](https://github.com/dromara/carbon) is a Go date and time
library in the style of PHP's Carbon: a `Carbon` value wrapping `time.Time`
with a week start, a locale and a layout, creators (`CreateFromDate…`,
`CreateFromTimestamp…`, `Parse`, `ParseByLayout`, `ParseByFormat`),
travellers (`AddYears`, `AddMonthsNoOverflow`, `AddHours`, …), boundaries
(`StartOfWeek`, `EndOfQuarter`, …), differences (`DiffInMonths`,
`DiffForHumans`), comparisons, PHP-style `Format` letters, dozens of
`To…String` outputs, JSON wrapper types, and Hebrew, Julian, Chinese lunar
and Persian calendars. Pinned at `9c24fbd` (after v2.6.17, 2026-09-19).

## Build

The patch adds `go.mod` changes and twelve test files in `package
carbon_test`: `hegel_test.go` (plumbing, the collector, the `known` value
of thirty-one switches — one per recorded bug, all off by default — and the
case judge), `hegel_idioms_test.go` (the harness idioms shared with the
excelize, graphql-go, cobra and cascadia targets), `hegel_moments_test.go`
(the records the properties draw — a moment in one of thirteen zones,
pairs and triples of moments, week settings, amounts, duration strings —
and their package-level generators, every weight tuned until its realised
rate is the nominal one, the measured figure beside it),
`hegel_models_test.go` (the zones, the shared models and the tables),
`hegel_core_test.go` (the fourteen core properties: a case record per
family, a model `expected(c, k)` of every checked value that follows the
recorded bugs in `k` as replicas of the library's code, the classifier that
names a case's shape from the model alone, the judge), `hegel_core_shapes_test.go`
(eleven narrow properties, one per bug the core properties can reach),
`hegel_format_test.go` (the three formatting and parsing properties: the
format records with a pure renderer, the forty-nine output entries, the
locales read from the library's `lang/*.json`, the models with the replicas
of the literal-marker, timestamp-layout, literal-copying, receiver-moving
and English-`l` rules), `hegel_format_shapes_test.go` (six narrow
properties), `hegel_calendar_test.go` (the four calendar properties: a
case record per calendar with a drawn locale or probe date, the models
with the replicas of the fourteen calendar rules),
`hegel_calendar_refs_test.go` (the reference algorithms and tables: Reingold
& Dershowitz, the 2820-year cycle with the official deviation, the Julian
day of an instant, the Hong Kong Observatory tables, and the library's
rules transcribed as replicas), `hegel_calendar_shapes_test.go` (fourteen
narrow properties) and `hegel_pins_test.go` (thirty-one pins). No external
tool is needed; the run takes about twenty-five seconds at the default
case count (the shrinking of the properties that reach a bug) and under
ten under `HEGEL_NO_KNOWN=1`.

## Oracles

- **`time.Time` itself** for everything a Carbon delegates: getters,
  `AddDate` for the calendar travellers, `time.Unix(sec+k, nsec)` for the
  clock travellers (so overflow of `time.Duration` is visible), `time.Date`
  for setters and boundaries, instants for comparisons, `Min`/`Max`/
  `Closest`/`Farthest`, and the Go layout twin of each PHP format for
  `Format`/`Layout`.
- **Bracketing** for the calendar differences: `DiffInYears(k)` must satisfy
  `s + k years ≤ e < s + (k+1) years`, and likewise for months, days and
  weeks (the documented value is the `k` the bracket gives, found by binary
  search).
- **Replicas** of the library's rules for the recorded bugs, each under its
  switch of the `known` value (`DiffInSeconds` on whole-second timestamps,
  days as elapsed seconds over 86400, the year and month fields read in each
  side's own zone with one correction, the clock amount multiplied into a
  `time.Duration`, `IsSagittarius` from November 22, the zero-time shortcut
  of `BetweenIncluded*`, …): the model with every switch off states the
  documented behaviour, and the classifier runs it with each switch alone
  and each switch removed to name the shape of a case before the library is
  called.
- **A PHP `Format` model** written letter by letter from the documentation
  (including the `S`/`U`/`V`/`X` timestamps, `W`/`N`/`K`/`L`/`G`/`w`/`t`/
  `z`/`o`/`q`/`c` specials and `\` escapes), and round trips
  `Format → ParseByFormat`, `Layout → ParseByLayout` and every `To…String`
  output through `Parse`/`ParseByLayout`, with the Go `time` limits (LMT
  sub-minute offsets, numeric zone abbreviations, two-digit years) as
  explicit gates.
- **Reference calendar algorithms**: Reingold–Dershowitz for the Hebrew
  calendar (calibrated on published Tishri dates), the Birashk 2820-year
  cycle for the Persian calendar with the official calendar's deviation in
  1403/1404 and the published Nowruz dates 1398–1408, `JD = unix/86400 +
  2440587.5` for Julian days, and the Hong Kong Observatory leap-month and
  New Year tables 1900–2100 for the Chinese lunar calendar (the month
  lengths read from the library's own table in its clean region — noon in
  Shanghai, a year in the table — and relabelled for 2033), with round
  trips through each calendar's `ToGregorian` in the drawn zone, and the
  month and weekday names in both locales of each calendar against tables
  of the test's own.
- **Tables** for seasons, zodiac signs and `DiffForHumans` strings.

## Properties

| Test | Checks | Reaches |
|---|---|---|
| `TestHegelGettersAgreeWithTime` | every getter (year … nanosecond, day of week/year, week of month/year, quarter, days in month, leap and long years, week and month names) against `time.Time` for a drawn week start and weekend | carbon/1 whenever the week does not start on Monday |
| `TestHegelCalendarAdditionAgreesWithAddDate` | `Add/SubYears/Quarters/Months/Weeks/Days` and the `NoOverflow` variants against `AddDate` and a clamping model; receiver untouched | — |
| `TestHegelClockAdditionAgreesWithUnix` | `Add/SubHours … Nanoseconds` against `time.Unix` arithmetic, amounts up to about 9500 years | carbon/6 when the amount overflows a `time.Duration` |
| `TestHegelAddDurationAgreesWithParseDuration` | `AddDuration`/`SubDuration` against `time.ParseDuration`; a bad string gives an error on the copy only | carbon/7 on a bad string |
| `TestHegelBoundariesAgreeWithModel` | `StartOf/EndOf` century … second against `time.Date` models for every week start | — |
| `TestHegelSettersAgreeWithDate` | `SetYear … SetNanosecond`, `SetDate`, `SetTime`, `SetDateTime`, `SetTimezone` against `time.Date` | — |
| `TestHegelDiffInYearsAndMonthsBracketTheEnd` | `DiffInYears`, `DiffInMonths` (and `Abs`) bracket the end for any pair, in the same or different zones | carbon/4 when the zones differ and the fields disagree, carbon/30 from the 29th–31st |
| `TestHegelDiffInSmallUnitsAgreeWithElapsed` | `DiffInDays … DiffInSeconds` and `DiffInDuration` against elapsed time and calendar days | carbon/2 on sub-second parts, carbon/3 across a DST change |
| `TestHegelDiffStringsAgreeWithModel` | `DiffInString`, `DiffAbsInString`, `DiffForHumans` against a unit model | carbon/2, 3 and 30 as above |
| `TestHegelComparisonsAgreeWithInstants` | `Eq/Ne/Gt/Gte/Lt/Lte/Between*`, `IsSame*`, `Compare` against instants | carbon/28 on a zero receiver and bound |
| `TestHegelExtremaAgreeWithInstants` | `Max`, `Min`, `Closest`, `Farthest` | carbon/2 on sub-second parts |
| `TestHegelSeasonAndConstellationAgreeWithTables` | `Season`, `Is<Season>`, `Constellation`, `Is<Sign>` against the tables | carbon/5 on November 22 |
| `TestHegelCreatorsAgreeWithTime` | `CreateFromDate/Time/DateTime/Timestamp*/StdTime`, `Parse` of RFC 3339 and the default layouts | — |
| `TestHegelWrapperTypesRoundTrip` | `DateTime`, `Date`, `Time…`, `Timestamp…` wrapper types through `encoding/json` and `database/sql` scanning | — |
| `TestHegelFormatAgreesWithModel` | `Format` against the letter model (the names from the drawn locale) and `Layout` against the Go twin, in every zone, week start and locale | carbon/1 on `D` with a non-Monday week start, carbon/25 on `l` under a locale |
| `TestHegelFormatParsesBack` | `ParseByFormat(Format(f), f)` and `ParseByLayout(Layout(l), l)` recover the instant to the format's precision; the format's literals drawn from a pool that includes Go-token spellings | carbon/10 on a timestamp letter, carbon/13 on a colliding literal |
| `TestHegelOutputStringsParseBack` | 45 `To…String` outputs and the four timestamp layouts match their documented text, `Parse`/`ParseByLayout` read them back, a drawn timezone argument leaves the receiver | carbon/8 on a Zulu/Http output outside UTC, carbon/10 on a timestamp layout, carbon/14 on a timezone argument |
| `TestHegelHebrewCalendarAgreesWithReingoldDershowitz` | `Hebrew()`/`CreateFromHebrew` and the `hebrew` package against the reference algorithm, both ways, in the drawn zone; the month and weekday names in `en` and `he` | carbon/27 on month 12 of a leap year |
| `TestHegelPersianCalendarAgreesWithBirashk` | `Persian()`/`CreateFromPersian` against the cycle with the official deviation and the Nowruz dates, both ways; the names in `en` and `fa` | carbon/19 on years 1–473, carbon/22 before 1582-10-15, carbon/18 in 1404, carbon/26 on a Sunday in `fa`, carbon/31 on a day that begins with a DST gap |
| `TestHegelJulianDayAgreesWithTheInstant` | `Julian().JD()/MJD()` against `unix/86400 + 2440587.5`, read back through `NewJulian` and `CreateFromJulian` | carbon/23 before 1886-04-03 or from 2132-08-31, carbon/24 before 1582-10-15, carbon/29 at any non-zero offset |
| `TestHegelLunarCalendarRoundTripsAndMatchesTheTables` | `Lunar()`/`FromStdTime` against the clean-region oracle, `NewLunar` validation on a drawn probe date, round trips in the drawn zone and in the default one, leap months and New Year dates against the HKO tables | carbon/15 west of Beijing, carbon/16 outside 1900–2100, carbon/17 on an impossible probe, carbon/20 in a flipping hour, carbon/21 in lunar 2033 |
| `TestHegelWeekNamesIgnoreTheWeekStart` | the week-name getters with a non-Monday week start | carbon/1 |
| `TestHegelDiffInSecondsKeepsSubSecondParts` | the second/minute/hour differences and `Closest`/`Farthest` on a pair whose sub-second parts matter | carbon/2 |
| `TestHegelDiffInDaysCountsCalendarDays` | `DiffInDays`/`DiffInWeeks` on a pair across a DST change (ten zones' transitions, 1971–2037) | carbon/3 |
| `TestHegelDiffInYearsIsZoneIndependent` | `DiffInYears`/`DiffInMonths` on a pair in two zones whose fields disagree | carbon/4 |
| `TestHegelNovember22IsScorpio` | the sign predicates on any November 22 | carbon/5 |
| `TestHegelClockAdditionBeyondDurationRange` | a clock amount beyond ±292 years in any unit | carbon/6 |
| `TestHegelAddDurationLeavesTheReceiver` | an unparsable duration string | carbon/7 |
| `TestHegelSetDefaultKeepsTheWeekStart` | `SetDefault` with `WeekStartsAt` unset keeps the week start (the global default restored afterwards) | carbon/9 |
| `TestHegelZeroCarbonIsUsable` | twenty-two methods on the zero `Carbon{}` against the Carbon created from the zero time | carbon/11 |
| `TestHegelZeroTimeIsNotBetweenAnEmptyRange` | `BetweenIncluded*` on a zero receiver with an equal, inverted or invalid bound | carbon/28 |
| `TestHegelDiffInMonthsNeverPassesTheEnd` | `DiffInMonths` from the 29th–31st to an end its one correction does not reach | carbon/30 |
| `TestHegelZuluOutputsAreUtc` | the six GMT/Z outputs on a moment outside UTC, printed and read back | carbon/8 |
| `TestHegelTimestampLayoutsReadBack` | the `unix…` layouts and the `S`/`U`/`V`/`X` letters through both parsers | carbon/10 |
| `TestHegelFormatLiteralsAreLiteralWhenParsing` | a round-trip format with a literal that spells a Go layout token | carbon/13 |
| `TestHegelOutputWithTimezoneLeavesTheReceiver` | an output call with a timezone argument, good or bad | carbon/14 |
| `TestHegelFormatWeekdayNameIsLocalised` | `Format("l")` under a non-English locale | carbon/25 |
| `TestHegelDiffForHumansReadsTheNowResource` | `DiffForHumans` with a `now` resource of several `\|`-separated forms | carbon/12 |
| `TestHegelLunarDatesAreDatesInEveryZone` | a lunar date through `ToGregorian(zone)` west of Beijing and `CreateFromLunar` | carbon/15 |
| `TestHegelLunarOutsideTheTableIsAnError` | `Lunar()` and `lunar.FromStdTime` on a moment outside 1900–2100 | carbon/16 |
| `TestHegelNewLunarRejectsImpossibleDates` | `NewLunar` with month 13 or 0, a 30th of a 29-day month, a wrong leap flag or day 31 | carbon/17 |
| `TestHegelPersian1403IsTheLeapYear` | a day of 1404 or 30 Esfand 1403, both ways | carbon/18 |
| `TestHegelPersianYearsStartIn622` | a day of Persian years 1–473, both ways | carbon/19 |
| `TestHegelLunarDayChangesAtMidnight` | a moment in an hour the elapsed-time day count misplaces | carbon/20 |
| `TestHegelLunar2033LeapMonthIsTheEleventh` | a moment from 2033-08-25 to 2034-01-19 | carbon/21 |
| `TestHegelPersianRoundTripsBeforeTheReform` | a day before 1582-10-15 through `Persian()` and back | carbon/22 |
| `TestHegelJulianDayReadsBackAtAnyMagnitude` | a moment before 1886-04-03 or from 2132-08-31 through the MJD and `CreateFromJulian` | carbon/23 |
| `TestHegelJulianDayIsProlepticBeforeTheReform` | a day before 1582-10-15 | carbon/24 |
| `TestHegelPersianSundayIsYekshanbeh` | `ToWeekString("fa")` on a Sunday | carbon/26 |
| `TestHegelHebrewAdarsAreNumberedInLeapYears` | `ToMonthString` of month 12 in a leap year, both locales | carbon/27 |
| `TestHegelJulianDayIsZoneIndependent` | a moment at a non-zero offset and the same instant in UTC | carbon/29 |
| `TestHegelPersianDateIgnoresTheDstGap` | a day that begins with a DST gap, both ways | carbon/31 |

The fourteen core properties draw the shapes of the recorded bugs at their
natural rates — a sub-second part in two moments of three, a bad duration
string one in ten, an overflowing clock amount one in twenty, two zones in a
quarter of the year/month pairs, November 22 one day in 365, the zero time
as the engine's first case — and are the expected failures mapped to the
bug they shrink to most often over forty rounds (`target.toml`: the
getters, duration, small-unit, string, extrema and comparison properties
plain, the clock addition, year/month and season ones intermittent; the
formatting properties plain to carbon/1, 10 and 14, the last the plurality
over carbon/8 by twenty-one rounds to nineteen; the Persian, Julian and
lunar calendar properties plain to carbon/19 — twenty-six rounds to
carbon/31's thirteen — 23 and 16, the last two on the engine's first case,
the Hebrew one intermittent to carbon/27, which it reaches in thirty-one
rounds of forty; `HEGEL_NO_KNOWN=1` switches the shapes off, and under it
every property passes and only the pins fail).
Five of them (the calendar travellers, boundaries, setters, creators and
wrappers) reach no recorded bug and pass; the three formatting and the
four calendar properties draw their shapes too. The thirty-one narrow
properties draw one bug's shape each, with random contents, and fail every
run; under `HEGEL_NO_KNOWN=1` they draw the region next to the shape and
pass. Thirty-one pins record the bugs in `bugs.toml` — wrong weekday names for
non-Monday week starts, whole-second differences, DST-blind day counts,
zone-dependent year and month differences, `time.Duration` overflow in the
clock travellers, local wall clocks labelled GMT/Z, `SetDefault` resetting
the week start, unreadable `unix` layouts, panics on the zero value and
outside the lunar table, unprotected format literals, output calls mutating
the receiver, and a set of calendar defects (lunar dates shifted by zone and
by the 2033 leap month, the Persian 2820-year cycle and epoch,
Julian-calendar reading before 1582, zone-blind Julian days, the
`NewJulian` digit heuristic, the Persian date of a day that begins with a
DST gap) plus a few naming slips — and fail while they
stand.

## Drawn shapes

The classifier names a case's bug from the model alone, before the library
is called: the first bug in id order whose switch alone moves the model
from the documented values, else the first whose switch the full set needs
(a year/month pair in two zones from the 29th needs both carbon/4 and
carbon/30 when the year does not change), else a hole — none over 3000
cases of any property, and on every shaped case the replica with every
switch on agrees with the library. Where shapes overlap the id order
decides: a pair with sub-second parts across a DST change is carbon/2, a
pair in two zones from the 29th is carbon/4. Three notes were corrected
while the shapes were drawn (each checked standalone): `Constellation()` of
November 22 says Scorpio, only `IsSagittarius` disagrees (carbon/5); the
`BetweenIncluded*` shortcut needs the receiver and the included bound both
zero, and runs after `start.Gt(end)` (carbon/28); and the zero `Carbon{}`
panics in nineteen methods (the boundaries, the setters, the `NoOverflow`
travellers, `IsLongYear`, `DaysInMonth`, `WeekOfMonth`), reports Sunday,
day-of-week 2 and an empty season, and is fine in the rest (carbon/11).
Two documented edges are modelled, not gated: a `Date`-layout wrapper of
0001-01-01 in a zone east of UTC marshals its wall-clock date, reads back
in the default zone as the zero instant and marshals `null` the second
time (`MarshalJSON` writes `null` for a zero value; `UnmarshalJSON` parses
in the default zone); and `TimestampNano` is checked within 1700–2200 only.
The formatting properties draw a locale (`en` seven times in ten, one of
the other thirty-three otherwise), a timezone argument for an output (none
seven in ten, a good zone two, a bad name one), the timestamp layouts and
letters one time in twenty, and format literals from a pool whose half
spells a Go layout token; their models follow the library under the
switches as replicas (`D` from the Sunday-first names indexed by the day of
the week counted from the week start; `l` the English name; a timestamp
layout an error from the parsers; `ParseByFormat` parsing with the layout
`format2layout` builds, literals copied; the marked outputs printing the
local wall clock and the Zulu layouts read in the given zone; the receiver
moved by the timezone argument) and the classifier names every shaped case
by sufficiency with the replica agreeing on all of them. Four more notes
were widened or corrected standalone: `ToRfc7231String` is wrong in UTC
too (prints `UTC`) while the GMT and Z outputs are right at a zero offset,
and the Zulu layouts have a parse face (`ParseByLayout` reads a Zulu text's
wall clock in the given zone) (carbon/8); `DiffInString` and
`DiffAbsInString` panic like `DiffForHumans` (carbon/12); a colliding
literal wins only after the fields (carbon/13). The Go `time` limits are
not gates and are drawn past: a two-digit year outside 1969–2068, a
non-alphabetic abbreviation under a `Z`/`T` letter, a sub-minute LMT offset
under any zone letter, and the outputs that are not default `Parse` layouts
are counted by name and their read-back not asked. Under
`HEGEL_NO_KNOWN=1` the shapes are generator shape: whole seconds,
one zone and one offset per pair, no overflowing amount, no bad string, no
zero time, no November 22, and the exact carbon/30 region filtered by the
classifier (one case in 270); `D` and `l` only escaped or under Monday and
`en`, no timestamp layout, literals from the harmless half of the pool, no
timezone argument, no marked output outside a zero offset.
The calendar properties draw the moment in all thirteen zones (the old
test converted in Shanghai and read back in UTC), the lunar one its years
from the table seven times in ten, a listed edge year two and a year
outside the table one, with a probe date for `NewLunar` that is impossible
half the time, the Persian one a day that begins with a DST gap three
times in a hundred, and a locale for the names of each calendar; their
models follow the library under the switches as replicas transcribed from
its code (the day count as elapsed time from the zone's 1900 midnight
truncated to the UTC hour; the Beijing-midnight instant read in the zone;
the year-only validation; the leap-7th labels of 2033; the truncating
cycle division; the historical day number before 1582-10-15; the digit
count of `NewJulian`; the wall clock read as UT; the unnumbered Adar; the
Farsi table; the local midnight built with `time.Date`), and the
classifier names every shaped case by sufficiency, the lower id first
where shapes overlap (a 2033 date is carbon/21 and an impossible probe
carbon/17 before the zone's carbon/15, which is dropped as one check of
the case; a pre-reform Persian date of years 1–473 is carbon/19 before
carbon/22; a Julian moment before 1886 is carbon/23 before 24 and 29).
Three more notes were corrected or widened standalone: the lunar day
flips not in "a day whose offset differs from 1900's" but when the UTC
hour boundary below the moment falls before the epoch's wall clock — the
first hour of every DST summer, Shanghai's own 1986–91 summer time, and
the first minutes of a fractional-offset zone (Kolkata 00:00–00:29), while
Shanghai's standard time never flips (carbon/20); the mislabelled 2033
months end on 2034-01-19, the 12th month being right (carbon/21); the sign
counts as a digit, so the zero time's MJD −678577 reads as a JD
(carbon/23). One bug was found by the replica's disagreement with the
library and recorded: `persian.FromStdTime` and `Persian.ToGregorian`
build the day's local midnight with `time.Date`, a day early where the
day begins with a DST gap (carbon/31). The lunar year range and the Hebrew
and Persian epochs are drawn past and counted by name; under
`HEGEL_NO_KNOWN=1` the lunar moments are in the table and east of
Beijing in the hours that do not flip, the Julian ones in UTC within the
five-digit MJD range, the Persian ones from 1583 on outside 1404 and gap
days, and the names are asked only where the tables agree.

## History

- 2026-09-20: base bumped e83625c5fe4a → 9c24fbd5e35d (2026-09-19, "perf(lunar): Derive the day tables once instead of recounting them per call (#357)"; v2.6.17+); 30 bug(s) still reproduce. 21 tests pass.
- 2026-10-10: rewrite, part 1 of three — the fourteen core properties on
  records drawn from package-level generators at the nominal rates, the
  `known` value with replicas of the library's rules, the classifier, nine
  shapes drawn and eleven narrow properties; part 2 — the three formatting
  and parsing properties on format and output records, five more shapes
  drawn and six narrow properties; part 3 — the four calendar properties
  on calendar records in every zone with the reference algorithms kept,
  the thirteen calendar shapes drawn and fourteen narrow properties, the
  older generators and the `Known` gates removed, and carbon/31 found by
  the Persian replica's one disagreement with the library.
