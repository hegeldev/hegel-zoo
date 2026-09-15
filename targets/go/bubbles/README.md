# go/bubbles — charmbracelet/bubbles v2 (`textinput`, `textarea`, `viewport`, `paginator`, `table`, `list`, `help`, `progress`, `filepicker`)

Hegel property tests for `charm.land/bubbles/v2`, the component library of Bubble Tea, pinned
at `0a69b19b` (main, 2026-09-01). Nine slices so far: `textinput`, the single-line editor
(`textinput/hegel_test.go`, package `textinput`, internal so the window offsets are readable),
`textarea`, the multi-line editor (`textarea/hegel_test.go`, package `textarea`, internal
for the wrap grid and the viewport offset), and `viewport`, the scrolling pager
(`viewport/hegel_test.go`, package `viewport`, internal for the highlight index and the
soft-wrapped rows), `paginator` (`paginator/hegel_test.go`) and `table`
(`table/hegel_test.go`, package `table`, internal for the rendered window's first row) and
`list` (`list/hegel_test.go`), `help` (`help/hegel_test.go`) and `progress`
(`progress/hegel_test.go`, package `progress`, internal for the frame messages and the shown
percentage) and `filepicker` (`filepicker/hegel_test.go`, package `filepicker`, internal for
the window indices; it builds its directory trees under the system temp directory), with the
shared harness in `internal/zootest`.
Run with `go test -run TestHegel ./textinput ./textarea ./viewport ./paginator ./table ./list
./help ./progress ./filepicker`.
No AI-contribution policy is published in the repository (checked 2026-09-15); the zoo only
records bugs.

## Approach

- **A rune-slice model of the editor.** Random inputs (letters, spaces, digits, wide CJK
  runes, accented letters) are set up with a prompt, an optional width (set before the
  content), a `CharLimit`, one of three validators (none, a maximum length, "required") and an
  echo mode, then driven for up to 40 steps through `Update` with every binding of the default
  key map (characters, left/right/home/end, backspace/delete, ctrl+w, alt+d, ctrl+k, ctrl+u,
  alt+b/alt+f), `tea.PasteMsg` with tabs and newlines, `SetValue`, `SetCursor` and `Reset`.
  After each step `Value`, `Position` and `Err` must equal the model's (word motions: past
  spaces, then past the word; masked modes jump to the ends; the sanitizer maps tabs and
  newline characters to single spaces; `CharLimit` cuts pastes and `SetValue`).
- **The view, parsed into cells.** `View()` is split into graphemes with their reverse-video
  flag (the virtual cursor). It must be prompt + the echoed window `value[offset:offsetRight]`
  (the library's own offsets) + a blank cursor if the cursor is past the window + padding to
  exactly `Width+1` cells; the reversed run must sit at `prompt + width(echo(value[offset:pos]))`
  and be as wide as the rune under the cursor. `Cursor()` (the real cursor) must report the
  same column.
- **Placeholders and suggestions.** The placeholder view is the placeholder cut to `Width+1`
  runes and padded, cursor on its first cell when focused. Suggestions are modelled as the
  case-insensitive prefix matches of the value with the index reset when the match list
  changes; up/down cycle, tab appends the current suggestion's remainder, and the view shows
  that remainder after the cursor.
- **textarea: a line-slice model with a selection.** Random text (several lines, wide runes,
  sometimes tabs, CRs or CRLFs) is edited for up to 30 steps through every default binding —
  characters, Enter, backspace/delete, ctrl+k/ctrl+u, ctrl+w/alt+d, left/right/home/end,
  alt+b/alt+f, ctrl+home/ctrl+end, ctrl+t, alt+u/l/c, shift+arrows, alt+shift+b/f, ctrl+g —
  plus pastes, `SetValue`, `InsertString`, `SetCursorColumn` and `Reset`, with a `CharLimit`
  and a `MaxHeight` some of the time; `Value`, `Line`, `Column`, `LineCount`, `HasSelection`
  and `SelectedText` must follow the model (CRLF is one line break, limits count runes, a
  paste is cut to the line limit, an empty selection anchors at the cursor). Vertical motion
  is checked against the library's own `wrap` grid: Up and Down move exactly one visual row.
  `View()` is parsed into cells and compared row by row with the grid (prompt, line number or
  blank gutter, the row's runes, padding, end-of-buffer rows), the cursor's row must be in the
  viewport and its cell the only reversed one at `gutter + CharOffset`; `Cursor()` and
  `PositionAt` must agree with that cell; `LineInfo` must describe the grid row.
- **viewport: a scroll model over rows of cells.** A viewport of random size (sometimes with a
  `NormalBorder` frame, a two-cell gutter, `SoftWrap`, `FillHeight`; the content area is always
  at least one cell) gets up to eight random lines (wide runes, sometimes tabs or CRLF) and is
  driven for up to twelve steps with every default binding (j/k/arrows, f/b/space/pgdown/pgup,
  d/u, h/l/arrows), the mouse wheel (three directions), `SetYOffset`/`SetXOffset`, `GotoTop`/
  `GotoBottom`, `ScrollDown`/`ScrollUp`, `SetContent`, `SetHeight` and `EnsureVisible`. The
  model keeps the lines as rows of cells (soft-wrapped greedily at the content width) and the
  two offsets (down moves stop at the bottom, up moves snap a past-bottom offset back, a page
  is the content height, a horizontal step is six columns). After each step `YOffset`,
  `XOffset`, `TotalLineCount`, `AtTop`/`AtBottom`, `ScrollPercent` and the view must follow:
  the view is parsed into cells row by row and must be exactly `height` rows of `width` cells,
  each the gutter plus the row's cells in `[x, x+width)` (a wide cell across the right edge is
  dropped, one across the left edge is kept whole, as `ansi.Cut` does), blank or `~ ` rows
  below the content.
- **viewport: highlights.** Random byte ranges of the content (sorted, disjoint, on rune
  boundaries — a range may start at or run over a newline) are set with `SetHighlights` under
  a `Reverse` style; `HighlightNext`/`HighlightPrevious` and scrolling are driven and the
  selected index and the offsets must follow (the nearest match is the first one starting at
  or below the top row; `EnsureVisible` scrolls only when the match is outside, horizontally
  to `colstart − 6` when its end is past the width). The reversed cells of every visible row
  must be exactly the matched cells clipped to the window; a newline counts as one cell after
  its line's last.
- **paginator: pages over a slice.** `PerPage` 1–5 and 1–40 items; the default bindings and
  `NextPage`/`PrevPage` move the page by one within `[0, pages−1]`, `SetTotalPages` recomputes
  `ceil(items / PerPage)`, `GetSliceBounds`/`ItemsOnPage` are the page's slice, `View` is the
  dots or the Arabic format for the page.
- **table: the selection in view.** Random columns (1–4, widths 0–7, titles), rows of that
  many fields (letters, spaces, wide runes; sometimes a row with one field too many), a height
  of 2–9 and a width of 8–50, the styles set to `Reverse` for the selection and the default
  paddings. Every default binding, `MoveUp`/`MoveDown` by any count, `SetCursor`, `SetRows`,
  `SetColumns`, `SetHeight`, `SetWidth`, `GotoTop`/`GotoBottom`, `Blur`/`Focus` and
  `FromValues` are driven against a cursor clamped to the rows; `Cursor` and `SelectedRow`
  must agree with it, `View` must be the header (each title truncated with `…` and padded to
  its column, between one space each side) over `Height` consecutive rows rendered the same
  way and cut to the width, the cursor's row must be shown and be the only reversed line.
- **list: items, filter and selection.** Up to 25 items titled `wNN` plus one to five letters
  from `a`–`e` (so fuzzy terms of one to three such letters match some of them), a width of
  20–60 and a height of 12–30, the default delegate with or without descriptions. The model
  keeps the items, the filter state and term, the visible indices (all items, or
  `DefaultFilter`'s ranks — the library's own filter is the oracle for the order; the list's
  bookkeeping around it is what is tested), the selection index and a mirror of the paginator
  (`PerPage` from the height minus the chrome, the page count as the library last computed
  it). Every default binding, the filter input (typing, backspace, enter/down to accept, esc),
  `Select`, `SetItems`, `SetItem`, `InsertItem`, `RemoveItem`, `SetSize`, the section toggles,
  `SetFilterText`, `ResetFilter`, the page/end methods and `InfiniteScrolling` are driven;
  the commands `Update` returns are run at once and their messages fed back. After each step
  `Index`, `Cursor`, `Page`, `TotalPages`, `PerPage`, `SelectedItem`, `GlobalIndex`,
  `VisibleItems`, `FilterState`/`FilterValue` and the lines of `View` (the title or filter
  line, the status text, the page's items with the selected one marked by the border, the
  pagination dots or `p/n`) must agree.
- **help: a layout model.** Up to six bindings (keys and descriptions from a small set of words
  — empty, `?`, `ctrl+c`, `↑/k`, `move down`, a wide `全角` — 15 % of them disabled), up to
  four groups of up to three (some nil), the separators and the ellipsis changed some of the
  time, a width of 1–40 or none. `ShortHelpView` must be the enabled items `key desc` joined by
  the separator; `FullHelpView` one column per group with an enabled binding — the separator on
  the first line, keys and descriptions each padded to the widest, columns joined at the top;
  with a width, both must stop before the first item or column that does not fit and end in
  ` …` when it fits, so the output is never wider than the width. `View` follows `ShowAll`.
- **progress: a cell model with colours.** Up to five options in random order (`WithColors`
  with none, one, two or three colours, `WithDefaultBlend`, `WithColorFunc`, `WithScaled`,
  `WithFillCharacters` — sometimes wide runes — `WithoutPercentage`, `WithWidth`), then
  `SetWidth`, `PercentFormat` and `EmptyColor` some of the time. `ViewAs(p)` for p in −0.1…1.1
  is parsed into runes with their SGR foreground and background and must be round(tw·p) full
  runes, tw − fw empty runes and the percentage text, tw = Width − text width; the colours
  follow the documented option semantics — the solid colour, `Blend1D` over the bar or (scaled)
  the filled part with two steps per half block (foreground and background), the colour
  function at i/tw and, for the half block's background, i/tw + 1/2tw, the empty colour. The
  animation property draws a spring (frequency 1–60, damping 0.1–2.0) and one to three
  `SetPercent`/`IncrPercent`/`DecrPercent`, checks the clamped target and that stale or
  foreign frames are ignored, then feeds frame messages until `IsAnimating` is false: the shown
  percentage must be within 0.001 of the target with a settled velocity, `View` must be
  `ViewAs` of it throughout, and a frame after that must be a no-op.
- **filepicker: a directory tree and a window mirror.** Each case builds a random tree in a
  fresh temporary directory (files of a few extensions, some hidden; one level of
  subdirectories; sometimes symlinks to a file, a directory or nowhere), sets a height (or
  none), `ShowHidden`, `AutoHeight`, the permission/size columns, `FileAllowed`/`DirAllowed`
  and `AllowedTypes`, and drives the picker for up to 25 steps: every default binding (g, G,
  j/k/arrows/ctrl+n/ctrl+p, J/K/pgup/pgdown, h/backspace/left/esc, l/right, enter),
  `WindowSizeMsg`, `SetHeight`, toggling `ShowHidden`, changing the allowed flags and types;
  the commands are run and their messages fed back. The model keeps the listing as `readDir`
  defines it (directories first, names ascending, hidden names filtered), the selection, the
  window with the library's own arithmetic (mirrored line for line, since the shapes that break
  it are the bugs) and the view stack; after each step `CurrentDirectory`, `Path`,
  `HighlightedPath`, the internal indices and the lines of `View` (cursor, mode, size, name,
  symlink target; the padding; the empty-directory message) must match, the window must hold
  the selection and neither more rows than the height nor fewer than the entries allow, and
  after an enter `DidSelectFile`/`DidSelectDisabledFile` must report the entry it was pressed
  on per the allowed flags and types.

## Properties

| Test | What it checks |
|---|---|
| `TestHegelEditingFollowsTheModel` | every key, paste, SetValue/SetCursor/Reset vs the model; Value, Position, Err, View after each step |
| `TestHegelPlaceholderFillsTheField` | the placeholder view (ASCII, width > 0; the other shapes are pinned) |
| `TestHegelSuggestionsFollowThePrefix` | matched suggestions, index, `CurrentSuggestion`, tab completion, the completion in the view |
| `TestHegelRealCursorSitsUnderTheVirtualOne` | `Cursor()` vs the column where View draws the cursor |
| `TestHegelTextareaEditingFollowsTheModel` | every key, paste and setter vs the line-slice model: value, cursor, selection |
| `TestHegelVerticalMotionMovesOneVisualRow` | Up/Down move exactly one row of the wrap grid |
| `TestHegelViewShowsTheWrappedRows` | the view vs the wrap grid: gutter, rows, padding, EOB rows, the reversed cursor cell |
| `TestHegelRealCursorAndPositionAtAgree` | `Cursor()` and `PositionAt` vs the virtual cursor's cell |
| `TestHegelLineInfoDescribesTheWrappedRow` | `LineInfo` vs the wrap grid (row, start, width, offsets) |
| `TestHegelViewShowsTheScrolledRows` | every scroll binding, wheel, setter, `SetContent`/`SetHeight`/`EnsureVisible` vs the row model: offsets, counts, `AtTop`/`AtBottom`, `ScrollPercent`, the view row by row |
| `TestHegelHighlightsMarkTheMatches` | `SetHighlights`, next/previous, scrolling: the selected index, the offsets, the reversed cells of every visible row |
| `TestHegelPaginatorFollowsTheModel` | bindings, helpers and `SetTotalPages` vs the page model: `Page`, the first/last flags, the slice bounds, `View` |
| `TestHegelTableShowsTheSelectedRow` | every binding and setter vs the cursor model: `Cursor`, `SelectedRow`, the header and the rows of `View`, the selection shown and reversed |
| `TestHegelListFollowsTheModel` | bindings, filter input, setters and messages vs the item/filter/selection model: the indices, the paginator, `VisibleItems`, `SelectedItem`, the lines of `View` |
| `TestHegelHelpFitsTheWidth` | `ShortHelpView`, `FullHelpView` and `View` vs the layout model: enabled items, separators, aligned columns, the width and the ellipsis |
| `TestHegelProgressDrawsTheModel` | `ViewAs` rune by rune vs the options model: fill and empty runes, the solid, blend, scaled and colour-function colours, the percentage text, the width |
| `TestHegelProgressSettles` | the setters' clamping and commands, stale and foreign frames ignored, the spring driven to equilibrium |
| `TestHegelFilepickerFollowsTheModel` | every binding, resize and setter over a random directory tree vs the listing/window/selection mirror: the paths, the indices, the lines of `View`, the window invariants, the `DidSelect` reports |

Set `BUBBLES_COLLECT=1` (and `HEGEL_TEST_CASES=n`) to collect mismatches and statistics
instead of failing at the first one; shapes of pinned bugs are counted as `bubbles/N-shape`.

## Bugs (see `bugs.toml`)

| id | severity | title |
|---|---|---|
| bubbles/1 | high | textinput: delete-word-forward steps past the rune under the cursor: it panics on the last rune and eats the next word |
| bubbles/2 | medium | textinput: without a width the placeholder is cut to its first rune |
| bubbles/3 | medium | textinput: the placeholder is sliced by display width, writing NUL runes after wide characters and overflowing the width |
| bubbles/4 | low | textinput: a negative width with a placeholder panics in View |
| bubbles/5 | medium | textinput: SetValue and Reset keep the previous value's matched suggestions; tab then completes the wrong text or panics |
| bubbles/6 | low | textinput: up with no matched suggestion sets the index to -1 and CurrentSuggestion panics |
| bubbles/7 | medium | textinput: the scrolling window is only re-fitted when the cursor crosses an edge; SetWidth, typing inside the window and ctrl+u leave it wider than the width |
| bubbles/8 | medium | textinput: Cursor() places the real cursor at prompt + rune index, ignoring the scrolled window and wide runes |
| bubbles/9 | low | textinput: backspace on an empty input clears Err without asking the validator |
| bubbles/10 | low | textinput: ctrl+w on a word at the start of the input deletes the single space before it as well |
| bubbles/11 | medium | textinput: scrolling forward, the rune under the cursor is not shown; the cursor is a blank at the right edge |
| bubbles/12 | low | textinput: with EchoNone the padding is computed from the hidden value, so the field shrinks as text is typed |
| bubbles/13 | medium | textarea: Delete on the last rune of a line also joins the next line |
| bubbles/14 | medium | textarea: Up and Down mis-step across short wrapped rows (Down skips a row of ≤ 2 runes, Up sticks below it, Down on a lone trailing-space row goes up, Up onto a row ending in a wide rune falls through) |
| bubbles/15 | low | textarea: LineInfo at the start of a wrapped row reports the previous row's CharWidth |
| bubbles/16 | medium | textarea: a double-width rune after width−1 columns of a word makes a wrap row wider than the width; the view truncates it and the rune vanishes |
| bubbles/17 | low | textarea: CharLimit is compared against display columns but cuts pastes by rune count |
| bubbles/18 | low | textarea: the line-number gutter is sized at render time from MaxHeight's digits, the text width at SetWidth; with MaxHeight 0 line 10 shifts the text |
| bubbles/19 | medium | textarea: SetValue/InsertString leave the viewport at the top while the cursor is on the last line; Cursor() points below the box until the next message |
| bubbles/20 | medium | textarea: CRLF line breaks are doubled |
| bubbles/21 | low | textarea: MaxHeight refuses Enter at the limit but a paste adds lines past it |
| bubbles/22 | low | textarea: a MaxWidth below the prompt and gutter width drives the text width negative; the view shows no text |
| bubbles/23 | low | textarea: a white-space placeholder renders no cursor |
| bubbles/24 | low | textarea: ctrl+w on the first word of a line deletes the leading space too |
| bubbles/25 | low | textarea: Enter ignores CharLimit; Length then exceeds the limit |
| bubbles/26 | high | textarea: an empty keyboard selection keeps a stale anchor: the next shift+arrow selects from where the cursor was, and if the anchor's line is gone the next edit panics |
| bubbles/27 | medium | viewport: SetContent keeps a carriage return on every line of CRLF content |
| bubbles/28 | medium | viewport: tabs count 0 cells for the viewport and 4 for the renderer: rows overflow, are wrapped, and the view is taller than its height |
| bubbles/29 | medium | viewport: the horizontal scroll limit is longest − Width rather than longest − content width, so with a gutter or a frame the last columns can never be shown |
| bubbles/30 | medium | viewport: PageDown, PageUp and the half-page moves scroll by Height including the frame, skipping lines in a bordered viewport |
| bubbles/31 | low | viewport: ScrollPercent ignores the frame: it reaches 100 % before the bottom of a bordered viewport, and is always 100 % when the content is shorter than Height but taller than the content area |
| bubbles/32 | medium | viewport: a double-width rune on a cut boundary widens the row; lipgloss re-wraps it and the view grows a row — under soft wrap and under horizontal scrolling |
| bubbles/33 | medium | viewport: under soft wrap EnsureVisible and findNearestMatch take a real line index for a visual offset, so the highlighted match is scrolled off the screen |
| bubbles/34 | low | viewport: HighlightPrevious with no selected match lands on the second-to-last one |
| bubbles/35 | low | viewport: highlights of styled content are misplaced: graphemes are walked on the stripped text but newlines looked up in the raw text |
| bubbles/36 | low | viewport: the selected match is re-styled with SelectedHighlightStyle alone, so with the default (unset) style the current match is the one match not highlighted |
| bubbles/37 | low | viewport: a Style width smaller than the viewport's caps the render but not the cut, so rows are wrapped and the view grows |
| bubbles/38 | low | viewport: under soft wrap the gutter of FillHeight's blank rows gets a real-line Index against a visual TotalLines, so they are numbered |
| bubbles/39 | low | viewport: SetContent clamps the vertical offset to the new content but not the horizontal one, so narrower content stays scrolled off the left |
| bubbles/40 | medium | paginator: Page is never clamped: when SetTotalPages shrinks the count below it, OnLastPage is false, NextPage keeps counting up and GetSliceBounds returns a start past the end |
| bubbles/41 | low | paginator: SetTotalPages with fewer than one item keeps the previous page count, so an emptied list still shows its old pages |
| bubbles/42 | high | table: a row with more fields than there are columns panics in renderRow as soon as it is within a page of the cursor (a stray separator in FromValues is enough) |
| bubbles/43 | medium | table: SetCursor and SetHeight (and the other setters) do not scroll the selection into view; after SetCursor(50) in a hundred rows the view shows rows 45–49 |
| bubbles/44 | medium | table: MoveUp never scrolls down to a selection below the view, so one hidden by a setter stays hidden through every up move |
| bubbles/45 | medium | table: a move on an empty table sets the cursor to −1, and SetRows only clamps downwards, so with rows back there is no selected row and one row fewer is rendered |
| bubbles/46 | low | table: the header line is not cut to the table's width while the rows are, so a wide header overhangs the table |
| bubbles/47 | low | table: a height under two is not clamped: at 0 Height() is −1, at 1 the viewport is empty, and View has two lines either way |
| bubbles/48 | low | table: a tab in a cell value is truncated at width 0 and rendered at width 4, so a<TAB>b in a five-wide column shows a alone |
| bubbles/49 | medium | list: with an empty filter every visible item carries index 0, so GlobalIndex is 0 whatever is selected |
| bubbles/50 | high | list: RemoveItem under a filter removes filteredItems[index] instead of the match for that item, so a removed item stays visible and the later matches' global indices are stale |
| bubbles/51 | low | list: RemoveItem with a negative index panics, though the doc says an index out of bounds is a no-op |
| bubbles/52 | high | list: the FilterMatchesMsg handler does not update the pagination, so after SetItems, SetItem or InsertItem under a filter the page count is stale — the list is stuck on one page, or items at the end are unreachable |
| bubbles/53 | medium | list: SetItems and RemoveItem keep the cursor's position on the clamped page, past the end of a shorter list, so SelectedItem is nil and no item is marked until the next message |
| bubbles/54 | medium | list: New does not size the help or the filter input (only SetSize does), so a fresh list renders its help line at full width and every line is padded to it |
| bubbles/55 | medium | list: the chrome is not fitted to the width: the status bar is never truncated, the help and the pagination are fitted before their two-cell padding and the title bar to width−1 before its own, so the view is wider than its width |
| bubbles/56 | low | list: the key bindings fall out of step with the items and pages: RemoveItem and the section toggles do not refresh them, cancelling a filter re-enables / on an empty list, and accepting one refreshes them before the pagination, so the page keys can stay dead |
| bubbles/57 | medium | help: when the next item does not fit and the ellipsis does not fit either, the item is added anyway, so ShortHelpView and FullHelpView overflow their width |
| bubbles/58 | low | help: an ellipsis that would end exactly at the width is dropped: the room test is strict, so at width 11 the short help writes all three items instead of a b • c d … |
| bubbles/59 | medium | progress: IsAnimating compares the signed velocity with 0.01, so a bar animating downward stops dead the first time it passes near the target, while the same spring animating upward bounces to rest |
| bubbles/60 | low | progress: WithColors with two or more colours sets the blend but leaves an earlier colour function in place (with one colour or none it is cleared), so the options depend on their order |
| bubbles/61 | low | progress: the bar counts runes, not cells, so wide fill characters render twice the width |
| bubbles/62 | low | progress: ViewAs passes its argument to the colour function unclamped, so total is 1.7 or −0.3 while the bar and the text are clamped |
| bubbles/63 | low | progress: SetPercent clamps with math.Max/math.Min, which pass NaN through, so IncrPercent(NaN) leaves Percent() NaN and an animation that never reaches equilibrium |
| bubbles/64 | medium | filepicker: when PageDown or PageUp clamps at an end of the listing the window is set to Height+1 entries, so the view shows one row more than the height |
| bubbles/65 | medium | filepicker: a smaller height cuts the window from its top, so a selection near the bottom falls out of view and no cursor is drawn |
| bubbles/66 | medium | filepicker: without a height G sets minIdx to len(files), so the view is empty and stays so through Up moves |
| bubbles/67 | low | filepicker: a larger height does not fill the window: SetHeight keeps the old bottom and a WindowSizeMsg the old top, so rows stay blank while entries are hidden |
| bubbles/68 | medium | filepicker: the selection is never clamped to a re-read listing, so after ShowHidden is turned off inside a directory Back restores a selection past the end of the parent and Open panics |
| bubbles/69 | medium | filepicker: an unreadable directory is entered anyway: CurrentDirectory changes before the read and a read error is ignored, so the parent's entries are shown under the new path |
| bubbles/70 | low | filepicker: Back from the default directory . goes nowhere, since filepath.Dir(.) is . |
| bubbles/71 | low | filepicker: the view of a non-empty directory ends in a newline after its Height lines, one line taller than Height and than the empty directory's view |
| bubbles/72 | medium | filepicker: after enter selects a directory the picker has already entered it, so DidSelectFile looks at the new listing's first entry and a directory holding only files, or nothing, is never reported |
| bubbles/73 | low | filepicker: Back restores the parent's saved window verbatim, so after a resize inside a subdirectory the parent shows the old window: more rows than the height, or fewer |
| bubbles/74 | low | filepicker: a negative height (AutoHeight from a terminal under six rows) is accepted and added by the page keys, so PageUp moves down and PageDown up, off the listing |

Eight of the twelve were visible in the source on a first reading (`textinput.go` is under a
thousand lines); the properties confirmed them and found bubbles/7's typing and ctrl+u cases,
bubbles/9 and bubbles/10. The editing property gates bubbles/1, /7, /9, /10 and /11 by cause,
the placeholder property /2, /3 and /4, the suggestion property /5 and /6, the cursor property
/8; each is pinned.

For textarea (2 100 lines, read in full first) eleven of the fourteen were suspicions from the
reading, confirmed by one probe file; the properties found bubbles/14's third and fourth cases,
bubbles/25 and bubbles/26 — the last as a panic in the test's own model, whose cause (a stale
anchor the library keeps) turned out to crash the library too. The editing property gates
/13, /17, /20, /21, /24, /25 and /26 by cause, the vertical property /14 (rows of two runes or
fewer, or ending in a wide rune, around the move), the view and cursor properties /16 (a
row wider than the width), the LineInfo property /15; each is pinned.

For viewport (765 lines plus `highlight.go`, read in full first) eleven of the thirteen were
on paper — `SetContent` splitting before the CRLF check, `maxXOffset` against `Width()`,
`PageDown`/`ScrollPercent` against `Height()`, `EnsureVisible`/`findNearestMatch` in real lines
under soft wrap, `(hiIdx−1+n)%n` from −1, `parseMatches` indexing the raw content with a
stripped position, `StyleRanges` replacing the style, tabs at width 0 — and a probe of
`ansi.Cut` on wide runes gave bubbles/32; the properties found bubbles/38 (numbered fill rows)
and bubbles/39 (the stale horizontal offset). The view property gates /27, /28, /29, /30, /31,
/32, /38 and /39 by cause, the highlight property /32, /33 and /34; /35, /36 and /37 need a
style and are pinned only; each is pinned.

For paginator (200 lines) and table (453 lines), both read in full first, seven of the nine were
on paper — the unclamped page, the early return for no items, `renderRow` indexing the columns
by the row's fields, the offset untouched by the setters, `MoveUp`'s cases, the `−1` cursor of an
empty table, the header outside the viewport — and a probe of cell contents gave bubbles/48;
the property showed that bubbles/42 fires only once the long row is within a page of the cursor
and that bubbles/44 is every up move, not just the first. The table property gates /42 (a panic
on the op that brings the row into the window), /43 (a setter that leaves the selection out of
view), /44 (an up move while it is out), /45 (a negative cursor with rows) and /46 (a header
wider than the width) by cause; the paginator property /40 and /41; /47 and /48 are pinned only
(heights are drawn from 2 and values carry no tabs); each is pinned.

For list (1 321 lines plus the delegate, keys and styles, read in full first) six of the eight
were on paper — `itemsAsFilterItems` without indices, `RemoveItem`'s one index for two slices,
the `FilterMatchesMsg` handler returning before `updatePagination`, the cursor left by the
index restore, `New` without the `SetWidth` calls, the paddings outside the truncations — the
probe of a negative `RemoveItem` gave bubbles/51, and the property found bubbles/56 (`/`
opening the filter on an emptied list; the page keys dead after a toggle). The property
mirrors the bindings as `updateKeybindings` last set them and gates /49 (a zero
`GlobalIndex` under an empty term, counted and carried on), /50 (a divergence right after
`RemoveItem` under a filter, or a stale `GlobalIndex` after one), /51 (the panic), /52 (a
page count differing from the matches under an applied filter — the model mirrors the stale
count while a term is typed, where the navigation keys are disabled), /53 (`SelectedItem`
nil with the index past the end), /55 (a chrome line wider than the width, counted and
carried on) and /56 (a page key or `/` pressed while the mirror and the truth differ); /54 is
avoided by `SetSize` after `New` and pinned; each is pinned.

For help (253 lines) and progress (438 lines), both read in full first, help's two were in
`shouldAddItem` on paper and confirmed by a width sweep; of progress's five, four were on paper
— the signed velocity, `WithColors` without the reset, the raw total, the NaN through the clamp
— and the wide runes came from asking what the width contract covers. The properties found
nothing new in either bubble but made a known bug visible: every blend step next to a black
stop renders a bright spike in a zero channel — lipgloss/28, x/ansi's channel shift, counted
under that id (`lipgloss/28`) and not as a bubbles bug. The help property gates /58 (a tail
that would end exactly at the width) before /57 (an output wider than the width); the progress
draw property /60 (a colour function surviving `WithColors`), /61 (wide runes: only the width
check) and /62 (a total other than clamp(p)), the settle property /59 (|velocity| ≥ 0.01 at
the stop); /63 is pinned only (NaN is not drawn); each is pinned.

For filepicker (539 lines, read in full first) eight of the eleven were on paper — the page
keys' `maxIdx − Height`, the resize handlers without `selected`, `G`'s `len − 0`, `SetHeight`'s
index-against-count test, the `readDirMsg` handler without a clamp, the missing `errorMsg`
case, `Dir(".")`, the padding loop's newline — and confirmed by one probe file; the property
found bubbles/72 (the selection report after entering a directory), bubbles/73 (the restored
window under another height) and bubbles/74 (the negative height). The window's invariants —
the selection inside it, no more rows than the height, no fewer than the entries allow — are
checked on the library's indices with a sticky cause per invariant: a resize (/65, /67), `G`
without a height (/66), a page key (/64, or /74 once a page key was pressed at a negative
height), a `Back` whose listing changed (/68) or whose height changed (/73) or whose saved
window already carried a shape, and a page key from a window already oversized (it inherits
that window's cause: the library's page arithmetic strands the selection); /68 is also
counted before an Open with the selection out of range, /72 as a `DidSelect` report differing right after an enter that entered a directory;
/69, /70 and /71 are pinned only (readable trees, absolute paths, the trailing newline
modelled); each is pinned.

## Not bugs (modelled as documented)

- Tab keeps the typed prefix's case and appends the suggestion's remainder (`bb` + `BbAa` →
  `bbAa`); matching is case-insensitive.
- When the value becomes empty the matched list is cleared but the suggestion index is left
  where it was (it is reset the next time the matches change); `CurrentSuggestion()` is `""`.
- `SetValue` validates the text before `CharLimit` cuts it; an insertion at the limit returns
  before validating, so `Err` is unchanged; `Reset` does not touch `Err`.
- In `EchoPassword`/`EchoNone` the word motions go to the ends and the word deletions
  delete to the ends (documented: not to reveal word breaks).
- A paste's `\r\n` becomes two spaces (each character is replaced on its own).
- The field is `Width+1` cells wide: the cursor has a cell of its own after the last rune.
- textarea: a line exactly `width` columns wide gets a second visual row holding the wrap's
  extra trailing space, where the cursor sits at the line's end; the cursor at the end of a
  wrapped row that is not the last is shown at the start of the next (`LineInfo`'s
  wrap-around); a continuation row may begin with the space that did not fit on the row above.
- textarea: `Word()` looks at the rune *before* the cursor, so at a word's start it is `""`;
  ctrl+t at the end of a line transposes the last two runes (Emacs); alt+u/l/c and ctrl+t do
  not clear a selection; word motions cross line ends (alt+b lands on the previous line's last
  rune first); `InsertString` does not replace a selection (it is only exercised without one).
- textarea: tabs become four spaces, other control characters and U+FFFD are dropped.
- viewport: a wide rune across the right edge of the window is dropped and one across the left
  edge is kept whole (`ansi.Cut`; the widening it causes is bubbles/32); `HalfPageDown` in a
  one-row viewport is a no-op; a lone `\r` is kept; `SetContent("\n")` is two lines;
  `SetHeight` may leave the offset past the bottom (documented `PastBottom`) and the next
  upward move snaps it back; a match that begins at a newline belongs to the line before it,
  the newline being one cell after its last, and `EnsureVisible` scrolls for that cell.
- table: keys are ignored while blurred; a row with fewer fields than columns just has fewer
  cells; columns of width 0 are skipped in the header and the rows; a cell's newline is dropped
  (`Inline`) after truncation; `SetRows` keeps the offset, so a shrunk table may show the
  selection lower than before.
- paginator: `SetTotalPages` returns the count it set; a fresh paginator has one page.
- list: `/` moves the selection to the first item and esc/cancel does not restore it; the
  filter is re-run from the setters' commands, not synchronously (the tests run the commands);
  `SetFilterText` of a term matching nothing leaves an applied filter over nothing (`“zz” 0
  items`, `No items.`); a list too short for its chrome plus one item still shows one item and
  is taller than its height; the up/down keys accept a filter being typed; the dots of the
  active and inactive pages are the same character in different colours.
- help: an enabled binding with empty help renders as a lone space between separators; the
  separator of the full view is on the first line only (a one-line block joined at the top);
  keys or descriptions with newlines are not aligned between the columns.
- progress: a width below the percentage text (five cells) renders the text alone, wider than
  `Width()` (the text cannot be cut); the text rounds half to even (`%3.0f`) while the fill
  rounds half away from zero (`math.Round`); `Blend1D` with fewer steps than stops is a prefix
  of the stops (lipgloss's own rule); `Percent()` is the target, not the shown percentage; a
  stale frame (an older tag) is dropped, so two quick setters animate from the second.
- filepicker: enter on a directory with `DirAllowed` both selects and enters it; a symlink to
  a directory is entered through its own path (`Back` returns to the link's directory) and is
  styled as a symlink, not a directory; a broken symlink does nothing on Open or enter and
  shows an empty target; `AllowedTypes` are suffixes (`e` matches `file`); `Path` keeps the
  last selection across navigation; the empty-directory message is padded to the height.

## Not covered (yet)

`tree`, `key`,
`timer`/`stopwatch`/`spinner`, `cursor` blinking; help's styles; progress's `PercentageStyle`
and springs outside frequency 1–60 / damping 0.1–2; filepicker's styles, a custom `Cursor`,
directories that change underneath it beyond `ShowHidden`, `IsHidden` on Windows; textinput's clipboard paste (`Paste` reads the
system clipboard) and its styles; textarea's PageUp/PageDown, `DynamicHeight`/`MinHeight`,
`MaxContentHeight`, `SetPromptFunc`, the mouse selection API (`BeginSelection`/`ExtendSelection`/
`EndSelection`), `CopySelection` (clipboard), the placeholder beyond bubbles/23, `ScrollPercent`,
styles and the `Base` frame; viewport's shift+wheel, `StyleLineFunc`, `HorizontalScrollPercent`,
`YPosition`, gutters of other widths, `Style` width and height beyond bubbles/37,
`SetHighlights` on styled content beyond bubbles/35; table's `HelpView`, custom key maps and
styles with their own paddings; paginator's `PerPage` of 0 (a division by zero); list's
spinner, status messages (timers), full help (`?`), `SetShowFilter`/`SetFilteringEnabled`,
delegates other than the default, `UnsortedFilter`, the delegate's spacing 0 (its pagination
margin) and `Select` past the end (bubbles/40's shape).
