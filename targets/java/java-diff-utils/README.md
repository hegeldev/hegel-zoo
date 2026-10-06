# java-diff-utils

[java-diff-utils/java-diff-utils](https://github.com/java-diff-utils/java-diff-utils): the Java
diff library — Myers' algorithm (greedy and linear-space) over lists of any type, `Patch`/`Delta`/
`Chunk` with apply, restore, fuzzy apply and conflict output, unified-diff generation and parsing
(`UnifiedDiffUtils` and the multi-file `unifieddiff` reader/writer), and `DiffRowGenerator` for
side-by-side rows with inline word/character highlighting. Pinned at the 4.18-SNAPSHOT commit
5e2e5b98 (2026-05-16); Apache-2.0. No CONTRIBUTING.md; the README and issue templates say
nothing about AI — the zoo only records bugs, it contributes nothing. The seventh Java target:
the patch adds a Maven module `hegel/` depending on `io.github.java-diff-utils:java-diff-utils:
4.18-SNAPSHOT`, which `[run] setup` builds and installs from the pinned tree (core module only,
Spotless/GPG/enforcer skipped — Spotless 2.30 fails on JDK 25). The harness `Zoo.java`, the
judge's `ZooListener` and two test classes live in `hegel/src/test/java/zoo/`. See HACKING.md
for the Java mechanics.

## What is tested

The inputs are short line lists (0–20 lines from a 17-word alphabet with duplicates, empty lines,
whitespace-only lines, `<`, `&`, punctuation and an emoji) and revisions derived from them by
0–5 random insert/remove/replace/move edits, or unrelated lists. The oracles are an LCS dynamic
program (the edit cost of a minimal diff is `N + M − 2·LCS`), a GNU-style unified-diff applier
(`applyUnified`: header arithmetic, context lines, `-`/`+` bodies), direct reconstruction of the
texts from generated rows, and the rules stated in the Javadoc and the README.

`DiffUtilsTest`:

- **diffsAreMinimalAndPatchesRoundTrip** — `MyersDiff` and `MyersDiffWithLinearSpace`, with and
  without `includeEqualParts` and with a trimming equalizer: deltas sorted and disjoint, chunks
  quoting the texts, type/size invariants, EQUAL deltas contiguous with the gaps; the edit cost
  equals the LCS bound (greedy Myers only); the listener's `diffStart`/`diffEnd` once each;
  `applyTo`, `restore`, `DiffUtils.patch`/`unpatch`, `applyToExisting`/`restoreToExisting`;
  `verifyChunk` OK on the original and `POSITION_OUT_OF_TARGET` past the end; the default and
  explicit overloads agree; `diff(String, String)`; Java serialization of a `Patch`; `withChunks`
  equality; a mutated line → `PatchFailedException` with `CONTENT_DOES_NOT_MATCH_TARGET`; the
  `CONFLICT_PRODUCES_MERGE_CONFLICT` output against a model (conflict block for the failing delta,
  the others applied); a truncated target → `PatchFailedException` (skipped when the chunk has one
  line: bug /3); the other algorithm's patch applies too.
- **inlineDiffsRebuildTheRevisedString** — `diffInline`: chunks compressed to one string each,
  replacing from the back rebuilds the revised string, cost minimal.
- **unifiedDiffsAreWellFormedAndParseBack** — `generateUnifiedDiff` for context 0–3: file header,
  hunk headers and bodies applied by the GNU model (an empty range numbered with the line
  before; a null original name drawn freely), context lines bounded by 2·context per delta;
  `parseUnifiedDiff` → `applyTo` and `restore`, 1-based `changePosition`s; `applyFuzzy` on the
  original and on a shifted target (skipped when the chunk's lines occur at more than one
  position);
  `generateOriginalAndDiff` header, context lines = unchanged lines, `-`/`+` = deleted/inserted.
- **diffRowsReconstructBothTexts** — `DiffRowGenerator` under random builder options
  (`showInlineDiffs`, `inlineDiffByWord`, `ignoreWhiteSpaces`, `columnWidth`,
  `mergeOriginalRevised`, `reportLinesUnchanged`, `decompressDeltas`, HTML or identity
  normaliser, custom tags): stripping tags and `<br/>` from the rows gives the normalised texts,
  EQUAL sides equal, INSERT/DELETE rows have an empty side, tags balanced, no tag inside an HTML
  entity, no leading or doubled `<br/>`, the untagged remainders of a single-line inline CHANGE
  row agree (a multi-line change is diffed as one text, so its common text may sit on different
  rows of the two sides: `["a"] -> ["b", "a b"]` gives `[CHANGE,a,{+b+}]` then
  `[CHANGE,,a{+ b+}]`, which is not judged), inline tags intact on every wrapped row (widths 0,
  1, 3, 8), the README's examples.
- **splittersPreserveTextAndEqualizersFollowTheirRules** — `SPLITTER_BY_WORD` and
  `SPLITTER_BY_CHARACTER` preserve the text, no two adjacent word pieces; the
  `IGNORE_WHITESPACE_EQUALIZER`, `DEFAULT_EQUALIZER` and `LINE_NORMALIZER_FOR_HTML` models.
- **unifiedDiffReaderAndWriterRoundTrip** — `UnifiedDiff.from(header, tail, UnifiedDiffFile
  .from(from, to, patch))` → `UnifiedDiffWriter.write` (header, `---`/`+++` lines, GNU model on
  the hunks, `--` tail) → `UnifiedDiffReader.parseUnifiedDiff`: one file, names, header or
  `diff --git` command or a free `diff` line of two to six words, tail, `applyPatchTo` and the
  file's patch reproduce the revision; the reader also parses `UnifiedDiffUtils.generateUnifiedDiff`
  output.

`DiffPinsTest` — one pin per bug in bugs.toml, asserting the documented (or GNU-diff) behaviour;
each fails while its bug exists and is listed in `target.toml` `[expected_failures]`.

## Not tested

The `java-diff-utils-jgit` module; `DeltaMergeUtils` beyond what `DiffRowGenerator` exercises;
`applyFuzzy` with `maxFuzz > 0` (fuzz needs context deltas that only the parsers produce, and
the search then hits bug /3 constantly); the reader's grammar for `index`/`rename`/`copy`/`mode`/
`Binary` lines, timestamps in file names and `\ No newline at end of file`; `MyersDiffWithLinearSpace`
minimality (it is not minimal by design); custom `DiffAlgorithmI` implementations; performance.

## Bugs

See bugs.toml. Eleven so far: empty hunk ranges numbered one line too high, by `generateUnifiedDiff` and by `UnifiedDiffWriter` (/1); a null original
name giving `@@ -0,N` for any single-delta patch, whose parse then loses the position (/2);
`Chunk.verifyChunk` reading one line past the target, so `applyTo` and `applyFuzzy` throw
`IndexOutOfBoundsException` (/3); `reportLinesUnchanged` ignored by inline diffs (/4);
`columnWidth` wrapping tearing inline tags (/5); word-level inline diffs leaving tags open across
rows (/6); `applyFuzzy` keeping stale positions after a size-changing hunk (/7); inline diffs, by
word and (found 2026-10-06) by character, putting tags inside `&lt;`/`&gt;` (/8); `wrapText` emitting a leading or doubled `<br/>` at a
surrogate pair (/9, at this commit a lone emoji at width 1 or emoji following each other at an even width); the merge-conflict output throwing when the chunk runs past the target (/10);
`UnifiedDiffReader` throwing `ArrayIndexOutOfBoundsException` on a short `diff` line (/11). All
still reproduce.

Drawn by default (STYLE.md rule 11, the whole target since 2026-10-06): the generators draw the
shapes of all eleven bugs — empty hunk ranges and null original names in the unified-diff
properties, a short `diff` line in the reader's header, inline rows with `reportLinesUnchanged`,
`columnWidth` 1 (with and without emoji), multi-line word changes, a size-changing hunk before
another, and a conflicting patch applied to a target cut inside the chunk — and each wide
property is an expected failure mapped to the bug it shrinks to, every run, since each shape is
10–33% of cases: `diffsAreMinimalAndPatchesRoundTrip` → /10, `unifiedDiffsAreWellFormedAndParseBack`
→ /1 (its shrunk hunk often also carries /2), `unifiedDiffReaderAndWriterRoundTrip` → /1 through
the writer's copy of the numbering, `diffRowsReconstructBothTexts` → /5, the most drawn of its shapes (the shrunk case sometimes shows /4's or /9's instead). One
narrow property per bug draws only that bug's region with random contents and fails
deterministically beside the pin: `emptyHunkRangesAreNumberedWithTheLineBefore` (/1),
`nullOriginalNameKeepsTheOriginalLineNumbers` (/2), `reportLinesUnchangedSuppressesInlineMarkup`
(/4), `columnWidthWrappingKeepsInlineTagsIntact` (/5), `wordInlineDiffsTagEachRowSeparately` (/6),
`applyFuzzyFollowsAnEarlierHunkThatChangedTheLineCount` (/7), `inlineDiffsKeepHtmlEntitiesWhole`
(/8), `columnWidthWrappingOfSupplementaryCharactersPlacesEveryBreak` (/9),
`mergeConflictOutputOfAChunkRunningPastTheEndReportsTheConflict` (/10),
`readerAcceptsADiffCommandLineOfFewerThanFourWords` (/11). `HEGEL_NO_KNOWN=1` (`Zoo.NO_KNOWN`,
read once into the `Known` switches) turns the shapes off by drawing their neighbourhoods
instead (same-count replacements, a null name only for an empty original, width 0 when inline,
a count-keeping first hunk, a target cut at the chunk's end, 4–6-word `diff` lines), with
residual skips of 1.6% (/6), 1.5% of rows (/9) and under 0.1% (/8 by character); every property
then passes. The fixed /3 shape (a one-line victim, a target one line short) is drawn and passes.

## Observed and not recorded

- `Patch.applyFuzzy` throws `UnsupportedOperationException` for `InsertDelta`/`DeleteDelta`
  (only `ChangeDelta`, i.e. parser output with context, supports fuzzy application) — an explicit
  limitation in the code.
- `DiffUtils.diff(String, String)` drops trailing empty lines (`String.split("\n")`).
- `CONFLICT_PRODUCES_MERGE_CONFLICT` throws `UnsupportedOperationException("Not supported yet.")`
  when a delta's position lies beyond a short target (the conflict check cuts the target only
  inside the last delta's chunk).
- `DiffRowGenerator.Builder` Javadoc says `ignoreWhiteSpaces` defaults to true and `columnWidth`
  to 80; both default to false/0. `ignoreBlankLines` and `ConflictProducingConflictOutput` are
  documented but do not exist.
- `MyersDiff`'s Javadoc promises "an empty diff on error"; it throws `IllegalStateException`
  (never observed).
- `LINE_NORMALIZER_FOR_HTML` escapes only `<`, `>` and tabs, not `&` or quotes.
- `UnifiedDiffUtils.parseUnifiedDiff` skips everything up to the first line starting with `+++`,
  including a `+++x` content line of a headerless diff, and drops body lines it does not
  recognise; `UnifiedDiffReader` stops at any `--x` line after a hunk.
- `UnifiedDiffWriter` writes no `+++` line when the target name is null and never writes
  `\ No newline at end of file`.

## History

- 2026-09-16: created at 5e2e5b98 (4.18-SNAPSHOT); bugs /1–/11.
- 2026-09-18: base bumped 5e2e5b981533 → 06438525cfb1 (2026-09-19, "upgraded release plugin"; 4.18-SNAPSHOT); 10 bug(s) still reproduce; fixed upstream: java-diff-utils/3. 6 tests pass.
- 2026-10-06: weekly 1000-case run 37296133806 failed `diffRowsReconstructBothTexts`; triage: an oracle flaw (a multi-line CHANGE whose only difference is a moved line break has no tag to show - the no-tag check now excludes multi-line changes like the remainder check) and /8 reached through the character splitter, now in the record; narrow property, pin, first `HEGEL_NO_KNOWN` gate of this target.
- 2026-10-06: unsteered (rule 11 for the whole target): one `Known` switch per bug, off by default; the wide properties draw every shape and are mapped to what they shrink to; one narrow property per bug; the /3 exclusion removed (its shape passes); `columnWidth` 1 and the conflict output on a cut target added; /1 found to reach `UnifiedDiffWriter` too and /9's shape re-read at this commit (notes in bugs.toml).
