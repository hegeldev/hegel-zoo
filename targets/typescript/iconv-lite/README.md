# typescript/iconv-lite — pillarjs/iconv-lite (against Python's codecs and TextDecoder)

iconv-lite converts between JavaScript strings and some ninety character encodings in pure
JavaScript (~210M weekly downloads: Express's body-parser, Nodemailer, Grunt). The pin is the
1.0.0-alpha.2 rewrite (Node >= 22, UTF-16 and UTF-7 through the WHATWG rules, new UTF-32). The
patch checks every codec against Python's `codecs` module, the platform's `TextDecoder`, its own
round trips and its own streaming form, and pins 7 bugs.

## How it is built

No build: `lib/index-node.js` is CommonJS with no runtime dependencies; Hegel goes under
`.hegel/`. The oracle needs `python3` on PATH (stdlib only: `codecs`, `base64`, `json`).

## How it is tested

`hegel/hegel.test.mjs` runs under `node --test`; `hegel/hegel-zoo.mjs` is the zoo's shared
harness. `hegel/oracle.py` is held open for the whole run and answers over two FIFOs (one JSON
line per request, bytes as base64, see `hegel/enc.mjs`): decode and encode with
`errors=replace` or strict, whole decode tables, whole encode tables, and a CESU-8 model
(each UTF-16 code unit as UTF-8 with `surrogatepass`).

Tables come first. At start the harness compares iconv-lite's decode table with Python's for
every single byte, every two-byte sequence of the multi-byte codecs, EUC-JP's 0x8F plane and
GB18030's four-byte BMP plane, and the encode tables for every BMP character; the cells where
the two disagree (table flavours: WHATWG's Shift_JIS versus cp932's private-use area, GBK's
extensions, Big5-HKSCS 2008, the old Mac tables, GB18030-2005 versus -2022) are recorded, and
a generated case that touches one is counted, not judged. What is judged is the code: the
trie walk and resynchronisation on invalid bytes, the four-byte GB18030 arithmetic, surrogates,
sequences, chunk boundaries, BOMs, labels.

| Property | What it checks |
|---|---|
| `TestHegelRoundTripsThroughEveryEncoding` | `decode(encode(s)) == s` for text drawn from the codec's own repertoire (found by decoding random valid bytes), for all 90 codecs, with and without `addBOM`; the hex codec round-trips bytes |
| `TestHegelStreamingMatchesOneShot` | `getDecoder().write` over random chunks (empty chunks, splits inside sequences and BOMs) equals one-shot `decode`, on valid, mutated and junk bytes; `getEncoder().write` over random string chunks (splits inside surrogate pairs) equals one-shot `encode` (UTF-7 compared by decoded text: its encoder is stateless by design) |
| `TestHegelUnicodeCodecsAgreeWithPython` | UTF-8, UTF-16LE/BE, UTF-32LE/BE, the BOM-marked `utf16`/`utf32` and UTF-7: encoding equals Python's (UTF-7: each side reads the other's form); decoding of mutated bytes, lone surrogates included, equals Python's `errors=replace`; `fatal: true` throws exactly when Python's strict decode fails; CESU-8 against the code-unit model |
| `TestHegelTableCodecsAgreeWithPython` | the eight multi-byte codecs and the single-byte ones Python has: encoding of repertoire text with strangers equals Python's (`?` for the untranslatable); decoding of valid, mutated and junk bytes equals Python's `errors=replace` off the disagreeing cells, with `TextDecoder` as tie-breaker where Python departs from the WHATWG rule for how many bytes an ill-formed sequence consumes |
| `TestHegelBOMOptionsAreHonoured` | `addBOM` prepends U+FEFF (default true only for `utf16`/`utf32`), `stripBOM` strips exactly one, the callback fires exactly when a BOM was present, `stripBOM: false` keeps it, all under random chunking; the auto codecs follow a big-endian BOM, detect the order of Latin text without one in either endianness, and fall back to `defaultEncoding` on undecidable input |
| `TestHegelLabelsFollowWHATWG` | every alias resolves in any case with ASCII whitespace around it and a year appended; a label with a forbidden character (C0 except ASCII whitespace, DEL to NBSP, U+2028/9) is rejected; any label `TextDecoder` accepts resolves to the same codec (or an ASCII-compatible one where WHATWG unifies ISO-8859-1/9, ASCII and TIS-620 into Windows code pages) |
| `TestHegelStreamsMatchOneShot` | `decodeStream`/`encodeStream` with `.collect` over `Readable.from(chunks)` equal the one-shot functions |
| `TestHegelHostileInputNeverCrashes` | on junk and mutated bytes in Buffers and unaligned `Uint8Array` views, with odd options, every codec returns a string (the same for both views) and encodes any string to a Buffer; `fatal` throws only an Error and only in the codecs that have it; wrong argument types are TypeErrors |

Generators (`hegel/enc.mjs`): Unicode text biased to zero runs, the special ranges and a list of
notable code points (BOM, U+FFFD, noncharacters, U+10FFFF, combining marks), with lone
surrogates on request; repertoire text per encoding; byte mutations (insert, delete, replace,
duplicate, with lead bytes and separators favoured); random chunkings. `ZOO_COLLECT=1` turns
mismatches into `# COLLECT` counts and `HEGEL_TEST_CASES` (default 100) widens the sweep.
Known bugs are gated in `hegel/known.mjs` by the shape of the input; `ZOO_NO_KNOWN=1` lifts them.

## Bugs

7 open, all pinned (see `bugs.toml`). In 1000-case sweeps every property agrees with the
oracles on every case not touched by them:

- The multi-byte stream decoders drop characters when a chunk boundary falls inside a sequence
  that turns out invalid or completes an astral character: the output buffer is sized for the
  new chunk alone, and writes past a Buffer's end are silently ignored (2, high).
- A CESU-8 stream ending in an incomplete sequence decodes to `"0"` + U+FFFD (1).
- GB18030 four-byte sequences outside the defined ranges decode to arbitrary code points or lone
  surrogates instead of U+FFFD (7).
- A UTF-7 base64 run of length 1 mod 4 loses the characters decoded before its bad tail (3).
- The hex encoder is stateless, so odd-length chunks in an encode stream lose a nibble (4).
- The single-byte encoders map U+FFFD to the code page's undefined byte, not `?` (5).
- A multi-byte sequence truncated at the end of input is re-parsed byte by byte after its first
  byte, so GB18030 `81 30` at the end gives U+FFFD + `"0"` (6).

## Accepted differences and notes (not counted as bugs)

- Table flavours (above) are recorded at start and excluded from judgement; they are not bugs
  of either side. Shift_JIS decodes its user-defined area to private-use characters that it
  does not encode (as the WHATWG index has it): those are left out of the round trip.
- Replacement counting: Python may fold an ill-formed sequence and the byte that ends it into one
  U+FFFD where iconv-lite (and WHATWG) re-read that byte; such cases are counted, not judged.
  Python's utf-7 replaces lone surrogates and drops the byte after a bad shift-in, where
  iconv-lite passes the surrogate through and keeps the byte (both documented); counted.
- A single-byte encoder writes one `?` per UTF-16 code unit of an astral character (two), Python
  one; not judged.
- The `utf-16`/`utf-32` labels are iconv-lite's endianness-detecting codecs, not WHATWG's
  UTF-16LE (documented); their BOM-less decoding is judged only on Latin text, where the
  heuristic is specified to work.
- A UTF-7 encode stream splits runs at chunk boundaries (a stateless encoder); the bytes differ
  from one-shot, the text does not. An encode stream that received no data writes no BOM where
  `encode("")` with `addBOM` does.
- Labels with `:` before four trailing digits are read as a year by the lenient normaliser
  (`cp:1252`), a documented rule, so the generator does not build them.

## Not tested

The Web backend (`backends/web.js`, Uint8Array results), `enableStreamingAPI` injection,
UTF-7-IMAP against an external oracle (Python has none; round trip and streaming only), the
single-byte tables Python lacks (cp808, mik, tcvn, viscii, armscii8, georgian, hp-roman8, ...:
round trip and streaming only), performance, and the type definitions.

## History

- 2026-09-20: created at 2472166 (1.0.0-alpha.2), 8 properties, 7 bugs.
