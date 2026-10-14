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
installs it in its venv). The patch adds, as the external package `gronx_test`,
`hegel_zoo_idioms_test.go` (the generator idioms shared with the other rewritten Go targets:
weighted choices, fair-bit dice, halving helpers), `hegel_zoo_test.go` (the harness, the
collector, the `known` switch set, the judge and the classifier), `hegel_zoo_model_test.go`
(the expression model, the exact tick model in daylight-saving zones, the replica of gronx's
rules, and one `*Expected` function per property with the switch set threaded),
`hegel_zoo_cases_test.go` (the case records and their generators), `hegel_zoo_props_test.go`
(the seven wide properties), `hegel_zoo_shapes_test.go` (one narrow property per bug),
`hegel_oracle_test.go` (the croniter child) and `hegel_pins_test.go` (one plain test per bug),
and requires `hegel.dev/go/hegel v0.6.33` in go.mod (the `go` directive moves from 1.13 to
1.26.0 for it; gronx itself has no dependencies). `HEGEL_TEST_CASES`, `HEGEL_SEED` and
`HEGEL_VERBOSE` are passed through to the engine; `HEGEL_COLLECT=1` records mismatches instead
of failing and prints the counts per class; `HEGEL_NO_KNOWN=1` switches the known shapes off
(below).

## Oracles

- **A model of the documented grammar**, built from a structured record rather than parsed:
  per segment a list of items (`N`, `N-M`, `*/S`, `N/S`, `N-M/S`, names, `L`, `NW`, `NL`,
  `N#K`) with the bounds gronx documents (weekday 0-7 with 7 as Sunday, and gronx's readings of
  `7-x`, `x-7` and `7/s`), the normalisation (trim, whitespace runs, case, names anywhere, tags,
  a fourth digit run making the sixth segment a year), and validity. Wrong items are drawn
  deliberately (out of bounds, reversed, zero steps, garbage, modifiers in the wrong field, full
  names such as `SUNDAY`, extra range and step parts) and impossible modifier values (`9#1`,
  `32W`) as a class of their own.
- **A model of "due"**: the wall-clock fields against the sets, `L`/`W`/`nL`/`n#k` against the
  month's calendar, and the Vixie day rule gronx implements (both day segments restricted: either
  matches, unless the day-of-month starts with `*` or is `?` or the weekday starts with `*/`, in
  which case both must).
- **A model of the ticks**: in fixed-offset zones a day walk from the reference (up to 120 years
  each way) over the days the date fields accept, then the hour, minute and second sets in
  order, giving the earliest instant after (or at) the reference or "none". In zones with
  daylight saving the same walk is exact: on each day every due wall clock is mapped to an
  instant under each UTC offset in effect that day and kept when the instant reads that wall
  clock in the zone (a wall clock in a spring-forward gap gives none, one in a fall-back fold
  gives two); the earliest kept instant after the reference is the tick, the latest before it
  the previous one. The function was checked against a second-by-second search in a probe.
- **A replica of gronx's own rules** behind the switches: the segment walk of `SegmentsDue`
  (last segment first, the weekday's union skipping the day-of-month check), `CheckDue`'s
  item-by-item bail-out, `isSyntaxValid`, the modifier readings of `validator.go`, the
  `normalize` trim, and a transcription of `next.go`'s `loop`/`bump`/`bumpReverse` search with
  `time.Date` on wall-clock fields, carrying a trace of what it crossed (an ambiguous wall
  clock, a missing midnight, a stepped-over hour).
- **croniter** (Python, one persistent child) as a second voice on the subset both read the same
  way, asked once per case before the library: `match`, `get_next`, `get_prev` with
  `second_at_beginning=True` on gronx's normalised segments, compared with the model (a
  disagreement there is a model defect or a croniter difference, never a library failure). The
  subset leaves out what croniter reads differently or refuses: `?` (the reference's day in
  croniter), 7 as a weekday in lists and in the six-segment form, ranges via 7 and steps from 7,
  `0/s` below a field's bound, `W` beyond the 28th or in a list or beside a weekday, `n#k` beside
  literals or a day-of-month (croniter intersects the two day fields for modifiers, gronx
  unions), a stepped day-of-month with a weekday (croniter unions, gronx follows Vixie and
  intersects), `nL` (croniter writes `Ln`), single-value ranges (`16-16`, which croniter
  misreads), open steps `N/S` (croniter wraps them), year steps (counted from 1970 by croniter,
  from 0 by gronx), years outside 1970-2099, the union under a restricted year and a `*/s`
  day-of-month item beside a weekday covering the week (two readings found at the rewrite).

Cases are records drawn from package-level generators: an expression record (the mode - valid,
invalid, nonsense or tag at each property's share -, the written form at 50/20/13/17 percent
for five, six, six-with-year and seven segments, each segment a star at 45 percent (`?` a
quarter of the time in the day fields) or one to four items at 70/30 with the item kinds at
35/20/13/10/8/14 for a value, a range, `*/s`, `a/s`, `a-b/s` and a modifier, names at 30
percent, the whitespace between segments and around them, a trailing newline at 4 percent, the
letter case of names mixed), an instant record (years 2020-2032 at 80 percent else 1995-2090,
month ends and winter firsts, edge hours, a sub-second part at 30 percent where asked), the
five fixed zones or the five daylight-saving zones (New York, Berlin, London, Santiago, Lord
Howe; the reference within three hours of a transition 60 percent of the time), the batch as
one to six entries with a fifth of the later ones duplicates, the tag name as drawn letters
with a counter suffix (an upper-case alphabet a quarter of the time). Every weight is drawn
through the fair-bit dice of the idioms and the realised rate measured over 3000 cases in
context stands beside it; a share moves by up to five points between seeds at the same weight.
A case costs 125 to 450 draws on average, under 1400 at most (the batch).

## Method

| Property | Checks |
|---|---|
| ValidityFollowsTheGrammar | `IsValid` is true for every grammatical expression (and tag) and false otherwise, and `IsDue` errors on exactly the invalid ones; a wrong number of segments is always an error |
| SegmentsNormaliseAsDocumented | `Segments` gives the modelled six or seven segments for every written form, whitespace, case, name and tag |
| IsDueFollowsTheModel | `IsDue` equals the model at random instants and at instants the model says are due, in five fixed-offset zones, invalid and impossible items included; croniter's `match` agrees with the model on the shared subset |
| NextAndPrevTicksFollowTheModel | `NextTickAfter` and `PrevTickBefore`, including and excluding the reference, equal the model's earliest/latest due instant, come back in the reference's zone, and error when the model finds nothing; croniter's `get_next`/`get_prev` agree with the model on the shared subset |
| TicksInDSTZonesAreDueAndMinimal | in the five daylight-saving zones, around the transitions: `NextTickAfter` and `PrevTickBefore` equal the exact model's minimal instants |
| BatchDueAgreesWithIsDue | `BatchDue` over lists with duplicates, tags and invalid expressions gives each entry the model's answer, carrying the expression text |
| TagsExpandToTheirExpression | a tag added with `AddTag` is valid, has the expression's segments, is due and ticks when the expression does; a second `AddTag` is a conflict; an invalid expression is refused; built-in tags read in any case |
| thirteen narrow properties | one per bug (below): the bug's shape forced, the rest of the case drawn as in the wide property, judged by the same model |

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
- A `*/s` year item whose next tick lies beyond the model's horizon (year 9999) is not judged.

## Bugs found

Thirteen, recorded in `bugs.toml` with a pin test each. Three medium: `BatchDue` ignores the
day-of-month/weekday union that `IsDue` applies (**gronx/1**); an out-of-range item is only
reported when the check reaches it, so `IsDue("0 0 * * 1,99")` errors on every day but Monday
and `IsValid`, which checks against the process start time, says true for `0 0 * * <today>,99`
(**gronx/2**); at a daylight-saving fall-back `NextTickAfter` lands on the second reading of the
wall clock and skips up to an hour of ticks, and `PrevTickBefore` from the first reading returns
an instant after the reference (**gronx/9**); and when a day has no midnight (America/Santiago's
spring transition) `NextTickAfter` across it fails with "tried so hard" (**gronx/10**). Low:
impossible modifier values (`9#1`, `1#6`, `32W`, `0W`, `-1W`, `15L`) are valid (gronx/3); a
trailing newline makes an expression invalid (gronx/4); a tag with a capital letter can never be
used (gronx/5); the inclusive `NextTickAfter` returns the reference with its fraction (gronx/6);
a stepped year `2000/5` is "unreachable" (gronx/7); `AddTag` registers an invalid expression
(gronx/8); with the reference excluded, `NextTickAfter` and `PrevTickBefore` return the
reference itself when it is due and no other tick exists (gronx/11); extra range and step parts
are ignored, `1-2-3` passing `IsValid` as 1-2 and `5/2/1` refused by `IsValid` but run as 5/2
(gronx/12, found at the rewrite by the validity, due and batch properties); at Lord Howe's
half-hour spring-forward the hour bump steps over the half hour that exists and its ticks are
skipped (gronx/13, found at the rewrite by the exact tick model). Eleven found on 2026-09-20
(turn 329), two on 2026-10-14.

## Properties and the recorded bugs

The model states the documented behaviour; the `known` switch set (`type known [13]bool`, one
index per bug id, all off by default) turns a replica of the library's rule on in its place,
each transcribed from the lines of `gronx.go`, `checker.go`, `validator.go`, `next.go`,
`prev.go` and `batch.go` it follows. The classifier runs the model per switch on the case before
the library is called and names the first bug in id order whose switch alone changes the
expected checks (sufficiency), else the first whose switch is needed (necessity), else a hole;
every mismatch by default is a named shape and no named shape passes.

Over 3000 default cases the classifier names every mismatch by sufficiency (three by necessity
in the batch property) with the library agreeing with the replica in all of them: the validity
property 958 shapes (gronx/2 628, 3 258, 4 60, 12 12), the due property 663 (2 347, 3 256, 4
56, 12 4), the ticks property 589 (2 157, 3 247, 4 57, 6 118, 7 9, 11 1), the DST property 241
(9 126, 4 110, 10 5; 13 in none to two per 3000), the batch property 1281 (2 992, 1 200, 4 72,
12 17), the tag property 1288 (8 1051, 5 237; gronx/12 suffices in 65 of them, all also named
by 8). Where two switches suffice the first id wins, so gronx/12 is named only where gronx/2's
walk reaches its item, and the narrow properties of 2 and 8 draw a strict bad pool without the
extra-part texts. The wide properties shrink to the simplest failing alternative: over forty
rounds at a hundred cases the validity property reaches gronx/3 (31; `* * 0W * *`), the due
property gronx/3 (28), the ticks property gronx/6 (27; `* * * * *` at a fractional reference,
inclusive), the batch property gronx/2 (25; `* * 32 * *`) and the tag property gronx/8 (33;
`@a7v = * * 32 * *`), each failing every round; the segments property reaches gronx/4 in 35
rounds and passes the other five (the newline is drawn in four percent of the non-tag cases),
and the DST property gronx/9 in 31 (4 seven, 10 one), passing once. The thirteen narrow
properties force the shape with the rest of the case drawn as in the wide property, each named
as its bug in every case (the half-hour gap's reference is constructed in the half hour before
Lord Howe's transition, the extra-part item placed where the walk reaches it; rejections under
one percent). A default run takes two to three minutes on this machine under a foreign load
(most of it the twenty failing properties shrinking), a thousand cases under
`HEGEL_NO_KNOWN=1` about half a minute.

Under `HEGEL_NO_KNOWN=1` the shapes are off: the newline, the impossible modifiers, the
upper-case tag alphabet, the invalid expression in `AddTag`, the fraction on an inclusive
reference and the five extra-part texts are at weight zero (4, 3, 5, 8, 6, 12); the invalid
mode draws a lone bad item in a segment the walk reaches (2); a stepped year before the
reference, a lone tick on the reference, the ambiguous wall clocks, the missing midnights and
the half-hour gap are filtered out by the classifier (7, 11, 9, 10, 13; one percent of the tick
cases, five of the DST cases); in the batch property the union shape's due check is dropped
from the case and counted (1; five percent of cases). The narrow properties draw the region
past their shape and pass. The pins alone fail there.

## Shrinking

The simplest alternative comes first in every choice: the shrink target is `* * * * *` at
2020-01-01 00:00:00 UTC with the plainest mode of the property, so the shrunk cases read as
`* * 0W * *`, `* * * * *\n`, `* * 1-2-3 * *`, `@a7v = * * 32 * *`. The harness bounds a shrink
by a budget of failing judgements, since the engine keeps every attempt in memory; the budget
was never reached here.

## History

- 2026-09-20 (turn 329): target created at `12c77ca` (v1.20.4); 11 bugs.
- 2026-10-14: rewritten to the standard: the eleven `Known` gates on by default, which skipped
  each bug's shape, turned into thirteen switches off by default with a replica of gronx's rules
  and the classifier naming the shape; the generators as records in combinator style with
  measured rates; an exact tick model in daylight-saving zones in place of the minimality check,
  `PrevTickBefore` judged there too; croniter asked once per case before the library; the
  impossible and invalid items judged by the due and tick properties; thirteen narrow
  properties; gronx/12 and gronx/13 found and recorded; the notes of 3, 9 and 10 widened after
  standalone checks.
