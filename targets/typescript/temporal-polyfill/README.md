# typescript/temporal-polyfill — fullcalendar/temporal-polyfill (`polyfill/`)

Hegel property tests for [`temporal-polyfill`](https://github.com/fullcalendar/temporal-polyfill)
1.0.5, pinned at `b28e5a85` (main, 2026-09-11): FullCalendar's lightweight polyfill of the TC39
Temporal proposal (Instant, ZonedDateTime, the Plain* types, Duration, Now, calendars and the Intl
integration), the one most bundlers pick for its size. TypeScript, MIT, a pnpm workspace whose
`polyfill/` package depends on the workspace's `temporal-utils` and `temporal-spec` (types). The
repository's `AGENTS.md`/`CLAUDE.md` instruct coding agents (scope work in `polyfill/`, run
test262) and set no contribution restriction (checked 2026-09-17); the zoo only records bugs.

Tests are `polyfill/test/hegel.test.mjs` (ESM, run by `node --test`) with the zoo's harness
`polyfill/test/hegel-zoo.mjs`. Hegel is `@hegeldev/hegel` 0.4.5.

## How it is built

`dist/` is not committed and `pnpm` is the package manager, so the setup installs Hegel,
TypeScript 5.9.3 and the reference implementation under `polyfill/.hegel/` and compiles
`polyfill/src` together with `utils/src` to CommonJS into `.hegel/dist` with the zoo's
`test/tsconfig.hegel.json` (path mappings for `temporal-spec`/`temporal-utils`, `--noCheck`, the
polyfill's own tests and type overrides excluded). Two small package.json files committed under
`test/` mark the output CommonJS and make the compiled utils a package, and a symlink
`.hegel/dist/node_modules/temporal-utils` lets the compiled polyfill resolve its workspace
dependency. The tests `require()` `classApi/full/index.js` (the build with every calendar).

## How it is tested

The oracle is `@js-temporal/polyfill` 0.5.1, the champions' reference polyfill of the same
specification. Every case builds the same value from plain data (ISO strings, property bags, epoch
nanoseconds, option bags) in both implementations and compares the results — the canonical
`toString()`, the fields, or the class of the error thrown. The specification's own laws are
checked on the polyfill alone. The reference is six months behind the specification in places
and leans on this Node's ICU, so every divergence was adjudicated against the specification's
grammar and algorithms and the relevant test262 files before being recorded; the divergences that
are the reference's are listed below as *oracle limits* and skipped.

- **Parsing** (`TestHegelParsesLikeTheReference`): a generated RFC 9557 string (all year forms,
  basic and extended format, month-day and year-month forms, `T`/`t`/space, `24:00`, fractions
  with `.` or `,`, offsets with and without colons and seconds, `Z`/`z`, `[tz]`/`[!tz]` including
  unknown zones and bracketed offsets, `[u-ca=…]` with duplicates and unknown calendars, unknown
  annotations, and truncations, appendices and case changes) or a Duration string is parsed by
  all eight `from` methods, with `overflow`, `disambiguation` and `offset` options. Found bugs 2,
  3, 5, 6 and 8.
- **Date arithmetic** (`TestHegelPlainDateTimeArithmeticLikeTheReference`): PlainDate and
  PlainDateTime `add`/`subtract` with `overflow`, `until`/`since` with every `largestUnit`,
  `smallestUnit`, increment and rounding mode, `round`, `with`, `toString` with `calendarName`;
  laws `a.add(a.until(b)) = b`, `a.subtract(a.since(b)) = b`, antisymmetric `compare`.
- **Durations** (`TestHegelDurationLikeTheReference`): `round` with and without `relativeTo`
  (dates and zoned date-times), `total`, `compare`, `toString`/`toJSON` with `smallestUnit`,
  `fractionalSecondDigits` and rounding modes, `negated`/`abs`/`sign`/`blank`/`with`, time-only
  `add`/`subtract`; laws on negation, `abs` and `blank`. Found bug 7.
- **Instants** (`TestHegelInstantLikeTheReference`): epoch nanoseconds across the whole range and
  just outside it; `add`/`subtract`, `until`/`since`, `round`, `toString` with time zones and
  rounding, `fromEpoch*`, `compare`, `toZonedDateTimeISO`. Found bug 1.
- **Times and month types** (`TestHegelPlainTimeAndMonthTypesLikeTheReference`): PlainTime
  `add`/`until`/`toString`/`with`/`compare`; PlainYearMonth `add`/`subtract`/`until` and its fields;
  `toPlainDate`, PlainMonthDay `from`/`with`/`toPlainDate`, conversions from PlainDate. Found bug 4.
- **Calendars** (`TestHegelCalendarFieldsLikeTheReference`): for iso8601, gregory, hebrew,
  islamic-umalqura, japanese, persian, buddhist, indian, coptic, ethiopic and roc, the date
  fields of `withCalendar`, the round trip through `{year, month, day}`, `monthCode` and era
  bags, `toPlainYearMonth`/`toPlainMonthDay`, `add` with every date unit and `overflow`, `until`
  and `with` (including out-of-range days, months and leap month codes). Found bug 9 (at 3000
  cases: the shape is about one case in eight thousand, so the property is intermittent).

The generators draw the shapes of the recorded bugs by default (`gen.mjs` builds every case as a
record from `@hegeldev/hegel`'s combinators and renders it with pure functions), so the wide
properties fail on them and are listed in `target.toml` mapped to the bug they shrink to; the
parsing property reaches five of the nine and is mapped to the one it shrinks to, and a wide
property whose shape is under two percent of its cases (`Instant`, `Duration`, `Calendars`) is
marked intermittent. Beside them, one narrow property per bug (`TestHegelPreEpochInstantsRoundTowardThePast`,
`TestHegelPlainTimeRejectsInvalidDateParts`, `TestHegelPlainTimeIgnoresCalendarAnnotations`,
`TestHegelYearMonthArithmeticRejectsUnitsBelowMonths`, `TestHegelBracketedOffsetsWithSecondsAreRejected`,
`TestHegelOffsetsBeyondTheGrammarAreRejected`, `TestHegelDurationsThatRoundToZeroPrintWithoutASign`,
`TestHegelTimeZoneAnnotationsComeBeforeOtherAnnotations`, `TestHegelYearsUntilAnEarlierShevatFromAdarIAreWhole`)
draws random contents over the bug's
shape region and is the deterministic expected failure; where the reference is wrong too (bug 4's
sub-month units, mixed-separator offsets) the polyfill is judged by the specification, as the pins
are. `HEGEL_NO_KNOWN=1` (read once) swaps each known shape for its neighbouring region, and every
property must then pass; the recorded shapes and the oracle limits met in a run are counted
(`ZOO_COLLECT`). The pins beside the narrow properties are the regression examples and assert the
specification's behaviour until the bug is fixed.

## Bugs

| id | title | kind | severity |
|---|---|---|---|
| temporal-polyfill/1 | Directional rounding of a pre-1970 Instant rounds toward 1970 instead of toward the past | wrong-result | medium |
| temporal-polyfill/2 | PlainTime.from accepts a string whose date part is not a valid date | contract | low |
| temporal-polyfill/3 | PlainTime.from rejects a time string carrying a non-ISO calendar annotation | contract | low |
| temporal-polyfill/4 | PlainYearMonth.add/subtract accept units below months next to a year or month part, and a negative mixed duration lands a month early | wrong-result | medium |
| temporal-polyfill/5 | A bracketed UTC offset with seconds ([+05:30:15]) is accepted as a time zone by the Plain types | contract | low |
| temporal-polyfill/6 | A UTC offset with an hour of 24 or more, or a minute of 60, is accepted by the Plain types | contract | low |
| temporal-polyfill/7 | A negative duration that rounds to zero in toString keeps its minus sign: -PT0.000S | wrong-result | low |
| temporal-polyfill/8 | A time zone annotation placed after another annotation ([u-ca=iso8601][UTC]) is accepted by every parser | contract | low |
| temporal-polyfill/9 | PlainDate.until/since with largestUnit year from Adar I of a Hebrew leap year to a later day of Shevat of an earlier common year counts one year fewer and twelve months | wrong-result | low |

## Oracle limits (the reference's divergences, skipped and not counted)

`@js-temporal/polyfill` 0.5.1 (March 2025) on Node 22's ICU:

- returns `undefined` or ICU's names for `era`/`eraYear` where the specification's 2024 era codes
  (`ce`, `be`, `am`, `ap`, `ah`, `shaka`, …) apply; eras are compared for iso8601 only;
- computes `weekOfYear`/`yearOfWeek` for every calendar (the specification defines them for
  iso8601 only);
- throws "Era am … was not matched" for coptic and ethiopic dates (and for `PlainYearMonth`/
  `PlainMonthDay` strings with those annotations); such cases are skipped;
- accepts `PlainTime.from("11-17")` and other strings ambiguous with a month-day or year-month;
- lets `offset: "ignore"` override a `Z` designator;
- accepts `PlainYearMonth.add({ months: 1, days: 1 })` (the specification throws; bug 4 is the
  polyfill's side of the same shape) and applies `overflow: "reject"` to the end-of-month
  intermediate date of a subtraction (test262 `subtract/overflow`: no effect in ISO 8601);
- still accepts the `islamic` and `islamic-rgsa` calendar ids the specification dropped in 2025;
- rejects `[u-ca=ISO8601]` in upper case on year-month and month-day strings (ids are
  case-insensitive, test262 `argument-string-calendar-case-insensitive`);
- accepts a UTC offset with mixed separators (`-0145:32`);
- mis-parses ICU's Chinese/Dangi leap month codes, so `chinese` and `dangi` are not exercised;
- follows ICU into the Julian calendar before 1582 and its Umm al-Qura table ends in 2077, so
  the non-ISO calendar field comparisons stay within 1650–2047 (their arithmetic moves up to
  30 years) and year-month/month-day strings with a non-ISO calendar are parsed only for
  1600–2077.

## Not tested

`Temporal.Now`, `Intl.DateTimeFormat` integration and `toLocaleString`, the `Duration` date-unit
arithmetic with `relativeTo` (`add`/`subtract` lost `relativeTo` in the specification), the
`chinese`/`dangi` calendars, and the non-`full` build (which asks Intl for calendars).

## History

- 2026-09-17: created against b28e5a85 (1.0.5); 6 properties, 8 bugs.
- 2026-09-26: generators rewritten in combinator style (`gen.mjs`); the known shapes are drawn by
  default and the wide properties are the expected failures; one narrow property per bug added;
  `HEGEL_NO_KNOWN=1` switches the shapes off; the notes of bugs 1, 3, 5 and 6 corrected after
  re-checking their examples. The 3000-case run of the rewritten calendar property found bug 9
  (Hebrew `until` from Adar I).
