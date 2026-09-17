# typescript/dayjs — iamkun/dayjs (against moment)

dayjs is a 2 kB moment.js replacement with "the same modern API"; its core parses, formats,
gets/sets, adds/subtracts, compares and diffs instants, and plugins add UTC and time-zone modes,
custom-format parsing, durations, relative time, week/quarter/ordinal getters and more. The patch
compares dayjs (core + 27 plugins) with moment 2.31.0 and moment-timezone 0.6.4 across twelve
host time zones, and pins 22 bugs.

The in-repo docs are stubs; the reference is https://day.js.org (the parse regex, the token
tables, the separator list, the utcOffset rule and the duration API were read there).

## How it is built

`npm install --prefix .hegel` puts Hegel, moment, moment-timezone and esbuild under `.hegel/`
(a single install: a second `--prefix .hegel` install removes the first). `hegel/build.mjs`
runs the esbuild binary directly (`.hegel/node_modules/esbuild/bin/esbuild` is native code, not
a Node script) and bundles `src/index.js` to `.hegel/dist/dayjs.cjs`, every
`src/plugin/*/index.js` to `.hegel/dist/plugin/<name>.cjs` and five locales, with a shim so the
locale bundles' `require("dayjs")` resolves to the freshly built core. The CommonJS exports are
under `.default`.

## How it is tested

`hegel/hegel.test.mjs` runs under `node --test`. `hegel/hegel-zoo.mjs` is the zoo's shared
harness (same file as in the other TypeScript targets). Every test case picks a host zone
(`process.env.TZ`, which Node re-reads on every call: UTC, London, Paris, New York, Whitehorse,
Auckland, Santiago, Lord Howe, Tehran, Sao Paulo, Apia, Kolkata) and an instant biased towards
that zone's DST transitions, then runs the same calls on dayjs and moment through `same()` and
compares a rendering of the results (instant + offset + utc flag, or `THROW <Class>`,
`Invalid`, and `Duration(ms ISO)` for durations).

| Property | What it compares |
|---|---|
| `TestHegelParseLikeMoment` | numbers, Dates, ISO strings in every documented form, arrays, objects, junk, clone, `isValid`, default `format()` |
| `TestHegelFormatLikeMoment` | random token strings (all documented tokens except `E`, `z`) in `en` and `en-gb`, local and UTC |
| `TestHegelGetSetLikeMoment` | every getter, plural getters, `get(unit)`, every setter incl. plugin units and `set(unit, v)` |
| `TestHegelManipulateLikeMoment` | `add`/`subtract` in every unit, `startOf`/`endOf` (incl. `isoWeek`), `utc()`/`local()`, `utcOffset(n[, keepLocalTime])`, `.tz(zone[, true])`, `dayjs.tz(string, zone)` |
| `TestHegelCompareLikeMoment` | `diff` (integer and float, every unit), `isBefore/isSame/isAfter/isSameOrBefore/isSameOrAfter` with units, `isBetween` with inclusivity, `min`/`max` |
| `TestHegelCustomParseLikeMoment` | `dayjs(text, format[, strict])` and array-of-formats for texts moment produced from the same format (documented tokens and separators), epoch tokens, time-only formats, mutated texts |
| `TestHegelDurationLikeMoment` | constructors (ms, `(n, unit)`, object, ISO 8601, text), `humanize`, `asMilliseconds`/`valueOf`/`toJSON`/`toISOString`, every getter, `get`/`as`, `add`/`subtract` |
| `TestHegelRelativeTimeLikeMoment` | `from`/`to` with an explicit reference (with and without suffix), `calendar` |

`ZOO_COLLECT=1` turns mismatches into `# COLLECT` counts instead of failures;
`HEGEL_TEST_CASES=1000` (default 100) gives a wider sweep. Known bugs are skipped through the
`Known` switches at the top of the file, accepted differences through `Accepted`; each skip is
counted so a `# COLLECT` line shows how often it fired.

## Bugs

22 open, all pinned (see `bugs.toml`). By area:

- Parsing: ordinal dates (3), fractional seconds by digit count (8), years 0–99 → 1900s (15).
- customParseFormat: case-sensitive names and meridiems (6), strict `S`/`SS` (13), strict `Z`
  only for +00:00 (14), word token followed by `.` (20).
- Time zones and offsets: `utcOffset(16)` as hours (5), `utcOffset(n)` across a host DST change
  (11), the repeated hour resolved to the earlier occurrence in `startOf`/`endOf`/`diff`/day
  arithmetic (12), `utcOffset(n, true)` from UTC mode (16), `weekday(n)` across a DST gap (17),
  `tz()` before 1970 with milliseconds (2), `tz(zone, true)` with the offset of the wrong instant
  (22), the default UTC format with localizedFormat/advancedFormat loaded (1).
- Getters/setters: `set`/`get` of plugin units (4), `add`/`subtract` of 1.5 days asymmetric (9).
- Durations: `(n, unit)` bubbling days into 365/12-day months (7), mixed-sign components (10),
  `-PT1H` losing its sign (18), comma decimals dropped (19), weeks not counted by `days()` or
  `dayjs.add(duration)` (21).

## Accepted differences (skipped, not counted)

Documented dayjs behaviour, moment's own quirks, or outside the contract:

- `toString()` is `toUTCString()` (documented); "Invalid Date" vs moment's "Invalid date".
- `utcOffset()` rounds to 15 minutes, so local-mean-time offsets (pre-1900 in most zones, with
  seconds in Whitehorse) are skipped everywhere.
- `isBetween` accepts swapped bounds (a dayjs test says so); `min`/`max` of nothing is `null`.
- Overflowing strings (`2019-13-01`, `2019-02-30`) are valid unless parsed strictly (documented);
  anything the parse regex does not match falls through to `new Date(string)` (documented), so
  digits-only strings, lowercase `t`, `2020-01-02T012345`, five-digit years and non-ISO junk
  under `utc()` follow the host's Date parser; negative years are out of scope (there is a
  negativeYear plugin).
- Unsupported units (`quarter` in durations, `date`/`weekday` in arithmetic), non-numeric
  amounts, `utcOffset("Z")` and `utcOffset(0.5)`: untyped input.
- Durations: a month is 365/12 days and days bubble into months in valid ISO input (documented
  as "12 months, 365 days"); overflowing or fractional components render as given (`PT90M`,
  `PT0.5M`, both valid ISO 8601) where moment normalises; fractional non-lowest components make
  moment durations invalid (NaN); moment folds 31+ days into months in its getters and keeps an
  object's days apart from its milliseconds when adding; `as*()` results are compared to 12
  significant digits; -0 equals 0.
- relativeTime: dayjs rounds the calendar-month difference and calls 26–45 days "a month",
  moment rounds whole months plus a 30.436875-day remainder; spans across a host DST change
  differ by an hour of rounding; humanize is measured from "now".
- `diff(..., float)` in months/quarters/years across an offset change; `isoWeek`/`W`-style
  dates in strings; moment's `YYYYYY` re-tokenising; moment's strict meridiem regex accepting a
  bare `P`; zone abbreviations (Intl `GMT+3:30` vs moment-timezone `+0330`, and before 1970 or
  after 2037); Date limits (±8.64e15 ms) within a month.
- DST gaps: day-and-up arithmetic or a date setter whose wall time lands in a gap (Lord Howe
  02:00 on a spring-forward Sunday) is resolved differently by the two Date-based rebuilds.
- Zone data: dayjs reads offsets from Intl (Node's ICU, tzdata 2026a here), moment-timezone
  0.6.4 ships tzdata 2026d; where they disagree (Casablanca's Ramadan table for 2046 and 2096,
  for instance) the `tz` cases are skipped.

## Not tested

Locales other than en/en-gb (text differs by design), `fromNow`/`toNow`/`calendar()` without a
reference (they race the clock), `updateLocale`, `Intl`-based `format("z")` outside the ASCII
abbreviations, badMutable/devHelper/bigIntSupport plugins, TypeScript typings.

## History

- 2026-09-17: created at 436bde0 (1.11.22 dev head), 8 properties, 22 bugs.
