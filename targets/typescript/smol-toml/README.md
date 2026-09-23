# typescript/smol-toml — squirrelchat/smol-toml (a TOML 1.1 parser and serializer)

Hegel property tests for [`smol-toml`](https://github.com/squirrelchat/smol-toml) 1.8.0, pinned at
`6d0f4774` (mistress, 2026-08-11), the most downloaded TOML parser on npm (~26M weekly downloads;
used by Vite, Prettier and many tools). TypeScript sources, no runtime dependencies, BSD-3-Clause.
No AI-contribution policy is published (README and `.github/` checked 2026-09-16; there is no
CONTRIBUTING); the zoo only records bugs.

Tests are `test/hegel.test.mjs` (ESM, run by `node --test`) with the zoo's harness
`test/hegel-zoo.mjs`, the generators and renderers `test/hegel-gen.mjs`, the oracle bridge and
bug-shape predicates `test/hegel-toml.mjs`, and the oracle `test/hegel-toml-oracle.py`. Hegel is `@hegeldev/hegel` 0.4.5.

## How it is built

`package.json` declares `devEngines.packageManager = pnpm` with `onFail: "error"`, which makes npm
refuse to install anything into the package (even `npm view` fails inside it). Hegel and the
TypeScript compiler are therefore installed with `npm install --prefix .hegel` (one command, so the
second install does not prune the first) and the harness imports Hegel from
`.hegel/node_modules`. The sources import each other as `./x.js`, so Node's type stripping cannot
run them; they are compiled with the pinned TypeScript 5.9.3 into `.hegel/dist`
(`test/tsconfig.hegel.json` spells out the options of the `@tsconfig/*` presets upstream extends
and rewrites the `.ts` type-import extensions). `.hegel/` is a build product outside the patch.
The parse properties need `python3` ≥ 3.11 for `tomllib`.

## How it is tested

- **Documents against a model** (`TestHegelParseAgreesWithTheModel`): a random value tree
  (tables, arrays of tables, arrays, inline tables, the four date-time kinds, integers in every
  base with underscores, floats with exponents/`inf`/`nan`, the four string kinds with every escape
  and the line-ending backslash) is rendered as a TOML document with random syntax — header
  sections, dotted keys or inline tables per table, `[[x]]` sections or inline arrays per array of
  tables, super-tables left implicit, bare/basic/literal key parts, whitespace, comments, CRLF —
  and the value `parse` returns must equal the model in all three integer modes (`integersAsBigInt`
  true, `"asNeeded"`, default; the default must reject an integer beyond 2^53). About a third of
  the documents use TOML 1.1 syntax (`\e`, `\x`, seconds omitted, newlines and trailing commas in
  inline tables).
- **Documents against tomllib** (`TestHegelParseAgreesWithTomllib`): the same documents (TOML 1.0
  ones) go to Python's `tomllib`, held open over two FIFOs with one JSON line per request; values
  cross in a canonical form (integers in decimal, floats by their IEEE bits, date-times to the
  millisecond in UTC, tables as sorted key sets), and tomllib, the model and smol-toml must agree.
- **Rejection differential** (`TestHegelMutationsAreJudgedAlike`): a valid document is mutated
  (characters and tokens inserted, deleted or replaced; lines duplicated, removed or swapped) and
  both parsers must accept or reject alike, with equal values when both accept. Disagreements are
  explained by a written list of the oracle's limits (TOML 1.1 syntax smol-toml accepts, dates
  such as February 30 that smol-toml documents as accepted, year 0000, which Python's datetime
  cannot hold) or by a recorded bug; anything else fails. This property found bugs 6-10.
- **`stringify` round trips** (`TestHegelStringifyRoundTrips`): random JavaScript objects
  (strings with every awkward character, numbers incl. -0, ±∞, NaN, unsafe integers, BigInts,
  booleans, `Date`, `TomlDate` of all four kinds, nested tables, arrays, arrays of tables, keys
  such as `""`, `__proto__`, `constructor`, `a.b`, `"`, DEL) are serialised with and without
  `numbersAsFloat`; `parse` must read the output back to the documented expectation (nulls and
  undefined dropped from tables, integral numbers as integers unless `numbersAsFloat`) and so must
  tomllib, and the documented rejections (null in an array, functions, symbols) must throw
  `TypeError`.
- **`TomlDate`** (`TestHegelTomlDateReadsWhatItWrites`): every date-time kind with random
  separators, fractions and offsets: the `is*` flags, the value, `toISOString()` as authored (to
  the millisecond, in the authored offset), the string read back, and `stringify`/`parse` of it.

Under `ZOO_COLLECT=1` the counts show which bug shapes and limits the generator reached and how
many mismatches had no known shape; the recorded bugs are skipped by shape (`Known` in the test
file) so the properties stay strict on everything else, and each has a pin. Rounds of 500–3000
cases per property were run until two consecutive rounds added nothing.

## What was found (10 bugs, `bugs.toml`)

| id | severity | title |
|---|---|---|
| smol-toml/1 | low | `stringify` writes `-0.0` as `0.0` under `numbersAsFloat` |
| smol-toml/2 | low | `TomlDate.toISOString()` keeps a lowercase `z` zone designator as authored |
| smol-toml/3 | medium | a `null` in a table written inline makes `stringify` throw a `TypeError` instead of being ignored |
| smol-toml/4 | medium | `undefined`, functions and symbols in inline tables and arrays are written as the word `undefined` |
| smol-toml/5 | low | a lone surrogate is written as a `\uD800` escape, which `parse` rejects |
| smol-toml/6 | medium | a quote after a line-ending backslash is dropped when it is one of the closing delimiter's extra quotes |
| smol-toml/7 | low | any JavaScript whitespace after a number or date is accepted (lone CR, NBSP, form feed, BOM, …) |
| smol-toml/8 | medium | inside an array, a comment after a scalar swallows the following lines up to the next comma or bracket |
| smol-toml/9 | medium | a quoted key containing `=` makes the parser skip to the next `=` in the document |
| smol-toml/10 | medium | an array-of-tables header closed by a single `]` (plus at most one other character before the line end) is accepted |

Bugs 6-10 are parser defects (one wrong value, four invalid documents accepted, three of them with
data silently dropped); 1, 3, 4 and 5 are in the serializer; 2 is in the date wrapper.

## Oracle limits and documented behaviour (not recorded)

- `tomllib` implements TOML 1.0 and normalises every CRLF of the document to LF before parsing,
  whereas the specification says newlines inside multi-line strings "remain intact" (smol-toml
  keeps them): comparisons with tomllib are made modulo that when the text contains CRLF.
- smol-toml documents that invalid calendar dates (`2023-02-30`) are accepted (V8's `Date` rolls
  them over) and that invalid UTF-8 is not rejected (unobservable from JavaScript strings); it
  also accepts year `0000`, which Python's `datetime` cannot represent. TOML 1.1 syntax is
  accepted by design.
- Integers beyond 2^53 throw in the default mode and `1.0` reads back as `1` (documented).
- A `null` element of a pure array of objects makes `stringify` throw a `TypeError` with the
  message of `Object.keys(null)` rather than the documented "arrays cannot contain null" — still
  a rejection, so not recorded.
- `Date` values are written as offset date-times in UTC; `TomlDate` carries millisecond precision
  only, and extra fraction digits are truncated by both implementations.

## History

- 2026-09-16: created at 6d0f4774 (1.8.0); 9 bugs.
- 2026-09-23: generators rewritten in combinator style (STYLE.md): a document is a tree whose nodes carry
  their spelling beside their data (`test/hegel-gen.mjs`), rendered by pure functions; the mutations are
  a list of edits applied modulo the live text; same properties and pins. 10 found by the generator
  rewrite's 1000-case mutation run.
