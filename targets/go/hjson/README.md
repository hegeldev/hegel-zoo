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

## Properties

`TestHegelJSON`, `TestHegelParse`, `TestHegelRoundTrip`, `TestHegelTypedRoundTrip`,
`TestHegelNodeFixedPoint`, `TestHegelOrderedMap`, `TestHegelNodeAPI`.

## Bugs

Twelve, in `bugs.toml`. The parser combines no `\u` surrogate pairs (1); `Node.Insert` shadows
its return values (2); the encoder's single-line `'''` form loses leading whitespace (4) and
breaks the document for strings ending in a quote (5); quoteless strings are trimmed of Unicode
spaces the encoder does not quote (6); multi-line `comment` tags are split on `Eol`, so CRLF
output does not parse (7); a root string with a colon reads back as an object (9); a `Node`
round trip doubles the base indentation (3), doubles the CR of CRLF line ends (8) and adds a
blank line before a multiline string in an array (10); `1.` fails with "Internal error" into
`interface{}` but is 1 in a `Node` (11), and `1e400` is a string in a `Node` but an error into
`interface{}` (12).

## Modelled as recorded

- Strings: the models reproduce bugs 4, 5, 6 and 9 (`stringOutcome`); strings that break the
  document are skipped and counted.
- Node fixed point: the doubled base indentation (3, not for a braceless root object), the
  doubled CR (8, not on a key line whose bracket follows, not inside multiline strings — the
  latter and strings ending in a colon are skipped) and the blank line before a multiline
  string in an array (10; skipped when `IndentBy` is empty or a string ends in a line feed,
  where the layout is ambiguous).
- The typed round trip skips a multi-line `comment` tag under CRLF (7).
- The grammar model generates no `1.`-style numbers, no exponents beyond float64 and no root
  quoteless strings with a colon; surrogate pairs decode as two U+FFFD (1) in both decoding
  properties.

## Not tested

`ElemTyper`, `json.Marshaler`/`TextMarshaler` values in the encoder, `json.Unmarshaler`
destinations, `DisallowUnknownFields`, the struct field type hints for quoteless values in
nested and pre-filled destinations, the `hjson-cli` tool, the comment-carrying `Node` round
trip of hand-written documents (comments in every position), the nesting-depth limits.

## History

- 2026-09-21: created at v4.7.1 (`033fae8`); 12 bugs.
