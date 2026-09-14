# cron

[robfig/cron](https://github.com/robfig/cron) (`github.com/robfig/cron/v3`) is the cron
library of the Go ecosystem: a spec parser (`ParseStandard`, `NewParser` with field options,
`TZ=`/`CRON_TZ=` prefixes, `@hourly`-style descriptors, `@every <duration>`), a `Schedule`
interface whose `SpecSchedule.Next` finds the next activation in a time zone, `Every` for fixed
intervals, and a `Cron` runner with job-wrapper chains (`Recover`, `DelayIfStillRunning`,
`SkipIfStillRunning`). About 1200 lines of Go; the last commit is from January 2021, five
commits past the v3.0.1 tag. Pinned at bc59245 (v3.0.1+), MIT, no AI policy.

## Oracles

- A bit-set model of the documented grammar: for each field `* | ? | N | N-M | */S | N/S |
  N-M/S`, names for months and weekdays in any case, lists with commas; the six bit sets of
  the resulting `SpecSchedule` (which are exported) are compared exactly, including the
  library's star bit (set for `*` and `?`, also with `/1`, cleared for a larger step — the
  rule its day matching depends on). Missing fields take the documented defaults (`0` for
  time fields, `*` for date fields); every layout of `NewParser` is exercised (standard, with
  seconds, optional seconds, optional day-of-week, date only, hour and minute, descriptors
  only). Descriptors map to their documented equivalents; `@every d` to
  `ConstantDelaySchedule{max(1s, trunc(d))}`.
- A calendar model of `Next`: the earliest instant after `t` whose wall clock in the
  schedule's zone matches every field, or the zero time when none falls within five years.
  It walks days (month bit, then the day rule: with `*`/`?` in either day field both must
  match, otherwise either may) and, for each matching wall-clock time, asks `time.Date` for
  the instants that really read that wall clock — none in a DST gap, two in a fall-back — so
  DST is handled by definition rather than by adjustment. A schedule without a zone
  (`time.Local`) is read in the zone of the time given, as documented.
- Small models for `Every`, the entry bookkeeping of a `Cron` that has not been started
  (IDs from 1, insertion order, `Remove`, `Entry`, `Location`), and `Chain.Then` nesting with
  `Recover`.

## Properties

- `TestHegelParserBuildsTheDocumentedBitSets` — random specs for every layout, with and
  without `TZ=`/`CRON_TZ=` prefixes over ten IANA zones, tabs and runs of spaces between
  fields, leading and trailing blanks, descriptors and `@every` durations.
- `TestHegelParserRejectsInvalidSpecs` — wrong field counts, values out of range, negative
  values, reversed ranges, zero steps, too many hyphens or slashes, non-numbers and unknown
  names, unknown zones, unknown descriptors, descriptors on a parser without the option, bad
  `@every` durations: an error and a nil schedule.
- `TestHegelNextFollowsTheCalendarModel` — schedules built directly from random bit sets or
  parsed from random text, in UTC, Asia/Tokyo, Asia/Kolkata, America/New_York,
  America/Los_Angeles, Europe/London, Europe/Berlin, Australia/Sydney, Australia/Lord_Howe
  (30-minute DST), Pacific/Chatham (+12:45), or `time.Local`; start instants from 1995 to
  2036 with a bias to the DST months and the small hours, expressed in a random zone: `Next`
  equals the model, comes back in the argument's zone, and `Next(Next(t))` is later and again
  equals the model. Zones whose transitions happen at midnight are kept out of this property
  because of cron/2.
- `TestHegelEveryRoundsToWholeSeconds` — `Every(d)` for negative, sub-second, fractional and
  huge durations; `Next` lands on the second; `ParseStandard("@every " + d.String())` agrees.
- `TestHegelCronKeepsItsEntriesWhileStopped` — random `AddFunc`/`Schedule`/`Remove` sequences
  on a `Cron` with `WithLocation` and optionally `WithSeconds`: `Entries`, `Entry`, IDs, zero
  `Next`/`Prev`, invalid specs rejected without an entry.
- `TestHegelChainWrapsInOrder` — `NewChain(m1..mn).Then(job)` runs m1 outermost; `Recover`
  swallows a panic and logs it once.

All general properties pass at 1000 cases × 3 (under a second). Five pinned expected
failures. The run command is `go test -run TestHegel` because the upstream tests sleep for
about 40 seconds.

## Bugs (5)

| id | title | severity |
|----|-------|----------|
| cron/1 | Parse panics (slice bounds out of range) on a spec that is only a zone prefix, such as `TZ=UTC` or `CRON_TZ=Asia/Tokyo` | medium |
| cron/2 | Next skips a whole day whose midnight does not exist (DST gap at 00:00, e.g. Asia/Beirut, America/Havana, America/Santiago): a 03:00 run on 31 March 2024 in Beirut is scheduled for 31 May | medium |
| cron/3 | Anything after `*` or `?` in a range is ignored: `*-5` parses as `*` and `?-5/2` as `*/2` | low |
| cron/4 | A field made only of commas (`,`, `,,`) parses to an empty set with a nil error, and the schedule never fires | low |
| cron/5 | The zone prefix must be followed by a space: `TZ=UTC<tab>0 0 * * *` fails with "provided bad location" although every other separator may be any blank | low |

cron/1, /3 and /4 were visible from reading `parser.go` (the unchecked `strings.Index`, the
star branch that never reads `lowAndHigh[1]`, `strings.FieldsFunc` dropping empty items) and
confirmed by one probe; cron/2 from reading the day loop's hour "correction" and confirmed in
Asia/Beirut, America/Havana and America/Santiago with the model; cron/5 came out of the parser
property (a tab after the prefix).

## Not bugs (documented, asserted upstream, or lenient by design)

- `*/2` clears the star bit, so `* * */2 * 1` means "every second day OR Monday" (Vixie cron
  treats a field starting with `*` as unrestricted and would AND them). The doc points at the
  Wikipedia description, which says "restricted"; the model follows the library's rule and
  the README records the difference.
- `?` is accepted in every field, not only day-of-month/day-of-week; the generator uses it
  only where documented.
- `+1`, `01` and `1,,2` are accepted (strconv.Atoi and FieldsFunc leniency); `*/61` in a
  minute field is `{0}` (a step larger than the range), as in Vixie cron.
- Day-of-week `7` is rejected (documented range 0–6; Vixie accepts 7 as Sunday); `sunday`
  and `january` are rejected (three-letter names only, documented).
- `@every` with less than a second, zero or a negative duration means one second
  ("Delays of less than a second are not supported (will round up to 1 second)").
- A job whose wall-clock time falls into a spring-forward gap is skipped for that day
  ("jobs scheduled during daylight-savings leap-ahead transitions will not be run!"); a time
  repeated by a fall-back runs twice. Both are what the model says too.
- `Next` gives up after five years (`0 0 30 2 *` → zero time); the model uses the same
  limit, measured from the year of the start instant.
- `time.Local` in a schedule means "the zone of the time given to Next", not the machine's
  zone; documented in `Next`'s comment and modelled.
- The scheduler loop (`Start`, `Run`, `Stop`, jobs firing) and the two `IfStillRunning`
  wrappers depend on real time and goroutine timing; not covered (upstream's tests sleep).
