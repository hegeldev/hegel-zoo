# json-iterator

[json-iterator/go](https://github.com/json-iterator/go) ("jsoniter") is the other widely used
drop-in replacement for Go's `encoding/json`: a hand-written iterator/stream core with reflection
codecs built on `modern-go/reflect2`, an `Any` lazy-access API, and a `Config` whose
`ConfigCompatibleWithStandardLibrary` "tries to be 100% compatible with standard library
behavior" (`EscapeHTML`, `SortMapKeys`, `ValidateJsonRawMessage`). About 9 000 lines. The pinned
commit is the September 2022 head, eight commits past v1.1.12, the last release; the project is
quiet but has 13 000+ stars and is a dependency of Kubernetes and much else. MIT, no
CONTRIBUTING.md and no AI policy at the pinned commit.

## Oracle

The standard library's `encoding/json`, in process, against `ConfigCompatibleWithStandardLibrary`
(bound to `json` in the test file so the calls read like the standard ones): byte-for-byte on
encoder output, `reflect.DeepEqual` on decoded values, the same verdict on validity. Two caveats:

- On the Go this ran with (1.27.1) `encoding/json` is implemented on top of `encoding/json/v2`.
  Where that layer is known to differ from the classic implementation (float map keys, raw
  U+2028/U+2029 with HTML escaping off, `More()` at EOF inside an unterminated container, tag
  names containing quotes, a `,string` integer written as `"05"`) nothing is recorded and the
  generators stay away; each case is listed under "Not bugs" below. Every recorded bug was
  checked against the classic semantics as well (the documented contract, RFC 8259, or
  behaviour json-iterator itself shows elsewhere).
- json-iterator's `MarshalIndent` prefix argument is documented as unsupported (it panics), its
  `Decoder` has no `Token` method, and there is no `Compact`/`Indent`; those are not compared.

## Properties

- `TestHegelMarshalMatchesEncodingJSON` — random values from a struct universe (`hgRich`:
  embedding, pointers, every integer width, both float widths, `,string` on integers and a
  string, `omitempty`, `[]byte`, a fixed array, slices of structs, maps with string / int32 /
  TextMarshaler keys, `Number`, `RawMessage`, Marshaler and TextMarshaler fields, `interface{}`,
  `-`, `-,`, an unexported field) and from `interface{}` trees; `Marshal`, `MarshalIndent` with a
  random space indent, an `Encoder` with random `SetEscapeHTML`/`SetIndent` encoding two values,
  and a `Config` with `EscapeHTML` off against `SetEscapeHTML(false)`: byte-identical output and
  the same error verdicts.
- `TestHegelUnmarshalIntoInterfaceMatchesEncodingJSON` — random valid texts rendered from a
  tree with random whitespace, random escape choices (`\uXXXX` in either case, surrogate pairs,
  lone low surrogates, `\/`, short escapes) and random number spellings; `Unmarshal` into
  `interface{}` and `Decoder.UseNumber` give exactly encoding/json's values, and `Valid` agrees.
- `TestHegelUnmarshalIntoStructsMatchesEncodingJSON` — encoding/json's own encoding of a random
  `hgRich`, re-rendered with random formatting and key order, sometimes upper-cased keys and
  optionally an unknown key: both libraries decode to the same struct, which re-encodes to the
  original; a `Decoder.DisallowUnknownFields` rejects exactly the texts with the unknown key.
- `TestHegelValidMatchesEncodingJSON` — random valid texts and texts with one mutation (a
  structural byte deleted, duplicated or inserted, a letter/digit/sign/backslash inserted, or
  the text truncated): `Valid` and the `Unmarshal` verdict (into `interface{}` and into
  `RawMessage`) agree with the oracle, and so does the decoded value when there is one.
- `TestHegelDecoderStreamMatchesEncodingJSON` — one to four values with random separators,
  optionally followed by garbage: the `Decode` sequence and `More()` match.
- `TestHegelMarshalUnmarshalRoundTrip` — json-iterator alone: `Unmarshal(Marshal(v))` re-encodes
  to the same bytes for the struct universe and for `interface{}` trees.

The generators draw the shape of every recorded bug by default (STYLE.md rule 11): indents of
any string, empty maps, containers as map values and container RawMessages under indentation,
trailing bytes and bare numbers at top level, big and out-of-range numbers, the `Decode` call
after the last value, raw Marshaler output, `\b`/`\f` and invalid UTF-8 on both sides, escapes
in struct texts, a bare `null` RawMessage, negative leading zeros, control characters after an
escape, a surrogate pair after a lone surrogate. The wide properties fail on the first shape
they meet, named in the failure message, and are listed in `[expected_failures]` mapped to the
basin the shrinker lands in (`Marshal` on /1, `UnmarshalIntoInterface` on /7,
`UnmarshalIntoStructs` on /30, `Valid` on /24, `DecoderStream` on /10, the round trip on /15).
`hegel_shapes_test.go` holds one narrow property per bug whose shape has random contents
(nineteen: /1-/10, /14-/16, /20, /21, /24, /30-/32), each a generator over that bug's region,
judged like the wide property that found it, so every one of them fails deterministically and
shrinks to a minimal example; the thirteen bugs whose shape is a single fixed input (/11-/13,
/17-/19, /22, /23, /25-/29) have pins only. `HEGEL_NO_KNOWN=1`, read once into a `Known`
struct, switches the shapes off: the wide generators stop drawing them, the narrow properties
draw the neighbouring region the bug does not touch, and all 25 properties pass at 3000 cases.
The 32 pins in `hegel_pins_test.go` are the regression examples. `JSONITER_COLLECT=1` makes
the properties record mismatches instead of failing and print them shortest-first - that is
how the list below was built, one collect run per generator change.

The run command carries `-vet=off`: Go 1.27's vet (run by `go test`) rejects a non-constant
format string in upstream's `example_test.go`, so the package would not build otherwise.

## Bugs (32; details in bugs.toml)

| id | summary | severity |
|----|---------|----------|
| json-iterator/1 | `MarshalIndent` panics on an indent that is not spaces (a tab) | medium |
| json-iterator/2 | `Encoder.SetIndent` uses `len(indent)` spaces instead of the string | low |
| json-iterator/3 | `MarshalIndent` writes an empty map as `{\n \n}` | low |
| json-iterator/4 | `MarshalIndent` with an empty indent is compact instead of line-broken | low |
| json-iterator/5 | Containers that are map values are not indented one level deeper | low |
| json-iterator/6 | `Valid` checks only the first value: `1 2`, `[1]]`, `truex` are valid | medium |
| json-iterator/7 | `Valid` rejects every bare top-level number (`0`, `-1`, `1.5`) unless whitespace follows | medium |
| json-iterator/8 | `Valid` rejects in-range `0.`-mantissa numbers above float32 range | low |
| json-iterator/9 | `Valid` rejects out-of-range numbers encoding/json calls valid | low |
| json-iterator/10 | `Decoder.Decode` after the last value returns a syntax error, not `io.EOF` | medium |
| json-iterator/11 | `Decoder.Decode` into a `RawMessage` after leading whitespace shifts the bytes | low |
| json-iterator/12 | An invalid `RawMessage` is marshalled as `null` (or verbatim) without error | medium |
| json-iterator/13 | An invalid `json.Number` is written verbatim, producing invalid JSON | medium |
| json-iterator/14 | Marshaler/`RawMessage` output is neither compacted, HTML-escaped nor re-indented | low |
| json-iterator/15 | Invalid UTF-8 in a Go string is written as `�` escapes | low |
| json-iterator/16 | `\b`/`\f` are written as ``/`` | low |
| json-iterator/17 | `map[bool]T` encodes as `{"true":…}` instead of an unsupported-type error | low |
| json-iterator/18 | `,string` is applied to slices and nil pointers | low |
| json-iterator/19 | A NUL byte after a value ends the input (`1\x00garbage` is valid) | medium |
| json-iterator/20 | Invalid UTF-8 in input strings is passed through, not replaced | low |
| json-iterator/21 | A lone surrogate escape before a valid pair corrupts the pair | low |
| json-iterator/22 | `null` clears string, `,string` string and `Number` fields | low |
| json-iterator/23 | `null` into a TextUnmarshaler value calls `UnmarshalText("")` | medium |
| json-iterator/24 | `null` into a `RawMessage` field stores nil, not `null` | low |
| json-iterator/25 | A type error zeroes the field instead of leaving it | low |
| json-iterator/26 | Decoding stops at the first type error | low |
| json-iterator/27 | A short JSON array leaves the rest of a Go array unchanged | low |
| json-iterator/28 | `,string` decoding is lenient (`" 5"`; `"5"` into a string gives `""`) | low |
| json-iterator/29 | Invalid quoted strings are accepted into `json.Number` | low |
| json-iterator/30 | `,string` numbers and integer map keys are read without unescaping | low |
| json-iterator/31 | `Valid` accepts `-00`, `-01`, `-.5` inside containers | low |
| json-iterator/32 | Raw control characters in a string pass once the string holds an escape | medium |

How they were found: the go-json harness (`targets/go/go-json`) was re-targeted in one step and
run in collect mode; the first run's mismatches, sorted shortest-first, pointed at /1, /3, /5,
/6, /7, /10, /14, /15, /16, /24 and /30 directly, and a series of hand-written probes over the
same shapes (indent strings, top-level literals, `null` into every field kind, type errors on a
prefilled struct, NUL bytes, invalid UTF-8 and surrogates, unsupported types, `,string` and
`Number` inputs) added the rest; /8 came out of the second collect run as `[0.25E+56]` and was
bisected over exponents to the float32 boundary; /11 fell out of the probe for /24; /31 and /32 were the
last property failures standing (`[-00]`, a tab inside an escaped string) once everything else
was guarded — the 1000-case runs kept finding one more shape after each collect run said zero.

## Not bugs (documented, ambiguous between the two encoding/json generations, or design)

- `MarshalIndent`'s prefix argument: "Prefix is not supported" is documented on the function,
  although panicking on it is unfriendly. Not passed.
- `Decoder.Token()` does not exist ("in progress" in the adapter's comment); `Compact` and
  `Indent` do not exist. Not compared.
- `ConfigDefault` and `ConfigFastest` differ deliberately (unsorted map keys, six-digit floats,
  unvalidated raw messages, unescaped object keys); only `ConfigCompatibleWithStandardLibrary`
  is tested.
- `map[float64]…` keys: json-iterator encodes them as Go 1.27's encoding/json does; classic
  encoding/json rejected them. Not generated.
- A raw U+2028/U+2029 in a string with HTML escaping off is written raw, as classic
  encoding/json did; Go 1.27's escapes it. Escaping stays on for values containing them.
- `More()` after `{` or `[` at end of input is false in json-iterator and classic encoding/json,
  true in Go 1.27's. Not generated.
- A tag name containing a `"` is used as-is by json-iterator and ignored by encoding/json here;
  the two encoding/json generations differ on such tags as well. Not generated.
- `"05"` into a `,string` integer: rejected by json-iterator, accepted by Go 1.27's encoding/json,
  rejected by classic ("invalid use of ,string struct tag"). Not asserted.
- A stream `-8.31.`: encoding/json's Decoder returns -8.31 and fails on the next call,
  json-iterator fails at once; a grammar ambiguity, not compared (the `1.` garbage suffix is
  left out of the stream property).
- Error messages and error types differ everywhere; only the presence of an error is compared.
- `Any`, `Get`, `RegisterExtension`, the naming/fuzzy-decode extensions under `extra/`, and the
  iterator/stream API itself are json-iterator's own and not covered.

## History

- 2026-09-14: written against 71ac16282d122fdd1e3a6d3e7f79b79b4cc3b50e with hegel v0.6.33;
  32 bugs.
- 2026-09-26: generators rewritten in combinator style (weighted choices, `chance`, `maybe`,
  case records rendered by pure functions, edits as mutation lists applied modulo the live
  size) and the known-bug steering turned off by default; `hegel_shapes_test.go` (nineteen
  narrow properties) and `hegel_pins_test.go` split out. The stream judge now tells `io.EOF`
  from an error, and `MarshalIndent`'s panic is reported as an error rather than crashing the
  run. Bug 7's notes widened: no bare top-level number passes `Valid` without trailing
  whitespace, unsigned integers included.
