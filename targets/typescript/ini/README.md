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
- The shapes of the recorded bugs are read off the input by a classifier (`shapes()`), counted,
  and a case that has one is only checked when it happens to round-trip anyway; a case with
  none must round-trip exactly. Each shape has a pin. Under `ZOO_COLLECT=1` the counts show
  which shapes the generator reached and how many mismatches had no known shape.

## Properties

| Test | What it checks |
|---|---|
| `TestHegelEncodeDecodeRoundTrips` | `decode(encode(obj, opt), opt)` against the model, all options |
| `TestHegelUnsafeUndoesSafe` | `unsafe(safe(s)) === s` |
| `TestHegelDecodeIsStable` | `decode` never throws on INI-ish text; `decode(encode(decode(t)))` is `decode(t)` minus empty sections |

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
With every shape excluded three runs of 4 000 cases per property had no unexplained mismatch.

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
generator avoids by using distinct keys per object).

## History

- 2026-09-15: created at 3c96c74f (7.0.0); 12 bugs.
