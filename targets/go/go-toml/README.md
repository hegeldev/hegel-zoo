# go-toml

[pelletier/go-toml](https://github.com/pelletier/go-toml) v2 is the reference TOML library for Go:
a TOML v1.1.0 parser and encoder modelled on `encoding/json` (`Marshal`/`Unmarshal`, `Encoder`
with `SetTablesInline`/`SetArraysMultiline`/`SetIndentTables`/`SetIndentSymbol`/
`SetOmitEmptySuperTables`, `Decoder` with strict mode via `DisallowUnknownFields`), struct tags
(`omitempty`, `omitzero`, `inline`, `multiline`, `commented`, `comment`), `LocalDate`/`LocalTime`/
`LocalDateTime`, `TextMarshaler`/`TextUnmarshaler` support and the `unstable` package (`Parser`,
`RawMessage`, `Marshaler`/`Unmarshaler`, `unstable/edit`). `AGENTS.md` welcomes AI agents under
the contributing rules. Tests in `hegel_test.go`, external package `toml_test` (dot import).

## Oracles

- **Python's `tomllib`** (3.12, a TOML 1.0 reader sharing no code with go-toml), run as a child
  process over JSON lines and answering with a tagged tree (`int`, `float`, `string`, `bool`,
  `datetime` with offset, `local-datetime`, `local-date`, `local-time`, `array`, `table`). It reads
  every document go-toml's encoder writes, and every generated document; datetimes are compared at
  microsecond precision because Python's `datetime` carries no more.
- **A value model of our own**: random trees of the nine TOML value kinds (integers over the whole
  int64 range, every finite double plus ±inf/nan, strings with quotes, backslashes, control
  characters, tabs, newlines and non-ASCII, dates 0001–9999 with nanoseconds and whole-minute
  offsets within ±23:59, arrays of anything including arrays of tables, tables with bare and quoted
  keys including the empty key). The tree is converted to Go values for the encoder (integers
  spread over `int8`…`uint64`) and written as **TOML 1.0 text by a generator with random syntax
  choices** for the decoder: bare/basic/literal keys, dotted keys, `[table]` headers,
  `[[array of tables]]`, inline tables, literal/basic/multiline strings with `\uXXXX`/`\UXXXXXXXX`
  escapes and line-ending backslashes, hex/octal/binary integers with underscores, `e`/`E`
  floats, `T`/`t`/space and `Z`/`z`/`±HH:MM` date-times, comments, tabs, CRLF, trailing commas.
- **go-toml against itself** for round trips: `Marshal` → `Unmarshal` into `map[string]interface{}`
  and into a 40-field struct (sized integers, floats, `time.Time` and pointers to it, the local
  types with `Precision`, fixed arrays, slices of structs, nested maps, embedded and inline
  structs, `interface{}`, a `TextMarshaler`, `omitempty`/`omitzero`/renamed/skipped fields) under
  every combination of encoder options; `unstable.RawMessage` capture (each raw value re-parses to
  the value) and splicing (`EnableMarshalerInterface`).
- **Strict mode**: `DisallowUnknownFields` fails exactly when unknown keys are present, with a
  `StrictMissingError` carrying one entry per unknown key.
- **Numeric typing**: an integer literal decodes into `int8`…`uint64`/`float32`/`float64`/
  `interface{}` exactly when the value fits, a float literal never decodes into an integer field
  and overflows `float32` exactly when its float32 conversion is infinite.

Properties (9 general): `TestHegelMarshalOutputIsReadBackByTomllibAsTheInput`,
`TestHegelMarshalThenUnmarshalIntoAnInterfaceIsTheIdentity`,
`TestHegelGeneratedDocumentsDecodeIntoTheTreeTheyWereWrittenFrom` (also `Decoder.Decode` versus
`Unmarshal`), `TestHegelIntegerLiteralsDecodeIntoNumericFieldsExactlyWhenTheyFit`,
`TestHegelFloatLiteralsDecodeIntoFloatFieldsAndNotIntoIntegerFields`,
`TestHegelStructsRoundTripThroughMarshalAndUnmarshal`, `TestHegelStrictModeReportsExactlyTheUnknownKeys`,
`TestHegelRawMessagesCaptureAndSpliceValuesLosslessly`; 2 pinned expected failures below. All
general properties pass at 1000 cases × 3.

`[run] setup` checks `python3 -c 'import tomllib'`; the test file passes `HEGEL_TEST_CASES`
through `hegel.WithTestCases` and wraps each property in a `recover` (the zoo's Go conventions,
see `HACKING.md`).

## Bugs (2)

- **go-toml/1** (wrong-result, medium): an integer written in hex, octal or binary cannot be
  decoded into a float field — `a = 0x10` into `float64` fails with `unable to parse float`,
  while `a = 16` and the same literal into `interface{}` work.
- **go-toml/2** (wrong-result, medium): a float literal above `MaxFloat32` that still rounds to
  the finite `MaxFloat32` is rejected for a `float32` field; the encoder's own output for
  `float32(math.MaxFloat32)` (`340282350000000000000000000000000000000.0`) cannot be read back.

## Not bugs (and what the general generators avoid)

- go-toml implements TOML 1.1 (`\e`, `\xHH`, seconds optional in times, newlines in inline
  tables…); generated documents stay within TOML 1.0 so that `tomllib` can arbitrate, and
  documents that go-toml accepts and `tomllib` rejects are not exercised.
- Invalid UTF-8 in strings and keys is encoded as `�` (lossy, deliberate upstream); the
  generators produce valid UTF-8 only. Unsigned integers above `MaxInt64`, `time.Time` offsets not
  on a whole minute and years outside 0–9999 are encoding errors by design and are not generated.
- `LocalTime.Precision` is presentation: `String()` prints exactly that many fractional digits
  (truncating `Nanosecond`), or the minimal digits when it is 0; round trips compare
  hour/minute/second/nanosecond and generate nanoseconds consistent with the precision.
- `[]interface{}{nil}` is an encoding error ("cannot encode a nil interface") while a nil map
  value is skipped; `map[bool]` keys are refused; `SetIndentSymbol` with a non-whitespace symbol
  produces unreadable documents — all as documented or reasonably implied.
- `unstable.RawMessage` bytes must be a bare value: a trailing `# comment` is refused by the
  encoder's validation.
- Fixed-size array targets silently drop extra elements (as `encoding/json` does).
- Generators avoid each pinned shape: float fields receive decimal integer literals only
  (go-toml/1); float32 values stay below 10³⁸ and float literals in `(MaxFloat32,
  MaxFloat32 × (1 + 2⁻²⁵))` are skipped (go-toml/2).
- Upstream's own tests all pass at this commit.

## History

- 2026-09-14: written at 686c980c4758 (after v2.4.3, 2026-07-18), hegel.dev/go/hegel v0.6.33.
