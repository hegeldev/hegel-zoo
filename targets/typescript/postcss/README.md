# typescript/postcss — postcss/postcss (parser, stringifier and AST API against themselves)

PostCSS is the CSS parser/AST/stringifier behind Autoprefixer, Tailwind, stylelint and cssnano
(~100M weekly downloads). The library promises a byte-exact `parse → toString` round trip, an AST
whose `raws` carry every formatting detail, exact source positions, and a node API for plugins.
The patch checks those promises against each other over a structured CSS generator and pins 7 bugs.

## How it is built

`lib/` is plain CommonJS, so nothing is built. The runtime dependencies are installed without the
dev tree (`--omit=dev --legacy-peer-deps`: the dev tree has a `typescript` peer conflict that npm
refuses even when it will not install it); Hegel and `postcss-parser-tests` (upstream's parser
fixtures, a devDependency) go under `.hegel/`.

## How it is tested

`hegel/hegel.test.mjs` runs under `node --test`; `hegel/hegel-zoo.mjs` is the zoo's shared harness.
There is no independent CSS parser as oracle; the properties are round trips and metamorphic
relations between the parser, the stringifier and the node API, plus a model of `list.split`.

The generator writes nested stylesheets (depth ≤ 4) from rules with combinator/pseudo/attribute
selectors and comments inside them, at-rules with and without blocks and params, declarations
with `*`/`_` hacks, functions (`url()` in all quoting styles, nested `calc()`/`var()`), strings
containing `;{}/*`, escapes (`\\31 23`, `\;`, `a\\<newline>b`), `!important` in every spelling
(`!IMPORTANT`, `! important`, with comments and newlines around it), custom properties with
`{a:b}` blocks, empty and whitespace-only values, stray `;`/`{}`, BOMs and `\\r\\n`/`\\f`
whitespace. 25% of the round-trip cases are additionally damaged with random junk.

| Property | What it checks |
|---|---|
| `TestHegelRoundTripExact` | `parse(css).toString() === css` byte for byte, also through `stringify(root, builder)`, `root.clone()`, `fromJSON(JSON.parse(JSON.stringify(root.toJSON())))` (text and structure) and `postcss().process(css, {from: undefined}).css`/`.root`; on a `CssSyntaxError` the error has a valid line/column/offset and `toString()` names the reason |
| `TestHegelMutateStringifyReparse` | 1–8 random API operations on a parsed tree (`append`/`prepend`/`insertBefore`/`insertAfter` with nodes or CSS strings, `remove`, `replaceWith`, `cloneBefore`/`cloneAfter`, `removeAll`, `each`+`remove`, `walk` with clone-and-remove, `assign`, `cleanRaws`, setting `prop`/`value`/`important`/`selector`/`selectors`/`name`/`params`/`text`, moving nodes between two parsed trees), then `parse(root.toString())` must have the same structure (types, props, values, importance, selectors, names, params, comment texts, nesting) as the mutated tree, stringify again identically and survive the JSON round trip |
| `TestHegelSourcePositions` | for every node: `start`/`end` line, column and offset agree with `Input.fromOffset` and with a text-based count (`end.offset` exclusive, `end.line/column` naming the last character); the range starts with the node's selector/`@name`/hack+prop, contains the raw value, ends at `}` for blocks, is exactly `/*left text right*/` for comments; children lie inside their parent, siblings do not overlap; `rangeBy({})`, `positionInside()` and `node.error()` agree with the offsets; the root spans the whole input |
| `TestHegelListSplit` | `list.space`/`list.comma`/`list.split(s, seps, last)` against a model that respects quotes, escapes and parentheses |
| `TestHegelParserTestsFixtures` | (fixed) every case of `postcss-parser-tests` 8.10.0 round-trips and produces exactly the fixture AST (`jsonify`) |

`ZOO_COLLECT=1` turns mismatches into `# COLLECT` counts instead of failures; `HEGEL_TEST_CASES`
(default 100) widens the sweep. Known bugs are skipped through the `Known` switches at the top of
the file (trailing whitespace of last custom properties, their `source.end`, comments in
`raws.between`, hack prefixes in root-level `raws.before`, param-less at-rules before `}`/EOF,
whitespace left by dropped comments, `! important` followed by whitespace).

## Bugs

7 open, all pinned (see `bugs.toml`). The round trip itself never failed: every bug is in what the
AST *means* or in what the stringifier emits for a changed tree.

- A last custom property without a semicolon takes the block's closing whitespace into its value,
  and the stringifier omits exactly that semicolon, so appending `--x: 1` to a rule changes the
  re-parsed value to `"1\n"` (1); its `source.end` also stops before that whitespace (2).
- The autodetected `colon` raw keeps the characters of a comment between property and colon, so
  `b/*x:y*/:c` makes every raws-less node print as `d::e`, which postcss cannot parse (3).
- `Root.normalize` copies a neighbour's `raws.before` verbatim, spreading `*`/`_` hack prefixes to
  inserted nodes or, on `prepend`, to the old first node (4).
- A param-less childless at-rule before `}` or EOF has no `source.end` (5).
- A dropped trailing comment leaves its whitespace in `value` (`x: 1 /*c*/;` → `"1 "`) (6).
- `x: none! important ;` is not important; the value is `"none! important"` (7).

## Accepted differences and notes (not counted as bugs)

- The stringifier rewrites `<style`, `</style` and `<!--` in any raw or value as `\3c style` …
  (a deliberate defence against breaking out of an HTML `<style>` element), which breaks
  byte-exactness for such inputs; the generator does not produce them.
- A statement that starts with a `--` word and contains a colon is a custom property, even
  `--x > a:hover {}` (then `Unknown word`); the CSS Syntax spec's rule is "ident starting with `--`
  followed by a colon", so `--x:hover {}` agrees and the combinator form is a corner the parser
  does not distinguish. The generator prefixes such selectors with `.`.
- Comments are kept in `raws` (`raws.value.raw`, `raws.important`, `raws.between`, `raws.after`),
  not as nodes, when they sit inside a declaration or after an unterminated at-rule at the end of a
  block; once the surrounding semicolon disappears (the declaration becomes last, the at-rule is
  removed) the same text re-parses with the comment as a node. The mutation property normalises
  those raws before mutating and documents it here rather than as a bug; the trailing-whitespace
  part of it is bug 6.
- `x: a:b` without quotes is `Missed semicolon`, `--x: {` is `Unclosed block`, a `!` with nothing
  after it is part of the value: parser decisions, not bugs.
- `end.offset` is exclusive while `end.line/column` are inclusive (documented in `lib/node.js`).
- Custom properties keep their raw value including leading/trailing whitespace and comments
  (`--x: a{b}` is a value, not a rule), and `!important` is still recognised on them.
- `raws.important` with a trailing comment (`!important/*c*/;`) and `! important` spellings
  round-trip exactly; only the shape of bug 7 is misread.

## Not tested

Source maps (`map` options, `PreviousMap`), `LazyResult`/plugins/async processing, `Document`
and custom syntaxes (`parser`/`stringifier`/`syntax` options), `Result.warn`/`messages`,
`CssSyntaxError.showSourceCode` colouring.

## History

- 2026-09-17: created against 15471986 (8.5.28); 7 bugs.
