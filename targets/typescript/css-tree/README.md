# typescript/css-tree — csstree/csstree (CSS tokenizer, parser, generator, walker and lexer)

css-tree is the CSS parser and AST toolkit behind csso, stylelint's value validation and many CSS
tools (~30M weekly downloads). It promises a CSS Syntax Level 3 tokenizer, a detailed AST with
source positions, a `generate` that writes an equivalent style sheet back, a walker over that AST
and a lexer that matches property values against the mdn-data value grammars. The patch checks
those promises against a second spec tokenizer, against each other and against the grammars over a
structured CSS generator, and pins 16 bugs.

## How it is built

`lib/` is plain ESM, so nothing is built. The runtime dependencies (`mdn-data`, `source-map-js`)
are installed without the dev tree (`--omit=dev`); Hegel and `@csstools/css-tokenizer` 4.0.1 (the
CSS Syntax tokenizer of PostCSS's csstools, used as oracle) go under `.hegel/`.

## How it is tested

`hegel/hegel.test.mjs` runs under `node --test`; `hegel/hegel-zoo.mjs` is the zoo's shared harness,
`hegel/gen.mjs` the CSS generators, `hegel/model.mjs` small models (line/column counting, structure
traversal, CSSOM string serialization) and `hegel/pins.mjs` the bug pins.

The stylesheet generator writes rules with combinator/pseudo/attribute/namespace selectors,
`&`-nested rules, at-rules (`@media` with level-4 range and nested conditions, `@supports`,
`@container`, `@layer`, `@import` with `layer()`/`supports()`, `@font-face`, `@keyframes`,
`@page`, `@property`, `@scope`, `@starting-style`, `@counter-style`, `@font-feature-values`,
`@nest`, unknown at-rules), declarations with hack prefixes and every spelling of `!important`,
values made of idents (with escapes and non-ASCII), numbers, every unit css-tree knows, hashes,
strings, urls in all quoting styles, unicode ranges, nested functions and brackets, comments in odd
places, and CDO/CDC tokens; a "soup" generator draws from a CSS-flavoured alphabet including NUL,
BOMs, escapes and unterminated constructs. A second generator builds values from the lexer's own
grammars (definition-syntax AST), and a third builds random definition-syntax ASTs.

| Property | What it checks |
|---|---|
| `TestHegelTokenizerAgreesWithTheReferenceTokenizer` | `tokenize` covers the source contiguously and gives the same token types and boundaries as `@csstools/css-tokenizer`; `ident.decode`, `string.decode`, `url.decode` and the parsed value/unit of numeric tokens equal the reference's decoded values |
| `TestHegelGenerateParseIsAFixpoint` | `parse` reports no structure warnings (`lexer.checkStructure`); when the parse is clean, `parse(generate(ast))` equals `ast` without locations, `generate` is idempotent, `generate(ast, {mode: 'spec'})` round-trips too and is no longer than the compact form, and the `declaration`/`declarationList`/`selectorList` contexts and `parseValue: false`/`parseRulePrelude: false` agree with the full parse |
| `TestHegelLexerMatchesValuesBuiltFromItsGrammar` | a value generated from a property's or type's grammar matches (`matchProperty`/`matchType`, as AST and as text), every top-level node has a trace, css-wide keywords match every property, `findValueFragments` finds something |
| `TestHegelWalkVisitsEveryNodeInStructureOrder` | `walk` enter/leave order (natural and `reverse`) equals a traversal driven by `lexer.structure`; `visit`, `find`/`findLast`/`findAll`, `this.skip`/`this.break`, `item`/`list` arguments and the walk context (`this.rule`, `this.atrule`, ... are the strict ancestors) |
| `TestHegelPositionsPointIntoTheSource` | with `positions: true` and random `offset`/`line`/`column`/`filename`, every node's `loc` is consistent with a line/column model of the source (LF, CRLF, CR, FF newlines), its text matches the node kind, children lie inside parents and siblings are ordered; `onToken` and `onComment` see contiguous tokens |
| `TestHegelPlainObjectAndCloneRoundTrip` | `clone` is deep and equal, `toPlainObject` gives arrays that generate the same text and `fromPlainObject` gives Lists back, `walk` over plain objects passes indices |
| `TestHegelListBehavesLikeAnArray` | `List` against an array model: every mutator, cursor-safe iteration while mutating, `nextUntil`/`prevUntil`, `reduce`/`some`/`map`/`filter` |
| `TestHegelNamesAndEncodersFollowTheirDocs` | `property()`, `keyword()`, `vendorPrefix`, `isCustomProperty` against a model of docs/utils.md; `string`/`ident`/`url` `encode` → `decode` round-trips and the encoded text is a single token in both tokenizers; `string.encode` matches CSSOM serialization for control-free strings |
| `TestHegelDefinitionSyntaxRoundTrips` | random definition-syntax ASTs generate/parse/generate to the same text, `walk` counts and `decorate`; the real grammars round-trip and `lexer.dump()` (compact and pretty) equals `definitionSyntax.generate` |

`ZOO_COLLECT=1` turns mismatches into `# COLLECT` counts instead of failures; `HEGEL_TEST_CASES`
(default 100) widens the sweep. Known bugs are gated through the `Known` switches at the top of
`hegel/hegel.test.mjs`, so the properties pass while the pins in `hegel/pins.mjs` fail.

## Bugs

See `bugs.toml` (css-tree/1–16): tokenizer deviations from CSS Syntax 3 (bad-string swallows the
newline, backslash at EOF, NUL not replaced, bad-url remnants skip the code point after an escape,
an escaped `url(` name is not a url token),
`url.decode` of whitespace-only and escaped-trailing-space urls, `string.encode`/`url.encode` inserting a
space after a NUL that follows a hex escape, `generate` not idempotent on a
backslash-newline and writing `-- >` as a CDC token, the walker's `visit: 'Declaration'` missing
@supports conditions, `property()` descriptors not shared across spellings, the descendant combinator
without `loc`, `onParseError` fired for valid nested conditions, and two CSS Nesting gaps (relaxed
nesting without `&` is Raw — upstream #268 —, nested `@layer` blocks are not style blocks).

## Accepted differences and notes (not counted as bugs)

- Non-ASCII ident code points: css-tree follows CSS Syntax 3 CR (≥ U+0080), the reference
  tokenizer the newer editor's draft (U+00B7 and the ranges above); the generators avoid U+0080–U+00B6.
- A leading BOM is skipped by css-tree (a documented convenience) and kept by the reference
  tokenizer; the tokenizer property strips it, and a BOM later in the source is not generated.
- `Operator` nodes for `+`/`-` keep the surrounding whitespace in `value`; the positions property
  compares trimmed text.
- The walk context (`this.rule`, `this.block`, ...) is the nearest strict ancestor, so inside the
  callback for a Rule node `this.rule` is the enclosing rule, not the node itself.
- `parse(text, {context: 'value'})` throws on leftover tokens; `lexer.checkStructure` only accepts
  Lists (not `toPlainObject` output); `keyword()` lower-cases even custom identifiers.
- With parse errors css-tree wraps bad content in Raw nodes that `generate` writes verbatim; where
  the Raw text ends is decided by the neighbouring tokens, so garbage is not a fixpoint and the
  fixpoint checks are restricted to sources parsed without Raw content.
- A `<'property'>` reference in a grammar excludes the property's top-level comma multiplier (CSS
  Values 4, `Lexer.js syntaxHasTopLevelCommaMultiplier`); the grammar-driven generator does the same.
- `@supports foo(bar)` becomes a `GeneralEnclosed` node (issue #295); `||` column combinators and
  `scroll-state()` container queries are not parsed and are not generated.

## Not tested

Source map output (`generate(ast, {sourceMap: true})`), the `TokenStream` class, `fork`/
`createSyntax` and custom node types, at-rule prelude/descriptor matching (`matchAtrulePrelude`,
`matchAtruleDescriptor`), selector-specific lexer checks, the CommonJS and `dist/` builds.

## History

- 2026-09-19: created at f898015 (3.2.1, 2026-09-16) with 9 properties and 15 bugs; the first CI run found
  css-tree/16 (100 cases hit a control character followed by NUL), gated and pinned the same day.
