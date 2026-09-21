# go/go-pretty

Hegel property tests for [jedib0t/go-pretty](https://github.com/jedib0t/go-pretty), the
table/list/progress renderer: its `text` package, the ANSI-aware string utilities the renderers
are built on (widths, trimming, wrapping, alignment, case conversion, colours, the escape
sequence parser, the transformers); its `table` package (the boxed, CSV, TSV, Markdown and HTML
renderings, filtering, sorting, hidden columns, the pager); and its `list` package.

## Build

The patch adds a `hegel/` package; `go test -count=1 -run TestHegel -v ./hegel` needs nothing
beyond the module.

## Oracle

A model of the documented behaviour over strings holding escape sequences. A scanner splits a
string into sequences and visible runes by ECMA-48 (a CSI sequence ends at its final byte, an
OSC sequence at BEL or ESC \); the visible text and its width (`text.RuneWidth` per rune, the
package's own definition) follow. An SGR state (foreground, background, the attributes 1-9,
set by their codes and cleared by 22-29, 39, 49 or 0) is tracked through the sequences, so
that the state in force at every visible rune can be compared between input and output. On
these: the documented rules of Trim, Snip, Pad, RepeatAndTrim, Widen, InsertEveryN, ProcessCRLF,
Align (trimming, padding, justification, the numeric test of AlignAuto), VAlign, Format
(sequences untouched), Escape (the sequence applied from the start and after every reset), the
parser's restored sequence (must denote the state), and for the wrap functions the invariants:
every line fits the width, the visible non-space runes and their escape state are preserved in
order, a wrapped output leaves no state open, WrapSoft keeps words that fit, a string that fits
is returned as it is. The transformers are checked against `fmt.Sprintf` with the documented
sign colours and against `time.Format` with the documented unit detection.

For the `table` package, a model of the rows as documented: cells stringified as
`convertValueToString` does (transformers applied), rows filtered by the documented operators,
columns hidden or suppressed, numeric columns detected; on it the exact CSV/TSV records (read
back with `encoding/csv`), the exact Markdown and HTML outputs (plus the cells a GFM table
parser reads back), and for the boxed rendering the line layout (title, header, rows, footer,
separators), one width for every line (or `Size.WidthMax`), the cells' text, the auto-index
numbers and a row's `AutoMerge`. Sorting is checked as a permutation in an order the keys allow.
The pager's pages must re-join to `Render()`, hold the page size, and navigate as documented.
For the `list` package, the exact `Render`/`RenderMarkdown` output and the `<ul>`/`<li>` nesting
of `RenderHTML` against the items and their levels.

## Properties

- `TestHegelWidth`: `StripEscape`, `StringWidthWithoutEscSequences`, `RuneCount`,
  `LongestLineLen`, `Trim`, `Pad`, `Snip`, `Widen`, `RepeatAndTrim`.
- `TestHegelInsert`: `InsertEveryN`, `ProcessCRLF`.
- `TestHegelAlign`: `Align.Apply` (all six alignments), `VAlign.Apply`, `VAlign.ApplyStr`.
- `TestHegelFormat`: `Format.Apply`.
- `TestHegelEscape`: `Escape`, `Colors.Sprint`, `EscSeqParser.ParseString/Sequence/IsOpen`.
- `TestHegelWrap`: `WrapHard`, `WrapSoft`, `WrapText`.
- `TestHegelTransform`: `NewNumberTransformer`, `NewTimeTransformer`,
  `NewUnixTimeTransformer`.
- `TestHegelTableCSV`: `RenderCSV`, `RenderTSV`, `FilterBy`, `SortBy`, `SetColumnConfigs`
  (Hidden, transformers), `SuppressEmptyColumns`, `SetAutoIndex`, `CSV.FieldProtection`,
  `Length`, `ImportGrid`.
- `TestHegelTableMarkdown`: `RenderMarkdown` (with and without `PadContent`).
- `TestHegelTableHTML`: `RenderHTML`.
- `TestHegelTableRender`: `Render` with title, caption, `SeparateRows`, auto-index, colours, a
  column `WidthMax`, `Size.WidthMin`, `Size.WidthMax`, `RowConfig{AutoMerge}`.
- `TestHegelTablePager`: `Pager`, `SetPageSize`, `PageSize`, `GoTo`, `Next`, `Prev`,
  `Location`.
- `TestHegelList`: `list.Writer` `Render`, `RenderMarkdown`, `RenderHTML`, `Indent`,
  `UnIndent`, `UnIndentAll`, `Length`.

## Bugs

Forty-five, in `bugs.toml`. In `text`, twenty-four. Sequences: a CSI sequence is terminated only by `m`, so the
package's own cursor and erase sequences swallow the text after them (1, medium); an OSC
sequence terminated by BEL is recognised only for OSC 8 (2); the parser reads a 24-bit colour
as five attributes (9, medium), restores colours in numeric order rather than the last set
(10, medium), ignores 28 (11), and applies 256-colour codes before the other codes of the same
sequence, so `ESC[0;38;5;31m` loses its colour (23, medium). Wrapping: a reset leaves the
earlier sequence to be re-opened on later lines (5, medium); a word broken across lines
restarts with the raw sequence found in the word, losing the other attributes (6, medium); a
hyperlink's parameters are read as SGR codes so the following lines are concealed (7, medium)
and the hyperlink word is never wrapped (8); the state is dropped at a paragraph break and, in
WrapText, at a line break (20, medium); a wide rune straddling the width makes the line one
column too wide (21, medium). Strings: Format.Apply ends every sequence at `m`, case-changing
a hyperlink's URL and label (3, medium); FormatTitle upper-cases instead of title-casing (16);
Escape with an empty sequence removes every reset (4) and removes the input's own
sequence+reset pair, leaving the output open (24); AlignAuto reads the number from the raw
text (15); AlignJustify panics on a blank text and a negative length (22); RepeatAndTrim counts
runes but trims by width (17); Snip neither pads as documented nor keeps the length with a wide
indicator (18); ProcessCRLF lets escape sequences take columns (19). Transformers: negatives
are formatted as `-` plus the format of the negated value, breaking widths and MinInt64 (12);
times at or before the epoch render as "" (13, medium); unix times are accepted as int64 and
string only (14).

In `table`, twenty-one. Crashes: `Pager()` keeps the previous pager's page and panics past the
new page count (39, medium); `Render` divides by zero re-balancing a merged cell wider than its
columns (42, medium). Rows: an empty row gets one field too many in CSV/TSV (25) and is dropped
by `Render` and `RenderHTML` (26); a row of one empty cell is an empty CSV line that readers
skip (45); `ImportGrid` turns an empty inner row into a `[]` cell (38); `RowConfig` stays with
a position when rows are sorted or filtered (35, medium). Sorting and filtering: a numeric sort
with a non-numeric cell leaves the numbers unordered (29, medium); duplicate keys are applied,
not discarded (30); `SortBy.Name` is matched after the header transformer (31); `Equal` compares
strings (32); a row lacking the column fails every operator (33); `Length()` reports the
previous render's filter (34); `SuppressEmptyColumns` decides on the first non-empty cell (40,
medium). Layout: Markdown `PadContent` pads by the raw width (27) and backslashes are not
escaped (28); `Size.WidthMin` sizes the title beyond capped columns (36) and beyond
`Size.WidthMax` (41); `Size.WidthMax` of 1 or 2 renders nothing (37); the auto-index header row
is not counted in the widths (43); a footer-only table gets a `++` top border (44).

## Modelled as recorded, not counted

- Widths are `text.RuneWidth` per rune (runewidth with the box-drawing rule): a combining mark
  is 0, an emoji 2, a ZWJ sequence the sum of its parts; the model uses the same function.
- Align trims spaces on the padded side only when the raw string has a space at that end (a
  sequence at the end prevents it); Justify splits the raw text on spaces, so a sequence
  standing alone is a word and a blank text loses its sequences.
- WrapSoft pads the lines it ends early with spaces to the width (the package's tests assert
  it); a string that fits is returned with its line breaks and space runs, while a longer one is
  re-flowed; tabs become four spaces first.
- ProcessCRLF overwrites rune by rune, so a wide rune is one column; Pad appends characters,
  not columns; Trim drops the visible runes after the first that does not fit.
- NewUnixTimeTransformer reads a value >= 10^10 as milliseconds, >= 10^13 as microseconds,
  >= 10^16 as nanoseconds; float32 values are formatted after conversion to float64.
- Table: `Format.Header`/`Format.Footer` (upper case) apply to the boxed rendering only; the
  CSV title and caption are written as raw lines; TSV quotes a field holding four spaces; a
  regex filter that does not compile falls back to an equality; a non-numeric cell under a
  numeric sort, and NaN, are unordered; Markdown `PadContent` keeps the separator at least
  three dashes wide (narrower columns misalign, as the option's own example shows); the GFM
  read-back trims cells and maps `<br/>` to a newline.
- List: `Indent` shifts only once past the previous item's level and never before the first
  item; the connector styles (`StyleConnected*`) are not exercised, `StyleDefault` and
  `StyleMarkdown` are.
- The `progress` package is not exercised.
