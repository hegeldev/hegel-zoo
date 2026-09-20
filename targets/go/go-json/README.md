# go-json

[goccy/go-json](https://github.com/goccy/go-json) is a "fast JSON encoder/decoder compatible
with encoding/json for Go", one of the two widely used drop-in replacements for the standard
library (the other is json-iterator). It compiles per-type opcode programs for the encoder and
decoder, re-exports encoding/json's `Number`, `RawMessage`, `Delim`, `Token`, `Marshaler`,
`Unmarshaler` and the error types, and adds context-aware variants, options (`UnorderedMap`,
`DisableHTMLEscape`, `DisableNormalizeUTF8`, `DecodeFieldPriorityFirstWin`, debug and colour
output) and a JSON-path API. About 10 000 lines at top level plus 14 000 in `internal/`; the
pinned commit is the July 2026 head, six commits past v0.10.6. MIT, no AI policy.

## Oracle

The standard library's `encoding/json`, in process: the README's promise of compatibility makes
every byte of encoder output, every decoded value and every valid/invalid verdict comparable
directly. Two caveats, both handled in the tests:

- On the Go this ran with (1.27.1) `encoding/json` is implemented on top of `encoding/json/v2`.
  Where that layer is known to differ from the classic implementation (float and bool map keys,
  U+2028 inside a `RawMessage` with HTML escaping off, `More()` at EOF inside an unterminated
  container, tag names containing quotes) nothing is recorded and the generators stay away;
  each such case is listed under "Not bugs" below. Every recorded bug was checked against the
  classic semantics as well (the documented contract, RFC 8259, or behaviour go-json itself
  shows elsewhere).
- Go 1.27.1's `encoding/json.Indent` loops forever on at least one invalid input with a
  non-empty prefix and an empty indent (the mutated text
  `"\t\r [[\n [-0],\r\n\r{\"&\\u005B\":\n  \"à\\u0022\",\"\":63721660033986015349.584769,\t\n\"\u2029日本\":true \n\r,\"-0Ȥ\":-356165845450043768.3E+32}],fal:se,\"Ĥᆕÿÿ\",\",\\/\\f\"\n ]"`
  with prefix `"\n"`), so the Indent comparison only calls the oracle on texts it considers
  valid; for the others its contract is simply an error. Not a go-json matter, but worth a
  report to Go.

## Properties

- `TestHegelMarshalMatchesEncodingJSON` — random values from a struct universe (`hgRich`:
  embedding, pointers, every integer width, both float widths, `,string` on integers and a
  string, `omitempty`, `[]byte`, a fixed array, slices of structs, maps with string / int32 /
  TextMarshaler keys, `Number`, `RawMessage`, Marshaler and TextMarshaler fields, `interface{}`,
  `-`, `-,`, an unexported field) and from `interface{}` trees; `Marshal`, `MarshalIndent` with
  random prefix/indent, an `Encoder` with random `SetEscapeHTML`/`SetIndent` encoding two values,
  and `MarshalWithOption(DisableHTMLEscape)` against `SetEscapeHTML(false)`: byte-identical
  output and the same error verdicts.
- `TestHegelUnmarshalIntoInterfaceMatchesEncodingJSON` — random valid texts rendered from a
  tree with random whitespace, random escape choices (`\uXXXX` in either case, surrogate pairs,
  lone low surrogates, `\/`, short escapes) and random number spellings; `Unmarshal` into
  `interface{}` and `Decoder.UseNumber` give exactly encoding/json's values, and `Valid` agrees.
- `TestHegelUnmarshalIntoStructsMatchesEncodingJSON` — encoding/json's own encoding of a random
  `hgRich`, re-rendered with random formatting and key order and optionally an unknown key:
  both libraries decode to the same struct, which re-encodes to the original; a
  `Decoder.DisallowUnknownFields` rejects exactly the texts with the unknown key.
- `TestHegelValidCompactIndentMatchEncodingJSON` — random valid texts and texts with one
  structural mutation (a bracket, brace, comma, colon, quote or blank deleted, duplicated or
  inserted): `Valid`, `Compact` and `Indent` agree with the oracle on verdict and output.
- `TestHegelDecoderStreamMatchesEncodingJSON` — one to four values with random separators,
  optionally followed by garbage: the `Decode` sequence, `More()` and the `Token` sequence match.
- `TestHegelMarshalUnmarshalRoundTrip` — go-json alone: `Unmarshal(Marshal(v))` re-encodes to
  the same bytes for the struct universe and for `interface{}` trees.

The generators avoid the pinned shapes and say where: floats in [1e-9, 1e-6) (go-json/13),
`\b`/`\f` on the encode side (/23), map keys that need escaping, are empty or contain bytes
below `"` (/14), zero-length arrays under `omitempty` (/15), pointer-receiver Marshalers in
arrays (/16), trailing whitespace for `Indent` (/18), out-of-range numbers (/22), mutations
that would split a number or an escape or leave a value before a stray bracket or after a
leading comma (/7, /10, /24), and optional escapes in the text given to the stream `Decoder`
(/25). All six pass at 1000 cases × 10 (about 3 s); 25 pinned expected failures. The run
command carries `-vet=off` because Go 1.27's vet rejects three upstream test files (printf
checks), which would otherwise fail the build of the test binary.

## Bugs (25)

| id | title | severity |
|----|-------|----------|
| go-json/1 | Unmarshal of `null` into a TextUnmarshaler value zeroes the first machine word of the value (a string field is left dangling; reading it crashes) | high |
| go-json/2 | Integers outside int64/uint64 wrap around silently: 9223372036854775808 into int64 gives -9223372036854775808 with a nil error; 3.5e38 into float32 becomes +Inf | medium |
| go-json/3 | float32 NaN and ±Inf are written as the bare tokens `NaN`, `+Inf`, `-Inf` (invalid JSON) with a nil error | medium |
| go-json/4 | A NUL byte ends the input: `1\x00garbage` is accepted by Unmarshal, Valid, Compact and Indent | medium |
| go-json/5 | Case-insensitive key matching only works for structs with at most sixteen fields | medium |
| go-json/6 | Integers in string form (`,string` fields, integer map keys) are parsed by prefix and misread leading zeros: `"1e2"` → 1, `"5x"` → 5, `"05"` → 0, `"+5"` rejected | medium |
| go-json/7 | Lenient number grammar: leading zeros, a trailing dot and a lone `-` are accepted | medium |
| go-json/8 | An unquoted `null` is accepted as an object key and becomes `""` | medium |
| go-json/9 | A nil pointer to a TextMarshaler marshals at top level as `""` instead of `null` | low |
| go-json/10 | The stream Decoder accepts truncated literals at EOF (`tru` → true), skips a leading `,`/`:` and accepts `\u` escapes with non-hex digits; Valid inherits it | medium |
| go-json/11 | Raw control characters inside strings are accepted by Unmarshal, Valid, Compact and Indent | low |
| go-json/12 | Compact and Indent do not validate escape sequences | low |
| go-json/13 | Exponents are zero-padded: `1e-07` where encoding/json writes `1e-7` | low |
| go-json/14 | Map keys are sorted by their quoted, escaped encoding, not by the key | low |
| go-json/15 | `omitempty` does not omit a zero-length array | low |
| go-json/16 | Non-addressable array elements get their pointer-receiver MarshalJSON called | low |
| go-json/17 | HTMLEscape decodes and re-encodes instead of escaping in place; no output on invalid input | low |
| go-json/18 | Indent drops trailing whitespace | low |
| go-json/19 | Decoding stops at the first UnmarshalTypeError instead of filling the rest | low |
| go-json/20 | `null` into a json.Number is an error | low |
| go-json/21 | `null` into a []byte keeps the old value | low |
| go-json/22 | Valid, Compact and Indent reject well-formed numbers outside float64 range | low |
| go-json/23 | `\u0008`/`\u000c` where encoding/json (Go ≥ 1.22) writes `\b`/`\f` | low |
| go-json/24 | A stray `]`/`}` after a top-level value is fine for Valid and Decoder.Token | low |
| go-json/25 | The stream Decoder fails on valid input when a `\uXXXX` escape in a struct key straddles its buffer refill | medium |

Most came out of a hand-written differential probe of edge cases run before the properties
(/2–/4, /6–/9, /11–/13, /15–/22); the properties themselves added /14's prefix-key and
empty-key cases, /23, /24, the `\u` part of /10 and /25 (from the struct property's
`DisallowUnknownFields` half, which failed only for documents longer than 512 bytes); /1 was
found when the probe harness itself crashed reading a value go-json had decoded; /5 showed up
as a 17-field struct in the probe behaving differently from an 8-field one.

## Not bugs (documented, ambiguous between the two encoding/json generations, or design)

- `UnorderedMap`, `DisableNormalizeUTF8`, `DecodeFieldPriorityFirstWin`, `Colorize`, `Debug`:
  options that deliberately diverge; not exercised.
- Invalid UTF-8 in a string is written as the escape `\ufffd`, where encoding/json writes the
  raw U+FFFD bytes; documented on `DisableNormalizeUTF8`, and the two decode identically. The
  generators produce valid UTF-8 only.
- `map[float64]…` and `map[bool]…` are "unsupported type" in go-json, as in classic
  encoding/json; Go 1.27's encoding/json accepts them. Not generated.
- A raw U+2028/U+2029 inside a `RawMessage` is copied through with HTML escaping off, as classic
  encoding/json did; Go 1.27's escapes it. The generators spell those two as `\u2028`/`\u2029`
  inside raw messages.
- `More()` after `{` or `[` at end of input is false in go-json and classic encoding/json, true
  in Go 1.27's. Not generated.
- The `omitzero` tag option (Go 1.24) is not implemented (go-json's go.mod says 1.19); a struct
  tagged `omitzero` encodes the field. Not recorded as a bug and not generated.
- A tag name containing a `"` (`json:"k e\"y"`) is used as-is by Go 1.27's encoding/json and
  ignored by classic (invalid tag → field name); go-json ignores it. Not generated.
- Error messages and error types differ (go-json returns its own `SyntaxError` for out-of-range
  numbers where encoding/json returns `UnmarshalTypeError`, `errors.errorString` for some stream
  EOFs); only the presence of an error is compared.
- `InputOffset()` after a `Decode` that hit EOF counts the trailing whitespace in go-json and
  not in encoding/json; `Buffered()` after a stream error is empty in go-json. Not compared.
- `Marshal` of a `Marshaler` returning ` 3 ` compacts to `3` in both; both reject `{oops`.
- The nesting limit of 10 000 is the same in both.
- `MarshalNoEscape`, `UnmarshalNoEscape`, the `*Context` variants, `path.go`/`query.go` (JSON
  path and field queries) and the colour/debug output are not covered.
- 2026-09-20: base bumped f1e755401429 → 15fe6a58bfc7 (2026-09-21, "Add bench-check task to fail CI on performance degradation (#623)"; v0.10.6+); 25 bug(s) still reproduce. 177 tests pass.
