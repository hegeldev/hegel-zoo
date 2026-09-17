# typescript/luxon — moment/luxon (against Temporal and its own laws)

Luxon is "a powerful, modern, and friendly wrapper for JavaScript dates and times": immutable
`DateTime`s in IANA zones whose offsets come from `Intl`, `Duration`s with casual or long-term
unit conversion, and half-open `Interval`s. The patch checks it three ways and pins 10 bugs.

The in-repo `docs/` (math, zones, parsing, formatting, validity) is the reference; the method
docstrings in `src/` were read for `set`, `shiftTo`, `splitAt`, `toISOTime` and `fixOffset`.

## How it is built

No build: `src/` is plain ES modules that Node 22 imports directly (`src/package.json` says
`"type": "module"`). `npm install --prefix .hegel` puts Hegel and the oracle,
`@js-temporal/polyfill` 0.5.1, under `.hegel/`; luxon has no runtime dependencies.

## How it is tested

`hegel/hegel.test.mjs` runs under `node --test`; `hegel/hegel-zoo.mjs` is the zoo's shared
harness. Every test case draws a zone (three quarters of the time from a curated list of
awkward ones — Lord Howe, Apia, Casablanca, Troll, St John's, Kathmandu, Chatham, Kolkata … —
otherwise from `Intl.supportedValuesOf("timeZone")`) and an instant, half the time near one of
the zone's real transitions found with Temporal's `getTimeZoneTransition`, sometimes an edge
(epoch, year 0, the Date limits), otherwise random between 1900 and 2100 or far outside.

Temporal reads its zone data from the same ICU as Luxon, so the two never disagree on an
offset; every check of a wall-time resolution accepts either occurrence of a repeated hour,
because the zones guide documents Luxon's choice there as undefined.

| Property | What it checks |
|---|---|
| `TestHegelFieldsLikeTemporal` | every calendar field, `offset`, ISO week fields, `daysInMonth/Year`, `weeksInWeekYear`; `toISO` in all option combinations, `toISODate/Time/WeekDate`, `toRFC2822`, `toHTTP`, `toSQL*`, the numeric `toFormat` tokens, `toMillis/toSeconds/toUnixInteger`; `fromObject`, `fromISO(toISO())` with and without `setZone`, `getPossibleOffsets`; `setZone` with and without `keepLocalTime`, `toUTC`, `equals`, `hasSame`, `min/max` |
| `TestHegelArithmeticLikeTemporal` | `plus`/`minus` with one to three integer or fractional units against a Temporal model of the documented rule (calendar units on the wall clock with the day clamped once, time units exact, gaps forward, `wasHole`); plus-then-minus; `startOf`/`endOf` of every unit; `hasSame`; `set` of every unit incl. `weekday`, `ordinal`, `weekNumber`, `weekYear`, `quarter`; `diff` in random unit sets: signs, integer intermediates, bounds, antisymmetry, `earlier.plus(later.diff(earlier))` inversion, integer parts against Temporal `until`; `Interval.toDuration/length` |
| `TestHegelDurationLaws` | `fromObject` round trip, `valueOf`/`toMillis`/`as`; `shiftTo` to random unit sets (total preserved, only the last unit fractional, consistent signs, no overflow, idempotent); `normalize`, `rescale`, `negate`, `plus/minus`, `mapUnits`, `set/get`, `reconfigure`, `equals`; `fromISO(toISO())`, `fromISOTime(toISOTime())`, `fromMillis(...).shiftTo(low units)` exact |
| `TestHegelIntervalAlgebra` | a brute-force model of half-open sets on a grid: `contains`, `isBefore/isAfter`, `overlaps`, `abuts*`, `engulfs`, `equals`, `intersection`, `union`, `difference`, `Interval.xor`, `Interval.merge`, `splitAt`, `splitBy`, `divideEqually`, `count`, `hasSame`, ISO round trips (`start/end`, `start/duration`, `duration/end`), `after/before`, `set`, `mapEndpoints` |
| `TestHegelParseTechnicalFormats` | ISO strings built from known fields in every documented form (calendar, week and ordinal dates, basic and extended, `T`/`t`, 0–4 time parts, 1–9 fraction digits, `.`/`,`, `Z`/`±HH:MM`/`±HHMM`/`±HH`, `[zone]`, offset plus `[zone]`) with `zone`/`setZone`; `fromSQL` (with offsets and zone names), `fromRFC2822` (with and without weekday/seconds, `GMT`/`UT`), `fromHTTP` (all three forms, two-digit years), `fromSeconds`, `fromJSDate`, `fromObject` with week and ordinal fields and a contradicting weekday |
| `TestHegelFormatParseRoundTrip` | `fromFormat(dt.toFormat(f), f)` for formats that determine the instant: 14 date token sets (numeric, names, week dates, ordinals, two-digit years), 15 time token sets (12/24-hour, fractions, the `t`/`T` macros), offset tokens `Z`/`ZZ`/`ZZZ`/`z`, literals and separators, `fromFormatExplain` |
| `TestHegelInfoAndZones` | `Info.isValidIANAZone`, `normalizeZone` of names and junk, `hasDST` (December vs June offsets this year), `FixedOffsetZone` names and `UTC±H:MM` specifiers, `Info.months/weekdays/meridiems` |

`ZOO_COLLECT=1` turns mismatches into `# COLLECT` counts instead of failures; `HEGEL_TEST_CASES`
(default 100) widens the sweep. Known bugs are skipped through the `Known` switches at the top
of the file, accepted differences through `Accepted`; each skip is counted.

## Bugs

10 open, all pinned (see `bugs.toml`). By area:

- Zones and offsets: `fromISO` discards the offset when a `[zone]` annotation follows (3); a wall
  time within a day after a transition is taken for a gap when the zone's current offset is far
  from its offset then — Pacific/Apia before its date-line move (4); the narrow offset format
  and `FixedOffsetZone` names leave single-digit minutes unpadded, `UTC+5:5`, which the zone
  parser rejects (6).
- Setting and parsing fields: `set` rolls out-of-range values over instead of invalidating (8);
  `set({quarter})` is ignored (2); a `q` token in `fromFormat` overwrites the parsed month (9);
  `toISOWeekDate` does not expand years outside 0000–9999 (1).
- Durations: `shiftTo`/`normalize` leave a fractional opposite-signed unit below one (7), and
  fractional intermediate units under long-term accuracy (10).
- Intervals: `splitAt` with a cut at the start or a repeated cut yields empty intervals (5).

## Accepted differences (skipped, not counted as bugs)

- A repeated wall time resolves to either occurrence — documented as undefined; the `set`,
  `plus`, `startOf`, `fromObject` and `keepLocalTime` checks accept both instants, and a `diff`
  whose unit boundary falls on a repeated or skipped hour may differ from Temporal in its
  integer part.
- Casual conversions between years, quarters, months and weeks do not preserve a duration's
  total (documented: 12 × 30 ≠ 365); totals are only checked where the chain is consistent.
  Fractional calendar units in `plus` are converted casually (1.5 months = 1 month + 15 days).
- Offsets with seconds (local mean time before ~1900, Whitehorse −9:00:12): `toISO` truncates
  to minutes so ISO round trips are off by the seconds; `wasHole` is not checked there.
- On the last day of the Date range (±8.64e15 ms) `fromMillis` in a zone whose offset pushes the
  wall clock beyond the range is invalid; wall-clock checks within two days of the limits are
  skipped.
- `hasSame` compares wall clocks across zones (documented). `overlaps`, `merge`, `xor`,
  `difference` and `count` treat an empty interval as a point (overlaps a containing interval,
  survives merge, counts 0 or 1 by alignment); `divideEqually(n)` of an interval not divisible
  by n yields sub-millisecond pieces. `toISOTime` of a negative duration is null (documented).
- `UTC+25` is a valid fixed-offset zone; `""` is not a zone. `toISO({ extendedZone: true })` of
  the UTC zone writes `[Etc/UTC]`. `fromSeconds` of a fractional second carries float noise;
  duration totals and components are compared to 1e-9 relative (1e-6 ms absolute).
- Not modelled: `T01:30` (a `T` prefix on a time-only string) is not documented as parseable;
  `yyyyy` is a parse-only token; `fromSQL` needs a time before a zone name.

## Not tested

Locales other than `en-US` (names differ by design), `toLocaleString`/`toLocaleParts` and the
macro tokens' text (Intl output), `toRelative*`/`diffNow`/`Duration.toHuman` (clock or Intl),
`useLocaleWeeks`/`localWeek*` (Intl week info), `Settings.throwOnInvalid`, custom `Zone`
subclasses, `Info.features`.

## History

- 2026-09-17: created at f427515 (3.7.2 dev head), 7 properties, 10 bugs.
