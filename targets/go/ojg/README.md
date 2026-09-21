# go/ojg

[ohler55/ojg](https://github.com/ohler55/ojg) ("Optimized JSON for Go") is a hand-written JSON
parser and validator, a JSON writer, a full JSONPath implementation (`jp`: Get, First, Has,
Locate, Set, Del, Remove, Modify, Walk, PathMatch, streaming `oj.Match`), the SEN notation
(JSON without commas and quotes), and the `alt` converters (Decompose/Dup, Generify, Diff,
Compare, Match, Checksum). Pinned at `cb591c2` (six commits after v1.28.6, 2026-09-18, MIT; no
AI policy in README, CHANGELOG or `.github`, no CONTRIBUTING).

## Build

The tests live in a new package directory `hegel/` of the upstream module and use the library
as a black box; `go.mod` gains `hegel.dev/go/hegel`. The run command is
`go test -count=1 -run TestHegel -v ./hegel`. No oracle outside Go is needed.

## Oracle

Values are ojg's "simple types" (nil, bool, int64, float64, string, `[]any`,
`map[string]any`), generated with edge cases (int64 limits, floats from awkward decimal
texts, strings with quotes, control characters, U+2028, an emoji, a BOM, `<&>`, keys with
spaces, quotes, dots and non-ASCII). A canonical string form with type tags compares them.

- Parsing: the model writes JSON text for a value with random whitespace, short and `\u`
  escapes (including surrogate pairs), `\/`, and number spellings (`%g`, `%e`, `%E`, `%f`, a
  `.0` appended to integral floats) so that the expected parse is known by construction, and
  `encoding/json` confirms the text is valid. Mutated texts (one or two random byte edits) are
  judged by `encoding/json`: `json.Valid` for a single document, a `json.Decoder` loop for the
  document streams `oj.Validate` accepts.
- Writing: `encoding/json` decodes what `oj` writes (ints and integral floats compared alike,
  since JSON does not tell them apart) and a token walk checks sorted keys.
- JSONPath: a brute-force evaluator over the value tree with RFC 9535 semantics (child, index
  with negatives, wildcard, descent, slice with Python bounds, union, filter with comparisons
  and existence; a filter on a non-object is Nothing), results compared as multisets;
  set/delete/remove edits modelled on a deep copy; the streaming matcher modelled with
  `PathMatch`'s coarseness (a slice matches every index, a negative index nothing).
- SEN and alt: round trips through the library's own writers and converters, with alt's
  default `OmitNil` (nil object members are dropped) applied to the expectation.

## Properties

- `TestHegelParse`: `ParseString`, `Parser.Parse`, `Load`, `Unmarshal` into an interface
  (float64 for every number, like `encoding/json`), `ValidateString` and `sen.Parse` on the
  model's text.
- `TestHegelWrite`: `JSON` (plain, indented, sorted), `Marshal`, `Write` are valid JSON with
  the value, sorted output has sorted keys, `Parse(JSON(v))` gives the value back.
- `TestHegelInvalid`: on mutated texts `Parse` agrees with `json.Valid` and `Validate` with the
  document-stream decoder (streams whose documents are not whitespace-separated, such as
  `7-9`, are skipped as a matter of taste).
- `TestHegelPath`: `Get`, `First`, `FirstFound`, `Has`, `Locate` (count, values, normalized
  paths accepted by `PathMatch`, `max`), `String()` and `BracketString()` reparse to an
  equivalent expression, `Normal`, `Walk` (all nodes and leaves), and `oj.MatchString` on the
  JSON of the data.
- `TestHegelPathEdit`: `Set`, `Del`, `Remove` through a path ending in a child, index,
  wildcard or union of an existing container, compared with the model's edit.
- `TestHegelSEN`: `sen.String`/`Bytes`/`Write` (plain and sorted/indented) parse back;
  `sen.Parse` reads the JSON of the value.
- `TestHegelAlt`: `Generify`+`Simplify`, `Dup`, `Decompose`, `Alter` with and without
  `OmitNil`; `Dup` is independent of the original; `Diff`/`Compare` empty exactly for equal
  values (nil members as absent); `Match` on the value and on key subsets; `Checksum` equal
  for equal values.

## Bugs

Eighteen, see `bugs.toml`: integers at the int64 limits parsed as `json.Number` (1);
`Validate` accepting unclosed arrays and objects (2); `Set` refusing to append to an existing
array although documented to add elements (3); `Del` erroring on an out-of-range index where
everything comparable is a no-op (4); the SEN writer leaving strings starting with `-` and the
words `null`/`true`/`false` unquoted (5, 6); `String()` of a descent followed by a bracket
fragment and `BracketString()` of any descent unparsable (7, 8); `Parse` accepting `1.` while
`Validate` rejects it (9); `Remove` with a union ignoring negative indices (10); `Get` panicking
on an empty array with a negative-step slice (11); negative-step slices clamping out-of-range
bounds onto the array (12); surrogate pair escapes not combined (13); union keys with a quote
or backslash rendered unescaped (14); `Locate` ignoring `max` for slices (15); `oj.Match`
not searching inside an element a descent matched, so `$..*` yields only top-level children (16) and only one callback for a filter matching
several elements, with the wrong path (17); a truncated literal before a comma (`[nul,1]`)
accepted by `Parse` and `Validate` with the value dropped (18).

## Modelled as recorded, not counted

- `Unmarshal` into an interface returns float64 for every number (`ForceFloat`, as
  `encoding/json` does); the other parsers return int64 for integers.
- `Parse` and `Validate` accept an empty or whitespace-only input (nil, no error); `Validate`
  accepts a stream of several documents (`1 2`, `null1`), the parsers only one; where two
  documents touch without whitespace the split differs (`7-9` is rejected).
- `alt.DefaultOptions` sets `OmitNil`, so `Dup`, `Decompose`, `Alter` and `Generify` drop
  object members whose value is nil; `Diff`, `Compare` and `Match` treat such members as
  absent (`{"b":null}` equals `{}`); explicit `Options{}` keeps them.
- `jp.PathMatch` and the streaming `oj.Match` have no data for a slice, so a slice matches
  every index and a negative index matches nothing; `Del`/`Set` refuse an expression ending
  with a slice or filter ("can not delete with an expression ending with a Slice") while
  `Remove` accepts slices.
- `jp.Walk` with `justLeaves` does not visit empty containers.
- SEN reads `.5` as the string ".5" (a token may start with '.').
