# go/tablewriter

Hegel property tests for [olekukonko/tablewriter](https://github.com/olekukonko/tablewriter),
the ASCII/Unicode table renderer: its helper packages `pkg/twwidth` (display widths of strings
holding ANSI escape sequences, truncation, the tab width), `pkg/twwarp` (word splitting and
minimum-raggedness wrapping) and `tw` (padding, header title formatting, camel-case splitting,
break points); and the table's Markdown, HTML and boxed renderings (`renderer.NewMarkdown`,
`renderer.NewHTML`, `renderer.NewBlueprint` under every border style and rendition setting)
with header, rows and footer, trimming, auto-formatting, alignments, padding, AutoHide, the
width constraints (`WithColumnWidths`, `With{Header,Row,Footer}MaxWidth`, `WithMaxWidth`) with
the wrap modes, and captions; and the input conversion of `Append`/`Bulk` (`[]string`, `[]any`,
typed slices, single values, structs with `tw`/`json`/`db` tags and AutoHeader); and cell
merging (`With{Header,Row,Footer}MergeMode`: horizontal, vertical, hierarchical and their
combinations, `Merging.ByColumnIndex`); and the streaming API (`WithStreaming`, `Start`,
`Header`/`Append`/`Footer` in any order, `Close`, `StrictColumns`, `WithColumnWidths` and
`WithColumnMax` as the fixed stream widths).

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
Width constraints follow `calculateContentMaxWidth`: the cell width is the per-column width
if set, else the section's maximum (which a table `MaxWidth` replaces by `MaxWidth` over the
record's cell count when no per-column width is set), else `MaxWidth` for a wrapping section;
less the padding, at least 1; each visual line is then wrapped by the section's mode
(`WrapNormal`: `WrapString`, or `WrapStringWithSpaces` unless both trims are on;
`WrapTruncate`: `Truncate` to one less with the ellipsis; `WrapBreak`: `BreakPoint` pieces
with the break character, a blank line vanishing), and a per-column width replaces the natural
column width outright (0 hides the column). A caption is wrapped to its width, else the table's
(else its own for a table under five cells), padded to that target by its alignment or the
spot's default, and printed above or below; side spots print nothing.

Input conversion, from the code's documented cases: a cell value is its `Format()`, else its
`io.Reader` content up to 512 bytes, else the `sql.Null*` value or empty, else `string([]byte)`,
`Error()`, `String()`, the `strconv` form of a basic type, and `fmt.Sprintf("%v")` for the
rest; a row is a `[]string`, a `[]any` or typed slice of cells, a Formatter/Stringer alone, a
struct or pointer to one reflected into its exported fields (embedded structs recursively; the
`tw` tag's `-` and `name=`, the first non-empty `json`/`db` tag naming the column, `-` skipping
it and `,omitempty` blanking a zero value; the header names titled), else one cell. AutoHeader
takes the header from the first struct appended (Bulk: its first element) when none is set.
The generated values include nil pointers, typed nils in interfaces, `sql.Null*` with both
validities, readers of 0-600 bytes, embedded structs by value and by (nil or set) pointer, and
dynamic struct types built with `reflect.StructOf`.

Cell merging, from `prepareWithMerges` and the merge passes: in a header, record or footer
with the horizontal bit, a run of equal non-empty logical cells (the visual lines joined and
trimmed; `-` never merges) merges into its first column and the others are blanked; a footer's
leading empty cells merge with its first content cell, which moves to column 0 (the `TOTAL`
pattern); with the vertical bit a run of equal non-empty cells down a column merges, and with
the hierarchical bit a cell merges with the one above only when it is the first column or the
cell to its left merged too (the passes run horizontal, vertical, hierarchical, each on the
content the previous one left); `ByColumnIndex` restricts the vertical and hierarchical
passes. The rendering follows `renderLine` and `Junction`: a merge's first cell spans the
widths of its columns and their separators (a row's from the normalized widths at render
time, a header's or footer's as pre-computed), the continuing cells print nothing, a cell
continuing a vertical or hierarchical merge is blank, an `AlignNone` cell starting a footer
merge or following a `total` cell is right-aligned, and a separator line's segments are
spaces where a vertical merge passes through, its junction glyphs chosen by the merge states
above and below (the column glyph inside a pass-through, the mid-left/mid-right glyphs at its
edges, the top-mid/bottom-mid glyphs where a horizontal span ends above or below).

Streaming, from `Start`, `streamCalculateWidths` and the `stream*` render functions: the
column count and the fixed widths come from `Widths.PerColumn` (missing columns 0, negative
ones dropped by the option), else from the first section that arrives with cells - each
trimmed cell's width (at least the ellipsis's under `WrapTruncate`) plus a variance of two
plus the padding, at least `MinimumColumnWidth` (8) - shrunk in proportion to `Widths.Global`
when the table is wider (separators counted, every column at least 1, the rounding
remainder spread column by column); every later row is padded or cut to the count, or refused
with an error under `StrictColumns`; a row without cells prints nothing; the cells wrap to the
fixed width less the padding (the section maximum widths and `MaxWidth` are ignored); the
horizontal merges are detected on the raw trimmed cells; the top border comes with the first
header or row, the header separator with the first row (or with the header when the footer
was stored first), a separator between rows when asked, and `Close` prints the stored footer
after its separator and the bottom border with the last line's merge states.

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
- `TestHegelConstraints`: the boxed rendering under `WithColumnWidths` (0, small, large and
  negative widths), `With{Header,Row,Footer}MaxWidth`, `WithMaxWidth`,
  `With{Header,Row,Footer}AutoWrap` (all four modes) and `Caption` (every spot, alignment and
  width), exact output.
- `TestHegelInput`: `Append` (single, variadic, slices), `Bulk`, `Configure` with
  `Behavior.Structs.AutoHeader`, an explicit `Header`, checked through the Markdown rendering.
- `TestHegelBlueprint`: the same with `renderer.NewBlueprint` over the eleven border styles
  (`StyleASCII` to `StyleGraphical`, `StyleMarkdown` and `StyleNone` included), every state of
  `Borders`, `Separators` and `Lines`, and `WithPadding` (default, none, `*`/`**`, `""`/`>`);
  exact output, and every line of a bordered table as wide as the others.
- `TestHegelMerge`: the boxed rendering with `With{Header,Row,Footer}MergeMode`
  (`MergeVertical`, `MergeHorizontal`, `MergeBoth`, `MergeHierarchical` and, through
  `Configure`, the combinations 5-7), `Row.Merging.ByColumnIndex`, over cells from a small pool
  so that equal neighbours are common, with `AutoHide`, padding and every rendition setting;
  exact output.
- `TestHegelStream`: `Start`/`Header`/`Append`/`Footer`/`Close` in three call orders with
  `StreamConfig.StrictColumns`, `WithColumnWidths`, `WithColumnMax`, the wrap modes, padding,
  the horizontal merge modes and every rendition setting, against the streamed Blueprint
  output and the count of rows `Append` refuses; exact output.

## Bugs

Forty, in `bugs.toml`. Tab width: a width set before the first `Size()` is overwritten by the
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
one-cell column wider than its cell lines (21). Captions and widths: a caption aligned left
on a centre or right spot is realigned to the spot's default, `AlignDefault` being `AlignLeft`
(22); with a caption an empty table becomes hard-coded `+--+` lines in any style (23);
`WithMaxWidth` does not bound the table width - padding, separators and borders are uncounted
and long words widen the columns (24, medium). Input: pointers to basic types render as
addresses (25, medium); a nil `*time.Time` (any nil pointer whose `String()`/`Error()`
dereferences) panics (26, high); `sql.NullInt32`/`NullInt16`/`NullByte` render as `{5 true}`
(27); a `[]byte` row is a numeric cell per byte, against the code's own comment (28); an
`io.Reader` of exactly 512 bytes gets the ellipsis (29); a nil embedded struct pointer drops
its columns and misaligns AutoHeader (30, medium); an error or reader appended alone is an
empty row (31); AutoHeader's extraction consumes the first row's readers (32). Merges: the
top border has no junction after a merged header cell, the row glyph standing where the header
line has its separator (33); a merged header keeps the widths of the columns `AutoHide` hides,
so the header line is wider than the rows (34, medium); the footer's lead merge drops the
later lines of a multi-line cell (35). Streaming: a merged header cell is rendered at its
first column's width, so the header line is narrower than the borders (36, medium); the
footer's horizontal merges are not applied though `Start` promises them (37); an empty row
appended first suppresses the header separator (38); the `Widths.Global` shrink spreads its
rounding remainder in map order, so the same table lays out differently from run to run (39,
medium). A streamed `Append` with a horizontal row merge blanks the merged cells in the caller's slice (40, medium).

The generators draw the shape of every recorded bug by default (STYLE.md rule 11): each
property finds several bugs, fails on the first shape it meets with the shape named in the
failure message, and is listed in `[expected_failures]` mapped to the basin the shrinker lands
in most often (`Width` on 3, `Truncate` on 5, `Wrap` on 6 (intermittent at the default case count), `Fn` on 8, `Markdown` and `HTML` on
11, `Blueprint` and `Constraints` on 18, `Merge` on 13, `Stream` on 36, `Input` on 26), the pins
beside them as the regression examples. `HEGEL_NO_KNOWN=1`, read once into the `Known`
switches, turns the shapes off in the generators (a tab width of 0, a visible column, a value
the input accepts; the all-hidden and random-remainder tables are filtered at a few percent)
and every property passes at 3000 cases.

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
  the cases of bugs 15, 19/20 and 21.
- Widths and captions: `WithColumnWidths` with 0 hides the column (and drops the separator
  after it, bug 15 again); a width narrower than the padding gives a content width of 1, and
  `WrapTruncate` at 1 empties the cell (bugs 5 and 12); the `MaxWidth` share is computed per
  record from its own cell count, so a short record wraps wider; `WrapBreak` keeps a trailing
  space before the break character and drops a blank visual line; `WithColumnMax`
  (`Widths.Global`, bug 12) and its shrinking pass are not generated; the side caption spots
  (`SpotLeftTop` ...) are defined but print nothing; a caption's `Width` pads the caption to
  that width even when the table is wider or narrower.
- Input: a struct appended alone is a row of its fields even when `convertToString` has a case
  for the type (`sql.NullString` alone is two cells, `String` and `Valid`); a nil pointer to a
  struct is the cell `<nil>`; a `[]int32` is numbers, not runes; `Bulk` takes the AutoHeader
  from its first element even after rows were appended; `IsZero` for `omitempty` looks at the
  interface for interface-typed fields, so a typed nil inside one is not zero; the `tw` tag's
  `align`, `max_width`, `pad_*`, `trim_*`, `auto_format` and `wrap` keys (table-wide side
  effects applied on the first row only) are not generated.
- Merges: `-` never merges (a placeholder); a horizontal merge compares the logical cell (all
  visual lines joined), so `x\ny` merges with `x\ny` only; the vertical pass runs over the
  horizontally merged content, so a cell blanked by a horizontal merge cannot start a vertical
  run; a vertical run continues across a record without cells; the hierarchical pass compares
  a snapshot taken after the vertical pass; the `total` rule looks at the previous cell of the
  same visual line; the header's and footer's `MergeMode` use only the horizontal bit;
  `TrimLine` drops a visual line blanked by a merge; `Behavior.Compact.Merge` and the
  merged-header expansion (never reached: each column is at least as wide as the shared header
  cell) are not generated.
- Streaming: `AutoHide`, the vertical and hierarchical merges, the section maximum widths and
  `MaxWidth` are ignored (`Start` warns about the first two); a footer-only table has no top
  border (bug 14's streaming twin, not counted); a hidden header or footer (`Control.Hide`)
  is as if never given, so it does not fix the widths; the header's `AutoFormat` runs after
  the width sample, so a formatted header can be wider than its column and is truncated; a
  merge in a header cell starts at raw-cell equality (`a` and `A` do not merge, `x\ny` and
  `x\n\ny` do not, unlike batch mode); blank visual lines are kept (`TrimLine` is batch
  only); the footer separator's junctions see no footer merge states; a row refused under
  `StrictColumns` leaves the stream as it was; cases where the global shrink leaves a
  rounding remainder over several columns are drawn (bug 39) and left out only under
  `HEGEL_NO_KNOWN=1`. `NewCSV` and the Colorized,
  Ocean and SVG renderers are not yet exercised.

## History

- 2026-09-21: written against 5f0c87a871a3084b2632f3a7775e45a75ea0422d (v1.1.5, 2026-09-15) with
  hegel v0.6.33; 39 bugs.
- 2026-09-26: generators rewritten in combinator style (case records per property, weighted
  choices, `chance`/`mostly`/`maybe`, embedded fields inserted modulo the live size) and the
  known-bug steering turned off by default; four latent model bugs fixed (blank cells still
  count as columns one wide, a row or header wrapping to no line does not move the stream's
  last position, the stream wraps after the horizontal merge); tablewriter/40 recorded (a
  streamed merge writes into the caller's slice), found by the stream property comparing its
  inputs before and after, reproduced standalone.
