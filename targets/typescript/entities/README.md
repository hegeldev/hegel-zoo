# typescript/entities — fb55/entities (against a model of the HTML specification)

entities is "encode & decode HTML & XML entities with ease & speed": the fastest HTML entity decoder
(a binary trie), used by htmlparser2, cheerio, commonmark.js and the AWS SDK (~215M weekly
downloads). The patch checks it against a model of the WHATWG character-reference algorithm and pins
2 bugs.

## How it is built

`src/` is TypeScript (upstream builds with tsc; `dist/` is not committed). `hegel/build.mjs` runs the
esbuild *binary* under `.hegel/` to bundle `src/index.ts` and `src/decode.ts` (the `entities/decode`
entry with `EntityDecoder` and the decode trees) into `.hegel/dist/*.mjs`. Hegel, esbuild and `he`
go under `.hegel/`; entities has no runtime dependencies.

## How it is tested

`hegel/hegel.test.mjs` runs under `node --test`; `hegel/hegel-zoo.mjs` is the zoo's shared harness.
The decoding oracle is the spec's "named character reference state", "numeric character reference
states" and "numeric character reference end state" written out over the library's **own tables**
(`maps/entities.json`, name → characters; `maps/legacy.json`, the names allowed without a semicolon):
longest identifier wins (identifiers include the semicolon), a legacy name in an attribute is not a
reference when `=` or an alphanumeric follows, strict mode needs the semicolon, NUL/surrogates/
> U+10FFFF become U+FFFD, C1 controls are remapped to windows-1252 (HTML only). Because the model
shares the data, every disagreement is algorithmic. `he` 1.2.0 is a second opinion on the HTML modes.

| Property | What it checks |
|---|---|
| `TestHegelDecodeLikeSpec` | strings of 1–8 fragments — table names (complete, truncated, extended, case-flipped, legacy or not, with and without `;`, followed by `=`, alphanumerics, `;`, `&`, spaces), decimal and hex references (0, leading zeros, C1 range, surrogates, U+FFFE/FFFF, U+10FFFF/110000, 32-bit and 50-digit values, 2040–2052-digit values for the length side channel), `&#;`/`&#x;`/`&#xg`/`& amp;`, adjacent references — through every entry point of every mode: `decodeHTML` (Legacy/Strict/Attribute), `decodeHTMLStrict`, `decodeHTMLAttribute`, `decodeXML`/`decodeXMLStrict`, `decode` with a level or an options object; `he.decode` in text and attribute mode is compared too |
| `TestHegelEncodeLikeSpec` | random strings (ASCII, controls, C1, Latin-1, BMP, astral, table values incl. the 93 two-code-point ones, U+00A0, noncharacters, lone surrogates, long plain runs for the inline/regex scan switch): exact models of `encodeXML`/`escape`, `escapeUTF8`, `escapeAttribute`, `escapeText`; structural check of `encodeHTML` and `encodeNonAsciiHTML` (exactly the documented characters are encoded, every reference well-formed and `;`-terminated, a name whenever the table has one, each reference decoding to the characters it replaced, ASCII output); `encode` routing for every `EncodingMode`/`EntityLevel`; round trips through `decodeHTMLStrict`/`decodeHTML`/`decodeHTMLAttribute`/`decodeXML` and `he.decode` |
| `TestHegelStreamingDecoder` | `EntityDecoder` fed one reference in random chunks (with a prefix and `offset` on the first write, `end()` when the input runs out) in Legacy/Strict/Attribute mode: characters consumed, code points emitted with their `consumed`, and the three `EntityErrorProducer` callbacks (`missingSemicolonAfterCharacterReference`, `absenceOfDigitsInNumericCharacterReference(consumed)`, `validateNumericCharacterReference(code)`) against the model; the remainder decoded one-shot agrees |
| `TestHegelTables` | (fixed) every one of the 2125 names, with/without `;` and with the attribute terminators, in every mode against the model (a name without its semicolon may contain a legacy name: `&centerdot` → `¢erdot`); every table value that needs encoding is encoded by name |

`ZOO_COLLECT=1` turns mismatches into `# COLLECT` counts instead of failures; `HEGEL_TEST_CASES`
(default 100) widens the sweep. Known bugs are skipped through the `Known` switches at the top of
the file (HTML round trips of strings with remapped C1 controls; the emission check for astral
named entities).

## Bugs

2 open, both pinned (see `bugs.toml`). The decoders agreed with the spec model on every input;
the bugs are at the encoder/decoder boundary and in the streaming API's contract:

- `encodeHTML`/`encodeNonAsciiHTML` write U+0080–U+009F as `&#128;`…, which HTML — and
  `decodeHTML` — read as the windows-1252 characters; the round trip loses 27 code points (1).
- `EntityDecoder` emits an astral named entity as two UTF-16 units although `emitCodePoint` is
  documented as receiving code points and numeric references arrive as one (2).

## Accepted differences and notes (not counted as bugs)

- A lone surrogate is encoded as a numeric reference to the surrogate (`&#55296;`), which decodes
  to U+FFFD; lone surrogates are not valid text and the round trip is not checked for them.
- `encodeHTML` encodes `\t`, `\n`, `\f` and the ASCII punctuation blocks `!-/`, `:-@`, `` [-` ``,
  `{-}` (`&Tab;`, `&excl;` …) but not `\r`, space, `~`, letters or digits — the code's bitset, which
  the readme's "such as `#`" only hints at; `encodeNonAsciiHTML` encodes `"&'<>` and non-ASCII.
- Which of several names a character gets (`&AMP;` vs `&amp;`, `&quot;` vs `&QUOT;`) is the
  generated encode map's choice and only checked to be *a* name for that value.
- `decodeHTML(s, mode)` with an unknown mode number behaves as Legacy. `&#x` followed by a
  non-digit is text (`&#x;` stays `&#x;`), as the spec's absence-of-digits error says.
- Legacy names match inside longer names without a semicolon (`&centerdot` → `¢erdot`,
  `&notin` → `¬in`) — the spec's longest-identifier rule, also what browsers and `he` do.

## Not tested

The `entities/escape` and `entities/decode` package entry points as such (the bundled sources are
tested), `determineBranch`/the trie layout, the html5lib-tests submodule (not fetched), the
browser bundle, the TypeScript types.

## History

- 2026-09-17: created at 0b16899 (v8.1.0), 4 properties, 2 bugs.
