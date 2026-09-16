# typescript/node-jsonc-parser — microsoft/node-jsonc-parser (JSON with comments)

Hegel property tests for [`jsonc-parser`](https://github.com/microsoft/node-jsonc-parser)
4.0.0-next.2, pinned at `ca66b23b` (main, 2026-09-16): the scanner, fault-tolerant parser, DOM,
`getLocation`, `format` and `modify` that VS Code uses for `settings.json`, `tsconfig.json` and
every other JSONC file (~48M weekly downloads). TypeScript, no runtime dependencies, MIT. No
AI-contribution policy is published (README, SECURITY.md and `.github/` checked 2026-09-16; the
Microsoft CLA applies to contributions); the zoo only records bugs. The target is named after the
repository because the zoo already has `rust/jsonc-parser`.

Tests are `test/hegel.test.mjs` (ESM, run by `node --test`) with the zoo's harness
`test/hegel-zoo.mjs`. Hegel is `@hegeldev/hegel` 0.4.5.

## How it is built

`lib/` is not committed, so the setup installs Hegel at the package root, TypeScript 5.9.3 under
`.hegel/` (it is a devDependency of the package, which the `--omit=dev` root install would prune)
and compiles `src/main.ts` + `src/impl/*.ts` into `.hegel/dist` (ESM, `preserveConstEnums` so
`SyntaxKind`, `ScanError` and `ParseErrorCode` exist at runtime) with `test/tsconfig.hegel.json`;
the tests import that build.

## How it is tested

Values are random JSON (leaves, arrays, objects with unique keys including `""`, `__proto__`,
`constructor`, `"q"`, `*`, `**`, emoji), written with random whitespace (`\n`, `\r\n` or `\r`
line endings, tabs, dense or airy), and optionally with comments (`/* */` and `//`), trailing
commas, alternative number spellings (`7.0`, `7e0`, `7E+0`, `70e-1`) and string escapes (`\/`,
`\uXXXX` in either case, escaped or raw surrogates, control characters as `\n` or `\u000a`).

- **`parse` agrees with `JSON.parse`** (`TestHegelParseAgreesWithJSONParse`): on comment-free text
  the value, the tree's `getNodeValue` and the leaves `visit` reports all equal `JSON.parse`, with
  no errors. Found bug 2.
- **Comments and trailing commas are trivia** (`TestHegelCommentsAndTrailingCommasAreTrivia`):
  with comments and trailing commas the value is unchanged and error-free under
  `allowTrailingComma`; `visit` sees each comment once; `disallowComments` reports exactly one
  `InvalidCommentToken` per comment and still recovers the value; without `allowTrailingComma`
  there are errors iff there are trailing commas, and the value is still recovered;
  `stripComments` leaves JSON that `JSON.parse` reads to the same value, and with a replacement
  character keeps the length and removes every comment. Found bug 8.
- **The scanner tiles the text** (`TestHegelScannerTilesTheText`): on valid and on mutated text
  the tokens are contiguous from 0 to the end, the EOF token is empty, each token's start line and
  character agree with a count of `\r\n`/`\r`/`\n` before it, an error-free string token's text
  is JSON with the token's value, an error-free number token is a JSON number, and comment tokens'
  values are their text. Found bugs 4 and 8.
- **Strict mode agrees with `JSON.parse`** (`TestHegelStrictModeErrorsAgreeWithJSONParse`): after
  0–2 random mutations, `parse` with `disallowComments` reports no error iff `JSON.parse` accepts
  the text, agrees on the value when it does, and every error lies inside the text at a line and
  character matching the model. Clean apart from bugs 2 and 4.
- **The tree and the locations agree** (`TestHegelTreeAndLocationsAgree`): every node lies inside
  its parent and points back to it; a property starts at its key, its `colonOffset` is a `:`
  between key and value; a value node's text parses to `getNodeValue(node)`; `getNodePath` leads
  back through `findNodeAtLocation`; offsets inside a leaf (and its right bound with
  `includeRightBound`) find it with `findNodeAtOffset`; `getLocation` inside a leaf has the leaf's
  path, `isAtPropertyKey` false and the leaf as `previousNode`, inside a key the object's path plus
  the key, `isAtPropertyKey` true and the property as `previousNode`; `matches` accepts the path,
  the path with a `*`, the path with a run replaced by `**`, and rejects a changed or longer path;
  `visit`'s `pathSupplier` agrees with the tree. Found bugs 1 and 7.
- **`format` equals `JSON.stringify`** (`TestHegelFormatMatchesJSONStringify`): on comment-free
  canonical text, `format` with random `insertSpaces`/`tabSize`/`insertFinalNewline`/`eol` gives
  exactly `JSON.stringify(value, null, indent)` with the text's line ending (or the option's when
  the text has none), and is idempotent. Clean.
- **`format` is lossless and idempotent** (`TestHegelFormatIsLosslessAndIdempotent`): with
  comments, trailing commas, `keepLines` and random ranges (boundaries never split a `\r\n`),
  the edits are in range and non-overlapping, the non-whitespace token stream is unchanged, the
  value and error count are unchanged, formatting again changes nothing, and formatting a range
  then everything equals formatting everything. Found bug 9.
- **`modify` matches a model** (`TestHegelModifyMatchesTheModel`): set the root; remove, append
  (`-1`), replace, insert (`isArrayInsertion`) or set beyond the end in an array; remove (present
  or missing), replace or insert (at `getInsertionIndex`, which must be called with the existing
  keys) in an object; with or without `formattingOptions`. The result parses without errors to
  the model's value, the edited object's key order is the model's, comments outside the edits
  survive, and a real change produces edits. Clean within the generated inputs; bugs 3, 5 and 6
  were found by reading `edit.ts` and are pinned (their shapes are excluded from generation).

## Bugs

| id | title | kind | severity |
|---|---|---|---|
| node-jsonc-parser/1 | `Location.matches()` never matches a pattern containing `**` | wrong-result | medium |
| node-jsonc-parser/2 | `parse()` sets the prototype for a `__proto__` key instead of an own property | wrong-result | medium |
| node-jsonc-parser/3 | `modify()` removing an out-of-range array index deletes the sole item or throws `TypeError` | crash | medium |
| node-jsonc-parser/4 | An unterminated block comment's token (and error) runs one character past the text | wrong-result | low |
| node-jsonc-parser/5 | `modify()` of a duplicated key edits the first occurrence, `parse()` reads the last | inconsistent | low |
| node-jsonc-parser/6 | `modify()` removing the only property before a trailing comma leaves `{,}` | wrong-result | low |
| node-jsonc-parser/7 | `getLocation()` says `isAtPropertyKey` inside an array element after an empty object | wrong-result | medium |
| node-jsonc-parser/8 | A comment token's value starts one character early; `stripComments(text, ch)` grows the text | wrong-result | medium |
| node-jsonc-parser/9 | `format()` of a range with `keepLines` drops the line breaks before the range's first token | wrong-result | low |

## Oracle limits and nits

- `JSON.parse` is the oracle for values and for strict-mode acceptance; comments and trailing
  commas are checked by construction (the generator counts what it inserted). `format` is
  modelled by `JSON.stringify` only for comment-free canonical text; with comments only
  losslessness, idempotence and range/whole agreement are checked. `modify` is modelled by hand
  on the JS value; positions of inserted text are checked through key order only.
- Not covered: `getLocation` in whitespace, after separators or in incomplete documents (the
  completion-oriented semantics are not documented precisely enough); `format` of invalid
  documents (it stops editing after the first error by design); `visit` callbacks returning
  `false`; `modify` through a non-existent nested path (documented as "will be created", and the
  intermediate types depend on the segment types).
- Nits not recorded as bugs: the error for a numeric segment on an object reads "Can not add
  property to parent of type object" and for a string segment on an array "Can not add index to
  parent of type array" (the words are swapped, edit.ts:138); `tabSize: 0` formats with 4
  (`options.tabSize || 4`); `modify(text, [], undefined)` throws "Can not delete in empty
  document" whatever the document.
