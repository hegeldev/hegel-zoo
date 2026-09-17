# sonic

[bytedance/sonic](https://github.com/bytedance/sonic) is ByteDance's JIT- and SIMD-accelerated
JSON library for Go (9 600 stars, 2 400 importers; amd64 and arm64). Its `ConfigStd` API is the
"compatible with `encoding/json`" configuration (`EscapeHTML`, `SortMapKeys`,
`CompactMarshaler`, `CopyString`, `ValidateString`), and the project keeps its own
compatibility catalogue against Go 1.27 (`docs/sonic-go127-compatibility.md`,
`compatibility/`). The pin is v1.15.4 (`f1003e1`, 2026-09-10). Apache-2.0; AGENTS.md and
CONTRIBUTING.md describe the build, the test suites and the commit conventions and say nothing
about AI-written code; the zoo keeps its tests in its own patch and files nothing upstream.

## Build

`go test -count=1 -vet=off -run TestHegel -v .` in the module root (`-vet=off` because Go 1.27's
vet rejects an unexported tagged field in upstream's `decode_test.go`; `-run TestHegel` leaves
upstream's own suite alone). The patch adds `hegel_test.go` (properties) and
`hegel_pins_test.go` (one plain test per bug), requires `hegel.dev/go/hegel v0.6.33` in go.mod
and deletes upstream's `go.work`/`go.work.sum` (workspace mode refuses the zoo's
`GOFLAGS=-mod=mod`, and the root module is the only one under test). The JIT path is what runs
on the zoo's amd64 machine and in CI's `ubuntu` job.

## Oracle

The standard library's `encoding/json`, in process, against `sonic.ConfigStd` (bound to `api`
in the test file): byte-for-byte on encoder output, `reflect.DeepEqual` on decoded values, the
same verdict on validity. The harness is the zoo's json-iterator harness
(`targets/go/json-iterator`) re-targeted, with its json-iterator gates opened.

On Go 1.27 `encoding/json` is implemented on top of `encoding/json/v2`, and the classic
implementation is still available as `GOEXPERIMENT=nojsonv2`. Every collect round was run under
both, and only differences that show under both are recorded as bugs; shapes where the two Go
backends disagree with each other are listed under "Not bugs" and kept out of the generators.

## Properties

- `TestHegelMarshalMatchesEncodingJSON` — random values from a struct universe (embedding,
  pointers, every integer width, both float widths, `,string` on integers and a string,
  `omitempty`, `[]byte`, a fixed array, slices of structs, maps with string / int32 /
  TextMarshaler keys, `Number`, `RawMessage`, Marshaler and TextMarshaler fields,
  `interface{}`, `-`, `-,`, an unexported field) and from `interface{}` trees; `Marshal`,
  `MarshalIndent` with random prefix-less indents (spaces, tabs, empty, letters), an `Encoder`
  with random `SetEscapeHTML`/`SetIndent`, and a `Config` with `EscapeHTML` off against
  `SetEscapeHTML(false)`: byte-identical output and the same error verdicts.
- `TestHegelUnmarshalIntoInterfaceMatchesEncodingJSON` — random valid texts with random
  whitespace, escape choices (`\uXXXX` in either case, surrogate pairs, lone low surrogates,
  `\/`, short escapes) and number spellings: `Unmarshal` into `interface{}` and
  `Decoder.UseNumber` give exactly encoding/json's values, and `Valid` agrees.
- `TestHegelUnmarshalIntoStructsMatchesEncodingJSON` — encoding/json's encoding of a random
  struct, re-rendered with random formatting and key order, sometimes upper-cased keys and an
  unknown key: both libraries decode to the same struct, which re-encodes to the original;
  `DisallowUnknownFields` rejects exactly the texts with the unknown key.
- `TestHegelValidMatchesEncodingJSON` — random valid texts and texts with one mutation (a
  structural byte deleted, duplicated or inserted, a letter/digit/sign/backslash inserted, or
  the text truncated): `Valid` and the `Unmarshal` verdict agree with the oracle, and so does
  the decoded value when there is one.
- `TestHegelDecoderStreamMatchesEncodingJSON` — one to four values with random separators,
  optionally followed by garbage: the `Decode` sequence and `More()` match.
- `TestHegelMarshalUnmarshalRoundTrip` — sonic alone: `Unmarshal(Marshal(v))` re-encodes to the
  same bytes for the struct universe and for `interface{}` trees.

A `Known` switch per recorded bug gates the input shape: no `-0` in floats or number literals
(/1, /2), no `<>&` or U+2028/9 in the `,string` string field (/3), mutated texts with a
malformed escape are dropped (/4), no `]`/`}`/`,` garbage after a stream (/5, /6), a bare number
that is not the last value of a stream is wrapped in an array (/7, /8), no tab in the mutation
alphabet (/9). With everything gated the six properties run clean at 1000 cases × 3 (about 3 s)
under both Go backends; `SONIC_COLLECT=1` makes them record mismatches instead of failing and
print them shortest-first.

## Bugs (9; details in bugs.toml)

| id | summary | severity |
|----|---------|----------|
| sonic/1 | `-0` inside a container or struct field decodes as `+0` | low |
| sonic/2 | `omitempty` does not omit a `-0` float | low |
| sonic/3 | `,string` on a string field escapes `<>&`/U+2028/9 at the outer level only (the two libraries' outputs decode to different strings) | low |
| sonic/4 | `Valid` accepts malformed escapes (`\x`, `\u00x2`, `\u12`) that `Unmarshal` rejects | medium |
| sonic/5 | `Decoder.Decode` reads a stray `]`/`}` as no error, forever, never EOF | medium |
| sonic/6 | `Decoder.Decode` reports `io.EOF` for a stray comma or truncated literal, losing what follows (and the valid value before it) | medium |
| sonic/7 | A stream of whitespace-separated numbers loses values (`1 2 … 12` → 1, 10, 11, 12) or fails part way | high |
| sonic/8 | A number at the end of a read is taken as complete: a reader delivering small pieces splits numbers | medium |
| sonic/9 | `Valid` accepts raw control characters inside strings, which `Unmarshal` rejects | medium |

How they were found: the first collect round (500 cases, default backend) showed 74 marshal,
152 struct-decoding, 33 validity, 125 stream and 115 round-trip mismatches; the legacy-backend
run of the same round told apart the Go 1.27 drift (`,string` escaping is *not* drift — both
backends double the backslashes; the `omitempty` and `-0` shapes were also confirmed under
both). Hand probes over the stream shapes found /5–/8 (the collect messages only said "EOF" or
"differs"; printing the stream text and trying lengths from 12 to 26 bytes exposed the loss of
values and the reader-boundary split). /9 was the last property failure standing.

## Not bugs (documented, ambiguous between the two encoding/json generations, or design)

- The project's own catalogue (`docs/sonic-go127-compatibility.md`) lists its known
  differences from Go 1.27: error-time mutation of the destination, float and pointer map
  keys, `,string` pointer fields receiving `"null"`, invalid UTF-8 written as `�` escapes,
  method dispatch on named pointers, partial writes before an error, quoted `MarshalText` map
  keys, interface state after a type error, self-referential values, `AppendText`,
  `"00012"`/`"0x1_4p-2"` into `,string` numbers, map values merged instead of replaced,
  error wrapping and metadata. None of these are re-recorded here; the generators never
  produced them (no cyclic values, no failing Marshalers, no float map keys).
- `More()` after a value followed by a control character or letters (`1\x01`, `2e-0nul`) is
  false in sonic and true in encoding/json; both then fail. Every garbage suffix in the stream
  property starts with a space.
- A number directly followed by a number (`0.95464-6e-09`) is one malformed token to sonic and
  two values to encoding/json; not generated (separators are only dropped between values that
  are self-delimiting on both sides).
- Only the presence of an error is compared, never its type or message.
- `ConfigDefault` and `ConfigFastest` differ deliberately (unsorted keys, no HTML escaping, no
  string validation); only `ConfigStd` is tested. The `ast`/`Get` API, `Pretouch`, the
  `encoder`/`decoder` option packages and `unquote`/`utf8` are not tested.
