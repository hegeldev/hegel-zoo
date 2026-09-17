# ugorji-codec — Hegel properties for `github.com/ugorji/go/codec`

[ugorji/go](https://github.com/ugorji/go) is the multi-format Go codec:
msgpack, CBOR, JSON, and its own binc and simple formats behind one
`Encoder`/`Decoder` API with a large option surface (`Canonical`,
`StructToArray`, `OptimumSize`, `SignedInteger`, `MapType`, per-format
options such as `WriteExt`, `IndefiniteLength`, `IntegerAsString`, ...).
Pinned at `181add7` (v1.2.14 plus the commits since), module `codec/`.

## Build

The patch adds `go.mod` changes and four test files to `codec/`:
`hegel_test.go` (plumbing, the `Known` gates), `hegel_model_test.go`
(value trees, canonical comparison, model msgpack and CBOR encoders and
decoders, half floats), `hegel_props_test.go` (the eight properties) and
`hegel_pins_test.go` (nine pins). `go get hegel.dev/go/hegel` raises the `go`
directive to 1.26. No external tool is needed. The properties run in about a
second at the default case count; `HEGEL_TEST_CASES=2000` takes ~5 s.

## Oracles

- **encoding/json** for the JSON handle: token-for-token equality of the two
  encoders' output (numbers compared by value, since codec writes `2.0`
  where encoding/json writes `2`), byte equality when the tree has no floats
  (`Canonical` sorts keys like encoding/json; `HTMLCharsAsIs` is matched with
  `SetEscapeHTML`), and decoding of encoding/json's text after re-escaping
  (`\uXXXX`, surrogate pairs, `\/`, whitespace) with codec's documented
  number rule (no `.eE` → integer, else float; `PreferFloat` → float).
- **A model msgpack encoder/decoder** written from the spec: codec's bytes
  must equal the minimal encoding under `WriteExt`/`PositiveIntUnsigned`/
  `NoFixedNum` (signed-family minimal widths, fixstr/str8/16/32, bin, ext
  timestamps), and codec must decode every header form the spec allows for
  a value (widened ints, all string/bin/array/map widths, the 32/64/96-bit
  timestamps).
- **A model CBOR encoder/decoder**: byte equality for definite lengths
  (`OptimumSize` → shortest exact float, f16 included), model decoding of
  codec's output under `IndefiniteLength`, and decoding of every spec form
  (widened heads, chunked indefinite strings, indefinite containers, half
  floats, tag 1 times as int or float).
- **The library's own round trips**, typed (a 30-field struct with every
  scalar kind, slices, maps, arrays, pointers, nested and embedded structs,
  `time.Time`, an `interface{}` tree, omitempty and `-` tags) and untyped
  (trees of nil/bool/int64/uint64/float64/string/[]byte/[]any/map), through
  all five handles with random options, through `[]byte` and `io.Reader`/
  `io.Writer` with small buffers, singly and as a stream of values.
- **Documented option semantics**: `Canonical` determinism, `IntegerAsString`
  `'L'`/`'A'`, `NilCollectionToZeroLength`, `StructToArray`,
  `MapKeyAsString`, `SignedInteger` (no uint64 in the output),
  `EncZeroValuesAsNil`, `RecursiveEmptyCheck`.
- **Malformed input**: every proper prefix of an encoding is an error (JSON:
  only for self-delimiting tops), and byte corruption never panics.

## Properties

| Test | Checks |
|---|---|
| `TestHegelTypedRoundTrip` | struct → any handle/options → struct equal (modulo the documented option effects) |
| `TestHegelUntypedRoundTrip` | tree → handle → `interface{}` canonical-equal; streams; `NumBytesRead`; typed containers |
| `TestHegelMsgpackWireMatchesModel` | bytes = model; model decodes codec; codec decodes every spec form |
| `TestHegelCborWireMatchesModel` | same for CBOR; negative integers below int64 are rejected |
| `TestHegelJsonMatchesEncodingJson` | encoder vs encoding/json; decoder on encoding/json text; number texts |
| `TestHegelStructTagsMatchEncodingJson` | `json:` tags, `-`, embedding, omitempty key sets vs the zero-value rule; encoding/json text decodes |
| `TestHegelMalformedInputIsAnError` | prefixes fail, corruption never panics |
| `TestHegelOptionsMeanWhatTheySay` | the options above |

## Bugs (9)

| id | severity | summary |
|---|---|---|
| ugorji-codec/1 | medium | `omitempty` compares memory: a zero-length string with a non-nil data pointer is emitted as `""` |
| ugorji-codec/2 | medium | CBOR negative integers below int64 wrap silently (`3b 80 00…` → `MaxInt64`) |
| ugorji-codec/3 | low | JSON integers below int64 (or above it with `SignedInteger`) fail to decode into `interface{}`; above uint64 they become float64 |
| ugorji-codec/4 | low | `NilCollectionToZeroLength` writes a nil `[]byte` as `[]`/fixstr, an empty one as `""`/bin |
| ugorji-codec/5 | low | the CBOR decoder rounds times to the microsecond; `TimeRFC3339` writes nanoseconds |
| ugorji-codec/6 | low | binc writes `-0.0` as `+0.0` |
| ugorji-codec/7 | medium | `SignedInteger` wraps unsigned values in [2^63, 2^64) to negative int64 |
| ugorji-codec/8 | high | a non-string map key decoded into a string-keyed map is read as a string header (CBOR, simple): wrong data, no error |
| ugorji-codec/9 | high | binc rewrites every integer in -4294967295..-4286578688 (`-4294967295` → `-255`) |

Each bug has a `Known` gate that keeps its input shape out of the
properties and a pin in `hegel_pins_test.go` asserting the correct behaviour;
the pins fail while the bugs exist (`[expected_failures]`).

## Not bugs (accepted differences, modelled in the tests)

- The JSON handle writes integral floats with a fraction (`2.0`, `-0.0`,
  `1e+21`), `1e-07` rather than `1e-7`, and NaN/±Inf as `null` (encoding/json
  refuses them). Only the values are compared.
- msgpack chooses the signed family for non-negative `int` values (`128` →
  `d1 00 80`, not `cc 80`) unless `PositiveIntUnsigned`; the spec's "smallest
  representation" is a SHOULD. The model follows the option.
- `Canonical` sorts map keys in their natural order (string order for
  strings), not RFC 8949's length-first order.
- CBOR times are tag 1 with a float64 epoch by default, so nanoseconds are
  not representable; the typed round trip uses whole seconds there and the
  spec-form check compares times to within the float's precision.
- The zero `time.Time` in an `interface{}` is encoded as nil and reads back
  as nil; unassigned CBOR simple values (`f0`, `f8 ff`) are rejected;
  CBOR bignums (tags 2/3) become float64.
- `IndefiniteLength` writes strings as indefinite text in chunks (a 10-byte
  string arrives as 4+4+2), so CBOR bytes are compared only for definite
  lengths and the indefinite output is checked by model decoding.
- `omitempty` on a non-nil interface, pointer, or a non-nil empty slice/map
  keeps the field (the value is not the zero value); encoding/json omits
  empty slices/maps. `RecursiveEmptyCheck` descends pointers and interfaces
  and treats empty slices as empty. Both are documented and modelled.
- Decoding into a populated value merges maps and decodes into the value an
  interface holds; `EncZeroValuesAsNil` (simple) turns `-0` into `+0` and a
  pointer to zero into nil; `IntegerAsString` and `PreferFloat` change the
  Go type an `interface{}` field reads back as.
- With `SignedInteger` no uint64 ≤ MaxInt64 appears (checked); the wrap
  above it is bug 7.

## History

- 2026-09-17: created at 181add7 (v1.2.14+), nine bugs.
