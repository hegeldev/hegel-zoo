# typescript/cron-parser — harrisiirak/cron-parser (against a brute-force schedule model)

cron-parser is "a JavaScript library for parsing and manipulating cron expressions", with
seconds, `L`/`#`/`H` extensions, IANA time zones through luxon, and a crontab file reader. The
patch tests the parser, the printer, the scheduler (`next`, `prev`, `take`, the iterator,
`includesDate`, `startDate`/`endDate`, strict mode, hashed fields, `CronFieldCollection.from`)
and `CronFileParser`, and pins 6 bugs.

The README (field table, strict mode rules, hash support, field manipulation, time zones) is the
reference; the source was read for the day-of-month/day-of-week rules (`#matchDayOfMonth`'s
comment), the single-month pruning of the day of month (`CronDayOfMonth.fromMonth`), the DST
bookkeeping (`CronDate.applyDateOperation`, `#matchHour`) and the crontab reader.

## How it is built

`src/` is TypeScript compiled to CommonJS. The setup installs everything under `.hegel/` with
`npm install --prefix .hegel` — Hegel, the runtime dependency luxon 3.7.2, the compiler and its
type packages — and compiles `src/` into `.hegel/dist` with `hegel/tsconfig.json`, which extends
upstream's tsconfig and points module resolution for luxon's types at `.hegel/node_modules`.
The tests `require` `.hegel/dist/index.js`; nothing in the upstream tree is touched and nothing
outside `hegel/` is added.

## How it is tested

`hegel/hegel.test.mjs` runs under `node --test`; `hegel/hegel-zoo.mjs` is the zoo's shared
harness. Expressions are generated field by field from the grammar — `*` and `?`, values,
ranges, steps, lists (kept disjoint: the library rejects overlapping list elements as
"duplicate values"), month and weekday names in either case, `L` in the day of month, `<d>L`
and `<d>#<n>` in the day of week, five or six fields — with a model of every field's value set.
Instants are drawn between 2000 and 2040, half of them with milliseconds; zones include UTC,
New York, Rome, Kolkata, Tokyo, Auckland, Santiago and Havana (midnight transitions), Chatham
(a shift at 02:45) and Lord Howe (a 30-minute shift).

The schedule oracle is brute force over wall-clock time in the zone: the next occurrence is the
first whole-second instant after `currentDate` whose local second, minute, hour, month and day
match, days being tested with the library's own documented rules (both day fields restricted:
either matches; otherwise the restricted one). On a DST transition day every matching wall-clock
triple is mapped through luxon, which moves a time in the gap forward by the gap's length (the
library's "landing hour") and takes the first pass through a repeated hour (the library does not
return a repeated hour twice), and the distinct instants are sorted.

- `parse` expands each field like the model, including the pruning of numeric days past a
  single month's length (kept when nothing would remain), `L`, `#` and weekday 7.
- `stringify(true)` re-parses to the same fields and is idempotent; the five-field form does when
  the seconds are 0; `fieldsToExpression(fields).stringify(true)` is the same string.
- `next()` and `prev()` equal the model in every zone, including transition days.
- `next()` is strictly increasing, `prev()` walks back through the same dates, `reset()` returns
  to the start, `take(n)`, `take(-n)` and the iterator agree with repeated `next()`.
- `includesDate` agrees with the model, for instants at and around occurrences.
- With `startDate`/`endDate` every result is inside the span and matches; `hasNext`/`hasPrev`
  are true exactly when `next`/`prev` succeed, which otherwise throw "Out of the time span".
- Strict mode rejects both day fields restricted, five fields and empty expressions, and accepts
  the rest; non-strict parsing pads five fields and defaults the empty string.
- Hashed fields (`H`, `H/s`, `H(a-b)`, `H(a-b)/s`) are deterministic in `hashSeed`, stay within
  their (clamped) ranges with the given step, cover the range, schedule like their expansion;
  strict mode rejects a range outside the field or a step wider than the range's value count.
- `CronFieldCollection.from` applies raw-value overrides and keeps the other fields.
- Random junk is rejected with an `Error` or parses to something that re-parses equal; values
  out of range, zero steps and reversed ranges are rejected.
- `CronFileParser.parseFileSync` reads a generated crontab (comments, blank lines, quoted
  variables, entries with commands, invalid entries) into the expected expressions, variables
  and errors.
- Predefined expressions (`@daily` …) parse and schedule like their long forms.

Known-bug shapes are skipped by name and counted (`ZOO_COLLECT=1` prints the counts); the
models never emulate a bug. Non-bugs met on the way: overlapping list elements are rejected by
design; `0-7` in the day of week is "restricted" while `*` is not (so `15 * 0-7` fires every
day by the either-matches rule), consistent with the documented rules; a `#` cannot be combined
with `,`, `-` or `/`; a step wider than a hashed range's value count is a single value.

## Bugs

- cron-parser/1 — `CronFieldCollection.from` with a month override keeps day-of-month values
  pruned for the old month; `stringify()` then prints a restricted range and the printed
  expression schedules differently (Thursdays become every day).
- cron-parser/2 — strict mode rejects `?` in the day fields although `?` is documented as an
  alias for `*`.
- cron-parser/3 — a whitespace-only expression is rejected while `""` defaults to `0 * * * * *`.
- cron-parser/4 — `CronFileParser` takes any entry whose command contains `=` for a variable
  assignment; the schedule vanishes.
- cron-parser/5 — `CronFileParser` splits entries on single spaces; tabs or aligned fields
  misread the entry (a double space silently yields a different valid schedule).
- cron-parser/6 — in Australia/Lord_Howe (30-minute DST) `next()` aborts with "loop limit
  exceeded" on the day DST ends and drops the gap occurrence on the day it starts.
