# joda-time

[Joda-Time](https://github.com/JodaOrg/joda-time) (`joda-time:joda-time` 2.14.3, pinned at the main commit of
2026-09-13, Apache-2.0): the pre-java.time date and time library — `DateTime`, `LocalDate`/`LocalDateTime`/`LocalTime`,
`Instant`, `Duration`, `Period`, `Interval`, the single-field periods, `DateTimeZone` with its own compiled tz tables
(2026d), the ISO, Gregorian, Julian, GJ (cutover), Buddhist, Coptic, Ethiopic and tabular Islamic chronologies, and
the pattern, ISO and period formatters.

The tests are a Maven module `hegel/` added by the patch; `[run] setup` installs the library from the pinned tree
(the pom targets Java 1.5, so the compiler source/target are overridden to 8 and javadoc/sources skipped; the tz
tables are compiled by the build; about a minute). Upstream's own suite is JUnit 3/4 example tests (no property tests).

## The oracles

- **java.time** (`IsoTest`, `FormatTest`): the ISO chronology field by field over epoch days from ±150 000 to ±10⁸
  (fields, week-based year, era, leap flags, month/year lengths, arithmetic, differences, `Period` between dates,
  `toString`/`parse`), local times and date-times, and `DateTime` in 58 region zones whose Joda 2026d tables agree
  with the JDK's 2026b ones over 1900–2037 (checked once for every id both know: 263 agree, the rest differ by a
  transition or by data). Offsets, local fields, `toString`, standard offsets, transitions, gaps (`IllegalInstantException`
  vs no valid offsets), overlaps (`withEarlierOffsetAtOverlap`, `adjustOffset`), start of day, day intervals and
  `plusDays/Months/Years/Hours` are compared with `ZonedDateTime`. The ISO formatters are compared text for text
  and both libraries parse each other's output.
- **DateTimeZone laws** without an oracle (`ZoneTest`, all 590 zone ids): the offset, standard offset and name key are
  constant between `nextTransition`/`previousTransition`, something changes at each transition, local ↔ UTC
  conversions round trip, gaps are reported and resolved as the Javadoc describes, fixed-offset ids round trip
  through `forID`/`forOffsetHoursMinutes`/`forTimeZone`.
- **Independent day-count models** (`Cal`, `ChronoTest`): Julian and Gregorian via Julian Day Numbers, the GJ cutover
  at 1582-10-15, Buddhist = GJ + 543, Coptic/Ethiopic as 12×30 + 5/6 days with the year ≡ 3 (mod 4) leap rule, and the
  tabular Islamic calendar with the four 30-year leap patterns; fields, leap flags, month and year lengths, era and
  year of era, constructor acceptance of random y/m/d, `getDateTimeMillis`, `plusDays`, `daysBetween`, `plusYears`
  with day clamping.
- **Exact arithmetic** (`PeriodTest`): `BigInteger` totals for `toStandardDuration/Weeks/Days/...` and
  `normalizedStandard` over six `PeriodType`s (months into years, the day-and-below total redistributed greedily,
  `UnsupportedOperationException` vs `ArithmeticException` as documented), `Duration` plus/minus/multipliedBy/dividedBy
  with every `RoundingMode` against `BigDecimal`, the single-field periods, and `Interval` against the [start, end)
  model (contains, overlaps, abuts, overlap, gap, isBefore/isAfter with the documented zero-duration rules).
- **Print/parse round trips** (`FormatTest`): random patterns from ten date and ten time forms with `Z`/`ZZ`/`ZZZ`,
  the ISO basic/week/ordinal formatters, `ISOPeriodFormat`, `PeriodFormat.getDefault()`, `Period`/`Duration`/
  `YearMonth`/`MonthDay` text.
- Two read-only surveys of the source (formatting; chronologies, fields, zones and value classes), each verifying
  its suspicions in jshell, contributed the extreme-value and formatter defects; the jshell sweeps over every zone
  measured how widespread the overlap and transition findings are.

## What the properties found

The 18 recorded bugs (`bugs.toml`, pinned in `JodaTimePinsTest`) fall into four groups: **overlap and transition
handling** — `convertLocalToUTC(local, strict)` resolves an overlap to the later instant east of Greenwich and the
earlier west of it while `getOffsetFromLocal` always picks the earlier (273 of 486 zones with overlaps disagree),
`nextTransition`/`previousTransition` misbehave at `Long.MAX_VALUE`; **calendar bookkeeping** —
`IslamicChronology.withUTC()/withZone()` drop the leap-year pattern so every `LocalDate` in the Indian, 15-based or
Habash al-Hasib calendar is computed with the 16-based one, `getMaximumValue(ReadablePartial)` uses the era year
(Buddhist years, BC Julian/GJ years) or ignores the partial (`LimitChronology`: Islamic, Coptic, Ethiopic), October
1582 has "4" days in the GJ chronology, `plusMonths` past the maximum year is unchecked, rounding overflows at the
`long` extremes; **period arithmetic** — `toStandardWeeks/Days/...` are off by one for mixed-sign periods,
`dividedBy(-1)` of `MIN_VALUE` and `minus(MIN_VALUE)`, the ISO period printer folding seconds and millis into an
`int`; **formatter contracts** — `parseLocalDateTime` throwing for a zone id in a DST gap, `ZZZ` printing fixed-offset
ids it cannot parse, the lenient two-digit year accepting `-#`, an off-by-one failure position, and the basic ISO
formatters printing five-digit years they refuse to parse.

Design choices the tests respect rather than record: `previousTransition` returns the millisecond before the
transition and both transition methods fire on name-key changes without an offset change; `getOffsetFromLocal`'s
documented gap rule (the offset before the gap, so the result lands after it) and `LocalDateTime.toDateTime` throwing
in a gap while `toDateTimeAtStartOfDay`/`toInterval` skip a midnight gap; the ISO chronology's `centuryOfEra`/
`yearOfCentury` drop the sign of the year (`ISOYearOfEraDateTimeField`) while `yearOfEra` is `1 - year` for BC; the
Gregorian chronology has a year 0 and the Julian, GJ, Coptic and Ethiopic ones skip it; `Months.monthsBetween` counts
a month from Jan 31 to Feb 29 (clamped `plusMonths`), unlike java.time; the Islamic minimum year is 1; `Z`/`ZZ` print
whole minutes and a zone id does not disambiguate an overlapping local time; a date-only text with a zone id denotes
a midnight that may not exist; `Duration.parse` reads the `PTn.nS` form only; `Period.toString` merges seconds and
millis (compare `seconds*1000 + millis`); `forOffsetHoursMinutes(-1, 30)` and `(-1, -30)` both mean −01:30;
`adjustOffset` is documented as best-effort ("non-pathological cases") — it fails inside a few long or adjacent
historical overlaps, not recorded; the conversions overflow with `ArithmeticException` at the `long` extremes.
- 2026-09-20: base bumped b80254120c5b → 13691681d373 (2026-09-19, "Release v2.14.4"; 2.14.4); 18 bug(s) still reproduce. 14 tests pass.
