# typescript/query-string — sindresorhus/query-string (parse and stringify URL query strings)

Hegel property tests for [`query-string`](https://github.com/sindresorhus/query-string) 9.5.1,
pinned at `7fd81333` (main, 2026-09-01), the flat query-string library with seven array
formats (~15M weekly downloads). Plain ESM with three small runtime dependencies
(`decode-uri-component`, `filter-obj`, `split-on-first`), no build step. Tests are
`hegel/hegel.test.mjs` (run by `node --test`) with a model of the documented behaviour in
`hegel/model.mjs`, generators in `hegel/gen.mjs` and the zoo's harness `hegel/hegel-zoo.mjs`;
Hegel is `@hegeldev/hegel` 0.4.5, pinned in the harness (`HEGEL_PIN`, checked at load time)
and installed with `npm install --no-save`. Run with
`node --test --test-reporter=tap hegel/hegel.test.mjs` from the package root
(`HEGEL_TEST_CASES=n` sets the budget, `ZOO_COLLECT=1` records mismatches and the shapes seen
instead of failing at the first). No AI-contribution policy is published in the repository
(readme, `.github/` including `security.md`, checked 2026-09-20; there is no CONTRIBUTING
file); the zoo only records bugs. Upstream's own fast-check round-trip property in
`test/properties.js` is marked `test.failing`.

## What is tested

- **A model written from the readme** (`hegel/model.mjs`): pairs split at `&` and at the first
  `=`, a missing `=` giving `null`, `+` read as a space, percent-decoding with
  `decode-uri-component` (which the readme names), the seven `arrayFormat`s with their
  examples (`none`, `bracket`, `index`, `comma`, `separator`, `bracket-separator`,
  `colon-list-separator`) and `arrayFormatSeparator`, `sort` (default code-unit order, `false`,
  a function), `parseNumbers`/`parseBooleans`/`types` with the readme's precedence (a key's
  type first, the general options for what it does not apply to), and stringify's `strict`
  encoding, `skipNull`/`skipEmptyString`, `null` as a bare key and `undefined` dropped. Array
  markers are looked for on the key as written (an encoded bracket is text); key order is
  compared up to the engine's own rule that canonical array indices come first.
- **Round trip.** Random objects (0-5 keys from an alphabet with `& = + % [ ] : ; , | / ? #`,
  spaces, quotes, non-ASCII, and literals such as `100%`, `%20`, `a=b`, `true`, `1e3`,
  `[object Object]`; values strings, numbers including `-0`/`NaN`/`Infinity`, booleans,
  bigints, `null`, `undefined`, arrays of 0-4 of those) are stringified and parsed back with
  matching options in every array format, with separators from `, | ; : / $ @` and `+`. The
  expected object is the input with what the format cannot say removed: everything is text,
  `undefined` and skipped values vanish, a one-element array collapses to its element under
  `none`/`comma`/`separator`, an empty array vanishes except under `bracket-separator` (which
  writes `key[]`), an array whose every element is skipped vanishes, `null` elements read back
  as `null` under `none`/`bracket`/`index` and as `''` in the separator formats, and an empty
  key with a `null` value is an empty part that parse ignores.
- **Stringify and parse against the model** on the same objects and on random raw query
  strings (encoded and unencoded pieces, markers `[]`, `[n]`, `:list`, duplicate keys, `+`,
  bare keys, `&&`, a leading `?`/`#`/`&`/space, a trailing `&`, `=` or space, malformed
  percent sequences), with `parseNumbers`, `parseBooleans` and `types` (string, number,
  boolean, `string[]`, `number[]`, a function) drawn for the keys present. Accepted
  differences that the model reproduces: parse trims the string; a duplicate plain key
  collects under `none` and overwrites under every marker format; `types: 'string'` joins a
  collected array with the separator.
- **Stability**: `parse(stringify(parse(q)))` is `parse(q)` up to the same documented losses.
- **URL functions**: `extract` returns the query as written, `parseUrl` gives the base, the
  model's parse and the decoded fragment, `stringifyUrl(parseUrl(u))` parses back to the same
  thing, and `pick`/`exclude` keep exactly the chosen keys with their values, the base, and the
  fragment as written; URLs mix bases with userinfo/port/path/encoded path, relative and
  empty bases, and fragments with `=`, `&`, `?`, `%`, `#`, spaces and non-ASCII.
- Two shape spaces: CLEAN leaves out the shapes of the recorded bugs (marker-ending keys, the
  separator inside a bracket-separator element, `+` as separator, a key both plain and indexed,
  `sort: false` with `index`, encoded fragments through pick/exclude, object and function
  values); FULL has them all, and `knownForObject`/`knownForQuery` name the bug a mismatching
  case's shapes are about. Each bug has a pin.

## Properties

| Test | What it checks |
|---|---|
| `TestHegelParseInvertsStringify` | `parse(stringify(obj, o), o)` is the model's round-trip expectation, all formats and options |
| `TestHegelStringifyFollowsTheDocumentation` | `stringify(obj, o)` is the model's text |
| `TestHegelParseFollowsTheDocumentation` | `parse(q, o)` is the model's object, keys in the sort's order |
| `TestHegelStringifyAfterParseIsStable` | `parse(stringify(parse(q, o), o), o)` is `parse(q, o)` up to the documented losses |
| `TestHegelUrlFunctionsAgree` | `extract`, `parseUrl`, `stringifyUrl`, `pick`, `exclude` agree with each other and the model |
| `TestHegelPin…` | one plain test per recorded bug (see bugs.toml) |

## Oracles

The model in `hegel/model.mjs`, written from the readme (the W3C "collect URL parameters" rules
it points at, the array-format examples, the option descriptions); `decode-uri-component` for
percent-decoding, since the readme names it. No differential oracle: `URLSearchParams` has no
array formats and treats `+` and encoding differently enough that the comparison would be the
model anyway.

## Not tested

- `stringifyUrl` with a `query` object (only of `parseUrl`'s result), `encodeFragmentIdentifier`,
  `parseFragmentIdentifier: false`, `decode: false`, `encode: false`, and the `replacer` option.
- Keys named `__proto__` or other prototype names (the result is a null-prototype object; not
  a concern here).
- Astral and surrogate edge cases of the encoder (`encodeURIComponent` throws on lone
  surrogates, which is the platform's contract).

## History

- 2026-09-20: created (turn 316); 7 bugs recorded.
