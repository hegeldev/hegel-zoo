# go/bubbles — charmbracelet/bubbles v2 (`textinput`)

Hegel property tests for `charm.land/bubbles/v2`, the component library of Bubble Tea, pinned
at `0a69b19b` (main, 2026-09-01). This first slice covers `textinput`, the single-line editor:
`textinput/hegel_test.go` (package `textinput`, internal so the window offsets are readable)
with the shared harness in `internal/zootest`. Run with `go test -run TestHegel ./textinput`.
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

## Properties

| Test | What it checks |
|---|---|
| `TestHegelEditingFollowsTheModel` | every key, paste, SetValue/SetCursor/Reset vs the model; Value, Position, Err, View after each step |
| `TestHegelPlaceholderFillsTheField` | the placeholder view (ASCII, width > 0; the other shapes are pinned) |
| `TestHegelSuggestionsFollowThePrefix` | matched suggestions, index, `CurrentSuggestion`, tab completion, the completion in the view |
| `TestHegelRealCursorSitsUnderTheVirtualOne` | `Cursor()` vs the column where View draws the cursor |

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

Eight of the twelve were visible in the source on a first reading (`textinput.go` is under a
thousand lines); the properties confirmed them and found bubbles/7's typing and ctrl+u cases,
bubbles/9 and bubbles/10. The editing property gates bubbles/1, /7, /9, /10 and /11 by cause,
the placeholder property /2, /3 and /4, the suggestion property /5 and /6, the cursor property
/8; each is pinned.

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

## Not covered (yet)

`textarea` (the multi-line editor, 2 100 lines), `viewport`, `table`, `list`, `paginator`,
`progress`, `tree`, `filepicker`, `help`, `key`, `timer`/`stopwatch`/`spinner`, `cursor`
blinking; textinput's clipboard paste (`Paste` reads the system clipboard) and its styles.
