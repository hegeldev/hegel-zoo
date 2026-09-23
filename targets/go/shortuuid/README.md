# shortuuid

[lithammer/shortuuid](https://github.com/lithammer/shortuuid) (module
`github.com/lithammer/shortuuid/v5`) encodes UUIDs as short base-57 strings (or over any
alphabet), compatible with the Python `shortuuid` library: `NewEncoder`, `Encoder.Encode` /
`Decode`, `DefaultEncoder`, `New`/`NewV4`/`NewV7`/`NewV5`, `UUIDv5`, and the deprecated
`NewWithNamespace`, `NewWithAlphabet`, `NewWithEncoder`. It uses the Go 1.27 standard library
`uuid` package. The pin is `5cb5511` (2026-09-02, v5.0.0).

The repository is MIT; there is no CONTRIBUTING file, the README says nothing about AI-written
code, and there are no agent instructions. The zoo keeps its tests in its own patch and files
nothing upstream.

## Build

`go test -count=1 -run TestHegel -v .` in the module root (Go 1.27). The patch adds, in the
package itself as the upstream tests are (to reach the error sentinels), `hegel_test.go`
(harness, generator helpers), `hegel_props_test.go` (model, generators, properties, the Python
reference test) and `hegel_pins_test.go`, and requires `hegel.dev/go/hegel v0.6.33` in go.mod.
`TestHegelPythonReferenceAgrees` runs `python3` with the `shortuuid` module when it is on
PATH (the CI's venv installs it) and is skipped otherwise.

## Oracle

The godoc's definition of the encoding, computed with `math/big`: the alphabet is the sorted,
deduplicated runes of the string; a UUID is its 128-bit value written in base N, most
significant digit first, padded on the left with the first character to the smallest width L
with N^L >= 2^128; `Decode` reads any string as such a number, pads short input with zeros,
rejects a character outside the alphabet and a value of 128 bits or more. The README's claims:
fixed width, so string order is UUID order (the v7 sorting claim, for any alphabet, since UTF-8
preserves code-point order); the same characters in any order and with duplicates give the same
encoder, and the default alphabet in any order gives `DefaultEncoder`. RFC 9562 section 5.5 for
`UUIDv5`, and the documented namespace rule of `NewWithNamespace` (URL for an `http://` or
`https://` prefix in any case, DNS otherwise, a random v4 for the empty name). The Python
library is run on a batch of 400 UUIDs over eight alphabets (encode, decode of the encoding, a
suffix of it, one digit raised, one digit appended) and 20 names, and must agree.

Generators draw alphabets from one-, two-, three- and four-byte rune pools and the default
alphabet, unsorted and with duplicates, including large ones (more than 255 characters, for the
binary-search decoder) and ones with a wide code-point spread (no rune-index table); UUIDs
random or with leading/trailing zero bytes, all ones, small values; decode strings of every
length around the width, biased toward the largest digit (values near and over 2^128), with a
foreign character or an invalid byte inserted 12% of the time.

## Method

| Property | Checks |
|---|---|
| EncodeIsBaseN | `Encode` equals the model's digits, has exactly L characters, and `Decode` inverts it |
| DecodeIsBaseN | `Decode` of any string equals the model: the value, or the not-in-alphabet / out-of-range error |
| EncodingPreservesOrder | `Encode(a)` compares to `Encode(b)` as `a` compares to `b` |
| AlphabetIsASet | a shuffled alphabet with duplicates encodes alike; the default alphabet in any order is `DefaultEncoder` |
| V5FollowsTheRFC | `UUIDv5` is RFC 9562's, `NewV5` its encoding, `NewWithNamespace` picks the documented namespace |
| PythonReferenceAgrees | the Python `shortuuid` library encodes, decodes and derives v5 names alike (plain test, batch) |

## Accepted differences

- `UUIDv5` hashes the name's bytes as given, invalid UTF-8 included; the Python library takes a
  `str`, so the two cannot be compared on such names, and the reference test skips them.
- `NewWithNamespace("")` is a random v4 (documented); Python's `shortuuid.uuid("")` is the v5 of
  the empty name under DNS.
- `Decode` accepts more than L characters when the value fits (leading zero digits), as Python
  does, and reports the first error it meets: the model accepts either error when a foreign
  character and an overflow both occur.

## Bugs found

One, in bugs.toml: `NewEncoder` accepts an alphabet string that is not valid UTF-8, turning
each invalid byte into U+FFFD, which then appears in encodings. Everything else agreed: the
encoded width is exact for every alphabet size up to 5000 (the float formula happens to be
right), the grouped 128-bit arithmetic matches `math/big` in both directions, and the Python
library's output is reproduced for every alphabet tried.

## History

- 2026-09-21 (turn 344): target added at 5cb5511 (v5.0.0) with five properties, a Python
  reference test and 1 pin.
- 2026-09-23: generators rewritten in combinator style (STYLE.md): package-level generator
  values, `weighted`/`OneOf` choice, `Lists`/`Binary`/`Text` for collections; the collect
  harness and the `Known` switch removed. Same properties and pin.
