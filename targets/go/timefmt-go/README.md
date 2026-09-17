# timefmt-go

[itchyny/timefmt-go](https://github.com/itchyny/timefmt-go) is the strftime/strptime library
for Go used by gojq and many CLI tools: `Format`/`AppendFormat` with the glibc extensions
(widths up to 1024, the `-`, `_`, `0`, `^`, `#` flags, `%:z`/`%::z`/`%:::z`), `Parse` and
`ParseInLocation` with composed directives, century years, week dates (`%U`/`%W` with a
weekday, `%G-W%V-%u`) and Unix times, plus Python's `%f`. Pinned at 53188ff (v0.1.8+,
2026-09-14), MIT, no AI policy.

## Oracle

glibc 2.39's `strftime` and `strptime`, reached through Python's `ctypes` in one child process
held open for the whole run (JSON lines; `TZ=UTC`; `struct tm` with `tm_gmtoff`/`tm_zone`, so
`%z`/`%Z` see the fixed zone). The README points at `man 3 strftime`/`strptime`, i.e. glibc,
as the specification. Where glibc 2.39 has no implementation or a quirk of its own the
property uses a model instead (see below and "Not bugs").

## Properties

- `TestHegelFormatAgreesWithGlibc` — formats of 0–7 pieces (every shared directive with the
  five flags, widths 1–12 / 100–1024, unknown directives, literal text incl. non-ASCII,
  unfinished trailing sequences) on times of years 1000–9999 in twelve fixed zones (offsets
  with minutes and seconds) print exactly what glibc prints; `AppendFormat` appends the same
  text to a non-empty buffer.
- `TestHegelExtensionsMatchTheirModels` — `%:z`, `%::z`, `%:::z` follow GNU date's rules,
  `%::::z` is literal, `%f` is the six-digit microsecond, and `%c %D %x %T %X %R %r %F %v %+`
  equal their documented expansions.
- `TestHegelParseAgreesWithGlibc` — for a time formatted with 1–5 shared parse directives and
  separators, `Parse` and glibc's `strptime` accept the same sources and read the same
  broken-down time (glibc's un-normalised "December 32nd" from a week number is normalised
  first), including the dates derived from `%Y %j` and from `%U`/`%W` with a weekday, `%C%y`,
  12-hour clocks, `%s` and `%z`.
- `TestHegelParseInvertsFormat` — `Parse(Format(t, f), f)` gives back `t` for 22 date shapes
  (calendar, ordinal, ISO week, Sunday/Monday week, century+year, Unix time, `%c`) × 15 clock
  shapes × the four `%z` forms, up to what the format keeps (seconds, microseconds, offset
  rounded to the minute by `%z`, UTC when there is no zone directive).
- `TestHegelParseRejectsOutOfRangeFields` — a field outside its documented range (month 13,
  day 32, hour 24, minute 60, second 61, ordinal 367, week 54, weekday 7 / `%u` 0, `+24:00`,
  unknown month/day/AM names, five-digit years, negative centuries) fails whatever surrounds
  it.

All general properties pass at 1000 cases × 3 and the two differentials and the round trip at
10 000 (about a second a run). Two pinned expected failures.

## Bugs (2)

| id | title | severity |
|----|-------|----------|
| timefmt-go/1 | The `-` flag followed by a width below the default pads with spaces to the default (`%-1m` → ` 7`) | low |
| timefmt-go/2 | Parse ignores `%j` whenever a month or day directive is present, leaving the month at January | low |

timefmt-go is thoroughly tested upstream (2 500 lines of table tests, including negative years
and every flag/width combination on every directive); the differentials found the two corners
its tables skip — a flag/width combination and a directive combination. Both generators keep
the pinned shapes out (`-` with a width below the default; `%j` next to `%m`/`%d`).

## Not bugs (documented, asserted by upstream's tests, or glibc's own quirks)

- Years below 1000 and negative years: timefmt pads `%Y`/`%G` to four digits (`0999`,
  `-001`) and prints `%C`/`%y` of year −1 as `-0`/`01` (sign-magnitude); glibc prints `999`,
  `-1`, and `-1`/`99` (floor division). Both are self-consistent; upstream's tests assert
  timefmt's. The glibc differential uses years 1000–9999.
- Width on the composites `%c %D %x %T %X %R %r %F %v %+` is ignored (`%9F` → `2020-02-09`;
  asserted upstream); glibc pads the whole expansion (except `%c`). Kept out of the generator.
- `%^P` prints `AM`; glibc ignores `^` and `#` on `%P` (`am`). `%z` with a width: glibc's
  output is peculiar (`%10z` → `         +0000000000`), timefmt's is upstream-asserted
  (`%8z` → `+0000900`); both kept out of the differential.
- glibc 2.39 has no `%:z`/`%::z`/`%:::z` (GNU date has), no `%f`, `%v`, `%+`; these are
  checked against models. `%E`/`%O` modifiers are glibc's and unsupported here (README).
- Widths are limited to 1024 (README); glibc has no such limit.
- Parsing: `%p` adjusts an hour parsed with `%H` (`13:13:14 AM` → 01:13:14; asserted
  upstream) and a lone `%p PM` gives 12:00, where glibc and Python apply `%p` only with `%I`;
  a lone `%U`/`%W` week places the date on the week's first day where glibc needs a weekday
  and does nothing otherwise; `%j` without a year sets the date where glibc does not; `%s`
  accepts a sign (glibc does not) and always converts in UTC (glibc in TZ); `%n`/`%t` swallow
  every blank and a following literal blank then fails, where glibc's literal blanks match
  zero or more; glibc skips blanks before every number and accepts either the long or the
  short name for `%b`/`%B`/`%a`/`%A`. The parse differential feeds Format's output and keeps
  these shapes out.
- `%G`/`%V`/`%g` and `%Z` are parsed but ignored by glibc's strptime; timefmt's are checked by
  the round trip (`%Z` only through `%+`-free formats, since unknown abbreviations resolve
  through Go's `ParseInLocation`).
- Mixing `%G` with `%Y` in one format overwrites the ISO year (`%G-W%V-%u %Y` reads the `%Y`
  as the week-year); the documentation says to use one or the other.

## Conventions

External test package with a dot import; `HEGEL_TEST_CASES` via `hegelOpts`; `property()`
turns panics into test-case failures; the oracle child is started once per process
(`sync.Once`) and serialised with a mutex.
- 2026-09-17: base bumped 53188ffdc7cd → d13d369fb520 (2026-09-18, "add allocation tests of parsing and appending formatted time"; v0.1.8+); 2 bug(s) still reproduce. 20 tests pass.
