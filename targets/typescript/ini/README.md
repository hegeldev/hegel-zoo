# typescript/ini — npm/ini (an INI encoder/decoder for node)

Hegel property tests for [`ini`](https://github.com/npm/ini) 7.0.0, pinned at `3c96c74f` (main,
2026-06-18), the INI parser/serializer used by npm itself (~107M weekly downloads). The first
TypeScript/JavaScript target of the zoo: plain CommonJS, no build step, no runtime
dependencies. Tests are `test/hegel.test.mjs` (ESM, run by `node --test`) with the zoo's small
harness `test/hegel-zoo.mjs`; Hegel is `@hegeldev/hegel` 0.4.5, pinned in the harness (`HEGEL_PIN`, checked at load time) and installed with `npm install --no-save`.
Run with `node --test --test-reporter=tap test/hegel.test.mjs` (after `npm install --no-save
@hegeldev/hegel@0.4.5`; `HEGEL_TEST_CASES=n` sets the budget, `ZOO_COLLECT=1` records
mismatches and the shapes seen instead of failing at the first).
No AI-contribution policy is published in the repository (CONTRIBUTING.md checked 2026-09-15;
it only asks contributors not to touch the template-managed files); the zoo only records bugs.

## Approach

- **Round trip against a model of the format.** Random objects (up to three levels of
  sections; keys from an alphabet of letters, digits, space, tab, `.`, `;`, `#`, `=`, `[`, `]`,
  both quotes, backslash and non-ASCII; values strings from the same alphabet plus CR/LF, the
  booleans, `null`, numbers, and the literal strings `true`/`false`/`null`/`undefined`/`''`/`'`
  and friends; arrays of scalars) are encoded with random options (`whitespace`, `align`,
  `sort`, `newline`, `platform: win32`, `bracketedArray: false`, a `section` prefix) and decoded
  again. The expected result is the object with what INI cannot say removed: numbers come back
  as their decimal text (`safe` JSON-stringifies them, `decode` never parses numbers), empty
  arrays and empty sections are not written, and with `bracketedArray` off a one-element array
  is its element. Everything else must come back identical, with a structural comparison that
  ignores prototypes (`decode` builds null-prototype objects) and key order.
- **`unsafe` undoes `safe`** for every string (the README presents them as inverses).
- **`decode` is a normal form**: on random INI-ish text (headers, comments, `k=v` lines with the
  format's characters, CRLF and blank lines) it must not throw, and decoding what it encodes
  must give the same object again (minus empty sections).
- The generators draw the shapes of all twelve recorded bugs by default and the properties fail
  on them: `TestHegelEncodeDecodeRoundTrips` and `TestHegelDecodeIsStable` shrink to the empty
  key (ini/12: `{ '': true }`, and the text `[]\n1=\n`), `TestHegelUnsafeUndoesSafe` to `\;`
  (ini/5; about one run in four lands on the lone quote of ini/8 instead, an equally minimal
  case). One property per bug (`TestHegelLiteralStringValuesRoundTrip`,
  `TestHegelKeysContainingEqualsRoundTrip`, ..., `TestHegelEmptyKeysRoundTrip`, listed below)
  draws that bug's shape region with random contents around it and shrinks to that bug; the
  pins remain as one regression example each. The classifier `shapes()` reads the recorded
  shapes off the input, counts them and names them in a failure message. `HEGEL_NO_KNOWN=1`
  makes the generators leave the shapes out (restricted alphabets and literal pools, blank-name
  fix-ups in the INI text, the residue filtered by the classifier, gates firing on under 1.5%
  of cases) and skips the per-bug properties, for a run that looks past the known bugs.

## Properties

| Test | What it checks |
|---|---|
| `TestHegelEncodeDecodeRoundTrips` | `decode(encode(obj, opt), opt)` against the model, all options |
| `TestHegelUnsafeUndoesSafe` | `unsafe(safe(s)) === s` |
| `TestHegelDecodeIsStable` | `decode` never throws on INI-ish text; `decode(encode(decode(t)))` is `decode(t)` minus empty sections |
| `TestHegelLiteralStringValuesRoundTrip` | values that read as literals (`true`, `1.5`, `null`) round-trip (draws the shape region of ini/1; expected failure) |
| `TestHegelKeysContainingEqualsRoundTrip` | keys containing `=` round-trip (draws the shape region of ini/2; expected failure) |
| `TestHegelKeysEndingInBracketsRoundTrip` | keys ending in `[]` round-trip (draws the shape region of ini/3; expected failure) |
| `TestHegelDottedSectionsWithChildrenRoundTrip` | dotted section names whose parent has children round-trip (draws the shape region of ini/4; expected failure) |
| `TestHegelBackslashBeforeEscapableUndoesSafe` | `unsafe(safe(s))` for strings with a backslash before an escapable character (draws the shape region of ini/5; expected failure) |
| `TestHegelSectionNamesContainingBracketRoundTrip` | section names containing `]` round-trip (draws the shape region of ini/6; expected failure) |
| `TestHegelNullUnderDottedKeysRoundTrip` | `null` under a dotted key round-trips (draws the shape region of ini/7; expected failure) |
| `TestHegelLoneQuotesRoundTrip` | values that are a lone quote round-trip (draws the shape region of ini/8; expected failure) |
| `TestHegelRepeatedKeysAcrossSectionsRoundTrip` | the same key in the root and a section round-trips (draws the shape region of ini/9; expected failure) |
| `TestHegelRepeatedBracketKeysRoundTrip` | repeated `[]` keys (arrays) round-trip with `bracketedArray` off (draws the shape region of ini/10; expected failure) |
| `TestHegelBackslashDotSectionNamesRoundTrip` | section names with a backslash before a dot round-trip (draws the shape region of ini/11; expected failure) |
| `TestHegelEmptyKeysRoundTrip` | the empty key round-trips (draws the shape region of ini/12; expected failure) |

## Bugs (see `bugs.toml`)

| id | severity | title |
|---|---|---|
| ini/1 | medium | the strings true, false and null do not round-trip: encode writes them bare and decode turns them into the JSON values |
| ini/2 | medium | a key containing = is quoted by safe() but the decoder splits the line at the first =, so the key and the value are both wrong |
| ini/3 | low | a key ending in [] is read back as an array key, so an object with the key a[] and the value v becomes {a: [v]} |
| ini/4 | medium | a section whose name contains a dot keeps the backslash escape when it has sub-sections: {"a.b": {c: {...}}} comes back under a key that still carries the backslash escape |
| ini/5 | medium | a backslash before a backslash, semicolon or hash is lost: safe() escapes ; and # but never the backslash itself, and unsafe() eats it |
| ini/6 | medium | a section name containing ] cannot be read back: the header line is parsed as a key with the value true |
| ini/7 | low | a null value under a dotted key at the top level is treated as a section and split: a.b = null becomes {a: {b: null}} |
| ini/8 | low | a lone single quote becomes the empty string: unsafe("'") strips it as a quoted value and safe() does not quote it |
| ini/9 | medium | with bracketedArray off, duplicate keys are counted over the whole file, so a key repeated in another section comes back as an array there |
| ini/10 | low | with bracketedArray off, a repeated key that ends in [] loses its name: the second value lands under the empty key |
| ini/11 | low | a backslash before a dot in a section name is read back as an escaped dot, and a section name ending in a backslash swallows the dot before its sub-sections |
| ini/12 | low | an empty key is written as =value, a line the decoder skips |

All twelve were found by the round-trip property in its first collect runs (`lib/ini.js` is 280
lines; a first reading suggested /1, /2, /5 and /6, the property added the rest), then read off
the source and pinned; the classifier's shapes are `ini/literal-string` (/1), `ini/key-equals`
(/2), `ini/key-brackets` (/3 and /10), `ini/dotted-parent` (/4), `ini/backslash` (/5),
`ini/section-bracket` (/6), `ini/null-dotted` (/7), `ini/lone-quote` (/8),
`ini/duplicates-across-sections` (/9), `ini/backslash-dot` (/11) and `ini/empty-key` (/12).
Under `HEGEL_NO_KNOWN=1` runs of 1000 and 3000 cases per property have no mismatch; by default
every failure at 3000 cases carries a recorded shape. Until 2026-09-24 the classifier was used
the other way round, to excuse a mismatch that had a known shape; the generators now draw the
shapes and the properties find the bugs (the harness also gained a per-property example
database key: all properties had shared one).

## Not bugs (modelled as documented)

- INI is untyped: numbers are written with `JSON.stringify` and read back as strings (`1.5` →
  `"1.5"`, `1e21` → `"1e+21"`); non-finite numbers are not generated (`NaN` would be written as
  `null`).
- An empty array and an empty section produce no lines and are absent after a round trip; with
  `bracketedArray: false` a one-element array is written as one `k=v` line and read back as a
  scalar (the README says repetition makes an array).
- `__proto__` keys and sections are dropped by `decode` (prototype-pollution guard); the
  generator never produces them.
- The `section` option only prefixes: a dotted section option nests (not generated).
- `undefined` values are not generated (`encode` writes the text `undefined`).

## Not covered (yet)

The `align` padding widths themselves (only that the result reads back), comments inside a
round trip (the encoder writes none), `bin/ini` (the CLI), and the merging of a
`[a.b]` section into an existing `a` object when `a` also has a scalar `b` (a collision the
generator reaches only rarely).

## History

- 2026-09-15: created at 3c96c74f (7.0.0); 12 bugs.
