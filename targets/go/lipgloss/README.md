# go/lipgloss — charmbracelet/lipgloss v2 (`Style.Render`, joins, placement, wrapping, blends, table, tree/list, compositor)

Hegel property tests for `charm.land/lipgloss/v2`, the terminal layout and styling library
behind Bubble Tea, pinned at `6a419c65` (main, 2026-09-11). The tests live in
`hegel_test.go`, `hegel_canvas_test.go` and `hegel_blend_test.go` (package `lipgloss`, internal
so the property keys are reachable), `table/hegel_test.go` (package `table`, internal for the resizer) and
`tree/hegel_test.go` (package `tree_test`, covering `tree` and `list`); the shared harness and
cell model are in `internal/zootest`. Run with
`go test -run TestHegel . ./table ./tree`.

## Approach

- **A block model for `Style.Render`.** A style is drawn as a random subset of its properties
  (attributes, foreground/background/underline colours, Width, Height, horizontal and vertical
  alignment, Padding and PaddingChar, ColorWhitespace, Margin with MarginBackground and
  MarginChar, the ten preset borders with or without explicit sides and per-side colours,
  Inline, MaxWidth, MaxHeight, TabWidth, UnderlineSpaces, StrikethroughSpaces, Hyperlink,
  Transform) and the text as 1–4 lines of graphemes (ASCII, accented letters, wide CJK and
  emoji, ZWJ and Thai clusters, spaces, tabs, `\r\n`). The model builds the grid of cells the
  documented rules describe — tabs, transform, inline, wrapping (delegated to `ansi.Wrap`,
  which the `x-ansi` target checks), the text pen, the whitespace pen, padding, height,
  alignment to `max(widest, width)`, border edges cycled from the border runes, margins,
  MaxWidth by cells, MaxHeight — and the rendered string is parsed back (SGR and OSC 8
  replayed, graphemes measured with `ansi.DecodeSequence`) and compared cell by cell.
  Attributes a terminal cannot show on a blank (bold, faint, italic, blink, foreground) and
  an underline colour without an underline are ignored. `Width`, `Height`, `Size` and
  `GetFrameSize` are checked against the same cells.
- **String models** for `JoinHorizontal`/`JoinVertical` and `PlaceHorizontal`/`PlaceVertical`/
  `Place` (with `WithWhitespaceChars`), for `StyleRanges` (cell ranges on plain text) and for
  `Inherit` (set values win, padding and margins are not inherited, the margin background
  follows an inherited background).
- **Wrap invariants**: `Wrap` shows exactly `ansi.Wrap`'s text, keeps every non-blank
  grapheme with its pen and link, never carries an open pen across a newline, and its lines
  fit the limit unless `ansi.Wrap`'s own line already overflows (x-ansi/8, /12, /19, /21).
- **A grid model for `table`.** Random headers and rows (0–9 graphemes per cell, spaces,
  newlines, wide runes), a random border with any subset of its sides, per-cell styles
  (padding, margins, fixed width/height, background, alignment), `Width`, `Height`, `Wrap`,
  `Offset`. The model computes the expected column widths (content widths or fixed widths when
  they fit, otherwise only the total), the line structure (border lines, header, rows,
  overflow row), the border characters and column separators, and the text of each region
  (wrapped by `ansi.Wrap`, truncated with `…`, or clipped by the row height), plus
  idempotence of `String()` and the `Filter`/`DataToMatrix` data views. The shrinking
  heuristics are not modelled beyond the total width.
- **A layout model for `tree` and `list`.** Random trees (depth 3, hidden nodes, `Offset`,
  multi-line values, nested rootless trees) rendered with the default, rounded, Arabic and
  star enumerators, compared line by line with the documented layout (prefix blocks
  right-aligned to the widest enumerator, indenters for continuation lines, `Width`
  padding); `Roman` and `Alphabet` against reference formulas; `list` auto-nesting (`Child`
  with a rootless sublist parents it to the previous item) against a model of
  `ensureParent`.
- **Gradients against their own 1D ramp.** `Blend1D` is checked structurally (length, stops
  kept verbatim when `steps <= len(stops)`, nil stops dropped, a single stop repeated, first
  and last stop at the ends, stops appearing in order, reversal symmetry); `Blend2D` against
  `Blend1D(max(w, h))` as a rotated ramp (rows equal at 0°/180°, columns at 90°/270°, the
  180° rotation a mirror image, the top row monotone); a `BorderForegroundBlend` by parsing
  the rendered frame and walking its perimeter against `Blend1D((h + cols + 2) * 2)` rotated
  by the offset, with `BorderBackground` and partial sides. `StyleRunes` against per-rune
  style membership and `SetString`/`Value`/`Render` against `strings.Join`.
- **A cell model for `Layer`/`Compositor`.** A random layer tree (positions, z, styled
  content, children) is flattened to absolute rectangles, painted by z then insertion order
  (short lines padded with blanks), and compared with `Compositor.Render` (after
  `TrimSpace`), `Bounds`, `Layer.Width`/`Height` and `Hit`.

## Properties

| Test | What it checks |
|---|---|
| `TestHegelRenderFollowsTheBlockModel` | `Style.Render` vs the cell model, plus `Width`/`Height`/`Size`/`GetFrameSize` |
| `TestHegelJoinsFollowTheirModel` | `JoinHorizontal`, `JoinVertical` for all positions |
| `TestHegelPlaceFollowsItsModel` | `PlaceHorizontal`, `PlaceVertical`, `Place` with whitespace chars (constants; fractions are lipgloss/5) |
| `TestHegelWrapKeepsContentAndStyles` | `Wrap` invariants above |
| `TestHegelStyleRangesStyleTheirCells` | `StyleRanges` styles exactly the cells of each range |
| `TestHegelInheritTakesUnsetValuesOnly` | `Inherit` semantics |
| `TestHegelBlend1DRunsThroughItsStops` | `Blend1D` structure, ends, order, symmetry |
| `TestHegelBlend2DIsARotatedRamp` | `Blend2D` vs the 1D ramp at right angles and mirrors |
| `TestHegelBlend2DReachesBothEnds` | a one-row 0° gradient runs from the first stop to the last (lipgloss/25) |
| `TestHegelBorderBlendWrapsTheFrame` | `BorderForegroundBlend`/`Offset` vs the ring, perimeter walk, backgrounds |
| `TestHegelStyleRunesStyleTheirRunes` | `StyleRunes` styles exactly the matched runes |
| `TestHegelSetStringJoinsAndRenders` | `SetString`, `Value`, `String`, `Render` with a value |
| `TestHegelCompositorPaintsLayersInOrder` | `Compositor.Render`/`Bounds`/`Hit`, `Layer.Width`/`Height` vs the paint model |
| `TestHegelTableLaysOutItsGrid` | `table.Table.String()` vs the grid model, `VisibleRows`, idempotence |
| `TestHegelTableDataViews` | `Filter` and `DataToMatrix` |
| `TestHegelTreeFollowsTheLayout` | `tree.Tree.String()` vs the layout model for four enumerators, `Width` |
| `TestHegelListEnumeratorsCount` | `list.Roman`, `list.Alphabet` vs reference formulas |
| `TestHegelListsNestAsTrees` | `list.New(...)` auto-nesting vs a model of `ensureParent` |

Set `LIPGLOSS_COLLECT=1` (and `HEGEL_TEST_CASES=n`) to collect mismatches and statistics
instead of failing at the first one; shapes of pinned bugs are counted as `lipgloss/N-shape`
and skipped.

## Bugs (see `bugs.toml`)

| id | severity | title |
|---|---|---|
| lipgloss/1 | medium | Underline or Strikethrough styles the text rune by rune, tearing grapheme clusters apart |
| lipgloss/2 | medium | Reverse is dropped from spaces when the space styler is active |
| lipgloss/3 | low | Spaces get a single underline whatever UnderlineStyle the text has |
| lipgloss/4 | medium | A Hyperlink covers the padding, alignment, border and margin cells between the first and last line |
| lipgloss/5 | medium | PlaceHorizontal and PlaceVertical mirror fractional positions (upstream #236, open since 2023) |
| lipgloss/6 | medium | Height is ignored when AlignVertical is a fractional position |
| lipgloss/7 | low | A fractional horizontal alignment is treated as Left |
| lipgloss/8 | medium | table: Width ignores the borders when deciding whether to shrink, and the right border is clipped |
| lipgloss/9 | low | table: shrinkToMedian never shrinks the first column |
| lipgloss/10 | medium | table: the bottom border is clipped when a table with Height has no headers |
| lipgloss/11 | medium | table: the header row's height follows the last column's padding only |
| lipgloss/12 | medium | table: Wrap(false) drops every line after the first of a multi-line cell |
| lipgloss/13 | low | table: the overflow row takes the previous row's padding when the table has headers |
| lipgloss/14 | low | tree: two hidden children at the end of a branch leave the last visible child with ├── |
| lipgloss/15 | low | tree: Width pads only the last line of a multi-line item |
| lipgloss/16 | medium | tree: Offset's end is documented as an index but used as a count from the end |
| lipgloss/17 | low | list: the Alphabet enumerator labels every 26th block of 26 items with '@' |
| lipgloss/18 | medium | table: Wrap(false) ignores vertical padding, so a padded cell loses its text |
| lipgloss/19 | high | Compositor.Render draws layers at absolute coordinates on a canvas sized to the bounds |
| lipgloss/20 | low | tree: auto-nesting a rootless tree onto a hidden leaf makes it visible |
| lipgloss/21 | low | tree: a hidden first child keeps its index and shifts the enumeration |
| lipgloss/22 | medium | Compositor draws equal-z layers out of insertion order once there are more than twelve |
| lipgloss/23 | low | Border foreground blends skip two colours at the top-right and bottom-right corners |
| lipgloss/24 | low | Blend1D drops the last stop when there are fewer than two steps per segment |
| lipgloss/25 | low | Blend2D never reaches the last stop |
| lipgloss/26 | medium | StyleRunes pads multi-line strings, inserting spaces mid-line |
| lipgloss/27 | low | Blend2D right angles are inexact: the residue of sin/cos decides cells on a boundary |
| lipgloss/28 | medium | A colour channel below 1/256 is written out 256 times too bright (root cause in x/ansi `shift`) |
| lipgloss/29 | low | Render panics when every stop of a border foreground blend is nil |

The block-model property tolerates lipgloss/2–4 cell by cell (counted as `tolerated-*` in
collect mode) and skips the cluster cases of lipgloss/1 (`cluster-torn`); the generators use
only the position constants, so lipgloss/5–7 are pinned directly. The table, tree and
compositor properties gate the shapes of lipgloss/8–22 and pin each one; the blend properties
gate lipgloss/23–28 by cause (the two right-hand corners, rings with under two steps per
segment, the last cell, strings with a newline, cells on an exact index boundary, ring
colours with a 16-bit channel below 256) and lipgloss/29 is pinned only.

## Not bugs (modelled as documented)

- `UnderlineSpaces(true)` / `StrikethroughSpaces(true)` decorate spaces even when the text is
  not underlined or struck (documented), with a single underline.
- With Center, `Place*` puts the smaller half of an odd gap first, `Join*` the larger; the
  block model's own alignment puts the remainder on the right.
- A `Width` smaller than the horizontal padding leaves the text unwrapped.
- Tabs are expanded (4 cells by default) even when no other property is set.
- `list.Roman` is correct; a hidden child that follows a visible one is removed correctly
  from the branch and the enumeration (only a hidden *first* child, lipgloss/21, and
  *adjacent* hidden children, lipgloss/14, go wrong).
- `Compositor.Render` trims trailing unstyled blanks per line (`uv.TrimSpace`) but keeps
  styled blanks; a layer is a full rectangle for `Hit`, blank cells included.
- A table `Width` below the sum of the columns' frames (`width-below-minimum`) cannot be
  honoured; the property stops at the total width there. `Height` clips through
  `MaxHeight(min(Height, computeHeight))`, and `MaxHeight(0)` is no limit.
- A wide grapheme cut by a table `Width` at the right edge leaves its line one cell short
  (`wide-cut-at-edge`), as any cell clipping would.
- `Blend1D(steps <= len(stops))` returns the stops themselves, nil included; a completely
  transparent stop is treated as opaque (documented). A single nil stop in
  `BorderForegroundBlend` is ignored; `BorderForegroundBlendOffset` rotates so that the
  ramp's first colour sits `offset` cells along the perimeter (the top-left corner shows
  ring index `-offset mod n`).
- The Blend2D properties compare colours to within one 8-bit step per channel
  (`colorful.Color` values are compared after `RGBA()`).
- Table cells containing `-` or a line that starts with a space wrap through `ansi.Wrap`'s
  own quirks (x-ansi/12, /19); those cells are counted, not compared. Text sources are NFC
  (a decomposed `é` is x-ansi/5).

## Not covered (yet)

Blend2D at angles other than multiples of 90° beyond "every cell is a ramp colour",
`Lighten`/`Darken`/`Complementary`, `table` shrinking heuristics beyond the total width,
`tree` style functions and custom indenters.
