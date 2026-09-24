# typescript/qs — ljharb/qs (a query string parser with nesting and arrays)

Hegel property tests for [`qs`](https://github.com/ljharb/qs) 6.16.0, pinned at `07b1d4d8` (main,
2026-09-11), the query-string library behind Express's `req.query` (~90M weekly downloads).
Plain CommonJS with two small runtime dependencies (`side-channel`, `es-define-property`),
no build step. Tests are `test/hegel.test.mjs` (ESM, run by `node --test`) with the zoo's
harness `test/hegel-zoo.mjs`; Hegel is `@hegeldev/hegel` 0.4.5, pinned in the harness
(`HEGEL_PIN`, checked at load time) and installed with `npm install --no-save`. Run with
`node --test --test-reporter=tap test/hegel.test.mjs` (`HEGEL_TEST_CASES=n` sets the budget,
`ZOO_COLLECT=1` records mismatches and the shapes seen instead of failing at the first).
No AI-contribution policy is published in the repository (README, SECURITY.md and
.github checked 2026-09-15; there is no CONTRIBUTING file); the zoo only records bugs.

## Approach

- **Round trip against a model of the format, across the option matrix.** Random objects
  (three levels of objects and arrays; keys from an alphabet with the format's characters
  `& = + % , ; | . # ?`, brackets 6% of the time, non-ASCII and astral characters, and
  literals such as `utf8`, `constructor`, `%2E`, `a[b]`; values strings from a wider alphabet
  (3% with a lone surrogate), booleans, `null`, `undefined`, numbers, Dates, and literals
  such as `&#65;`, `x,y`, `utf8=%E2%9C%93`) are stringified and parsed again with a matching
  pair of options: `arrayFormat` indices/brackets/repeat/comma (with `commaRoundTrip`),
  `allowDots` with or without `encodeDotInKeys`/`decodeDotInKeys`, `strictNullHandling`,
  `skipNulls`, `allowEmptyArrays`, `charset` iso-8859-1 with or without
  `interpretNumericEntities` and the `charsetSentinel` (parse sometimes told the charset only
  by the sentinel), `format` RFC1738, `encodeValuesOnly`, `encode: false`, the delimiters
  `& ; |`, `addQueryPrefix`/`ignoreQueryPrefix`, a string-comparison `sort`, `plainObjects`.
  The expected result is the object with what the format cannot say removed: everything is
  text (numbers, booleans and dates come back as the text written), `null` is `''` unless
  `strictNullHandling`, `undefined` and empty objects vanish, an empty array vanishes unless
  `allowEmptyArrays`, a one-element array under `repeat` is its element and under `comma` a
  scalar unless `commaRoundTrip`, `comma` joins nulls as `''`, and under iso-8859-1 a character
  above U+00FF is its numeric entity unless interpreted. Comparison is structural and ignores
  prototypes (`plainObjects` gives null-prototype objects) and key order.
- **Parse is a normal form.** Random query strings from pieces that mean something to the
  parser (bracket groups, indices, `[]`, dots, `%5B`/`%2E`/`%252E`, `__proto__`,
  `constructor`, the utf-8 sentinels, `+`, bare `%`, entities) with random parse options
  (`comma`, `allowDots`, `decodeDotInKeys`, `duplicates`, `depth` including 0 and `false`,
  `arrayLimit` from -1 to 25, `parseArrays: false`, `allowSparse`, `allowPrototypes`,
  `plainObjects`, both charsets, the sentinel, `strictDepth`, `throwOnLimitExceeded`,
  `parameterLimit`, `strictMerge: false`): parse must not throw (a `RangeError` is allowed
  only under `strictDepth`/`throwOnLimitExceeded`), must not leave holes without
  `allowSparse`, must not produce a `__proto__` key or an array longer than `arrayLimit` under
  `throwOnLimitExceeded`, and stringifying the result with `indices` and parsing it again
  must give the same result.
- **Agreement with the WHATWG `URLSearchParams`** on flat objects of strings, both ways
  (`URLSearchParams` reads what `qs.stringify` writes in both formats; `qs.parse` reads what
  `URLSearchParams` writes).
- The shapes of the recorded bugs are read off the input by a classifier (`shapes()`), as are
  the format's documented limits (`limit/…`: empty and numeric keys, prototype names,
  unencoded keys under `encodeValuesOnly`/`encode: false`, dots in keys under `allowDots`
  without `encodeDotInKeys`, nesting inside arrays under brackets/repeat/comma, literal entity
  text, a literal `%2E` with `encodeDotInKeys`). A case with a shape is only checked when it
  round-trips anyway; a case with none must round-trip exactly. Each bug shape has a pin.

## Properties

| Test | What it checks |
|---|---|
| `TestHegelParseUndoesStringify` | `parse(stringify(obj, o), o)` against the model, all options |
| `TestHegelParseIsANormalForm` | parse never throws (bar the documented RangeErrors), no holes, no `__proto__`, `arrayLimit` honoured under `throwOnLimitExceeded`; `parse(stringify(parse(s)))` is `parse(s)` |
| `TestHegelAgreesWithURLSearchParams` | flat string objects through `URLSearchParams` and back, both directions |

## Bugs (see `bugs.toml`)

| id | severity | title |
|---|---|---|
| qs/1 | medium | the comma arrayFormat writes its separators percent-encoded, so parse with comma: true never splits the array it wrote |
| qs/2 | medium | under iso-8859-1 a plus sign is written bare and read back as a space |
| qs/3 | low | a lone surrogate in a string is fused with the following code unit into one four-byte sequence, so the next character is swallowed |
| qs/4 | medium | a key containing [ or ] cannot be written: the parser turns %5B and %5D back into brackets before splitting keys |
| qs/5 | low | interpretNumericEntities decodes &#N; in values only, so a key written under iso-8859-1 with a character above U+00FF comes back as entity text |
| qs/6 | low | sort is applied to array indices as strings, so under brackets or repeat an array of eleven or more elements is written out of order |
| qs/7 | low | with allowEmptyArrays a[]= (an array holding one empty string, as brackets writes it) parses as an empty array |
| qs/8 | low | with encodeValuesOnly, encodeDotInKeys writes a dot as %2E once, which the parser percent-decodes to a dot before it splits the key |
| qs/9 | low | with plainObjects or allowPrototypes a [__proto__] segment leaves an empty object where the key was |
| qs/10 | medium | with allowEmptyArrays the k[] of an empty array is written without the encoder, so a key containing & (or =, +, %XX) breaks the query string |
| qs/11 | medium | encodeDotInKeys re-encodes the dots of the prefix at every level, including the allowDots separator, so nesting three levels deep collapses |
| qs/12 | medium | under iso-8859-1 with interpretNumericEntities a comma-split value is joined back into one string |
| qs/13 | medium | with comma: true a comma-split value under an empty-bracket key (a[]=x,y) is wrapped before the arrayLimit check, so the inner array escapes the limit |
| qs/14 | medium | with arrayFormat comma and encodeValuesOnly the array elements are encoded without the charset, so under iso-8859-1 a character above U+007F is written as utf-8 bytes instead of an entity |

/1, /2, /3, /4, /5, /6 and /8 came from probing the source (`lib/parse.js` 416 lines,
`lib/stringify.js` 378, `lib/utils.js` 451) before the properties were written; /7, /9, /10,
/11 and /12 were found by the round-trip and normal-form properties in their first collect
runs (the `]`-in-a-nested-key half of /4 as well). With every shape excluded, 6 000 cases per
property had no unexplained mismatch. /13 and /14 came with the rewrite of the generators
(2026-09-24): the old test had met /13 about once in 8 000 normal-form cases as an unexplained
failure, and /14 lay behind the 55% of round trips its classifier explained away; the rewrite
draws alphabets and literals filtered by the classifier itself, so 98% of round trips are
checked and the remaining gates fire on under 2%.

## Not bugs (modelled as documented)

- The format is untyped: numbers (`1e21` → `1e+21`), booleans and Dates (ISO 8601) come back
  as text; `null` is `''` unless `strictNullHandling`; `undefined`, empty objects and (without
  `allowEmptyArrays`) empty arrays are not written.
- Brackets, repeat and comma do not preserve nesting inside arrays (`[[1], [2]]` flattens,
  `[{b: 1}, {b: 2}]` merges): the classifier skips them; `indices` is checked fully.
- Keys that are canonical array indices (`{a: {0: 'x'}}`) come back as arrays; `''` keys are
  dropped (upstream's `empty-keys-cases.js` documents this); prototype names (`constructor`)
  are dropped without `allowPrototypes`/`plainObjects`; `__proto__` is never generated.
- With `allowDots` a dot in a key nests unless `encodeDotInKeys`; a literal `%2E` in a key is
  indistinguishable from an encoded dot under `encodeDotInKeys`; literal `&#N;` text is
  indistinguishable from an entity under iso-8859-1 with `interpretNumericEntities`.
- `encodeValuesOnly` and `encode: false` leave keys (and values) raw, so keys with `& = + %XX
  [ ]` or the delimiter are the caller's problem.
- `parseArrays: false` still produces arrays for repeated keys (README: "duplicate keys may
  still produce arrays").
- `strictMerge: false` restores the legacy merge in which a primitive that collides with an
  object becomes a key with the value `true` (README), a boolean the format cannot write back.
- `depth` (default 5) lumps the remaining segments into one key; deeper objects are not
  generated in the round trip and the normal form re-parses with `depth: Infinity`.

## Not covered (yet)

`arrayLimit` and `parameterLimit` on the stringify side (arrays are at most 13 long), custom
`encoder`/`decoder`/`serializeDate`/`filter` functions, `duplicates: first/last` in the round
trip (only in the normal form), `interpretNumericEntities` on the sentinel-only charset switch
beyond what the round trip draws, and `allowSparse` in the round trip.

## History

- 2026-09-15: created at 07b1d4d8 (6.16.0); 12 bugs.
- 2026-09-24: generators rewritten in combinator style (test/gen.mjs; one record per property,
  the round trip's object drawn from alphabets filtered by the classifier, the query as a list
  of parts); qs/13-14 found by the rewrite. 3 properties pass, 14 expected failures.
