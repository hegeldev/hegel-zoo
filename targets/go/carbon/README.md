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

The patch adds `go.mod` changes and nine test files in `package
carbon_test`: `hegel_test.go` (plumbing, the collector, the `known` value
of thirty switches — one per recorded bug, all off by default — and the
case judge), `hegel_idioms_test.go` (the harness idioms shared with the
excelize, graphql-go, cobra and cascadia targets), `hegel_moments_test.go`
(the records the core properties draw — a moment in one of thirteen zones,
pairs and triples of moments, week settings, amounts, duration strings —
and their package-level generators, every weight tuned until its realised
rate is the nominal one, the measured figure beside it),
`hegel_core_test.go` (the fourteen core properties: a case record per
family, a model `expected(c, k)` of every checked value that follows the
recorded bugs in `k` as replicas of the library's code, the classifier that
names a case's shape from the model alone, the judge), `hegel_core_shapes_test.go`
(eleven narrow properties, one per bug the core properties can reach),
`hegel_gen_test.go` (the older generators and the models the formatting and
calendar properties still use), `hegel_props_test.go` (the three formatting
and parsing properties on the older generators), `hegel_calendar_test.go`
(four properties on the calendars with reference algorithms) and
`hegel_pins_test.go` (thirty pins). No external tool is needed; the run
takes about ten seconds at the default case count (the shrinking of the
properties that reach a bug) and four under `HEGEL_NO_KNOWN=1`.

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
  calendar (calibrated on published Tishri dates), the 33-year Birashk
  cycle for the Persian calendar checked against the published Nowruz dates
  1398–1408, `JD = unix/86400 + 2440587.5` for Julian days, and the Hong
  Kong Observatory leap-month and New Year tables 1900–2100 for the Chinese
  lunar calendar, with round trips through each calendar's `ToGregorian`.
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
| `TestHegelFormatAgreesWithModel` | `Format` against the letter model and `Layout` against the Go twin, in every zone and week start | (part 2) |
| `TestHegelFormatParsesBack` | `ParseByFormat(Format(f), f)` and `ParseByLayout(Layout(l), l)` recover the instant to the format's precision | (part 2) |
| `TestHegelOutputStringsParseBack` | 45 `To…String` outputs match their documented layout and `Parse`/`ParseByLayout` read them back | (part 2) |
| `TestHegelHebrewCalendarAgreesWithReingoldDershowitz` | `Hebrew()`/`CreateFromHebrew` and the `hebrew` package against the reference algorithm, both ways | (part 3) |
| `TestHegelPersianCalendarAgreesWithBirashk` | `Persian()`/`CreateFromPersian` against Birashk and the official Nowruz dates, both ways | (part 3) |
| `TestHegelJulianDayAgreesWithTheInstant` | `Julian().JD()/MJD()` and `CreateFromJulian` against `unix/86400 + 2440587.5` | (part 3) |
| `TestHegelLunarCalendarRoundTripsAndMatchesTheTables` | `Lunar()`/`CreateFromLunar` round trips, leap months and New Year dates against the HKO tables | (part 3) |
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

The fourteen core properties draw the shapes of the recorded bugs at their
natural rates — a sub-second part in two moments of three, a bad duration
string one in ten, an overflowing clock amount one in twenty, two zones in a
quarter of the year/month pairs, November 22 one day in 365, the zero time
as the engine's first case — and are the expected failures mapped to the
bug they shrink to most often over forty rounds (`target.toml`: the
getters, duration, small-unit, string, extrema and comparison properties
plain, the clock addition, year/month and season ones intermittent; `HEGEL_NO_KNOWN=1` switches
the shapes off, and under it every property passes and only the pins fail).
Five of them (the calendar travellers, boundaries, setters, creators and
wrappers) reach no recorded bug and pass. The eleven narrow
properties draw one bug's shape each, with random contents, and fail every
run; under `HEGEL_NO_KNOWN=1` they draw the region next to the shape and
pass. Thirty pins record the bugs in `bugs.toml` — wrong weekday names for
non-Monday week starts, whole-second differences, DST-blind day counts,
zone-dependent year and month differences, `time.Duration` overflow in the
clock travellers, local wall clocks labelled GMT/Z, `SetDefault` resetting
the week start, unreadable `unix` layouts, panics on the zero value and
outside the lunar table, unprotected format literals, output calls mutating
the receiver, and a set of calendar defects (lunar dates shifted by zone and
by the 2033 leap month, the Persian 2820-year cycle and epoch,
Julian-calendar reading before 1582, zone-blind Julian days, the
`NewJulian` digit heuristic) plus a few naming slips — and fail while they
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
Under `HEGEL_NO_KNOWN=1` the shapes are generator shape: whole seconds,
one zone and one offset per pair, no overflowing amount, no bad string, no
zero time, no November 22, and the exact carbon/30 region filtered by the
classifier (one case in 270).

## History

- 2026-09-20: base bumped e83625c5fe4a → 9c24fbd5e35d (2026-09-19, "perf(lunar): Derive the day tables once instead of recounting them per call (#357)"; v2.6.17+); 30 bug(s) still reproduce. 21 tests pass.
- 2026-10-10: rewrite, part 1 of three — the fourteen core properties on
  records drawn from package-level generators at the nominal rates, the
  `known` value with replicas of the library's rules, the classifier, nine
  shapes drawn and eleven narrow properties; the formatting (part 2) and
  calendar (part 3) properties still on the older generators with their
  `Known` gates.
