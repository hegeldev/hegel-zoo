# carbon — Hegel properties for `github.com/dromara/carbon/v2`

[dromara/carbon](https://github.com/dromara/carbon) is a Go date and time
library in the style of PHP's Carbon: a `Carbon` value wrapping `time.Time`
with a week start, a locale and a layout, creators (`CreateFromDate…`,
`CreateFromTimestamp…`, `Parse`, `ParseByLayout`, `ParseByFormat`),
travellers (`AddYears`, `AddMonthsNoOverflow`, `AddHours`, …), boundaries
(`StartOfWeek`, `EndOfQuarter`, …), differences (`DiffInMonths`,
`DiffForHumans`), comparisons, PHP-style `Format` letters, dozens of
`To…String` outputs, JSON wrapper types, and Hebrew, Julian, Chinese lunar
and Persian calendars. Pinned at `e83625c` (after v2.6.17, 2026-09-13).

## Build

The patch adds `go.mod` changes and five test files in `package
carbon_test`: `hegel_test.go` (plumbing, the `Known` gates and a per-gate
tally printed as `COUNTS`), `hegel_gen_test.go` (generators over thirteen
zones and years 1–9999, the models), `hegel_props_test.go` (seventeen
properties on the core type), `hegel_calendar_test.go` (four properties on
the calendars with reference algorithms) and `hegel_pins_test.go` (thirty
pins). No external tool is needed; the run takes well under a second at the
default case count, `HEGEL_TEST_CASES=3000` about four seconds.

## Oracles

- **`time.Time` itself** for everything a Carbon delegates: getters,
  `AddDate` for the calendar travellers, `time.Unix(sec+k, nsec)` for the
  clock travellers (so overflow of `time.Duration` is visible), `time.Date`
  for setters and boundaries, instants for comparisons, `Min`/`Max`/
  `Closest`/`Farthest`, and the Go layout twin of each PHP format for
  `Format`/`Layout`.
- **Bracketing** for the calendar differences: `DiffInYears(k)` must satisfy
  `s + k years ≤ e < s + (k+1) years`, and likewise for months.
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

| Test | Checks |
|---|---|
| `TestHegelGettersAgreeWithTime` | every getter (year … nanosecond, day of week/year, week of month/year, quarter, days in month, leap and long years, week names) against `time.Time` for a random week start |
| `TestHegelCalendarAdditionAgreesWithAddDate` | `Add/SubYears/Quarters/Months/Weeks/Days` and the `NoOverflow` variants against `AddDate` and a clamping model; receiver untouched |
| `TestHegelClockAdditionAgreesWithUnix` | `Add/SubHours … Nanoseconds` against `time.Unix` arithmetic |
| `TestHegelAddDurationAgreesWithParseDuration` | `AddDuration`/`SubDuration` against `time.ParseDuration`; bad strings give an error on the copy only |
| `TestHegelBoundariesAgreeWithModel` | `StartOf/EndOf` century … second against `time.Date` models for every week start |
| `TestHegelSettersAgreeWithDate` | `SetYear … SetNanosecond`, `SetDate`, `SetTime`, `SetDateTime`, `SetTimezone` against `time.Date` |
| `TestHegelDiffInYearsAndMonthsBracketTheEnd` | `DiffInYears`, `DiffInMonths` (and `Abs`) bracket the end for any pair |
| `TestHegelDiffInSmallUnitsAgreeWithElapsed` | `DiffInDays … DiffInSeconds` and `DiffInDuration` against elapsed time and calendar days |
| `TestHegelDiffStringsAgreeWithModel` | `DiffInString`, `DiffAbsInString`, `DiffForHumans` against a unit model |
| `TestHegelComparisonsAgreeWithInstants` | `Eq/Ne/Gt/Gte/Lt/Lte/Between*`, `IsSame*`, `Compare` against instants |
| `TestHegelExtremaAgreeWithInstants` | `Max`, `Min`, `Closest`, `Farthest` |
| `TestHegelFormatAgreesWithModel` | `Format` against the letter model and `Layout` against the Go twin, in every zone and week start |
| `TestHegelFormatParsesBack` | `ParseByFormat(Format(f), f)` and `ParseByLayout(Layout(l), l)` recover the instant to the format's precision |
| `TestHegelOutputStringsParseBack` | 45 `To…String` outputs match their documented layout and `Parse`/`ParseByLayout` read them back |
| `TestHegelSeasonAndConstellationAgreeWithTables` | `Season`, `Is<Season>`, `Constellation`, `Is<Sign>` against the tables |
| `TestHegelCreatorsAgreeWithTime` | `CreateFromDate/Time/DateTime/Timestamp*/StdTime`, `Parse` of RFC 3339 and the default layouts |
| `TestHegelWrapperTypesRoundTrip` | `DateTime`, `Date`, `Time…`, `Timestamp…` wrapper types through `encoding/json` and `database/sql` scanning |
| `TestHegelHebrewCalendarAgreesWithReingoldDershowitz` | `Hebrew()`/`CreateFromHebrew` and the `hebrew` package against the reference algorithm, both ways |
| `TestHegelPersianCalendarAgreesWithBirashk` | `Persian()`/`CreateFromPersian` against Birashk and the official Nowruz dates, both ways |
| `TestHegelJulianDayAgreesWithTheInstant` | `Julian().JD()/MJD()` and `CreateFromJulian` against `unix/86400 + 2440587.5` |
| `TestHegelLunarCalendarRoundTripsAndMatchesTheTables` | `Lunar()`/`CreateFromLunar` round trips, leap months and New Year dates against the HKO tables |

The general properties pass at 3000 cases. Thirty pins record the bugs in
`bugs.toml` — wrong weekday names for non-Monday week starts, whole-second
differences, DST-blind day counts, zone-dependent year and month
differences, `time.Duration` overflow in the clock travellers, local wall
clocks labelled GMT/Z, `SetDefault` resetting the week start, unreadable
`unix` layouts, panics on the zero value and outside the lunar table,
unprotected format literals, output calls mutating the receiver, and a set
of calendar defects (lunar dates shifted by zone and by the 2033 leap month,
the Persian 2820-year cycle and epoch, Julian-calendar reading before 1582,
zone-blind Julian days, the `NewJulian` digit heuristic) plus a few naming
slips — and fail while they stand.
- 2026-09-20: base bumped e83625c5fe4a → 9c24fbd5e35d (2026-09-19, "perf(lunar): Derive the day tables once instead of recounting them per call (#357)"; v2.6.17+); 30 bug(s) still reproduce. 21 tests pass.
