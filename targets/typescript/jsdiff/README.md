# jsdiff

[kpdecker/jsdiff](https://github.com/kpdecker/jsdiff) (npm `diff`, ~100M weekly downloads):
text diffing (`diffChars`, `diffWords`, `diffWordsWithSpace`, `diffLines`, `diffSentences`,
`diffCss`, `diffJson`, `diffArrays`), unified-diff patches (`structuredPatch`, `createPatch`,
`createTwoFilesPatch`, `formatPatch`, `parsePatch`, `applyPatch`, `reversePatch`) and the
`convertChangesToXML`/`convertChangesToDMP` converters. Pinned at 9.0.0 (87c5152b, 2026-08-24).
The tests are `test/hegel.test.mjs` with the zoo's harness `test/hegel-zoo.mjs`.

jsdiff ships tsc output that is not in the repository, so the setup builds `libesm/` the way
upstream's `generate-esm` script does (TypeScript 6.0.2 through `npx`, `--noCheck`) and the
tests import `../libesm/index.js`.

## What is tested

The oracles are GNU `patch` and `diff` (diffutils 3.10) and `git diff` (2.43), spawned per case
on scratch files, and models written out in the test: a positional hunk applier that checks
every number of every hunk header, an LCS edit distance, and the documented `diffLines`
tokenizer and equality. Texts are lines of shapes the unified diff format cares about (leading
`+`, `-`, space, `@@`, `\`, `---`/`+++`/`Index:`/`diff --git` markers, the `===` underline,
blank and whitespace-only lines, CR inside a line, non-ASCII) with unix, windows or mixed line
endings and with or without a final one; the new text is a few edits of the old (insert,
delete, replace, move, duplicate) or unrelated.

- **TestHegelPatchesApplyParseFormatAndReverse** — `structuredPatch` with every `context`
  (0–4, default, `Infinity`): the hunks applied exactly where their headers say give the new
  text (start lines, line counts, `\ No newline at end of file`), no more than `context` lines
  of context on either side, no hunks for identical texts; `applyPatch` on the structure and on
  `formatPatch`'s text gives the new text (with `autoConvertLineEndings` off, and on with one
  documented shape as a limit); `createTwoFilesPatch` = `formatPatch(structuredPatch)`;
  `parsePatch(formatPatch(p))` is `p` (names with spaces, quotes, backslashes, tabs, newlines,
  control characters, non-ASCII; headers) and `formatPatch(parsePatch(text))` is `text`;
  `FILE_HEADERS_ONLY`/`OMIT_HEADERS` variants parse to the same hunks and apply; `reversePatch`
  undoes the patch (as a structure, positionally, and through format/parse) and swaps the
  names; **GNU `patch` applies jsdiff's patch** to the old text and gets the new one; with
  `ignoreWhitespace`/`stripTrailingCr` the patch must still apply to the old text and give the
  new one up to the ignored differences.
- **TestHegelParsePatchReadsDiffAndGitOutput** — `diff -u --label` output: `parsePatch` reads
  the labels, the hunks apply positionally and through `applyPatch`, the reversed patch undoes
  them, `formatPatch`/`parsePatch` round-trips, and GNU `patch` accepts jsdiff's reformatting
  of GNU's patch; `git diff --no-index` output for modifications, creations and deletions
  (against `/dev/null`) with C-quoted file names (spaces, quotes, backslashes, tabs, newlines,
  control characters, non-ASCII): `isGit`, `a/`/`b/` names, `isCreate`/`isDelete` and the
  modes, positional and `applyPatch` application, `reversePatch` (a creation reversed is a
  deletion and back), and `formatPatch` → `parsePatch` keeping the git fields.
- **TestHegelApplyPatchFindsMovedAndFuzzedHunks** — the documented search: a line changed
  outside every hunk, or lines prepended/appended (when each hunk's old lines occur once in
  the text), leaves the result equal to the new text with the same foreign change; with one
  context line changed (not the nearest context line of an insertion) `fuzzFactor: 1` applies
  and gives the new text with that line changed, `fuzzFactor: 0` returns false.
- **TestHegelLineEndingsAndLineOptions** — a LF patch applied to the CRLF copy of the text
  gives the CRLF copy of the new text and vice versa (`autoConvertLineEndings`); `diffLines`
  with any combination of `ignoreWhitespace`, `newlineIsToken`, `ignoreNewlineAtEof`,
  `stripTrailingCr`, `oneChangePerToken` has the shape and values of `diffArrays` over the
  documented tokens with the documented equality, and rebuilds both texts.
- **TestHegelDiffsRebuildInputsAndAreMinimal** — every diff function: concatenating the
  non-added values gives the old input and the non-removed values the new one (for `diffWords`
  up to whitespace, which it redistributes by design; for `diffJson` up to trailing commas, the
  canonical JSON of both objects); counts sum to the token counts; **the number of added plus
  removed tokens equals the LCS edit distance** (`diffChars` with and without `ignoreCase`,
  `diffLines`, `diffCss`, `diffArrays`); `maxEditLength` equal to the edit distance returns
  the diff and one less returns `undefined`; common values come from the new text;
  `oneChangePerToken` gives count-1 changes that merge back to the default result;
  `convertChangesToXML`/`convertChangesToDMP` match their models; `diffJson` ignores key order,
  honours `undefinedReplacement` and agrees with itself on the canonical strings.

## Bugs

Five, all recorded in `bugs.toml` with a pin each:

- **jsdiff/1** (low) — file names with leading or trailing whitespace are not quoted by
  `formatPatch` and are trimmed by `parsePatch`: `createTwoFilesPatch("a ", " b", …)` parses
  back as `a`/`b`.
- **jsdiff/2** (low) — `ignoreNewlineAtEof` strips a trailing LF only: `diffLines("a\r\nb",
  "a\r\nb\r\n", {ignoreNewlineAtEof: true})` reports `b` changed.
- **jsdiff/3** (low) — `parsePatch` keeps only what is before the second tab of a `---`/`+++`
  line (`split('\t', 2)`), so a header `h1\th2` comes back as `h1`.
- **jsdiff/4** (low) — `applyPatch(text, "")` and `applyPatch(text, [])` throw a `TypeError`
  instead of returning the text (as a header-only patch does) or `false`.
- **jsdiff/5** (medium) — a patch created with `ignoreWhitespace` or `stripTrailingCr` takes
  its context lines from the new text and its deleted lines from the old, so it fits neither:
  `applyPatch` refuses it, or applies a hunk that happens to fit elsewhere at the wrong place
  (`createPatch("f", "\r\n", "x\n", …, {stripTrailingCr: true})` on `"\r\n"` gives `"\r\nx"`).

## Limits

- `limit/auto-convert-line-endings` — with `autoConvertLineEndings` (the default) a CRLF text
  patched with a patch whose lines carry no CR (LF insertions with `context: 0`), or a LF text
  with a patch of CRLF insertions, gets the insertions converted: the patch is
  indistinguishable from one made on a copy with the other line endings, as documented. The
  property asserts the exact result with the conversion off and counts this shape on.
- Names for GNU `diff --label` avoid a leading `"`, backslashes and outer whitespace (GNU diff
  prints labels verbatim, so those are the format's ambiguities, not jsdiff's); git file names
  avoid outer whitespace and a leading `.` or `-` for the same reason.
- `applyPatch` with `autoConvertLineEndings: false` on a text with the other line endings is
  documented to "usually fail" — not a property; the `compareLine` callback and `fuzzFactor`
  above 1 are not modelled.

## Not tested

- Async mode (`callback` option), `timeout`, `applyPatches` (callback driver over
  `applyPatch`), `diffWords` with an `Intl.Segmenter`, custom `Diff` subclasses, `diffJson`
  with a `stringifyReplacer`, git patches with renames/copies/mode changes (git's
  `--no-index` does not produce them).

## History

- 2026-09-15: created at 87c5152b (9.0.0); five bugs (jsdiff/1–5).
