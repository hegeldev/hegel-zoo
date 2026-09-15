# go/bubbles — charmbracelet/bubbles v2 (`textinput`, `textarea`)

Hegel property tests for `charm.land/bubbles/v2`, the component library of Bubble Tea, pinned
at `0a69b19b` (main, 2026-09-01). Two slices so far: `textinput`, the single-line editor
(`textinput/hegel_test.go`, package `textinput`, internal so the window offsets are readable),
and `textarea`, the multi-line editor (`textarea/hegel_test.go`, package `textarea`, internal
for the wrap grid and the viewport offset), with the shared harness in `internal/zootest`.
Run with `go test -run TestHegel ./textinput ./textarea`.
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

## Not covered (yet)

`viewport`, `table`, `list`, `paginator`, `progress`, `tree`, `filepicker`, `help`, `key`,
`timer`/`stopwatch`/`spinner`, `cursor` blinking; textinput's clipboard paste (`Paste` reads the
system clipboard) and its styles; textarea's PageUp/PageDown, `DynamicHeight`/`MinHeight`,
`MaxContentHeight`, `SetPromptFunc`, the mouse selection API (`BeginSelection`/`ExtendSelection`/
`EndSelection`), `CopySelection` (clipboard), the placeholder beyond bubbles/23, `ScrollPercent`,
styles and the `Base` frame.
