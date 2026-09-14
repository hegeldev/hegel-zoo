# go-yaml (goccy)

[goccy/go-yaml](https://github.com/goccy/go-yaml) is a YAML 1.2 library for Go written from scratch
(no libyaml lineage), the drop-in alternative to yaml.v3 with the better error messages: `Marshal`/
`Unmarshal` with options (`Indent`, `IndentSequence`, `UseSingleQuote`, `Flow`,
`UseLiteralStyleIfMultiline`, `JSON`, `AutoInt`, `OmitEmpty`/`OmitZero`, `WithSmartAnchor`;
`Strict`/`DisallowUnknownField`, `AllowDuplicateMapKey`, `UseOrderedMap`), `Encoder`/`Decoder`,
struct tags (`omitempty`, `omitzero`, `flow`, `inline`, `anchor`, `alias`, `-`, `json` fallback),
`MapSlice`, `RawMessage`, custom marshalers, an AST (`ValueToNode`/`NodeToValue`, `ast`, `parser`,
`token`) and `YAMLToJSON`/`JSONToYAML`. MIT, no AI-policy file. Tests in `hegel_test.go`, external
package `yaml_test` (dot import). The `[run] command` passes `-vet=off` because Go 1.27's vet step
fails on upstream's own `decode_test.go`.

## Oracles

- **yaml.v3** (`go.yaml.in/yaml/v3` v3.0.5, in-process): reads every document goccy's encoder
  writes and arbitrates the generated documents (a document yaml.v3 does not read as the tree is a
  test-suite defect, not a goccy bug).
- **PyYAML 6.0.3 with libyaml** (`yaml.CSafeLoader`, a YAML 1.1 reader sharing no code with either
  Go library), run as a child process over JSON lines and answering with a tagged tree; used on the
  encoder's output for trees without YAML 1.1-only resolutions (see below).
- **`encoding/json`** for the `JSON()` style, `YAMLToJSON` and `JSONToYAML`.
- **A value model of our own**: random trees of null/bool/int (whole int64 and uint64 ranges)/
  float (every finite double, ±inf/nan)/string/sequence/mapping, strings built from pieces that
  look like YAML syntax (`- `, `: `, `#`, `?`, `<<`, `---`, `...`, `1e3`, `.inf`, `0x`, `1_0`,
  `yes`, `null`, quotes, backslashes, tabs, newlines, non-ASCII, U+10FFFF, NBSP). The tree is
  converted to Go values for the encoder (integers spread over `int8`…`uint64`, sequences
  sometimes `[]string`) and written as **YAML 1.2 text by a generator with random syntax choices**
  for the decoder: plain/single/double-quoted scalars (`\uXXXX`/`\UXXXXXXXX`, `\ ` escapes),
  literal blocks with `-`/`+` chomping and explicit indentation indicators, hex/octal/binary/
  underscored/`+`-signed integers, `e`/`E`/`f`/`g` floats, block mappings and sequences at random
  indentation (compact `- k: v`, `-` on its own line, bare `key:` for null), flow collections with
  random spacing and trailing commas, comments, blank lines, `---`/`...`, leading comments.
- **goccy against itself** for round trips: `Marshal` → `Unmarshal` into `interface{}` (also
  `Decoder.Decode` and `UseOrderedMap`, whose `MapSlice` must come back in the encoder's sorted
  key order) and into a 40-field struct (sized integers, floats, `time.Time` and `*time.Time`,
  `Duration`, `MapSlice`, `[]byte`, a `TextMarshaler`, inline/embedded/flow/omitempty/renamed/
  skipped fields, `interface{}`, nested maps and slices of structs) under every combination of
  `Indent`, `IndentSequence`, `UseSingleQuote`, `Flow`, `UseLiteralStyleIfMultiline`, read back
  strictly (`DisallowUnknownField`).
- **Numeric typing**: an integer literal (decimal, hex, octal, binary, underscored) decodes into
  `int8`…`uint64` exactly when the value fits, and float literals decode into `float32`/`float64`
  exactly (or fail when out of range).
- **Strict mode**: `Strict()` fails exactly when unknown keys are present.

Properties (9 general): `TestHegelMarshalThenUnmarshalIntoAnInterfaceIsTheIdentity`,
`TestHegelMarshalOutputIsReadBackByYamlV3AsTheInput`,
`TestHegelMarshalOutputIsReadBackByPyYAMLAsTheInput`, `TestHegelJSONStyleOutputIsJSONWithTheSameValue`,
`TestHegelGeneratedDocumentsDecodeToTheTreeTheyWereWrittenFrom`,
`TestHegelIntegerLiteralsDecodeIntoNumericFieldsExactlyWhenTheyFit`,
`TestHegelFloatLiteralsDecodeIntoFloatFieldsExactly`, `TestHegelStructsRoundTripThroughMarshalAndUnmarshal`,
`TestHegelStrictModeFailsExactlyWhenUnknownKeysArePresent`; 30 pinned expected failures below. All
general properties pass at 1000 cases × 3.

`[run] setup` checks `python3 -c 'import yaml'`; the test file passes `HEGEL_TEST_CASES` through
`hegel.WithTestCases` and wraps each property in a `recover` (the zoo's Go conventions, see
`HACKING.md`).

## Bugs (30)

Encoder output that does not read back (found by probing the encoder's quoting rules, then pinned):

- **go-yaml/1** (roundtrip): floats written with an exponent and no fraction (`1e+21`, `5e-324`)
  read back as strings; `1e3` is a string in `interface{}` targets.
- **go-yaml/3** (roundtrip): leading/trailing tabs are not quoted — `"\t"` reads back as null.
- **go-yaml/4** (roundtrip): `.inf`/`.nan` spellings are not quoted and read back as floats;
  `+.inf` decodes as a string.
- **go-yaml/5** (roundtrip): strings starting with `?` are not quoted (`? a` becomes a mapping).
- **go-yaml/6** (roundtrip): `---`, `...`, `... a` are not quoted (read as null or fail).
- **go-yaml/7** (roundtrip): the key `<<` is not quoted and becomes a merge key.
- **go-yaml/8** (differential): control characters and a BOM are written raw; yaml.v3 and libyaml
  reject the documents.
- **go-yaml/9** (silent-corruption): `\r` is used as a literal block's line break — `"a\rb"` reads
  back as `"a\nb"`, `"a\rb\nc"` is invalid.
- **go-yaml/10** (roundtrip): `Flow(true)` puts literal blocks inside `{}`/`[]`.
- **go-yaml/11** (roundtrip): whitespace-only multi-line strings (`"\n"`, `" \n"`) read back as `""`.
- **go-yaml/12** (roundtrip): multi-line map keys are written as literal blocks.
- **go-yaml/13** (roundtrip): `UseSingleQuote` copies Go escapes into single quotes (`'a\n#b'`).
- **go-yaml/14** (contract): `JSON()` writes `\x00`, `\a`, `\v`, `\x7f` — not JSON.
- **go-yaml/18** (panic): `Marshal(map[any]any{nil: 1})` nil-pointer panics.
- **go-yaml/23** (roundtrip): `Flow(true)` leaves `[`/`{` bare inside strings.
- **go-yaml/25** (contract): `NodeToValue(ValueToNode(""))` is `"\"\""` — quoted strings keep
  their quotes.
- **go-yaml/26**, **/30** (silent-corruption): stripped literal blocks lose trailing space-only
  lines and trailing spaces on the last line (the encoder writes such strings as `|-`).
- **go-yaml/28** (roundtrip): literal blocks whose first content line starts with a space lack
  the indentation indicator — the space is lost or the document is invalid (always under
  `UseLiteralStyleIfMultiline`).
- **go-yaml/29** (roundtrip): `Indent(1)` mis-indents literal blocks in sequences.

Decoder:

- **go-yaml/2** (silent-corruption): tabs inside plain scalars are dropped (`a\tb` → `ab`).
- **go-yaml/15** (wrong-result): `!!int abc`, `!!int 1.5`, `!!float abc`, `!!timestamp abc`,
  `!!binary '!!!'` decode to zero values without error; `!!str` alone is null.
- **go-yaml/16** (wrong-result, low): `+-5` is the number 5.
- **go-yaml/17** (silent-corruption): `1e19` and `2^64` into `int64` wrap to `MinInt64`.
- **go-yaml/19** (wrong-result): `<<: [a, b]` gives later mappings precedence (typed maps: a
  `duplicate key` error).
- **go-yaml/20** (differential, low): `{a:1}` is key `a` value 1 (YAML 1.2: the scalar `a:1`).
- **go-yaml/21** (wrong-result, low): `k: |a` decodes as `""` without error.
- **go-yaml/22** (wrong-result): a leading BOM becomes part of the first key.
- **go-yaml/24** (wrong-result): keys ending in `<<` (`x<<: 1`) are treated as merge keys.
- **go-yaml/27** (wrong-result): a literal block with an explicit indentation indicator (or keep
  chomping) followed by empty lines at the end of the stream is an "invalid number of indent" error.

## Not bugs (and what the generators avoid)

- goccy resolves YAML 1.1 forms that the 1.2 core schema does not: underscores in numbers
  (`1_000`), leading-zero octal (`010` = 8), `<<` merge keys. It does not resolve sexagesimal
  numbers, `yes`/`no`/`on`/`off` booleans, timestamps into `interface{}` or the `=` value tag;
  PyYAML (1.1) does, so trees whose strings look like those (`yaml11Only`) skip the PyYAML
  read-back, and `08`/`0O17`/`1e3`-shaped strings the two Go libraries resolve differently are
  never emitted plain (the writer asks yaml.v3 whether a plain scalar would stay a string; with
  underscores it also asks about the string with the underscores removed, since yaml.v3 and
  goccy draw the `1_.5`/`.00_` line differently).
- yaml.v3 quirks worked around in the generators (libyaml agrees with goccy here): it rejects `?`
  inside flow plain scalars (`{a: b?}`), treats U+0085/U+2028/U+2029 as line breaks, reads
  `+9223372036854775808` as a float and rejects the `\/` escape — flow-style strings avoid `?`,
  `[`, `{`; the writer never emits those characters unescaped, uses `+` only up to `MaxInt64` and
  never writes `\/`.
- Permissive typed decoding is accepted as design: `"12"` (quoted) into an `int` field, `1.5`
  into an integer field (truncated), `1e3` into a float field, `[- a]` (a nested block sequence in
  flow context) all succeed.
- `AllowDuplicateMapKey` is off by default: generated mappings have distinct keys.
- Encoding-time avoidances per pinned bug: strings with `\r`, control characters, a BOM (8, 9);
  a first non-empty line starting with a space, whitespace-only multi-line strings, lines ending
  in spaces or made of spaces only, trailing `\n` + `\r` (11, 26, 28, 30); `.inf`/`.nan` spellings,
  two leading signs, a leading `?`, `---`, `...`, a trailing `<<`, strings yaml.v3 resolves as
  non-strings (4, 5, 6, 7, 16, 24); tabs never appear at the ends of strings and inside strings
  only in the printable modes' absence (2, 3); multi-line strings and flow indicators are kept
  out of keys and out of `Flow`/`UseSingleQuote` output (10, 12, 13, 23); `Indent(1)` is not
  generated (29); floats whose shortest form has an exponent and no dot are skipped (1); nil
  interface keys are never produced (18); `JSON()` runs on printable strings without inf/nan (14).
- Writer avoidances: no explicit indentation indicator with keep chomping and no blank lines
  after a block with an indicator or keep chomping (27); no flow entries without a space after
  the colon (20); no block scalar header text (21); no BOM (22); keys never end in `<<` (24).
- Upstream's own tests: `TestDecoder_*` in `decode_test.go` fail to vet under Go 1.27 (`-vet=off`
  in the run command); with vet off all upstream tests pass at this commit.

## History

- 2026-09-14: written at edee2f91616c (after v1.19.2, 2026-04-07), hegel.dev/go/hegel v0.6.33.
