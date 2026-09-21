# hjson

[hjson/hjson-go](https://github.com/hjson/hjson-go) is the Go implementation of
[Hjson](https://hjson.github.io), "a user interface for JSON": JSON with comments (`#`, `//`,
`/* */`), optional commas, quoteless keys and strings, `'''` multiline strings and an optional
root object without braces. The package (`github.com/hjson/hjson-go/v4`, about 2 900 lines of
Go) has a hand-written parser (`decode.go`, `parseNumber.go`) that reads into `interface{}`,
typed values (through `encoding/json`), an `OrderedMap` or a comment-carrying `Node` tree, an
encoder (`encode.go`, `structs.go`) with options (`Eol`, `BracesSameLine`, `EmitRootBraces`,
`QuoteAlways`, `QuoteAmbiguousStrings`, `IndentBy`, `BaseIndentation`, `Comments`), `json` and
`comment` struct tags, and the `Node`/`OrderedMap` editing API. MIT; the pin is the tag
`v4.7.1` (`033fae8`, 2026-09-01). README and LICENSE are the only project documents (no
CONTRIBUTING, SECURITY or code of conduct; `.github` holds two workflows): nothing about
AI-written code.

## Build

`go test -count=1 -run TestHegel -v ./hegel` in the module root. The patch adds the package
`hegel/` (the models and the properties, one file per oracle, and `hegel_pins_test.go` with one
plain test per bug), requires `hegel.dev/go/hegel v0.6.33` in go.mod and raises the module's
`go` directive from 1.12 to 1.26.0 (generics in the harness).

## Oracles

- **encoding/json** on generated JSON texts: Hjson is a superset of JSON, so every JSON text
  (random whitespace, escape spellings including `\uXXXX` and surrogate pairs, number
  spellings, key order, duplicate keys) must decode through hjson — into `interface{}`, with
  `UseJSONNumber`, into a `Node` and into an `OrderedMap` — to the value `encoding/json` gives
  it, objects in first-occurrence key order with the last value of a duplicated key;
  `DisallowDuplicateKeys` rejects exactly the texts with a duplicated key.
- **A model of the Hjson syntax** ([hjson.github.io/syntax.html](https://hjson.github.io/syntax.html))
  written as a document generator: it writes random documents — quoteless strings (checked
  against the parser's rule that a value is a number or keyword only when its text up to the
  next punctuator, comment or line end says so), single- and double-quoted strings with
  escapes, `'''` multiline strings with their indentation rules, numbers, keywords, objects with
  quoteless and quoted keys, arrays, commas or line ends as separators, trailing commas,
  comments of the three kinds between tokens, a braceless root — and the value each denotes.
- **Round trips**: `MarshalWithOptions` then `Unmarshal` over JSON-shaped values and a struct
  with fields of every supported kind (`json` tags, `omitempty`, `-`, `-,`, `comment` tags, an
  embedded struct) under every encoder option, up to a model of the string quoting rules
  (`stringOutcome`: which strings are written quoteless, quoted, escaped or as a multiline
  string, and what comes back). With `QuoteAmbiguousStrings` off, strings that spell a number or
  a keyword are ambiguous by design and skipped.
- **The Node fixed point**: the encoder's own output, read into a `Node` (whitespace and
  comments kept, or not) and encoded again with the same options, is the same text (the README:
  "an Hjson document can be read and written without altering the layout").
- **A sequence model** (an ordered list of pairs) of `OrderedMap` and of the `Node` editing and
  lookup methods (`Insert`, `Set`/`SetKey`, `Append`, `SetIndex`, `DeleteIndex`, `DeleteKey`,
  `AtIndex`, `AtKey`, `NI`, `NK`, `NKC`, `Len`) with their documented return values and errors,
  on object and array nodes.
- **encoding/json on typed destinations**: a generated Hjson object (quoteless, quoted and
  multiline values, arrays, objects, keys in several spellings, unknown and duplicate keys)
  decodes into a possibly pre-filled struct with fields of every kind (`string`, `*string`,
  numbers, `bool`, `json.Number`, `interface{}`, slices, arrays, maps, a `TextUnmarshaler`
  type, nested and embedded structs, `ElemTyper` types, a `json` tag) exactly as encoding/json
  decodes the JSON text in which each quoteless token is a string when its destination is
  string-typed (README: "A string destination will receive a string even if the quoteless
  string also was a valid number, boolean or null") and the raw token otherwise; with
  `UseJSONNumber` and `DisallowUnknownFields` too.
- **encoding/json on Marshaler values**: a value with `json.Marshaler` and
  `encoding.TextMarshaler` parts (value and pointer receivers, direct, behind pointers, in
  struct fields, lists and maps, as map keys) marshals to Hjson that decodes to what
  encoding/json writes for it; a failing `MarshalJSON` fails `Marshal`; maps with
  `TextMarshaler` keys are written in key order.
- **Comment round trips**: a hand-written document of the grammar model (comments of the three
  kinds wherever the syntax allows them, optional commas, braceless root, multiline strings),
  read into a `Node` (whitespace kept as comments, or comments only) and written with its
  comments, denotes the same value (up to the recorded string bugs, `expectedDecode`); the
  written text, read and written once more, does not change again (checked for documents
  without CR or multiline strings; trailing blanks on a line do not count).

## Properties

`TestHegelJSON`, `TestHegelParse`, `TestHegelRoundTrip`, `TestHegelTypedRoundTrip`,
`TestHegelNodeFixedPoint`, `TestHegelOrderedMap`, `TestHegelNodeAPI`, `TestHegelTypedHints`,
`TestHegelMarshalers`, `TestHegelCommentRoundTrip`.

## Bugs

Nineteen, in `bugs.toml`. The parser combines no `\u` surrogate pairs (1); `Node.Insert` shadows
its return values (2); the encoder's single-line `'''` form loses leading whitespace (4) and
breaks the document for strings ending in a quote (5); quoteless strings are trimmed of Unicode
spaces the encoder does not quote (6); multi-line `comment` tags are split on `Eol`, so CRLF
output does not parse (7); a root string with a colon reads back as an object (9); a `Node`
round trip doubles the base indentation (3), doubles the CR of CRLF line ends (8) and adds a
blank line before a multiline string in an array (10); `1.` fails with "Internal error" into
`interface{}` but is 1 in a `Node` (11), and `1e400` is a string in a `Node` but an error into
`interface{}` (12). The encoder never calls a pointer-receiver `MarshalJSON` or `MarshalText`
(13) and sorts `TextMarshaler` map keys by their Go value rather than their text (15); the
type hint that keeps a quoteless number a string is missing for `TextUnmarshaler` slice
elements, map values and fields behind a nil pointer (14) and for keys encoding/json folds onto
a field but `strings.ToLower` does not (16). Reading comments into a `Node` and writing them
back doubles a comment after a root scalar (17) and turns a multiline string after a key comment
ending in a line feed into a differently indented one that reads back changed (18). A string
spelling a number beyond float64 is written quoteless, and the text then fails to read into
`interface{}` (19).

## Modelled as recorded

- Strings: the models reproduce bugs 4, 5, 6, 9 and 19 (`stringOutcome`); strings that break
  the document are skipped and counted.
- Node fixed point: the doubled base indentation (3, not for a braceless root object), the
  doubled CR (8, not on a key line whose bracket follows, not inside multiline strings — the
  latter and strings ending in a colon are skipped) and the blank line before a multiline
  string in an array (10; skipped when `IndentBy` is empty or a string ends in a line feed,
  where the layout is ambiguous).
- The typed round trip skips a multi-line `comment` tag under CRLF (7).
- The typed-hints model gives no string hint to pointer-receiver `TextUnmarshaler` elements,
  map values and fields behind a nil pointer (14) and looks fields up by `strings.ToLower` (16);
  the Marshaler model replaces pointer-receiver marshalers by their fields (13) and sorts
  `TextMarshaler` map keys by `fmt %v` of the key (15).
- The comment round trip skips the fixed-point check for a root scalar with trailing comments
  or whitespace (17) and skips documents with a multiline string after a comment or a kept
  line end (18).
- The grammar model generates no `1.`-style numbers, no exponents beyond float64 and no root
  quoteless strings with a colon; surrogate pairs decode as two U+FFFD (1) in both decoding
  properties.

## Not tested

`json.Unmarshaler` destinations, the `hjson-cli` tool, the nesting-depth limits, the
`Marshal`/`Unmarshal` of `Node` trees inside other values, the exact comment placement of the
`Node` round trip (only the value and the fixed point are checked).

## History

- 2026-09-21: created at v4.7.1 (`033fae8`); 12 bugs.
- 2026-09-21: typed destinations (`TestHegelTypedHints`) and Marshaler values
  (`TestHegelMarshalers`); bugs 13-16.
- 2026-09-21: comment round trips of hand-written documents (`TestHegelCommentRoundTrip`);
  bugs 17-19.
