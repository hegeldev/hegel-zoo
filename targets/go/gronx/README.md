# gronx

[adhocore/gronx](https://github.com/adhocore/gronx) is a dependency-free cron expression
library for Go (about 520 stars; a port of the author's PHP cron-expr): five, six or seven
segments (`second minute hour day month weekday year`, the second prepended when missing),
lists, ranges, steps, month and weekday names, `@hourly`-style tags with `AddTag`, the Quartz
modifiers `L`, `W`, `nL` and `n#k`, `IsDue` for a reference time, `BatchDue` for many
expressions at once, `IsValid`, and `NextTickAfter`/`PrevTickBefore` to find the next or previous
run from any instant; plus a `tasker` daemon (not tested here). The pin is `12c77ca`, the
v1.20.4 tag (2026-09-17).

The repository has LICENSE (MIT), README, CHANGELOG and a .github with CODEOWNERS, FUNDING and
workflows; no CONTRIBUTING, no agent instructions, nothing about AI-written code. The zoo keeps
its tests in its own patch and files nothing upstream.

## Build

`go test -count=1 -run TestHegel -v .` in the module root, with `python3` and
[croniter](https://pypi.org/project/croniter/) 6.2.4 on the path (`pip install croniter`; CI
installs it in its venv). The patch adds `hegel_test.go` (the model and the properties),
`hegel_pins_test.go` (one plain test per bug) and `hegel_oracle_test.go` (the croniter child),
and requires `hegel.dev/go/hegel v0.6.33` in go.mod (the `go` directive moves from 1.13 to
1.26.0 for it; gronx itself has no dependencies).

## Oracles

- **A model of the documented grammar**, built from a structured generator rather than parsed:
  per segment a list of items (`N`, `N-M`, `*/S`, `N/S`, `N-M/S`, names, `L`, `NW`, `NL`,
  `N#K`) with the bounds gronx documents (weekday 0-7 with 7 as Sunday, and gronx's readings of
  `7-x`, `x-7` and `7/s`), the normalisation (trim, whitespace runs, case, names anywhere, tags,
  a fourth digit run making the sixth segment a year), and validity. Wrong items are generated
  deliberately (out of bounds, reversed, zero steps, garbage, modifiers in the wrong field, full
  names such as `SUNDAY`).
- **A model of "due"**: the wall-clock fields against the sets, `L`/`W`/`nL`/`n#k` against the
  month's calendar, and the Vixie day rule gronx implements (both day segments restricted: either
  matches, unless the day-of-month starts with `*` or is `?` or the weekday starts with `*/`, in
  which case both must).
- **A model of the ticks**: a day walk from the reference (up to 120 years each way) over the
  days the date fields accept, then the hour, minute and second sets in order, giving the
  earliest instant after (or at) the reference or "none"; in fixed-offset zones, where wall
  clocks are monotonic. In zones with daylight saving the property is weaker: the tick must be
  later, due, and no instant between the reference and it may be due (checked at every second,
  or every minute for long gaps).
- **croniter** (Python, one persistent child) as a second voice on the subset both read the same
  way: `match`, `get_next`, `get_prev` with `second_at_beginning=True` on gronx's normalised
  segments. The subset leaves out what croniter reads differently or refuses: `?` (the
  reference's day in croniter), 7 as a weekday in lists and in the six-segment form, ranges via 7
  and steps from 7, `0/s` below a field's bound, `W` beyond the 28th or in a list or beside a
  weekday, `n#k` beside literals or a day-of-month (croniter intersects the two day fields for
  modifiers, gronx unions), a stepped day-of-month with a weekday (croniter unions, gronx follows
  Vixie and intersects), `nL` (croniter writes `Ln`), single-value ranges (`16-16`, which croniter
  misreads), year steps (counted from 1970 by croniter, from 0 by gronx) and years outside
  1970-2099.

## Method

| Property | Checks |
|---|---|
| ValidityFollowsTheGrammar | `IsValid` is true for every grammatical expression (and tag) and false for a wrong number of segments and for an invalid item that stands alone; `IsDue` errors on exactly those |
| SegmentsNormaliseAsDocumented | `Segments` gives the modelled six or seven segments for every written form, whitespace, case, name and tag |
| IsDueFollowsTheModel | `IsDue` equals the model at random instants and at instants the model says are due, in five fixed-offset zones; croniter's `match` agrees on the shared subset |
| NextAndPrevTicksFollowTheModel | `NextTickAfter` and `PrevTickBefore`, including and excluding the reference, equal the model's earliest/latest due instant, come back in the reference's zone, and error when the model finds nothing; croniter's `get_next`/`get_prev` agree on the shared subset |
| TicksInDSTZonesAreDueAndMinimal | in New York, Berlin, London, Santiago and Lord Howe, around the transitions: the next tick is later, due (for gronx and the model), and nothing between is due |
| BatchDueAgreesWithIsDue | `BatchDue` over lists with duplicates, tags and invalid expressions gives each entry `IsDue`'s answer, carrying the expression text |
| TagsExpandToTheirExpression | a tag added with `AddTag` is valid, has the expression's segments, is due and ticks when the expression does; a second `AddTag` is a conflict; built-in tags read in any case |

Mismatches are classified before they count: a `Known` switch per recorded bug gates the input
shape (the day union in BatchDue, invalid items that share an expression with other restricted
items, impossible modifier values, trailing newlines, tags with capitals, fractional references
with `inclRefTime`, stepped years, invalid expressions in `AddTag`, ambiguous and missing wall
clocks, a due reference with no other tick). With everything gated the properties run clean;
`ZOO_COLLECT=1` prints class counts and the first 25 mismatches instead of failing.

## Accepted differences (not bugs)

- The day-of-month/weekday rule: gronx follows Vixie cron, where a day-of-month starting with
  `*` (`*/2`) or a weekday starting with `*/` counts as unrestricted and the other field is
  required as well; croniter unions in that case. Both are defensible readings.
- Weekday steps: `7/2` starts at Sunday (0, 2, 4, 6) by gronx's comment, and an open step `N/S`
  runs to Saturday only (`5/2` is Friday alone; croniter agrees), while a closed `4-7/3` reaches
  Sunday as 7. `7-3` is Sunday to Wednesday but `7-3/1` is an error.
- `0/5` in the day and month fields (below their bounds) is accepted and means 5, 10, ...;
  croniter refuses it.
- `NW` with N beyond the month's length never fires in that month (Quartz leaves this open;
  croniter picks the last weekday instead).
- Names are replaced anywhere by an upper-casing string replace, so `MON` in the month field is
  January and `l`, `w`, `jan`, `@Weekly` all work; `SUNDAY` becomes `0DAY` and is an error.
- A tag need not start with `@`; `AddTag` joins the normalised segments, so a five-segment tag
  expands to six.
- At the default second precision fractional references are truncated for the search and the
  inclusive `PrevTickBefore` returns the truncated instant.

## Bugs found

Eleven, recorded in `bugs.toml` with a pin test each. Three medium: `BatchDue` ignores the
day-of-month/weekday union that `IsDue` applies (**gronx/1**); an out-of-range item is only
reported when the check reaches it, so `IsDue("0 0 * * 1,99")` errors on every day but Monday
and `IsValid`, which checks against the process start time, says true for `0 0 * * <today>,99`
(**gronx/2**); at a daylight-saving fall-back `NextTickAfter` lands on the second reading of the
wall clock and skips up to an hour of ticks (**gronx/9**); and when a day has no midnight
(America/Santiago's spring transition) `NextTickAfter` across it fails with "tried so hard"
(**gronx/10**). Low: impossible modifier values (`9#1`, `1#6`, `32W`, `0W`, `15L`) are valid
(gronx/3); a trailing newline makes an expression invalid (gronx/4); a tag with a capital letter
can never be used (gronx/5); the inclusive `NextTickAfter` returns the reference with its
fraction (gronx/6); a stepped year `2000/5` is "unreachable" (gronx/7); `AddTag` registers an
invalid expression (gronx/8); with the reference excluded, `NextTickAfter` and `PrevTickBefore`
return the reference itself when it is due and no other tick exists (gronx/11). All found on
2026-09-20 (turn 329). `IsDue` itself, the normalisation and the tick search in fixed-offset
zones agreed with the model and croniter throughout.

## History

- 2026-09-20 (turn 329): target created at `12c77ca` (v1.20.4); 11 bugs.
