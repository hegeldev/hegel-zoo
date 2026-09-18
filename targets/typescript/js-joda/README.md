# typescript/js-joda — js-joda/js-joda, `packages/core` (against java.time itself)

js-joda is "an immutable date and time library for JavaScript", a port of ThreeTen-Backport,
the reference implementation of JSR-310 / `java.time` (3.2M weekly downloads; `@js-joda/core`
6.1.0). Its AGENTS.md says "the API closely mirrors `java.time` — method names and semantics
intentionally match Java's JSR-310 API", so the oracle is the JDK: `hegel/Oracle.java` answers
the same operation on the same ISO strings, and every property compares js-joda's result — or
the name of the exception it throws — with Java's (JDK 25). The patch pins 32 bugs.

## How it is built

`packages/core/src` is ES modules with extension-less imports, bundled upstream by rollup and
babel into an uncommitted `dist/`. The setup installs Hegel and esbuild under `.hegel/` and
`hegel/build.mjs` bundles `src/js-joda.js` into `.hegel/dist/js-joda.mjs`, which the tests
import. The Java side is one source file, `hegel/Oracle.java`, started once per test file with
the JDK's source launcher (`java hegel/Oracle.java`, JDK 11+; the GitHub runner image ships
JDKs, nothing is installed) by `hegel/oracle.mjs`, which speaks a tab-separated line protocol
over its stdin/stdout: `id op arg...` in, `id ok result` or `id err ExceptionName message` out.
Temporal values travel as the ISO `toString()` forms both libraries share, but the strings are
built by the harness from numbers by Java's rules, so a divergent `toString()` shows up as a
mismatch, not as a bad input.

## How it is tested

`hegel/hegel.test.mjs` runs under `node --test`; `hegel/hegel-zoo.mjs` is the zoo's shared
harness. `agree(label, thunk, op, ...args)` runs the js-joda expression and the oracle operation
and fails on any difference in value or exception class. Generators cover years over the whole
range with the extremes and 1900–2100 favoured, nanoseconds in the four printing shapes, offsets
down to seconds, amounts from small to ±2^53, every ChronoField and ChronoUnit, the IsoFields,
the thirteen TemporalAdjusters, Duration and Period texts by Java's grammar and their
mutations, pattern strings from the numeric pattern letters with Java's accepted (and some
refused) counts, literals, padding and optional sections, and mutations of formatted text.

| Property | What it checks |
|---|---|
| `TestHegelLocalDateConstructionAgreesWithJava` | `LocalDate.of/ofEpochDay/ofYearDay` validity and values, `toEpochDay`, `lengthOfMonth/Year`, `isLeapYear`, `dayOfWeek/Year`, `atStartOfDay`, `atTime` |
| `TestHegelLocalDateTemporalMethodsAgreeWithJava` | every supported field's value, `range`, `with(field, v)` in and out of range, `plus/minus(n, unit)`, `until`, `compareTo`, the `plusX/minusX/withX` methods, `until(date)` and `Period.between` |
| `TestHegelTemporalAdjustersAgreeWithJava` | the thirteen `TemporalAdjusters` on `LocalDate` and `LocalDateTime`, ordinals 0, negative and beyond 5 included |
| `TestHegelLocalTimeAgreesWithJava` | `LocalTime.of/ofSecondOfDay/ofNanoOfDay`, the generic temporal methods, `plusX/withX`, `truncatedTo`, `toSecondOfDay/toNanoOfDay`, `atOffset`; and that Java's `toString` follows the harness's rendering rule |
| `TestHegelLocalDateTimeAgreesWithJava` | the generic methods, `plusX/minusX`, `truncatedTo`, `toEpochSecond`, `toInstant`, `atOffset`, `LocalDateTime.ofEpochSecond` |
| `TestHegelInstantAgreesWithJava` | `Instant.ofEpochSecond` with any nanosecond adjustment, `ofEpochMilli`, the generic methods, `plusX/minusX`, `truncatedTo`, `toEpochMilli`, `atOffset`, and `toString` for years outside 0000–9999 |
| `TestHegelDurationAgreesWithJava` | `Duration.ofSeconds/of`, `parse` of well-formed text, `plus/minus`, `plus(n, unit)`, `multipliedBy` (factors up to 1e6), `negated/abs/compareTo`, the getters, `Duration.between`, and `plus/minus(duration)` on temporals |
| `TestHegelDurationParseAgreesWithJava` | `Duration.parse` on Java's grammar and mutations of it: junk, repeats, missing designators, case |
| `TestHegelPeriodParseAgreesWithJava` | `Period.parse` likewise |
| `TestHegelPeriodAgreesWithJava` | `Period.of/ofWeeks`, `plus/minus/multipliedBy/negated/normalized`, the getters, `plus/minus(period)` on dates |
| `TestHegelYearMonthMonthDayYearAgreeWithJava` | `YearMonth`, `MonthDay`, `Year`, `Month` and `DayOfWeek`: construction, the generic methods, `atDay/atEndOfMonth/isValidDay`, `atYear/isValidYear/withMonth`, `isLeap/atDay/atMonthDay/length`, `Month.length/firstDayOfYear/plus`, `DayOfWeek.plus` |
| `TestHegelZoneOffsetAgreesWithJava` | `ZoneOffset.of` over accepted and refused forms, `ofTotalSeconds`, `ofHoursMinutesSeconds`, `totalSeconds`, `getLong`, `compareTo` |
| `TestHegelOffsetDateTimeAgreesWithJava` | the generic methods, `withOffsetSameInstant/Local`, `toInstant`, `toEpochSecond`, `truncatedTo`, time-line comparison |
| `TestHegelOffsetTimeAgreesWithJava` | the generic methods, `withOffsetSameInstant/Local`, `truncatedTo` |
| `TestHegelPatternFormattingAgreesWithJava` | `DateTimeFormatter.ofPattern` acceptance, `format` of every kind, and that the text parses back the same way |
| `TestHegelPatternParsingAgreesWithJava` | parsing mutated text under SMART, STRICT and LENIENT |
| `TestHegelIsoFormattersAgreeWithJava` | the predefined ISO formatters: format, parse of the text and of a mutation, resolver styles |
| `TestHegelToStringParsesEverywhere` | every kind's default `parse` on its own `toString` and on mutations of it |
| `TestHegelIsoFieldsUnitsAgreeWithJava` | `plus/minus/until` in `QUARTER_YEARS` and `WEEK_BASED_YEARS` |
| `TestHegelIsoDateVariantsAgreeWithJava` | `ISO_ORDINAL_DATE`, `ISO_WEEK_DATE`, `BASIC_ISO_DATE` |
| `TestHegelOffsetDateTimeFieldsAgreeWithJava` | `OffsetDateTime`'s supported field set and `isSupported` |
| `TestHegelDurationScalingAgreesWithJava` | `multipliedBy`, `plus(n, unit)` and `Duration.of` with products past 2^53 nanoseconds |
| `TestHegelDurationDivisionAgreesWithJava` | `Duration.dividedBy` |
| `TestHegelDurationNegationAgreesWithJava` | `negated`, `abs` and `multipliedBy(-1)` of durations up to the safe-integer bounds |
| `TestHegelDurationToMillisAgreesWithJava` | `Duration.toMillis` on negative durations |
| `TestHegelInstantUntilSubSecondUnitsAgreesWithJava` | `Instant.until` in `MICROS`, `MILLIS`, `NANOS` |
| `TestHegelMinWidthPatternLettersAgreeWithJava` | patterns with `DD`, `nn..`, `NN..`, `AA..`, `F` and quoted literals with doubled quotes |
| `TestHegelUnsupportedUnitsThrowUnsupportedTemporalTypeException` | `truncatedTo` with a unit above days, `YearMonth.plus` of a period with days |

`TestHegelPin…` are plain tests, one per bug in `bugs.toml`, each asserting Java's answer
verbatim so they need no JVM. The ten properties from `TestHegelIsoFieldsUnitsAgreeWithJava`
on exist because a recorded bug is in their way: the general properties leave out the one
operation (quarter-year arithmetic, division, negation at the safe-integer bound, `toMillis`, sub-second `until`, the three ISO
date variants, the min-width letters, large truncation units, `OffsetDateTime`'s field set) and
these cover it; nothing models a bug.

## Bugs

See `bugs.toml`. Arithmetic: `plus(n, QUARTER_YEARS)` divides by 256 — the JDK 8 bug JDK-8033662
kept in the port — so 1000 quarters add 61 years (1, high); `Duration.dividedBy` truncates the
seconds and the nanoseconds separately, so 1.5 s / 3 is 0.499999999 s (8); `multipliedBy`
overflows on the nanosecond part when the result fits (9) and `negated` refuses -(2^53-1) seconds
because `MathUtil.safeMultiply` kept Java's `Long.MIN_VALUE * -1` check (33); `toMillis` floors negatives (10) and
`Instant.until` in `MICROS`/`MILLIS` floors (11) — both the JDK 8 algorithms later JDKs fixed;
`LocalTime.adjustInto` names an undefined constant and throws `NullPointerException` (12);
`Year.range(YEAR_OF_ERA)` ignores the era (15); `OffsetDateTime.until` has no fallback when the
end cannot be moved to this offset (16); `DayOfWeek.plus` is off by one at the edge of the safe
integers (31); a numeric string is concatenated by `plusDays` (32). Parsing texts:
`Duration.parse` and `Period.parse` are unanchored, so `PT1H1H` is `PT1H` and `P1D2Y` is `P1D`,
and `Period.parse` is case-sensitive (6, 7). The predefined formatters: `ISO_WEEK_DATE` is built
from the calendar year and the aligned week, so 2024-12-30 is `2024-W53-1` (2, high);
`ISO_ORDINAL_DATE` leaves the day of year unpadded (3); the three date-only variants lack the
optional offset (4) and `BASIC_ISO_DATE`'s year takes a sign and ten digits (5);
`ISO_ZONED_DATE_TIME` prints `[+02:00]` and `ISO_DATE_TIME` has no zone section (29); the offset
parser ignores `parseLenient`, so `2020-01-01T10:00:00+01` is rejected (21). Patterns and
resolution: `A`, `n`, `N` and `DD` are fixed-width (17); `F` maps to another field than the
JDK's (18); only the first `''` in a literal is unescaped (19); `xx`/`xxx`/`Z` swallow trailing
seconds (20); parsed time fields are neither cross-checked nor validated (22), a milli/nano
conflict is dropped (23), a quarter is not cross-checked (24); parsed `IsoFields` never resolve
to a date (25); `ReducedPrinterParser` drops its subsequent width (26); a fraction of a
one-based field does not round-trip (27); a fixed-width fraction is not adjacent-parsed (28);
the zone-id parser throws on an out-of-range offset (30). Contract: `OffsetDateTime.isSupported`
denies `INSTANT_SECONDS` and `OFFSET_SECONDS` (13); too-large units and unsupported fields throw
the base `DateTimeException` (14).

## Notes

- Accepted as the port's documented value model and counted, not reported (`accepted-*` in the
  collect statistics): years run over −999999..999999 where Java's run over ±999,999,999, so a
  Java result beyond that is a `DateTimeException` here (and a huge amount that Java rejects with
  `DateTimeException` may be an `ArithmeticException` here); numbers are JavaScript Numbers, so a
  Java `long` beyond 2^53 is an `ArithmeticException` here and a Java `int` overflow in `Period`
  is a plain number here (`P2147483648D` parses); `YearMonth.toString` writes the sign Java
  omits for years past 9999 (js-joda's form round-trips, Java's does not). Ranges bounded by
  those limits (`YEAR`, `YEAR_OF_ERA`, `PROLEPTIC_MONTH`, `WEEK_BASED_YEAR`, `EPOCH_DAY`,
  `INSTANT_SECONDS`) are not compared.
- Out of scope, as the package says: locale text (pattern letters `G`, `E`, `a`, `B`, `z`, `O`,
  `MMM` and up, `QQQ` and up, the localized week letters `w`, `W`, `Y`, `e`, `c`) needs
  `@js-joda/locale`; region zones need `@js-joda/timezone`. API absent from the port and not
  recorded as bugs: `ZoneOffset.isSupported/range`, `DateTimeFormatter.RFC_1123_DATE_TIME`,
  `withZone`, `parseBest`, `withResolverFields`, `appendZoneRegionId`, `appendOptional`, the
  pattern letter `g`, 13 of Java's 22 `appendOffset` patterns, `Duration.dividedBy(Duration)`.
- Message texts are not compared (js-joda's often name a derived field, e.g. `ofYearDay(2024, 0)`
  reports "Invalid value for MonthOfYear"); `Month.valueOf('FOO')` throws `DateTimeException`
  where Java throws `IllegalArgumentException`.
- The reading pass (two reviews of the sources against JDK 25 before the properties ran) named
  most of the formatter and resolution bugs; the properties found the quarter-year arithmetic,
  the week-date and ordinal-date formatters, the unanchored parsers, the `isSupported` gap and
  the exception classes on their own, and confirmed the rest through the dedicated properties.
