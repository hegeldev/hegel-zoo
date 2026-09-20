# golang-ical

[arran4/golang-ical](https://github.com/arran4/golang-ical) reads and writes iCalendar
(RFC 5545) in Go (about 400 stars; the usual choice for producing `.ics` feeds and invitations
from Go services): `ParseCalendar` over a folded content-line stream, a `Calendar` of typed
components (`VEvent`, `VTodo`, `VJournal`, `VFreeBusy`, `VTimezone` with `Standard`/`Daylight`,
`VAlarm`, and `GeneralComponent` for the rest) holding `IANAProperty` values with parameters,
setters and getters for the common properties (times in the DATE, floating, UTC and TZID forms,
durations, attendees, categories, recurrence rules), `Serialize` with a configurable line length
and line ending, and an `RRULE` parser/printer. The pin is `1cf2929` (2026-08-18, tag v0.3.6).

The repository has LICENSE (Apache-2.0) and CONTRIBUTING.md (lint and tests); no agent
instructions, nothing about AI-written code. The zoo keeps its tests in its own patch and files
nothing upstream.

## Build

`go test -count=1 -run TestHegel -v .` in the module root, with `python3` on PATH able to
`import icalendar` (icalendar 7.3.0, with python-dateutil and tzdata; the setup command checks
the import). The patch adds `hegel_test.go` (harness, the model, generators, the API builder,
the RFC writer and the three serialization/parsing properties), `hegel_api_test.go`
(recurrence rules, time getters, the property API), `hegel_oracle_test.go` (the icalendar
child) and `hegel_pins_test.go` (one plain test per bug), all in the external package
`ics_test`, and requires `hegel.dev/go/hegel v0.6.33` in go.mod (the `go` directive moves from
1.20 to 1.26.0 for it).

## Oracles

- **A model calendar.** Components with a name, an ordered list of properties (name, sorted
  parameters with one or two values, the logical unescaped value) and children, generated
  from the RFC's property list (TEXT properties with any characters including `, ; \ "` and
  newlines, typed properties with valid DATE-TIME, DURATION, URI, GEO, RRULE ... values,
  X- and unknown names as TEXT) and the RFC's component nesting (alarms in events and to-dos,
  STANDARD/DAYLIGHT in time zones, X- components anywhere). The model is built through the
  API (`NewCalendarWithOptions`, the constructors, `AddProperty`, the `Components` slices) or
  written by the harness in RFC 5545 syntax: TEXT escaping, parameters quoted when they contain
  `: ; ,` or at random, folding at arbitrary octet counts (never inside a character) with space
  or tab continuations, CRLF or LF, blank lines, sometimes lower-case names.
- **RFC 5545 as read by icalendar 7.3.0** (Python): `Contentlines.from_ical` unfolds and
  `Contentline.parts()` splits names, parameters and values (unescaped), `vRecur.from_ical`
  parses RRULE values and `vDDDTypes.from_ical` DATE/DATE-TIME values with a TZID. A
  persistent child answers JSON requests over a pipe.
- **The documented API semantics as a model**: `AddProperty` appends, `SetProperty` replaces
  the first match, `ReplaceProperty`/`RemoveProperty`/`RemovePropertyByValue` return what they
  remove, the getters; RRULE fields (INTERVAL defaulting to 1, `+` ordinals absorbed) and the
  canonical `String()` order; times via `time.Date` in the TZID's location, `time.Local` for
  floating values, UTC for `Z`.

## Method

| Property | Checks |
|---|---|
| SerializeParsesBack | an API-built model, `Serialize(WithLineLength(16..200), WithNewLine(LF or CRLF))`: every line within the limit and valid UTF-8 on its own, `ParseCalendar` reads the model back; `Serialize()` equals the 75/LF form |
| IcalendarReadsTheOutput | icalendar's content lines of that serialization, assembled by BEGIN/END, are the model (names, parameters, unescaped values) |
| ParsesLikeIcalendar | the harness's RFC text: icalendar reads the model (a check of the writer), `ParseCalendar` reads the model, and the parsed calendar's `Serialize` is read by icalendar as the model again |
| RecurrenceRulesFollowTheModel | generated RRULE values (parts in any order, `+`/`-` ordinals, WKST, UNTIL in each form) parse to the modelled fields, `String()` is canonical and re-parses equal, `vRecur` agrees part by part; out-of-range values and lower case are gated |
| TimesFollowTheModel | DTSTART/DTEND/DUE/DTSTAMP/RECURRENCE-ID and EXDATE/RDATE lists in the DATE, floating and UTC forms with or without TZID (six IANA zones and an unknown one) read back as the model's instant in the model's zone or fail; malformed values fail; `vDDDTypes` agrees on kind, wall clock and zone |
| PropertyEditsFollowTheModel | random sequences of Add/Set/Replace/Remove/RemoveByValue and the typed setters against the model list, with GetProperty/GetProperties/HasProperty after each step and a serialize/parse round trip at the end |

Mismatches are classified before they count: a `Known` switch per recorded bug gates the input
shape (parameter values with `: ; , " ' \`, lower-case names, CATEGORIES/RESOURCES lists after
a parse, out-of-range RRULE values, floating UNTIL on `String()`, `RemovePropertyByValue`);
the pins assert the correct behaviour and fail while the bug exists. `ZOO_COLLECT=1` records
mismatches instead of failing and prints the class counts.

## Accepted differences

- The harness writer never puts a backslash in a parameter value: RFC 5545 has no escaping
  there, but both golang-ical (bug 5) and icalendar treat `\\`, `\,` and `\;` as escapes, so
  neither is an oracle for it. Empty second values in a parameter list and blank-padded
  parameter values are not generated either (icalendar drops or trims them).
- A DATE value with a TZID parameter (forbidden by the RFC) is sent to icalendar without the
  parameter; golang-ical reads it as midnight in that zone, which the model accepts.
- Line lengths below 16 are not requested: BEGIN and END lines are written unfolded and
  `BEGIN:VCALENDAR` is 15 octets. `+1MO` ordinals, duplicate RRULE parts (last wins), an empty
  trailing list value `A=1,` and `20240101Z` (a golang-ical extension icalendar rejects) are
  accepted or not generated.

## Bugs found

Fourteen, in bugs.toml: `ComponentPropertyExtended` returns "X-X-" for every name;
`RemovePropertyByValue`/`RemovePropertyByFunc` invert their condition and remove everything
else; `Id()` unescapes twice; parameter values are backslash-escaped instead of quoted, which
icalendar rejects; a backslash inside a quoted parameter is dropped; CATEGORIES/RESOURCES
lists come out of a parse/serialize round trip with `\,`; `Serialize` hangs when a character
does not fit the line length; names are matched case-sensitively; error line numbers count
content lines; the REFRESH-INTERVAL token carries its parameter; `VTodo.SetDuration` ignores
an all-day start; `String()` appends Z to a floating UNTIL; RRULE ranges are unchecked; names
are found by an unanchored search.

## History

- 2026-09-20 (turn 332): target added at v0.3.6 with six properties, fourteen pins.
