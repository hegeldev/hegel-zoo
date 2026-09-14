# jsonparser

[buger/jsonparser](https://github.com/buger/jsonparser) is a zero-allocation JSON scanner for
Go (5.6k stars, 2.2k importing modules): `Get` and typed getters by key path, `ArrayEach`,
`ObjectEach`, `EachKey` (several paths in one pass), `Set`/`Delete`/`Append` on the raw bytes,
`[*]` wildcards, a `ReaderParser` over an `io.Reader`, a `Lenient` configuration (single
quotes, unknown escapes), `ParsePath`/`CompilePath`, and the scalar parsers `ParseInt`,
`ParseFloat`, `ParseBoolean`, `ParseString`, `Escape`/`Unescape`. The first Go target of the
zoo, written at upstream HEAD `36a686d` (after v1.6.1; the repository also carries a ReqProof
"formal verification" suite with `testing/quick` properties and an encoding/json reference
oracle in `reference_oracle_test.go`, whose ideas the zoo's tests extend). Tests in
`hegel_test.go`, an external test package (`jsonparser_test`) so that nothing collides with
upstream's many in-package test files.

## Oracles

- **The model tree** the documents are generated from: `nil | bool | number (exact text) |
  string | []any | object (ordered, unique keys)`, rendered by a randomised writer — random
  JSON whitespace between tokens, three escaping styles (minimal; `\u` for every non-ASCII
  character with surrogate pairs and `\/`; `\u00XX` for the short escapes too), single quotes
  and `\g`-style unknown escapes for the `Lenient` property. **Every document is decoded with
  encoding/json first** and must agree with the model, so the writer is checked before
  jsonparser is asked; jsonparser's results are compared to the model (numbers by exact text,
  strings after unescaping, containers by decoding with encoding/json).
- **strconv** for `ParseInt`/`ParseFloat` and the typed getters (agreement where strconv
  accepts, an error where it rejects), **encoding/json** for `Escape`.
- **jsonparser against itself**: `ReaderParser` (one-byte, half-size and chunked readers,
  sliding windows down to one byte) against the byte-slice `Get`; `CompiledPath` against the
  plain functions; `DefaultConfig`/`Lenient` against the strict entry points.

Properties: `TestHegelGetAgreesWithEncodingJSON` (value, type and offset on every path,
typed getters right on their type and erroring on the others, missing paths, the whole
document with no keys), `TestHegelIteratorsAgreeWithTheTree` (ArrayEach, ObjectEach, EachKey
over several paths with the `-1` return iff one is missing), `TestHegelSetThenGetAgreesWithTheModel`
(existing paths, new keys and chains of new keys, the index just past the end; `SetString`),
`TestHegelDeleteAgreesWithTheModel` (+ `DeleteFound`, missing paths leave the document alone),
`TestHegelAppendAgreesWithTheModel`, `TestHegelEscapeRoundTrips` (Escape/ParseString/Unescape
under every writer style and encoding/json's own), `TestHegelScalarParsersAgreeWithStrconv`,
`TestHegelParsePathRoundTrips` (dot, quoted and bracket components; CompiledPath ≡ plain),
`TestHegelReaderParserAgreesWithGet`, `TestHegelWildcardsAgreeWithTheModel` (EachKeyWildcard,
ArrayEachWildcard, SetWildcard), `TestHegelLenientConfigReadsSingleQuotesAndUnknownEscapes`,
`TestHegelNoPanicOnMutatedDocuments`; nine pinned expected failures below. All general
properties pass at 1000 cases × 3.

Conventions of the zoo's Go targets, first used here: hegel-go reads no environment variable,
so `hegelOpts()` passes `HEGEL_TEST_CASES` through `hegel.WithTestCases`; `property()` turns a
panic in the code under test into a failure of the current test case (hegel-go re-raises
panics after shrinking, which would abort the test binary and hide every later test); the
patch's `go.mod` change (`go get hegel.dev/go/hegel`) raises the `go` directive from 1.13 to
1.26.0, hegel-go's minimum; `go.sum` stays out of the patch (`GOFLAGS=-mod=mod` in `zoo test`).

## Bugs (9)

- **jsonparser/1** (contract, medium): `Set` at an index beyond the end (or a malformed
  `[-1]`, `[]`, `[1`, `[*]`) appends; upstream's own `TestOracleSetPr286Regression` asserts an
  error and fails at this commit.
- **jsonparser/2** (wrong-result, medium): a path shape that disagrees with the document
  (key on an array, index on an object) makes `Set` replace the container — `Set({"a":1}, 9,
  "[0]")` is `[9]`.
- **jsonparser/3** (wrong-result, medium): `Set` writes the new key unescaped (`{""":1}`).
- **jsonparser/4** (contract, low): `EachKeyWildcard` stops at the first element without the
  key.
- **jsonparser/5** (contract, low): `Escape` copies invalid UTF-8 through.
- **jsonparser/6** (contract, low): `GetFloat`/`GetInt`/`ParseFloat` accept `1_0`, `0x1p-2`,
  `-Inf`, `1.`, `-.5`, leading zeros.
- **jsonparser/7** (wrong-result, low): `ReaderParser.Get` does not find the empty key.
- **jsonparser/8** (wrong-result, high): `Get({"a":1,"b":[7]}, "a", "[0]")` is `7` — an index
  step after a scalar member reads a later array of the same object.
- **jsonparser/9** (wrong-result, medium): `Delete` of a key that starts with `[` leaves
  `{"[0]":}` behind.

## Not bugs (and what the general generators avoid)

- jsonparser scans, it does not validate: trailing garbage, unterminated documents, `1x` as a
  Number, missing commas and duplicate keys (first wins, documented) are all accepted; only
  the pinned number spellings (/6) are counted, because `GetFloat` documents a conversion.
- `Set` at index == length appends (upstream's own test asserts it) — modelled as an append.
  `Set` replacing a *scalar* with a new object/array on a deeper path is treated as the
  documented auto-vivification, not counted (only containers count, /2).
- `Escape` leaves U+2028/U+2029 raw where encoding/json escapes them — both valid.
- `EachKey` returns the offset where the last path matched when all paths were found and
  `-1` otherwise (undocumented; the property asserts only `-1` iff a path is missing).
  `ArrayEach`/`ObjectEach` callback offsets are undocumented and not checked.
- `ParsePath` takes `$.a."quoted.key"[0]`, not JSONPath's `$["a"]` (bracket components are
  indices or `[*]` only) — its grammar, not a bug. `ArrayEachWildcard` accepts a terminal `[*]`
  only (documented).
- `GetUint64("-0")` is 0 with no error (strconv rejects the sign); `GetObjectLen` counts
  pairs, so duplicate keys count twice (documented as "key-value pairs").
- Keys that start with `[` are read literally by `Get`/`Set` when the container is an object;
  the general `Delete` property keeps them out of its paths (/9), and the `Set` property uses
  keys that need no escaping (/3) and paths that agree with the document's shape (/1, /2);
  the general `Get` property never puts an index step after a scalar (/8) and the
  `ReaderParser` property never uses the empty key (/7) — each pinned separately.
- Upstream's own `TestOracleSetPr286Regression` fails at this commit (reported `UPSTREAM`,
  not judged).

## History

- 2026-09-14: written at 36a686d11807 (2026-08-21, after v1.6.1), hegel.dev/go/hegel v0.6.33.
