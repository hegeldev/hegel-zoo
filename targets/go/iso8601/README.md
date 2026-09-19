# iso8601

[relvacode/iso8601](https://github.com/relvacode/iso8601) (MIT), pinned at `4ea8ed45` (v1.8.0 plus
one commit, 2026-08-17): a hand-written ISO 8601 date-time parser (`Parse`, `ParseInLocation`,
`ParseISOZone`) and a `Time` wrapper for JSON.

The patch adds `hegel_test.go` (package `iso8601_test`) and the `hegel.dev/go/hegel` requirement
to `go.mod`. The oracle is a model of the grammar the parser documents - calendar dates
`YYYY[-MM[-DD]]`, ordinal dates `YYYY-DDD`, times `[T ]hh[:mm[:ss[.f]]]` with up to nine fraction
digits, zones `Z`, `+-hh`, `+-hhmm`, `+-hh:mm` - extended with the parser's evident lenience (any
number of digits per component, an empty trailing time component reading as 0, a zone directly
after an ordinal date), so that every accepted input must yield exactly the time its digits spell
and everything else must be refused with the documented error kind.

## What is tested

- `TestHegelValidDatesParseToTheirComponents` - generated valid strings (canonical and lenient
  digit counts, all date and time forms, all zone forms) parse to `time.Date` of their components
  through the four entry points; `ParseInLocation` uses the given location only when the input has
  no zone; Go's RFC 3339 formatting of the result re-parses to the same instant; the JSON wrapper
  agrees.
- `TestHegelParserFollowsTheModel` - valid strings mutated by up to three random edits (replace,
  insert, delete, truncate, append zone-like tails): acceptance, value, and the error kind
  (`UnexpectedCharacterError` vs `*RangeError` with its `Element`, `Given`, `Min`, `Max`, `Value`)
  against the model.
- `TestHegelZoneOffsetsFollowTheirDocumentation` - `ParseISOZone` on valid, mutated and random
  zone strings against the documented forms with hours 0-23, minutes 0-59 and no negative zero.
- `TestHegelJsonWrapperFollowsEncodingJson` - `null`, valid and mutated strings, short random
  strings and non-string values through `encoding/json` into `iso8601.Time` and `*iso8601.Time`:
  null leaves the value alone, strings parse (or fail as `Parse` does), other values give
  `ErrNotString`; `Marshal` round trips.
- `TestHegelRfc3339SubsetAgreesWithTimeParse` - RFC 3339 strings with in- and out-of-range fields
  agree with `time.Parse(time.RFC3339Nano)` on acceptance and value.
- `TestHegelPin...` - one plain test per recorded bug.

## Bugs

See `bugs.toml`: a leading `Z` is skipped like a `+` sign (1); `ParseISOZone` accepts malformed
and out-of-range offsets such as `+013`, `+01:`, `+25:00`, `+01:60` (2); more than nine fraction
digits with leading zeros are read as nanoseconds unscaled (3); `0000` alone fails with a month
range error (4); `Time.UnmarshalJSON`'s null test uses `&&` for `||`, so four-byte strings like
`"1l"` are silently treated as null (5).

## Notes

- Lenience that is deliberately modelled, not reported: components of any digit count
  (`2020-1-2T3:4`), an empty trailing time component (`2020-01-02T`, `...T10:`), a zone right
  after an ordinal date (`2020-032Z`, while `2020-01-02Z` is refused), `-00:00` refused as
  `ErrInvalidZone`, the empty string and `2020-` reported as "month 0 is not in range".
- Lowercase `z` is accepted by `ParseISOZone` but not by `Parse`; the model follows `Parse`.
