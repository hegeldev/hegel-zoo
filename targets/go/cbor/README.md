# cbor

[fxamacker/cbor](https://github.com/fxamacker/cbor) is the CBOR codec of the Go ecosystem
(1 100 stars, about 1 500 importers, Kubernetes among them): RFC 8949 encoding and decoding
with an `encoding/json`-shaped API, deterministic encodings (Core Deterministic, Canonical,
CTAP2), a streaming Encoder/Decoder, diagnostic notation, struct tags (`toarray`, `keyasint`,
`omitempty`, `omitzero`) and a long list of encoding and decoding options. The pin is the
master head after v2.9.4 (`d1789e8`, 2026-09-15). MIT; README.md, CONTRIBUTING.md,
SECURITY.md, CODE_OF_CONDUCT.md and the pull-request template ask for signed, non-anonymous
pull requests and say nothing about AI-written code; the zoo keeps its tests in its own patch
and files nothing upstream.

## Build

`go test -count=1 -run TestHegel -v .` in the module root. The patch adds `hegel_test.go`
(the model and the properties) and `hegel_pins_test.go` (one plain test per bug) and requires
`hegel.dev/go/hegel v0.6.33` in go.mod. The second oracle is Python's `cbor2` package: the
`[run] setup` step creates `.hegel/venv` and installs it; the harness looks for a Python with
cbor2 in `HEGEL_CBOR2_PYTHON`, then `.hegel/venv/bin/python`, then `python3`, and skips that
one property without it.

## Oracles

- **A model of RFC 8949** written in the test: a value tree (integers of both major types,
  byte and text strings, arrays, maps, tags, simple values, booleans, null, undefined, floats),
  its encoding under the three deterministic regimes (preferred heads, bytewise-lexicographic
  or length-first key order, shortest float with the model's own binary16 arithmetic, or
  float64 as written for CTAP2), *loose* encodings of the same tree (wider heads,
  indefinite-length strings in chunks split at rune boundaries, indefinite arrays and maps,
  any float width that holds the value, shuffled map order), and the well-formedness grammar
  of Appendix C.
- **Python cbor2**: the Go Canonical encoding of a value, decoded by cbor2 and re-encoded with
  `canonical=True`, is the same bytes; cbor2's own default encoding of that value decodes in
  Go to the same value. Tags cbor2 interprets itself (dates, decimal fractions, references,
  URIs, sets, …) are renumbered for it and boolean map keys dropped (Python's `0 == False`).
- **The documented options**: every EncOptions/DecOptions field the tests touch is checked
  against its documentation — what is rejected (NaN, Inf, big.Int, tags, indefinite lengths,
  invalid UTF-8, duplicate keys, the three limits), what is converted (NaN payload rules,
  Inf to binary16, strings to byte strings, time modes), which Go types come out of `any`.
- **encoding/json-like contracts**: struct tags, sized integer targets (UnmarshalTypeError
  exactly when the value does not fit), Marshaler/Unmarshaler, RawMessage/RawTag, the
  streaming Encoder's state machine and the Decoder over awkward readers.

## Properties

| Property | Checks |
|---|---|
| DeterministicEncodingsMatchTheModel | CoreDet, Canonical and CTAP2 `Marshal` of a Go value are the model bytes; the default mode is well-formed and value-preserving; re-encoding after decoding is byte-identical |
| AnyRepresentationDecodesToTheValue | every loose encoding decodes to the value; Wellformed/Diagnose accept it; UnmarshalFirst/DiagnoseFirst return exactly the trailing bytes; Unmarshal/Wellformed reject trailing bytes with ExtraneousDataError and prefixes with io.ErrUnexpectedEOF |
| EncodingOptionsPreserveTheValue | random Sort/ShortestFloat/NaNConvert/InfConvert/BigIntConvert/IndefLength/TagsMd/String: rejection exactly as documented, otherwise well-formed, same value after the documented conversions, exact bytes for the fully determined modes, EncOptions() round trip |
| WellformednessFollowsRFC8949 | random and mutated bytes: `Wellformed` agrees with Appendix C; Unmarshal and Diagnose never accept ill-formed data nor fail well-formed data with a syntax error |
| DecodingOptionsAreExact | MaxNestedLevels/MaxArrayElements/MaxMapPairs accept exactly the values within them; DupMapKeyEnforcedAPF, IndefLengthForbidden, TagsForbidden, UTF8RejectInvalid reject exactly the offending encodings; Wellformed applies the structural ones; IntDec modes give the documented Go types |
| StreamsDecodeItemByItem | Encoder output = concatenated Marshal; Decoder over OneByteReader/HalfReader/DataErrReader with Skip and NumBytesRead; io.EOF at the end; UnmarshalFirst/DiagnoseFirst walk the sequence; StartIndefinite*/EndIndefinite containers decode to the model |
| IntegersFitTheirGoTypes | big.Int encodes as the integer or the bignum (BigIntConvertNone), bignum content is the minimal magnitude; decoding into int8…uint64, big.Int, *big.Int and any; UnmarshalTypeError exactly on overflow; every Go integer type encodes as the model |
| FloatsKeepTheirValue | ShortestFloat16 picks the shortest exact width (model binary16), the default mode writes float64/float32 as written except Inf → binary16, NaN conversions (7e00, PreserveSignal, Quiet, Reject) as documented; every width decodes to the same float64 and to float32 when exact; Diagnose text parses back; NaN/Inf decode-forbidden modes |
| StructTagsFollowTheModel | keyasint, omitempty, omitzero (−0.0 is zero, as reflect says), `-`, toarray, nil vs empty containers, nested structs: CoreDet bytes are the model's, round trip into the struct |
| TimeRoundTrips | six TimeModes × EncTagNone/Required: tag 0/1, content as documented (RFC 3339 text exact, integer seconds, float seconds within binary64 precision), decoding under the three DecTagModes, zero time as null |
| DiagnosticNotationIsCompositional | Diagnose of a container is its items' notations joined by ", " within the RFC 8949 §8 brackets, `_ ` markers for indefinite items, leaves as decimals / JSON strings / h'…' / simple(n) / literals, bignums as integers; float precision indicators; CBORSequence mode |
| EncoderStateMachineIsExact | random Start*/Encode/EndIndefinite sequences against a model: refusals exactly where documented (Start inside a string, a chunk of the wrong type or nil, End with nothing open or an odd map), IndefLengthForbidden, and the finished output decodes to the model |
| MarshalerOutputIsValidated | MarshalCBOR/RawMessage/RawTag output accepted iff exactly one well-formed item allowed by IndefLength/TagsMd (and, for tags 0–3, the right content type), embedded verbatim; an Unmarshaler and RawMessage receive exactly the item's bytes |
| Cbor2AgreesOnCanonicalEncodings | the Python oracle above |

`Known` switches gate the two recorded bugs (TimeUnixMicro stays within 1679–2261; the
nesting limit is kept out of the band where the library's tag accounting and the documented
one disagree). With them on, the fourteen properties run clean at 500 cases (about 10 s;
`CBOR_COLLECT=1` records mismatches instead of failing and prints them shortest-first,
`HEGEL_VERBOSE=1` turns on the engine's log). Hegel's too-slow health check is suppressed for
the cbor2 property, which forks a Python interpreter per case.

## Bugs (3; details in bugs.toml)

| id | summary | severity |
|----|---------|----------|
| cbor/1 | `TimeUnixMicro` computes the float from `t.UnixNano()`, undefined outside 1678–2262: year 1000 encodes as 2169, year 9999 as 1816 (`TimeUnixDynamic` beside it is right) | medium |
| cbor/2 | `MaxNestedLevels` does not count a tag unless its parent is a tag: `[37([37([37([37(0)])])])]` (8 levels) passes a limit of 4 | low |
| cbor/3 | `TagsForbidden` does not stop `Marshal` writing bignum tags for a `big.Int` (`BigIntConvertNone`, or `Shortest` beyond 64 bits); the `TagsForbidden` decoder rejects the output | medium |

How they were found: hand probes of the time modes before writing the time property showed
the year-1000 and year-9999 round trips landing in 2169 and 1816 (cbor/1); the decoding-options
property's nesting model, which counts tags as the documentation says, disagreed with the
library on a value like `37([[[[…]]]])` at exactly the configured limit, and probes with tag
chains pinned the accounting down (cbor/2). Six collect rounds otherwise found only harness
mistakes: the default `InfConvertFloat16` (infinities leave the default mode as binary16), the
NaN payload shift for binary16, `reflect.Value.IsZero` treating −0.0 as zero (so `omitzero`
omits it, as `encoding/json` does), and the model's own duplicate keys under
`StringToByteString`.

## Accepted differences (not bugs)

- `uintptr` is an unsupported type (`encoding/json` encodes it); the supported-type list does
  not include it.
- A CBOR map whose integer key lies outside int64/uint64 cannot decode into `map[any]any`:
  the key would be a `big.Int`, which Go cannot hash (`InvalidMapKeyTypeError`, documented);
  likewise array, map and (Content-dependent) tag keys. The generators keep map keys within
  int64 and to hashable kinds.
- A Go map with both `"a"` and `ByteString("a")` keys encodes, under `StringToByteString`, to a
  CBOR map with a duplicate key: the caller asked for it.
- Python's `0 == False` and `1 == True`: cbor2 folds `{0: 0, false: true}` into one pair (the
  clean run's first failure, shrunk by Hegel to exactly that map); boolean keys are dropped for
  the cbor2 oracle.
- Duplicate-key detection compares decoded Go values: two `NaN` keys are never equal, and
  `1` and `1.0` are different CBOR keys (different major types) as well as different Go keys.
- The Encoder state-machine model writes whatever pairs the random sequence gives, so an
  indefinite-length map may repeat a key; its output is read back into `map[any]any` under the
  default `DupMapKeyQuiet`, which keeps the last value, and the model does the same (a CI run of
  the whole zoo caught the model keeping the first).
- `DupMapKeyQuiet` into a struct keeps the first value of a key (documented "keep first or
  keep last depending on the Go type"); with `FieldNameMatchingPreferCaseSensitive` a later
  exact-case key does not displace an earlier case-insensitive match.
- `null` and `undefined` set a pointer field to nil without calling its `UnmarshalCBOR`, as
  `encoding/json` does; an empty `RawMessage` encodes as null.
- Diagnostic notation writes a bignum (tag 2/3) as its integer, as RFC 8949 Appendix A does,
  and puts no precision indicator after `NaN` and `Infinity`.
- `RawTag` with number 0–3 must have content of the type RFC 8949 §3.4 assigns (text,
  number, byte string); the encoder validates Marshaler output with the built-in tag rules.

## Not tested

Registered tag sets (`TagSet`, `EncModeWithTags`), `BinaryMarshaler`/`TextMarshaler`/JSON
transcoding modes, `ByteSliceLaterFormat`/`ByteStringExpectedFormat` (tags 21–23),
`SimpleValueRegistry`, `DefaultMapType`/`DefaultByteStringType`, field-name matching modes
beyond the probe, `UnrecognizedTagToAny`/`TimeTagToAny`, `MarshalToBuffer`, JSON
interoperability.
