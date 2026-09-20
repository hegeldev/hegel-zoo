# yaml

[yaml](https://github.com/eemeli/yaml) is the `yaml` npm package: a YAML 1.1/1.2 parser and
stringifier with a lossless CST, a Document/node API and the standard schemas. Pinned at 9fa8098
(2026-09-20), the 3.0.0-2 prerelease of the v3 rewrite (collections around a Map, `doc.value`,
Array-based sequences), ISC. yaml@2.9.1, the previous stable release, is installed under
`.hegel/` as a second implementation. The setup bundles `src/index.ts` and `src/test-events.ts`
with esbuild into `hegel/yaml3.mjs` and `hegel/test-events.mjs` (no runtime dependencies) and
fetches the yaml-test-suite submodule. Tests: `hegel/hegel.test.mjs`, run with `node --test`.
`ZOO_FULL=1` opens the gates around the known bugs; `ZOO_COLLECT=1` prints mismatch statistics;
`ZOO_TRACE=<file>` writes each case's input before it runs (how the lexer hang was found).

`docs/CONTRIBUTING.md` requires LLM use in issues, pull requests and comments to be declared and
pre-approved. The zoo files nothing upstream; anyone reporting these findings should read that
section first.

## Oracles

- `hegel/writer.mjs`: a randomised YAML writer (from the js-yaml target) that renders a random tree
  of plain values in random styles (block/flow collections at random indentation, plain/quoted/
  literal/folded scalars, explicit keys, anchors, matching `!!` tags, comments, markers, a `%YAML`
  directive), staying inside what YAML 1.2 core and 1.1 readers agree on; the tree is the expected
  value. Plain-safety of a string is decided with yaml@2 under both schemas.
- yaml@2.9.1 as a second implementation: same error verdict and same values on every source,
  reads v3's output and v3 reads its output (the differences are counted, and were all v2's own).
- The language: `parse(stringify(x, opts), opts)` deep-equals `x` over the ToStringOptions matrix;
  `lex()` and `CST.stringify` reproduce the source; a plain JS model of the Document API.
- The library's own regular expressions for the YAML 1.1 types (documented deviations from the
  type repository) and the YAML 1.2 core schema, for plain scalar resolution and values.
- The yaml-test-suite (351 files) through the library's event format, as a check.

## Properties

| Test | Checks |
| --- | --- |
| `TestHegelWrittenDocumentsParseToTheirTree` | The writer's documents parse without errors or warnings to the tree, `parse` agrees with `parseAllDocuments`, yaml@2 reads the same, `toString()` re-parses to the tree in v3 and in yaml@2 |
| `TestHegelLexerAndCstAreLosslessAndParsingNeverThrows` | On written, mutated and hostile sources: `lex()` tokens (minus the C0 markers) and `CST.stringify` reproduce the source, `parseAllDocuments`/`toJS` never throw, error `pos`/`code` are sane, yaml@2 gives the same verdict and values |
| `TestHegelStringifyThenParseGivesTheValueBack` | Random values (objects, arrays, Map/Set with `mapAsMap`, Dates and bytes under yaml-1.1, BigInt with `intAsBigInt`) through `stringify`/`parse` with random `ToStringOptions`, schema and version; yaml@2 reads v3's output and v3 reads yaml@2's |
| `TestHegelDocumentEditsFollowTheModel` | `Document` built from a value, then `set`/`delete`/`has`/`get`/`getPair`/`keyOf`/`pairs()` on maps and `push`/`set`/`splice`/`unshift`/`shift`/`reverse`/`fill` on sequences against a plain JS model, `toJS()` and `toString()` re-parse after each step, `clone()` |
| `TestHegelCstScalarTokensRoundTrip` | `CST.createScalarToken` / `setScalarValue` for random strings and types resolve back to the value, and their source parses to it |
| `TestHegelPlainScalarsResolveLikeTheSchema` | Plain scalars under core, yaml-1.1 and failsafe resolve to the type the schema's rules give, with the numeric value (bases, underscores, sexagesimal) |
| `TestHegelLineCounterAgreesWithBruteForce` | `lineStarts` and `linePos` against a brute-force count; pretty error positions agree with the counter |
| `TestHegelYamlTestSuitePasses` | Every yaml-test-suite case: CST round trip, event stream, error verdict, JSON, stringify + re-parse (upstream's three skips kept) |

Gated in the default run (counted, then skipped): sources with a lone CR or U+2028/U+2029 (the lexer
hang, gated before `lex` is called), multi-line plain scalars taken during error recovery (line
counter), block scalar tokens at indent 0, `fill()` over more than one slot, strings with a
whitespace-only line, a null value in a flow mapping under the JSON schema, a tagged scalar
overwritten by `set()`, block scalar tokens for values with leading spaces, `-0.0e+0` in the writer's
documents, `toJS()` of an erroneous document, aliases to undefined anchors, root strings starting with
whitespace, leading-space lines under an `indent` other than 2, timestamps before the year 100, output
containing the word undefined, empty `!!binary` at unlimited width, `---`/`...` scalars on the marker line, empty sequence values under
`collectionStyle: block` with `indentSeq: false`. Not judged: NUL characters (v3 rejects them
in comments where yaml@2 read on; YAML forbids them anywhere), `nullStr: ""` in flow collections (it cannot be represented
there), the JSON schema writing non-finite numbers as `null` (as `JSON.stringify` does), and
yaml@2's own output when v3 rightly rejects it (`!!set` with `simpleKeys`). Pins (`TestHegelPin*`)
reproduce the bugs in `bugs.toml` and are listed as expected failures; the hang pin runs the lexer
in a worker with a five-second limit.

Two source reviews (parser/composer; nodes/stringify/schemas) named yaml/1-8, 10-19 and 21 before or
alongside the properties; every claim was confirmed with a pin, and the properties found yaml/1
(as a hang), 4, 5, 6, 7, 8, 9, 15, 20, 22, 23, 24, 25, 26, 27, 28, 29 and 30 on their own (the writer's mutated documents
hit the CST shapes).

## Not tested

- Comments and blank-line preservation through `toString()` beyond value equality; `keepSourceTokens`;
  `Composer` streaming API; `visitAsync`; the CLI; `applyReviver`/`replacer`; custom tags;
  `merge`/`createMergePair`; `!!omap`/`!!pairs` beyond what stringify of Map/Set exercises;
  `maxAliasCount`; `logLevel`; `strict: false` details; `compat`/`customTags`.
- Timing (the lexer hang is the only non-termination pinned).

## History

- 2026-09-20: created (turn 323); 30 bugs recorded.
