# typescript/date-fns — date-fns/date-fns (against a model of the calendar, across time zones)

`date-fns` is the most used date library of the JavaScript ecosystem (~30M weekly downloads): 250
pure functions over the built-in `Date` — `format`/`parse` with Unicode tokens, `parseISO`,
`formatISO`/`formatRFC3339`/`formatRFC7231`, the `add*`/`sub*`/`set*`/`get*` families,
`differenceIn*` (calendar and full units), `startOf*`/`endOf*`/`lastDayOf*`, ISO and locale
weeks, intervals (`each*OfInterval`, `intervalToDuration`, `isWithinInterval`, `clamp`,
`closestTo`) and business days. Everything is computed in the process time zone through the
Date setters, which is where DST rules bite. The patch checks it against a model of the
Gregorian calendar computed from local fields (`hegel/model.mjs`) under thirteen time zones with
every shape of daylight-saving rule, and pins 16 bugs.

## How it is built

Upstream is a pnpm monorepo (`pkgs/core` is the package; `subdir` points there). Node 22 runs the
TypeScript sources directly (type stripping, `.ts` import specifiers), so nothing is built: the
setup installs Hegel under `.hegel/` (`npm install --prefix .hegel`, the package's own
`node_modules` and lock file stay untouched) and the tests import `../src/index.ts`.

## How it is tested

`hegel/hegel.test.mjs` runs under `node --test`; `hegel/hegel-zoo.mjs` is the zoo's shared
harness, `hegel/model.mjs` the calendar model (civil day numbers, `local`/`near` — the instant
with given local fields, `near` keeping the input's offset when the wall time is ambiguous —,
ISO and locale weeks from `weekStartsOn`/`firstWeekContainsDate`, `addMonths` with clamping,
full days/months/years, every format token, `isoString`/`rfc7231`, and `parseIso`, a regex model
of the ISO 8601 profile `parseISO` documents), `hegel/gen.mjs` the generators. Each case picks a
zone (UTC a quarter of the time; otherwise New York, London, Dublin — negative DST in tzdata —,
Lord Howe — 30-minute DST —, Apia — a skipped day —, Santiago and Havana — DST at midnight —,
Kolkata, St. John's — -03:30 with DST, 00:01 transitions until 2011 —, Chatham — +12:45 —,
Casablanca — Ramadan fall-back —, Troll) and sets `process.env.TZ`, which V8 honours at run time.
Instants are drawn 1970-2040 with a third of them within hours or days of one of the zone's
offset transitions (found by scanning), plus years 1-1969, 2040-9999 and, in the `FULL` shape
space, years outside 0000-9999. Mismatches on shapes a recorded bug is about are counted under
the bug's id (`known date-fns/N`); anything else fails.

| Property | What it checks |
|---|---|
| `TestHegelFormatTokensMatchTheCalendar` | `format(d, token)` equals the model for every token (`G y Y R u Q q M L w I d D E i e c a b h H K k m s S X x O z t T`, all widths, ordinals) with random week options |
| `TestHegelParseInvertsFormat` | `parse(format(d, f), f)` gives d truncated to f's precision, for complete format strings (calendar, ordinal, ISO-week and locale-week dates, eras, signed years, 12/24-hour clocks, day periods, fractions, offset tokens, quoted text); ambiguous wall times and offsets with seconds are skipped |
| `TestHegelDifferencesMatchTheModel` | `differenceInCalendar*`, `differenceIn{Days,Weeks,Hours,Minutes,Seconds,Milliseconds,Months,Quarters,Years,BusinessDays}`, `compareAsc`, `isBefore`, `isSame*` against the model |
| `TestHegelAddSubSetGetMatchTheModel` | `add*`/`sub*`/`add`/`sub`, the getters (`getWeek`, `getISOWeek`, `getWeekYear`, `getDayOfYear`, `getWeekOfMonth`, ...), the setters (`setDate`, `setMonth`, `setYear`, `setDay`, `setISODay`, `setWeek`, `setISOWeek`, ...), `nextDay`/`previousDay`, `addBusinessDays`, `isExists` |
| `TestHegelStartAndEndOfUnitsMatchTheModel` | `startOf*`/`endOf*`/`lastDayOf*` for day, week, ISO week, month, quarter, year, decade, week year, ISO week year, hour, minute, second; `roundToNearestMinutes`/`Hours` |
| `TestHegelIntervalsMatchTheModel` | `each{Day,Weekend,Week,Hour,Month,Quarter,Year}OfInterval` (both orders, steps), `isWithinInterval`, `areIntervalsOverlapping`, `clamp`, `max`/`min`, `closestTo`/`closestIndexTo`, and `intervalToDuration` (adding it to the start gives the end; it is normalized) |
| `TestHegelIsoFormatsMatchTheModel` | `formatISO` (all representations and the basic format), `formatISO9075`, `formatRFC3339`, `formatRFC7231`, `parseISO`/`parseJSON`/`toDate` round trips, `lightFormat`, `fromUnixTime` |
| `TestHegelParseIsoFollowsIso8601` | `parseISO` on generated ISO 8601 strings, mostly valid and sometimes with one thing wrong (calendar, ordinal and week dates, basic and extended, expanded years with `additionalDigits`, fractions, hour 24, offsets), equals the model or both reject |

`TestHegelPin…` are plain tests, one per bug in `bugs.toml`.

Accepted differences, not recorded: `differenceInDays` counts by the calendar with the time of
day compared by wall clock (as documented; a 24-hour DST day is one day); the `b` token says
`noon`/`midnight` for the whole hour; an ambiguous wall time parsed without an offset may resolve
to either occurrence; a midnight that occurs twice (St. John's 00:01 fall-backs) makes
`eachDayOfInterval` count the next day when the interval ends in the repeated minutes; a BC year
formatted without an era or signed-year token cannot round-trip; offsets with seconds (local
mean time before standard time) cannot round-trip through `hh:mm` offsets.

## Bugs

See `bugs.toml`. With teeth: **`eachHourOfInterval` skips the repeated hour after a DST
fall-back** — it steps by `setHours(h + 1)`, so 01:00 EST never appears (11, medium);
**`startOfHour`/`startOfMinute`/`startOfSecond`, `endOfHour`/`endOfDay` and the setters leave the
input's unit at a transition** — an hour earlier in the repeated hour (`endOfDay(d) < d`),
after the input where Chatham's gap swallows the start of an hour (12, medium);
**`differenceInYears` is -1 for a two-minute interval across a fall-back** and
`intervalToDuration` reports `years: -1, months: 11, days: 29, hours: 24` for it — the dates are
compared by wall clock after being moved to 1584 (13, medium); **`parse` resolves a time on a
DST-gap day an hour late**, even with an explicit offset, because it sets hours before minutes
and h:00 does not exist (15, medium).

The rest: ISO years outside 0000-9999 are written in a form `parseISO`/`parse` cannot read (1);
`parseISO` accepts week 53 of a 52-week year (2), offsets with hours above 23 (3) and strings
outside the grammar — text after `Z`, an empty fraction, an empty time, a time after `YYYY-MM`,
a fraction on hour 24 (4); `differenceInYears(28 Feb 2021, 29 Feb 2020)` is 0 although `addYears`
lands there, so `intervalToDuration` gives `months: 12` (5); `differenceInMonths` ignores the time
of day on a month's last day (6); `isExists` is false for years 0-99 (7);
`differenceInBusinessDays` is not antisymmetric at weekends (8); `formatRFC3339`/`formatRFC7231`
write years below 1000 unpadded (9); `lastDayOfWeek`, `eachMonthOfInterval` and
`eachYearOfInterval` return 01:00 when the input day starts at 01:00 (10); `parseJSON` maps years
0-99 to the 1900s (14); `parseISO("...01.023Z")` is .022 (16).

## History

- 2026-09-20: created against 18cbd43 (4.4.0); 16 bugs.
