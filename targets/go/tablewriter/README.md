# go/tablewriter

Hegel property tests for [olekukonko/tablewriter](https://github.com/olekukonko/tablewriter),
the ASCII/Unicode table renderer: its helper packages `pkg/twwidth` (display widths of strings
holding ANSI escape sequences, truncation, the tab width), `pkg/twwarp` (word splitting and
minimum-raggedness wrapping) and `tw` (padding, header title formatting, camel-case splitting,
break points); and the table's Markdown, HTML and boxed renderings (`renderer.NewMarkdown`,
`renderer.NewHTML`, `renderer.NewBlueprint` under every border style and rendition setting)
with header, rows and footer, trimming, auto-formatting, alignments, padding and AutoHide.

## Build

The patch adds a `hegel/` package; `go test -count=1 -run TestHegel -v ./hegel` needs nothing
beyond the module. The tests fix the tab width at 4 (`SetTabWidth` after a first `TabWidth()`,
see bug 1) and set the East Asian and narrow-border options per test case.

## Oracle

A model of the documented behaviour. Escape sequences are found by ECMA-48 (a CSI sequence is
`ESC [`, parameters, intermediates and a final byte; an OSC sequence is `ESC ]` up to BEL or
`ESC \`); the visible text's width is the sum of `displaywidth`'s rune widths (the package's
own primitive) with the tab width and the narrow box-drawing rule applied, and, when the
per-rune switch is off, `displaywidth`'s grapheme-aware string width. `Truncate` is modelled
case by case from its doc comment: negative width, visually empty input, zero width, a string
that fits (a reset appended after sequences), and the truncation walk keeping the sequences
met and the visible prefix that fits the budget left by the suffix. Wrapping: the words are
`strings.FieldsFunc(unicode.IsSpace)`; the partition returned by `WrapWords` must keep the
words, end in a line that fits (or a single word), cost the brute-force optimum of the
raggedness the package minimises (the squared slack of every line but the last, plus a penalty
for an overflowing line) and equal an independent statement of the dynamic programme;
`WrapString` and `WrapStringWithSpaces` add the limit adjustment, the special cases for blank
input and the preserved leading and trailing spaces. The `tw` helpers are modelled from their
comments (`Title`'s dot rule, `SplitCamelCase`'s classes and the upper-run lending its last
rune, `IsNumeric` as `Atoi`/`ParseFloat`, `BreakPoint` over the visible width, the `Pad`
family by gap).

For the table, a model of the documented pipeline: cells trimmed by `TrimSpace`/`TrimTab`,
tabs expanded, header (and optionally row/footer) cells auto-formatted through
`SplitCamelCase` and `Title`, split at newlines into visual lines, a blank later line of a
record dropped (`TrimLine`), column widths the widest cell plus the padding; the Markdown
cells padded to the column width by the alignment rules (an explicit body alignment, else the
header's, else centre; at least three characters), the separator row `:--`/`--:`/`:-:` per
column; the HTML sections (`thead`/`tbody`/`tfoot`, classes, `text-align` styles for the
explicit alignments, `html.EscapeString` unless disabled), exact to the byte. For the boxed
rendering, the layout of `renderer.Blueprint`: the rendition's borders, separators and lines
merged over the defaults (everything on but the separators between rows), a top border, the
header lines, its separator, the records (a separator between them when asked), the footer
separator, the footer lines and a bottom border; a border line is a horizontal segment per
visible column between the style's corner, junction and edge glyphs (the first and last
segments shortened by the corners' excess over the column glyph, as `Line` does); a cell line
is every visible cell padded to its column width by its alignment (an explicit one, else the
section's default) between column glyphs, the padding strings repeated as `formatCell` does.

## Properties

- `TestHegelWidth`: `Width`, `WidthNoCache`, `WidthWithOptions`, `Filter`, `SetOptions`,
  `SetTabWidth` (with the cache switch off).
- `TestHegelTruncate`: `Truncate` with and without a suffix, both East Asian settings.
- `TestHegelWrap`: `SplitWords`, `WrapWords`, `WrapString`, `WrapStringWithSpaces`.
- `TestHegelFn`: `tw.Title`, `tw.SplitCamelCase`, `tw.IsNumeric`, `tw.BreakPoint`, `tw.Pad`,
  `tw.PadLeft`, `tw.PadRight`, `tw.PadCenter`.
- `TestHegelMarkdown`: `NewTable` + `Header`/`Append`/`Footer`/`Render` with
  `renderer.NewMarkdown`, under `WithTrimSpace`, `WithTrimTab`, `With{Header,Row,Footer}AutoFormat`,
  `With{Header,Row,Footer}AlignmentConfig`, `WithAutoHide`, `WithHeaderControl`, `WithFooterControl`.
- `TestHegelHTML`: the same with `renderer.NewHTML` and its `HTMLConfig` (escaping, classes,
  `AddLinesTag`).
- `TestHegelBlueprint`: the same with `renderer.NewBlueprint` over the eleven border styles
  (`StyleASCII` to `StyleGraphical`, `StyleMarkdown` and `StyleNone` included), every state of
  `Borders`, `Separators` and `Lines`, and `WithPadding` (default, none, `*`/`**`, `""`/`>`);
  exact output, and every line of a bordered table as wide as the others.

## Bugs

Twenty-one, in `bugs.toml`. Tab width: a width set before the first `Size()` is overwritten by the
detection (1, medium); `Width`'s cache is not purged when the tab width changes (2, medium).
Widths: emoji sequences (VS16, ZWJ, flags, modifiers) are measured rune by rune (3).
`Truncate`: an ESC inside a sequence restarts the scan, so an `ESC \`-terminated OSC (a
hyperlink) swallows the rest of the string (4, medium); at width 0 the documented suffix is not
returned (5). Wrapping: `WrapStringWithSpaces` splits a multi-byte last rune, mis-measuring the
last word and returning a limit its lines exceed (6, medium). `tw`: `BreakPoint` counts the
characters of escape sequences, so `WrapBreak` cuts coloured text inside its sequence (7,
medium); `SplitCamelCase` keeps groups of several underscores (8). Table: the Markdown
renderer does not escape `|` in cells (9, medium); a cell with newlines becomes extra
Markdown/HTML rows and one `<thead>`/`<tfoot>` per header/footer line, the renderers' `<br>`
code being unreachable (10, medium); the Markdown and HTML renderers render the columns
`AutoHide` hides (11, medium); `WithColumnMax` is shared by the columns though documented as a
column width, emptying cells under `WrapTruncate` (12). Blueprint: `AlignNone` cells are
left-aligned in every section, the section defaults it computes being discarded (13); no top
border when the table has a footer but no header (14, medium); the separator after a column
hidden by `AutoHide` is dropped, so the cell lines are narrower than the borders (15, medium);
lines of different widths when `AutoHide` hides every column (16); two separator lines between
a header and a footer without rows (17); a table whose only record is empty renders `++`/`++`
(18); header `AutoFormat` (on by default) splits and upper-cases the escape sequences of a
coloured header, which then print as text (19, medium); `Truncate` and `Width` parse a CSI
sequence with a leading intermediate byte differently, so a truncated string can be wider
than the limit (20); `StyleGraphical`'s two-cell corners make the border lines of a lone
one-cell column wider than its cell lines (21).

## Modelled as recorded, not counted

- `Width` strips only CSI and OSC sequences (as `Filter` documents): a two-character escape
  such as `ESC 7` leaves its final character visible; an OSC holding a newline is not a
  sequence. The generators produce neither.
- `Truncate` appends a reset after a string that fits when it holds ESC and does not end in
  `ESC[0m`; the East Asian setting returns the bare suffix when exactly the suffix fits, the
  other setting the sequences met plus a reset plus the suffix.
- `WrapString(" ")` is `[" "]` but two spaces are `[""]`; a newline or a tab is a word
  separator; `WrapStringWithSpaces` of blank input returns its width as the limit (smaller than
  the input limit) and truncates a blank wider than the limit; its leading spaces are not
  counted in the limit, so a line with them may be wider than the limit returned.
- `IsNumeric` accepts whatever `ParseFloat` accepts: `inf`, `NaN`, `1_000`, hexadecimal floats.
- The `Pad` family repeats the padding string by characters, not columns (a wide padding
  character over-pads), and `Pad` with an unknown alignment pads right.
- Table: a record without cells is dropped; a header or footer of zero cells is not rendered;
  the Markdown footer cells take the body's alignment (one alignment per column); Markdown
  always pads with at least a space even under `PaddingNone`; escape sequences in cells are
  written raw.
- Blueprint: `StyleMarkdown` and `StyleNone` have empty corner and junction glyphs, so their
  border lines are narrower than the cell lines (`----|----` under `| a | b |`); `StyleNone` is
  all spaces; `StyleGraphical`'s two-cell glyphs are absorbed by `Line`'s adjustment except in
  bug 21; a header-and-rows table draws a top border, a rows-only table too, a footer-only table
  none (bug 14); a record of fewer cells is padded with empty ones; `AutoHide` looks at the
  rows only (a column with a header but no row content is hidden); a multi-character padding is
  repeated whole and cut back by `Truncate` (visible with bug 20); the ragged-width check skips
  the cases of bugs 15, 19/20 and 21. Merges, width constraints, captions, streaming,
  `Bulk`/struct input and the Colorized, Ocean and SVG renderers are not yet exercised.
