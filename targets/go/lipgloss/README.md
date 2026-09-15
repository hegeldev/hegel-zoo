# go/lipgloss — charmbracelet/lipgloss v2 (`Style.Render`, joins, placement, wrapping)

Hegel property tests for `charm.land/lipgloss/v2`, the terminal layout and styling library
behind Bubble Tea, pinned at `6a419c65` (main, 2026-09-11). The tests live in
`hegel_test.go` (package `lipgloss`, internal so the property keys are reachable) and run with
`go test -run TestHegel .`.

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

## Properties

| Test | What it checks |
|---|---|
| `TestHegelRenderFollowsTheBlockModel` | `Style.Render` vs the cell model, plus `Width`/`Height`/`Size`/`GetFrameSize` |
| `TestHegelJoinsFollowTheirModel` | `JoinHorizontal`, `JoinVertical` for all positions |
| `TestHegelPlaceFollowsItsModel` | `PlaceHorizontal`, `PlaceVertical`, `Place` with whitespace chars (constants; fractions are lipgloss/5) |
| `TestHegelWrapKeepsContentAndStyles` | `Wrap` invariants above |
| `TestHegelStyleRangesStyleTheirCells` | `StyleRanges` styles exactly the cells of each range |
| `TestHegelInheritTakesUnsetValuesOnly` | `Inherit` semantics |

Set `LIPGLOSS_COLLECT=1` (and `HEGEL_TEST_CASES=n`) to collect mismatches and statistics
instead of failing at the first one.

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

The property tolerates lipgloss/2–4 cell by cell (counted as `tolerated-*` in collect mode)
and skips the cluster cases of lipgloss/1 (`cluster-torn`); the generators use only the
position constants, so lipgloss/5–7 are pinned directly.

## Not bugs (modelled as documented)

- `UnderlineSpaces(true)` / `StrikethroughSpaces(true)` decorate spaces even when the text is
  not underlined or struck (documented), with a single underline.
- With Center, `Place*` puts the smaller half of an odd gap first, `Join*` the larger; the
  block model's own alignment puts the remainder on the right.
- A `Width` smaller than the horizontal padding leaves the text unwrapped.
- Tabs are expanded (4 cells by default) even when no other property is set.

## Not covered (yet)

Border foreground blends, `Canvas`/`Layer`/`Compositor`, the `table`, `list` and `tree`
subpackages, `StyleRunes`, `Style.Value`/`SetString`.
