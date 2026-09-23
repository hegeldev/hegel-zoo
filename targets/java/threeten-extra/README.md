# threeten-extra

[ThreeTen-Extra](https://github.com/ThreeTen/threeten-extra) (`org.threeten:threeten-extra`; the pom carries
1.10.1-SNAPSHOT, the last release being v1.10.0 of 2026-06-16; pinned at the main commit of 2026-09-15) is Stephen
Colebourne's companion to `java.time`: extra calendars (Julian, Coptic, Ethiopic, British cutover, Discordian,
International Fixed, Pax, Symmetry454, Symmetry010, Accounting), `Interval` and `LocalDateRange`, the year-parts
`YearWeek`/`YearQuarter`/`YearHalf`, `DayOfMonth`/`DayOfYear`/`Quarter`/`Half`, `HourMinute`, `OffsetDate`, the
single-unit amounts `Days`…`Seconds`, `PeriodDuration`, `AmountFormats`, `PackedFields`, `Temporals` utilities and
the `UtcInstant`/`TaiInstant` time scales with a leap-second table. About 32 000 lines of source.

The tests are a Maven module `hegel/` added by the patch; `[run] setup` installs the library from the pinned tree
into the local Maven repository (Javadoc, sources, checkstyle, PMD, the enforcer and signing skipped).

## The oracles

- **`java.time` itself**: the ISO calendar for epoch days, `IsoFields` for week-based years and quarters,
  `LocalDate`/`LocalDateTime`/`OffsetDateTime` arithmetic and `until`, `Period`/`Duration` arithmetic and text.
- **Independent day counts** for the Julian calendar (the classic JDN formula), the Coptic and Ethiopic calendars
  (thirteen months, leap when the year is 3 mod 4, epochs at JDN 1825030 and 1724221) and the British cutover
  (Julian before 1752-09-14, ISO after).
- **Set models** for `Interval` and `LocalDateRange`: the relations (`encloses`, `abuts`, `overlaps`,
  `isConnected`, `isBefore`/`isAfter`, `contains`) as the documented comparisons of the bounds, and
  `intersection`/`union`/`span` as the bound minima and maxima; the documented equivalences (`isConnected` =
  `overlaps || abuts`) and symmetries.
- **Exact arithmetic** with `Math.*Exact`, `BigInteger` and `BigDecimal` for the amount classes, unit conversion,
  `durationFrom/ToBigDecimalSeconds`, `multiply`, and the word-based and unit-based text formats (the English
  resource bundle re-implemented).
- **The TAI definition**: TAI seconds count from 1958-01-01, `TAI = UTC + offset(day)`, the offset growing by one
  the day after each entry of `UtcRules.getLeapSecondDates()`.

`Gen` draws dates near the present, anywhere in years 1..9999, in the cutover decades, over the full `LocalDate`
range and at its ends; instants, offsets, durations and periods of mixed sizes and signs including the extremes.

## Properties (`ThreetenExtraTest`, 4; `ThreetenExtraAmountsTest`, 5)

- `calendarsRoundTripThroughEpochDays`: for every chronology, `dateEpochDay` ↔ `toEpochDay`/`LocalDate.from`/
  `date(LocalDate)`, the fields rebuild the date through `date(y, m, d)`, `date(era, yoe, m, d)` and
  `dateYearDay`, `lengthOfMonth`/`lengthOfYear` agree with the ranges and years are contiguous, `plus`/`minus` of
  days and weeks move the epoch day, `until` in days/weeks/months/years and the `ChronoPeriod` round trip,
  comparisons, `with` of the fields, month and year arithmetic clamps the day, `atTime` and `zonedDateTime`; Julian,
  Coptic, Ethiopic and the British cutover against the day-count models, including which `date(y, m, d)` are valid.
- `intervalsMatchTheSetModel`: the relations, `intersection`/`union`/`span`, the instant queries
  (`contains`, `starts*`, `ends*`, `isBefore`/`isAfter`), `withStart`/`withEnd`, `startingAt`/`endingAt`,
  `toDuration`, and `parse` of `toString`, of `start/duration`, `duration/end`, and of offset date-times with the
  end offset implied or different.
- `dateRangesMatchTheSetModel`: the same for `LocalDateRange` plus the documented refusals near `LocalDate.MIN`/
  `MAX`, `ofClosed`/`ofEmpty`/`ofUnbounded*`/`of(start, Period)`, `from(Temporal)` for dates, date-times,
  `YearMonth`, `Year`, `YearQuarter`, `YearWeek`, `stream`, `lengthInDays`, `toPeriod`, `withEndInclusive`, text.
- `yearPartsMatchJavaTime`: `YearWeek` against `WEEK_BASED_YEAR`/`WEEK_OF_WEEK_BASED_YEAR` (`atDay`, `is53WeekYear`,
  `plusWeeks`/`plusYears`, `until`, `of(y, 53)` rolling over, adjusting a date), `YearQuarter` and `YearHalf`
  against the month arithmetic (`atDay`, `atEndOf*`, `lengthOf*`, `isValidDay`, `plus*`, `until`,
  `quartersUntil`), `toString`/`parse` including the sign and `+` rules.
- `amountsMatchIntArithmetic`: `Days`, `Weeks`, `Months`, `Years`, `Hours`, `Minutes`, `Seconds` (reflectively):
  `plus`/`minus`/`multipliedBy`/`dividedBy`/`negated`/`abs` as exact int arithmetic, comparisons,
  `toString`/`parse` (simple and composite text, lower case, signs, junk), `from(TemporalAmount)` against the unit
  conversion model, `between`, `addTo`/`subtractFrom`, `toPeriod`/`toDuration`.
- `periodDurationsMatchPeriodAndDuration`: components, `toString` = `AmountFormats.iso8601`, `parse` of the text
  (lower case, negated), `plus`/`minus`/`multipliedBy`/`negated`, `normalizedYears`, `normalizedStandardDays`
  preserving the total, `truncatedTo`, adding to a `LocalDateTime` = period then duration, `between` round trip,
  the English word-based formats of periods, durations and both, and `parseUnitBasedDuration` against a
  `BigInteger` sum of the parts.
- `temporalsMatchTheModel`: `convertAmount` over all units against the documented conversion and its inverse,
  `chronoUnit`/`timeUnit`, the four working-day adjusters, `durationTo/FromBigDecimalSeconds`,
  `durationFrom/ToDoubleSeconds`, `multiply`, `parseFirstMatching`, `unitComparator`/`fieldComparator`.
- `smallTemporalsMatchJavaTime`: `HourMinute` against `LocalTime`, `OffsetDate` against `OffsetDateTime` (order,
  `until` with differing offsets, `toEpochSecond`, text), `PackedFields` (values, `with`, strict/lenient parsing,
  invalid packed values), `DayOfMonth`, `DayOfYear`, `Quarter`, `Half`.
- `utcAndTaiInstantsRoundTrip`: the leap-second table, `getTaiOffset`, `ofModifiedJulianDay` validation including
  leap seconds, UTC ↔ TAI ↔ `Instant` round trips (the UTC-SLS smear allowed only in the last 1000 s of a leap day),
  `plus`/`minus`/`durationUntil`, comparisons, `toString`/`parse` of both scales.

Known-bug shapes are skipped, never worked around: the Symmetry calendars are not exercised before year 0 (1) and
their era-based constructors not for BCE years (2); `durationToDoubleSeconds` is not asked about durations below
-9,223,372,036 s (3); word-based text is not checked for hour or day counts beyond an int (4) or for negative months
without years (5); amount text whose components overflow, and `-P-2147483648D`, is not parsed (6).

## Not tested

`AccountingChronology` (built per configuration); `MutableClock`; `AmPm`; the `resolveDate` of the chronologies
through `DateTimeFormatter`; word-based formats in other locales; `UtcRules.registerLeapSecond`; serialization.

## Bugs found

| id | severity | summary |
|---|---|---|
| threeten-extra/1 | medium | Symmetry454/010: `isLeapYear` wrong from year -3 back (negative remainder); `dateEpochDay` returns dates a week off or throws before year 0 |
| threeten-extra/2 | medium | Symmetry454/010: `prolepticYear(BCE, n)` = n; `date(BCE, 5, 1, 1)` is CE 5 |
| threeten-extra/3 | low | `Temporals.durationToDoubleSeconds` throws `ArithmeticException` below about -292 years |
| threeten-extra/4 | low | `AmountFormats.wordBased` casts hours and days to int (`PT2147483648H` → "-2147483648 hours") |
| threeten-extra/5 | low | `wordBased(P-13M)` is "-1 year and -1 month" while `P13M` is "13 months" |
| threeten-extra/6 | low | `Days…Seconds.parse` throw `ArithmeticException` instead of `DateTimeParseException` on overflowing text |
| threeten-extra/7 | medium | `InternationalFixedDate.plusWeeks` lands 28 days early when the target is the first week of a month (`1969/13/28 + 1 week` = 1969/13/07) |
| threeten-extra/8 | medium | `Symmetry454Date.until(WEEKS)` loses a week per five-week month spanned (63 days = 8 weeks) |
| threeten-extra/9 | medium | `Symmetry010Date.until(WEEKS)` mixes year-aligned weeks with month-aligned days of week (31 days = 3 weeks, 26 days = 4) |
| threeten-extra/10 | medium | Symmetry454/010 `with(field, 0)` returns the date unchanged (`EPOCH_DAY`, `YEAR`, `ERA`, `PROLEPTIC_MONTH`) |
| threeten-extra/11 | medium | `PaxDate.plusMonths` computes month 0 for a leap-year month 14 target, so `plus(1, MONTHS)` from 1860-13-01 and `until()` throw |
| threeten-extra/12 | low | Symmetry454/010: `plus(until(end))` misses `end` by days from a leap-week start (2004/12/37 -> P1Y2M2D -> 2006/03/02) |

Observed, not recorded: `until()` between calendar dates is not invertible for negative periods when the end day is
clamped (Coptic `2060-05-25 → 2057-13-02` gives `P-2Y-5M-23D`, adding it lands on `2057-12-12`) — the same
algorithm and documented behaviour as `java.time.LocalDate.until`, and `PeriodDuration.between` inherits it; the
British cutover month of September 1752 has `lengthOfMonth()` 19 but `range(DAY_OF_MONTH)` 1–30, and month
arithmetic into it keeps day 23 (the days exist), all consistent with the gap; `Discordian` and `InternationalFixed` count weeks by their calendar weeks (skipping St. Tib's Day and Year Day) in both `until(WEEKS)` and `plus(n, WEEKS)`, keeping the day of the week - the test's week model follows suit (this note used to claim `plus` adds plain days; it does not, and where it goes wrong is threeten-extra/7); a week step from a weekless day itself has no defined answer and is not judged; `UtcInstant` `23:59:60.999999999`
converts to the next day's `00:00:00Z` (the UTC-SLS smear). `getLeapSecondDates()` begins with 41317 (1972-01-01),
the start of the 10 s offset, not a leap second.

## History

- 2026-09-16: created (turn 180) at 7779aa9a7215 (1.10.1-SNAPSHOT of 2026-09-15, after v1.10.0); 6 bugs.
- 2026-09-23: generators rewritten in combinator style (turn 422); the week oracle became a calendar-week model,
  per-chronology year bounds replaced a gate that had skipped every IFC, Discordian and Symmetry case in realistic
  years, and the first runs of the rewritten properties found bugs 7-12.
