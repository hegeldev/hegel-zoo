# reflow

[muesli/reflow](https://github.com/muesli/reflow) is a collection of ANSI-aware text reflow
operations for terminal output — `wordwrap`, `wrap`, `indent`, `dedent`, `padding`, `margin`,
`truncate`, and the `ansi` helpers (`PrintableRuneWidth`, an SGR-tracking `Writer`) they share —
each as `String`/`Bytes` shorthands and as an `io.Writer`. Pinned at 83f637991171 (2023-03-16,
past v0.3.0). MIT. No CONTRIBUTING.md, AGENTS.md or AI policy; not archived, quiet since 2023.
Checked 2026-09-15. The harness lives in a test-only root package (`package reflow_test`) so one
`go test .` covers every package. Widths come from `github.com/mattn/go-runewidth` v0.0.14, the
module's own dependency.

## Oracles

- **Models from the README and the package documentation**: the unconditional wrapper (tabs to
  `TabWidth` spaces, newlines dropped unless kept, a rune that would exceed the limit starts a
  new line, whitespace after a forced break dropped unless `PreserveSpace`); indentation (every
  line prefixed, the indentation unstyled); padding (every line filled to the width, the text
  after the last newline only when it has width); truncation (unchanged when it fits, else the
  longest prefix within width − tail, the tail, and a reset if a style is open); dedentation
  (the smallest indentation of the non-blank lines removed from every line); margin = padding
  of the indented text.
- **An SGR model**: a result is read as printable runes each carrying the style (the SGR
  sequences since the last `ESC[0m`) in force where it appears, and compared with the input's
  runes and styles — "escape sequences do not affect the algorithms" as a semantic statement,
  plus byte equality for inputs without sequences.
- **Invariants** for word wrapping, where the algorithm is not specified to the character:
  every non-whitespace rune and sequence preserved in order, transparency to sequences, every
  line within the limit unless it is a single word wider than the limit, stability under a
  second wrap, `KeepNewlines = false` equal to wrapping the folded text.
- **Chunk invariance**: writing in pieces (never inside a sequence or a rune) equals one write.
- **go-runewidth**: `PrintableRuneWidth` against `StringWidth` of the stripped text.

## Properties

- `TestHegelWordWrapKeepsLinesWithinTheLimit` — clean; lines with a breakpoint (reflow/1),
  limits 1–2 and a word as wide as the limit after at most two cells (reflow/2) are not judged
  for width.
- `TestHegelWrapFollowsTheDocumentedRules` — clean; a text that fits whole with a tab or a
  dropped newline (reflow/5) and chunked writes of texts with whitespace (reflow/6) not judged.
- `TestHegelIndentPrefixesEveryLine` — clean (`String`, a `.` IndentFunc, `NewWriterPipe`).
- `TestHegelPaddingFillsEveryLineToTheWidth` — clean; styles not judged when one is in force
  across a newline (reflow/8).
- `TestHegelMarginIsIndentThenPadding` — clean.
- `TestHegelTruncateCutsAtTheWidth` — clean; a tail wider than the width (reflow/12) and a text
  fitting the width but not width − tail (reflow/18) not judged.
- `TestHegelDedentRemovesTheCommonIndent` — clean on texts whose non-blank lines are all
  indented with one character (reflow/13, /14 pinned).
- `TestHegelAnsiHelpersFollowTheirModels` — clean.
- `TestHegelWritersAreChunkInvariant` — clean for wordwrap (KeepNewlines), indent and padding;
  wrap with newlines, truncate, margin and wordwrap with `KeepNewlines = false` are pinned
  (reflow/6, /9, /10, /11, /19).

The generators use ASCII, `é`, `日`, `😀`, ASCII spaces and SGR sequences attached to words;
no-break spaces (reflow/3), a sequence between trailing whitespace and a newline (reflow/4),
non-SGR sequences (reflow/7), ZWJ/modifier sequences (reflow/17) and split runes or invalid
bytes (reflow/15, /16) appear only in the pins.

## Bugs

| id | severity | title |
|----|----------|-------|
| reflow/1 | high | wordwrap writes a breakpoint character without counting it, so lines with hyphens exceed the limit |
| reflow/2 | low | wordwrap does not move a word at least as wide as the limit to its own line when the current line holds at most two cells |
| reflow/3 | low | wordwrap measures whitespace in bytes, so a no-break space counts two cells and an ideographic space three |
| reflow/4 | low | wordwrap keeps trailing whitespace past the limit when an escape sequence follows it before the newline |
| reflow/5 | medium | wrap writes a chunk that fits the limit raw: tabs are not expanded and newlines are kept with `KeepNewlines = false` |
| reflow/6 | medium | wrap's fast path ignores the wrapping state: a fitting chunk adds its whole width to the current line and skips the whitespace handling after a forced break |
| reflow/7 | low | indent and padding end an escape sequence only at a letter, while `ansi.IsTerminator` also ends it at `@` |
| reflow/8 | medium | padding resets the active style at the end of every line and does not restore it, so a style spanning lines ends after the first |
| reflow/9 | high | `margin.Writer.Write` feeds the whole indented buffer so far to the padder on every call, duplicating earlier chunks |
| reflow/10 | medium | `truncate.Writer` restarts the printed width at zero in every Write, so text spread over several writes is never truncated |
| reflow/11 | medium | `truncate.Writer` subtracts the tail's width from its width on every Write |
| reflow/12 | medium | truncate emits the tail whatever the input when the tail is wider than the width, even for text that fits or is empty |
| reflow/13 | medium | dedent ignores lines without indentation when computing the common indentation, so indented lines lose theirs |
| reflow/14 | low | dedent counts a tab and a space as the same indentation, so lines indented with different characters are both stripped |
| reflow/15 | medium | every writer decodes each Write on its own, so a multi-byte rune split over two writes becomes two U+FFFD |
| reflow/16 | low | every writer rewrites invalid UTF-8 bytes as U+FFFD instead of passing them through |
| reflow/17 | low | widths are summed per rune, so ZWJ emoji sequences and modifier sequences count more cells than go-runewidth's `StringWidth` |
| reflow/18 | medium | truncate reserves the tail's width even when the text fits, truncating text wider than width − tail |
| reflow/19 | medium | wordwrap with `KeepNewlines = false` trims every Write call on its own, losing whitespace at chunk boundaries |

## Not bugs

- `indent` indents empty lines too (`"a\n\nb"` → `"  a\n  \n  b"`): not specified either way;
  the model follows the code.
- `wordwrap` drops the whitespace at a line break and trailing whitespace that would exceed the
  limit, and never splits a word wider than the limit (the README says to combine it with
  `wrap` for that).
- `wordwrap` keeps leading whitespace before a word wider than the limit (`" abcd"` at 3 stays);
  the word cannot fit anywhere and moving it gains nothing.
- The padding cells inherit the style in force at the end of the line; whether padding should be
  styled is a design choice, and the model accepts either.
- `truncate` writes the tail before the closing reset, so the tail takes the style of the cut
  text.
- `PrintableRuneWidth` treats only ESC-introduced sequences as invisible; an OSC hyperlink
  (`ESC ] 8 ;; url ESC \`) is not recognised and its parameters count as text. The package only
  claims SGR-style sequences.
