# yaml (go.yaml.in/yaml/v4)

[yaml/go-yaml](https://github.com/yaml/go-yaml) is the YAML project's own Go library, the
successor of gopkg.in/yaml.v3 (module `go.yaml.in/yaml/v4`, at v4.0.0-rc.6): a libyaml-lineage
scanner/parser/emitter (`internal/libyaml`) behind a new API — `Load`/`Dump` with functional
options (`WithIndent`, `WithCompactSeqIndent`, `WithQuotePreference`, `WithLineWidth`,
`WithUnicode`, `WithLineBreak`, `WithExplicitStart`/`End`, `WithFlowSimpleCollections`,
`WithCanonical`, `WithKnownFields`, `WithUniqueKeys`, `WithAllDocuments`, `WithSingleDocument`,
`WithStreamNodes`, `WithV2/V3/V4Defaults`, `Options`, `OptsYAML`, `WithPlugin`), streaming
`Loader`/`Dumper`, the legacy `Marshal`/`Unmarshal`/`Encoder`/`Decoder` (v3 defaults), `Node` with
comments, struct tags (`omitempty`, `flow`, `inline`, `-`), `TextMarshaler` support, typed errors
(`LoadError`, `DumpError`) and a `limit` plugin. It supports most of YAML 1.2 while keeping some
1.1 behaviour by design (see "Not bugs"). Apache-2.0; `CONTRIBUTING.md` has no AI policy. Tests in
`hegel_test.go`, external package `yaml_test` (dot import). The `[run] command` passes `-vet=off`
because `go get hegel.dev/go/hegel` raises the module's `go` directive to 1.26 and the newer vet
checks fail on upstream's own `node_test.go`.

## Oracles

- **yaml.v3** (`go.yaml.in/yaml/v3` v3.0.5, in-process): the previous major version; reads every
  document v4 writes and arbitrates the generated documents (a document yaml.v3 does not read as
  the tree is a test-suite defect, not a v4 bug). Several pins note that v3 shares the defect.
- **goccy/go-yaml** (`v1.19.3-0.20260407131736-edee2f91616c`, in-process, itself a zoo target):
  an independent Go implementation reading v4's output (not fed CRLF output or trees with
  YAML 1.1-only strings — see below).
- **PyYAML 6.0.3 with libyaml** (`yaml.CSafeLoader`, a YAML 1.1 reader), run as a child process
  over JSON lines and answering with a tagged tree; used on v4's output for trees without
  YAML 1.1-only resolutions.
- **A value model of our own**: random trees of null/bool/int (whole int64 and uint64 ranges)/
  float (every finite double, ±inf/nan)/string/sequence/mapping, strings built from pieces that
  look like YAML syntax (`- `, `: `, `#`, `?`, `<<`, `---`, `...`, `1e3`, `.inf`, `0x`, `1_0`,
  `yes`, `null`, `1:20`, `2001-12-14`, quotes, backslashes, tabs, newlines, non-ASCII, U+10FFFF,
  NBSP). The tree is converted to Go values for the encoder (integers spread over `int8`…`uint64`,
  sequences sometimes `[]string`, maps sometimes `map[any]any`) and written as **YAML 1.2 text by
  a generator with random syntax choices** for the decoder: plain/single/double-quoted scalars
  (`\uXXXX`/`\UXXXXXXXX`, `\ ` escapes), literal blocks with `-`/`+` chomping and explicit
  indentation indicators, hex/octal/binary/underscored/`+`-signed integers, `e`/`E`/`f`/`g`
  floats, block mappings and sequences at random indentation (compact `- k: v`, `-` on its own
  line, bare `key:` for null), flow collections with random spacing and trailing commas,
  comments, blank lines, `---`/`...`.
- **v4 against itself**: `Dump` under random options (v3 or v4 defaults, indent 2–9, compact
  sequence indent on/off, single/double/legacy quote preference, line width −1/0/10–200, ASCII-only
  output, CRLF line breaks, explicit `---`/`...`, flow simple collections), the legacy `Marshal`
  and an `Encoder` with `SetIndent(1..9)`/`CompactSeqIndent`/`DefaultSeqIndent`; read back by
  `Load`, `Unmarshal`, `Decoder.Decode`, `Load` into a `Node` + `Node.Decode`, and the Node dumped
  again under a second random option set. Streams: a `Dumper` writing 1–4 documents read back by a
  `Loader` document by document, by `Load(..., WithAllDocuments())`, and compared with
  `Dump(slice, WithAllDocuments())`. Structs: a 50-field struct (sized integers, floats, `time.Time`
  and `*time.Time`, `Duration`, `[]byte`, a `TextMarshaler`, an `IsZero` type with `omitempty`,
  `map[int]`/`map[bool]`/`map[float64]`, inline struct and inline map, flow struct/slice/map,
  renamed/omitempty/skipped fields, `interface{}`, a `Node` value, `**int`, nested maps and slices
  of structs) round-trips under every option set and is accepted with `WithKnownFields()` and
  `Decoder.KnownFields(true)`.
- **Numeric typing**: an integer literal (decimal, hex, octal, binary, underscored, `+`-signed)
  loads into `int8`…`uint64` exactly when the value fits (an error otherwise), into `float32`/
  `float64` as the conversion would, and into `interface{}` as an integer; float literals load
  into float fields exactly and into `interface{}` as `float64`.
- **Known fields**: `WithKnownFields()` and `Decoder.KnownFields(true)` fail exactly when unknown
  keys are present.

Properties (11 general): `TestHegelDumpThenLoadIntoAnInterfaceIsTheIdentity`,
`TestHegelDumpOutputIsReadBackByYamlV3AsTheInput`, `TestHegelDumpOutputIsReadBackByGoccyAsTheInput`,
`TestHegelDumpOutputIsReadBackByPyYAMLAsTheInput`, `TestHegelDumperStreamsAreReadBackDocumentByDocument`,
`TestHegelGeneratedDocumentsLoadToTheTreeTheyWereWrittenFrom`,
`TestHegelIntegerLiteralsLoadIntoNumericFieldsExactlyWhenTheyFit`,
`TestHegelFloatLiteralsLoadIntoFloatFieldsExactly`, `TestHegelStructsRoundTripThroughDumpAndLoad`,
`TestHegelKnownFieldsFailsExactlyWhenUnknownKeysArePresent`; 15 pinned expected failures below.
All general properties pass at 1000 cases × 3.

Numbers compare by value in the general properties (`1.0` is written as `1`, which every reader
takes for an integer — documented in `docs/`), so the int/float distinction is held only by the
typed-field properties. `[run] setup` checks `python3 -c 'import yaml'`; the test file passes
`HEGEL_TEST_CASES` through `hegel.WithTestCases` and wraps each property in a `recover` (the zoo's
Go conventions, see `HACKING.md`).

## Bugs (15)

| id | test | what |
|----|------|------|
| yaml/1 | `TestHegelCanonicalOutputKeepsScalarTypes` | `WithCanonical()` writes no tags and quotes every scalar: ints, bools, nulls, floats read back as strings |
| yaml/2 | `TestHegelStringsWhoseFirstContentLineStartsWithASpaceRoundTrip` | `"\n a"` → literal block without indentation indicator → `"\na"`; `"\n a\nb"` → unparseable |
| yaml/3 | `TestHegelLeadingSpaceMultilineStringsInSequencesAreReadableAtEveryIndent` | `[" a\nb"]` at indent ≠ 2 → `- \|4-` with content indented by 2: invalid for every parser (also `Marshal`, `SetIndent`) |
| yaml/4 | `TestHegelUniqueKeysCompareResolvedValues` | unique keys by raw text: `1`/`'1'` and any two collection keys rejected, `1`/`0x1`/`01`/`+1`, `true`/`True` accepted |
| yaml/5 | `TestHegelAPlainMergeIndicatorAsAValueIsAString` | plain `<<` as a value is dropped: `a: <<` → `{}`, `- <<` → `[]`, `<<` → null (v3: the string) |
| yaml/6 | `TestHegelOptsYAMLAcceptsTheDocumentedQuotePreferenceField` | `OptsYAML` rejects the documented `quote-preference` field |
| yaml/7 | `TestHegelNegativeZeroIsAnInteger` | `-0` is the float −0 (core schema, v3, goccy, libyaml: int 0); `!!int -0` errors |
| yaml/8 | `TestHegelTimestampsTheEncoderWritesAreReadable` | year 10000 / −1 times dumped as `!!timestamp` v4 cannot read, no error |
| yaml/9 | `TestHegelNumericLiteralsIntoDurationFieldsAreConsistent` | `d: 1e9` → 1s but `d: 1000000000` errors into `time.Duration` |
| yaml/10 | `TestHegelPointerToNodeTargetsReceiveTheNode` | `*Node` targets cannot receive scalars/sequences and lose mappings; the encoder writes them |
| yaml/11 | `TestHegelAnEmptyDocumentStreamCanBeDumped` | closing a `Dumper`/`Encoder` that wrote nothing, or `Dump([]any{}, WithAllDocuments())`, fails "expected STREAM-START" |
| yaml/12 | `TestHegelIndentThreeWithCompactSequencesWritesReadableNestedSequences` | `WithIndent(3)` + compact sequences: `- a:\n - null`, the nested sequence left of its parent — invalid |
| yaml/13 | `TestHegelStringsWhoseFirstContentLineStartsWithATabRoundTrip` | `"\ta\nb"` → literal block without indicator; v4, v3 and libyaml reject "tab where indentation expected" |
| yaml/14 | `TestHegelNullNodesWithAnEmptyValueStayNullInFlowStyle` | a null Node from `a:` / `- ` / `{a: }` is written `''` in flow style → the empty string |
| yaml/15 | `TestHegelDumpLeavesTheInputNodeUnchanged` | `Dump` clears resolvable tags and rewrites styles in the caller's Node; `!!float 1` decodes as int afterwards |

Details in `bugs.toml`. yaml/2, 3, 4, 8, 10, 11 and (partly) 14 are inherited from yaml.v3;
yaml/5, 7, 13 and 15 are regressions from v3 (v3 double-quoted strings with tabs and left Nodes
alone); yaml/12 and 14 come with the new options.

## Not bugs (documented or arbitrated against v4)

- YAML 1.1 behaviour kept by design (README): `yes`/`no`/`on`/`off` are booleans only into typed
  `bool` fields (strings into `interface{}`), `0777` is octal, no base-60. The encoder quotes
  such strings, so they survive round trips.
- Integral floats are written without a fraction (`1.0` → `1`) and read back as integers; the
  int/float tag mismatch is documented as acceptable. The general properties compare numbers by
  value for that reason; `1.0`/`1` and `-0.0`/`0` as `map[float64]`/`map[any]` keys therefore
  produce duplicate-key documents (the generators avoid them).
- `Load` requires exactly one document (`no documents in stream` for an empty input, `expected
  single document` for two) where `Unmarshal` keeps v3's leniency; `Load` also rejects trailing
  content (`[a]]`) v3 accepted — an improvement.
- `+9223372036854775808` (and larger `+`-signed integers) resolve to floats, as in v3.
- `[?a]` is the string `?a`, `a: !` is `""`, `&a&b` anchors are accepted (YAML 1.2-correct);
  `\x7f` is accepted inside scalars (v3 rejected it); a BOM inside a document becomes part of a
  key; `...\na` is accepted; implicit keys longer than 1024 characters are accepted (v3 rejected
  them).
- `time.Duration` into `interface{}` is a string (`1s`); `[]byte` is written as a sequence of
  integers; `time.Time` values are written with their zone offset and compare as instants.
- Exponent floats without a fraction (`1e+06`) are strings for goccy and PyYAML (their YAML 1.1
  heritage), so the generators keep a dot in every float; `2001-12-14 21:59:43.10 -5` is a plain
  string for v4 and a datetime for PyYAML (PyYAML's 1.1 timestamp form) — trees with such strings
  are not checked against the 1.1 readers.
- The `yts/` yaml-test-suite runner lists 222 known-failing suite cases; those are upstream's own
  known gaps and are not counted here.
- The block-sequence depth error message says `exceeded max depth of 100` when the default limit
  (10000) is hit through `- ` nesting: a message defect only, not counted.

## Generator avoidances

Each corresponds to a pin: multi-line strings whose first non-empty line starts with a space or
a tab (yaml/2, yaml/3, yaml/13); negative-zero floats (yaml/7); `map[any]any` with keys of
different types that print alike (yaml/4); `<<` is only produced quoted by the encoder (yaml/5)
and never written plain by the generator; `WithCanonical()` is not among the random options
(yaml/1); years outside 0001–9999 (yaml/8); no `*Node` field in the round-trip struct (yaml/10);
the stream property writes at least one document (yaml/11); indent 3 is left out of the random
indents (yaml/12); the Node re-dump of a generated document does not use
`WithFlowSimpleCollections` when the tree holds a null, since the writer produces bare `key:`
nulls (yaml/14). goccy is not fed CRLF output (goccy truncates single-quoted scalars folded
across CRLF — its own bug) nor trees with strings goccy reads differently by its own defects:
two-sign prefixes like `+-1` (go-yaml/16), keys ending in `<<` (go-yaml/24), underscored
near-numbers like `.0_` (goccy: 0).
