# typescript/jsonrepair — josdejong/jsonrepair (against JSON.parse, its own two implementations and a model of its repairs)

jsonrepair turns broken JSON (JavaScript notation, Python constants, comments, truncated or
newline-delimited documents, MongoDB and JSONP wrappers, HTML entities) into valid JSON (~2.6M
weekly downloads; JSON Editor Online). It ships two implementations of the same repairs, a
regular one and a streaming one for Node streams, "tested against the same suite of unit tests"
and documented to "work the same" with an infinite buffer. The patch checks that valid JSON is
left alone, that any output is valid JSON, that each documented repair gives back the value the
document had before it was broken, and that the two implementations agree, through the core and
through the Node Transform with infinite, finite and too-small buffers — and pins 22 bugs.

## How it is built

`src/` is TypeScript with `.js` import specifiers and no runtime dependencies; upstream builds
with Babel. The setup installs Hegel, TypeScript and Node's types under `.hegel/` and compiles
`src/` to `.hegel/dist` (ES2020 modules, `hegel/tsconfig.json`; the test files are excluded).
Node 22.

## How it is tested

`hegel/hegel.test.mjs` runs under `node --test`; `hegel/hegel-zoo.mjs` is the zoo's shared
harness; `hegel/jr.mjs` holds the generators, the corrupting serializer and the drivers of the
two implementations.

| Property | What it checks |
|---|---|
| `TestHegelValidJSONIsReturnedUnchanged` | random values (nested arrays and objects; strings over letters, punctuation, quotes of every kind, control characters, special whitespace, astral characters, and words the repairer knows such as `true`, `None`, `...`, `//`, `&quot;`, `NumberLong`) rendered as valid JSON with random whitespace, `\/` and `\uXXXX` escapes and non-canonical numbers are returned character for character |
| `TestHegelRepairedOutputIsValidJSON` | on random JSON-ish text, mutated valid and corrupted documents (deletions, insertions, duplications, truncations, quote swaps): the output parses with `JSON.parse` and is a fixed point of `jsonrepair`, or a `JSONRepairError` is thrown with a position inside the text and nothing else is thrown |
| `TestHegelDocumentedRepairsPreserveTheValue` | a random value is serialized with a random subset of the Readme's breakages — unquoted keys and values, single, special (`“ ” ‘ ’ \` ´`) and HTML-entity quotes, special whitespace, block and line comments, trailing, leading and missing commas, Python constants and `undefined`, MongoDB wrappers, raw control characters in strings, `+` concatenation, ellipsis, missing colons, truncated numbers — and wrapped in a fenced code block, a JSONP call, redundant or missing closing brackets, a JSON-stringified document or newline-delimited documents; `JSON.parse(jsonrepair(text))` deep-equals the value (an array of the values for NDJSON) |
| `TestHegelStreamingMatchesRegular` | `jsonrepairCore` with an infinite buffer on the same text, fed in random chunks, gives the same output as `jsonrepair`, or both throw |
| `TestHegelFiniteBuffersRepairLikeTheRegularImplementation` | with a `bufferSize` larger than the longest string and whitespace run of a valid document (the Readme's condition) and any `chunkSize` and chunking, the output is the regular one |
| `TestHegelSmallBuffersFailLoudly` | with a `bufferSize` and `chunkSize` of 1–12 on any text, the output is the regular one or an error is thrown — never a silently different output |
| `TestHegelTransformMatchesRegular` | `jsonrepairTransform` fed string chunks split anywhere or Buffer chunks split at any byte, with default or infinite-buffer options, gives the regular output or an error |

`ZOO_COLLECT=1` turns mismatches into `# COLLECT` counts and `HEGEL_TEST_CASES` (default 100)
widens the sweep; `ZOO_TRACE=<file>` appends every text handed to either implementation, which
is how the hang (22) was located. The generators draw the recorded bugs' shapes like any other (a
container's last string holding an unmatched bracket, ellipsis before a comma and whitespace, special
whitespace after a number, repeated commas, a Buffer chunk that does not decode on its own, ...), and a
wide property that meets one fails naming it (`hegel/known.mjs` classifies the mismatch by shape:
`(recorded shape jsonrepair/N)`), so the wide properties are expected failures at their natural rates
(`FiniteBuffers` and `Transform` every run, `DocumentedRepairs` and `Streaming` most runs,
`SmallBuffers`, `RepairedOutput` and `ValidJSON` in some), each mapped to the bug it most often shrinks
to. One narrow property per bug (`TestHegelValidJSONEndingInAStringWithAnUnmatchedBracketIsUnchanged`,
..., `TestHegelStreamingTerminatesOnAnArrayAfterAPropertyValue`) draws that bug's shape region with
random contents through the same oracle and fails every run; the pins stay as regression examples.
`HEGEL_NO_KNOWN=1` leaves the shapes out of the generators (brackets stripped from a container's last
string, plain whitespace after numbers, no adjacent or `/`-leading comments, no ellipsis after a dropped
or leading comma, Buffer chunks cut at code points, ...), skips the mismatch that still has one (under
2% of cases per property) and registers the narrow properties skipped. Ten more library bugs reproduced
during the unsteering but not yet recorded are skipped behind `candidate/typescript/jsonrepair-1..10`
gates in `hegel/known.mjs`, to be recorded with pins and properties of their own.

## Bugs

22 open, all pinned and each found by a property of its own (see `bugs.toml`). Under
`HEGEL_NO_KNOWN=1`, 5000-case sweeps of every property had no mismatch.

Valid JSON and the repairs of the regular implementation (shared by the streaming one unless
said otherwise):

- Valid JSON whose last string in a container holds an unmatched `{`, `[` or `(` is rejected
  (`{"a":"{"}`) or rewritten (`["["]` → `["",[""]]`): the bracket count that detects an embedded
  quote is run on the string content (1).
- An ellipsis in an object followed by a comma and whitespace throws `Object key expected`;
  the streaming implementation repairs it (2).
- A number followed by a special whitespace character becomes a string (`[1 ,2]` →
  `["1 ",2]`); an unquoted string keeps it, so `undefined` is not turned into `null` (3).
- `f()` repairs to the string `")"`; `f(}` and `f(` give an empty, invalid output (9).
- A missing colon before `true`, `false`, `null`, an unquoted string or a negative number is
  repaired only when the property is the last one (`{"a" true}` yes, `{"a" true, "b": 1}`
  throws) (11).
- Of two comments with nothing between them (`/**//**/`) only the first is stripped; the second
  then throws or, in `[1/**//**/,2]`, gives `[[1],2]` (12).
- A block comment whose body starts with a slash (`/*/x*/`) is closed at its own opening
  asterisk: `[1/*/x*/,0]` → `[1,"x*","/,0]"]`; the streaming implementation throws (17).
- An unquoted string inside a function call swallows the closing parenthesis:
  `callback(undefined);` → `"undefined);"` (13).
- A backslash before a raw carriage return or tab in a string leaves the raw character in the
  output, which `JSON.parse` rejects (15).
- In a single-quoted string an escaped backslash followed by a double quote leaves the quote
  unescaped (`'a\\"b'` → `"a\\"b"`), which `JSON.parse` rejects (19).
- Inside a string with HTML-entity or special quotes, an embedded quote followed by a backslash
  ends the string and the escape throws (`&quot;"\"b&quot;`, `“”\"a”`); with a letter after the
  embedded quote it is repaired (16).
- In newline-delimited JSON a document starting with an entity quote throws (`{}\n&quot;a&quot;`)
  while every other quote style, unquoted strings and keywords are recognised (18).

The two implementations disagree (the Readme: with an infinite buffer the streaming one "works
the same as the regular implementation"):

- **The streaming implementation never returns when an array follows a property value without
  a comma** (`{"a":1 [1]}`, or an unclosed object followed by an array on the next line, which
  the regular one repairs as NDJSON); eleven bytes hang a server that streams untrusted text
  through `jsonrepairTransform` (22). The harness runs the streaming implementation in a worker
  thread with a 5 s watchdog (`streamingGuarded`, `transformedGuarded` in `hegel/jr.mjs`), so a
  hang comes back as a verdict and is judged like any other result.

- Newline-delimited JSON followed by a redundant closing bracket: regular repairs, streaming
  throws `Unexpected end` (4).
- Repeated commas: streaming strips them, regular throws (`1,,`, `{"a":1,,"b":2}`) or turns
  `[1,,2]` into `[[1],2]` (5).
- The trailing whitespace of an unquoted string ends up inside the string in the streaming
  implementation (`[a ,b]` → `["a ","b"]`), and `undefined ` is not `null` (6).
- A missing comma before something that does not start like a value (`[1 ...]`, `[1 ;x]`) or
  before a regular-expression literal (`[1/x/]`): regular repairs, streaming throws (7).
- A leading comma followed by an ellipsis (`[[, ...], 1]`): streaming throws (14).
- A colon inside an array (`[1: 2]`): regular gives `[1,": 2"]`, streaming throws (20).
- The comma the streaming implementation inserts before an object that then needs a repair of
  its own is lost (`{}\n{{}` in NDJSON, `[l{{` in an array): the output lacks it and is not valid
  JSON (21).

The Node stream API:

- `jsonrepairTransform` decodes each Buffer chunk on its own, so a multibyte character split
  across two chunks — as a file stream's 64 KiB chunks will do — becomes replacement
  characters (8).
- A `bufferSize` larger than every string and whitespace run, the Readme's condition, can still
  throw `Index out of range`: one parsing step reads the whitespace before a token, the token,
  the whitespace after it and one more character (10).

## Accepted differences and notes (not counted as bugs)

- When both implementations throw, their messages and positions differ in places (`Object key
  expected` against `Unexpected character ":"` at the same position; `Unexpected end` reported
  at the text's end by the regular one and at the parser's position by the streaming one).
  Counted, not judged.
- A too-small buffer makes the streaming implementation throw a different `JSONRepairError`
  than the regular one on some inputs (it cannot look far enough ahead); the property accepts
  any error there and judges only silent differences.
- Two strings separated by a space at the root (`"a" "b"`) throw; a string followed by a space
  and a keyword or negative number inside an array (`["a" true]`) is repaired. The generator's
  missing-comma breakage only drops commas the parser can recover from: before a bracket, a
  digit or a string starting with a letter or digit, and never after an unquoted string.
- `callback({}) ;` (a space before the semicolon) throws; `callback({});` is stripped.
  Any disagreement between the two implementations on a text containing an identifier followed
  by `(` is attributed to bug 9 (`{a(a` is a call to one and a key to the other).
- A JSON-stringified document (`{\"a\":1}`) is repaired when its strings hold no quotes or
  backslashes and its whitespace is spaces; nested escapes (`\\\"`) and escaped tabs or newlines
  between tokens are not, and are not generated.
- Leading zeros turn a number into a string (`007` → `"007"`), as documented; the value
  changes, so the value-preservation property does not generate them.
- A lone surrogate in a string chunk does not survive the Node Transform, which encodes string
  chunks as UTF-8 (`U+FFFD`); the regular implementation keeps it. Texts that are not well-formed
  Unicode are not compared through the Transform.
- Inside an entity-quoted string a special double quote is normalised to an escaped regular
  quote (`&quot;“a&quot;` → `"\"a"`, while `"“a"` is left alone); the generator's entity style
  avoids special quotes in the content.

Not tested: the command-line interface; `chunkSize` beyond its effect on chunk boundaries;
documents larger than a few kilobytes.

## History

- 2026-09-20: created against 4a80ed8 (3.15.0); 22 bugs.
