# go/cellbuf — charmbracelet/x/cellbuf

The cell buffer and screen-diffing layer under Bubble Tea v2 and lipgloss v2: a 2-D `Buffer`
of cells (wide characters occupy a head cell plus zero-width placeholders), `Render`/`SetContent`
between buffers and ANSI text, cell `Style`s with SGR sequences and diffs, `Wrap`, `TabStops`,
and `Screen`, an ncurses-style optimiser that turns buffer changes into the shortest terminal
output (hashing lines for scroll detection, ECH/REP/ICH/DCH, cursor-movement optimisations).
Monorepo `charmbracelet/x`, `subdir = "cellbuf"`, pinned at c615ff2 (2026-09-13, after
cellbuf/v0.0.15). MIT; no CONTRIBUTING/AGENTS policy (checked in turn 128 for `go/x-ansi`).
The test lives in package `cellbuf` to read `Screen`'s two internal buffers.

## Oracles

- **A grid model** with the terminal's wide-cell semantics: a cell written over any column of
  a wide cell blanks that cell (style kept); a wide cell that does not fit becomes blanks;
  shifts move cells as units within the rectangle. Compared cell by cell (content, width,
  style, link), plus `String()` and `Bounds()`.
- **The monorepo's own terminal emulator** (`charmbracelet/x/vt`, same commit, pulled in as
  a test dependency): `Screen`'s output is replayed into `vt.NewEmulator(w, h)` after every
  `Render`+`Flush`, and the emulator's cells (content, width, attributes, underline, colours,
  hyperlink) must equal `Screen`'s new buffer; the current buffer must equal the new one too.
- **Round trips**: `Render(buffer)` → `SetContent(new buffer)` restores every cell;
  `ReadStyle(s.Sequence())` restores `s`; `o.Sequence()` then `s.DiffSequence(o)` yields `s`.
- **The SGR table** for `ReadStyle` (attributes, 22–29, 30–37/40–47/90–97/100–107,
  `38;5;n`, `38;2;r;g;b`, colon forms with a colour-space id, `4:k` underline styles, 39/49/59).
- **`Wrap`**: every output line fits the limit (measured without trailing whitespace); the
  non-whitespace graphemes, their order, and the style and link in force at each are preserved;
  explicit newlines survive.
- **A set model for `TabStops`** (interval 8): `IsStop`, `Find`/`Next`/`Prev` saturating at the
  edges, `Set`/`Reset`/`Clear`/`Resize`.
- **go-runewidth / uniseg** for `NewCell`, `NewCellString`, `NewGraphemeCell`.

## Properties

| Test | What it checks | Gates |
| --- | --- | --- |
| `BufferFollowsTheGridModel` | random `SetCell`/`FillRect`/`ClearRect`/`Insert*Rect`/`Delete*Rect`/`Resize` vs the model, structural invariant | wide cells in shifted regions (/1), a wide cell over another wide head (/2), shrinking through a wide cell (/3); rectangles kept inside the buffer (/10) |
| `RenderRoundTripsThroughSetContent` | Render → SetContent restores cells; `RenderLine` width and plain text | buffers with orphan placeholders (/2), styles DiffSequence cannot express (/6) |
| `StyleSequencesRoundTrip` | `Sequence`/`ReadStyle`, `DiffSequence` on top of the old style, empty styles | the SGR 22/25 sibling shapes (/6), equal styles (/16) |
| `ReadStyleFollowsTheSGRTable` | random parameter lists vs the table; `CSI m` resets | — |
| `WrapKeepsContentAndStyles` | widths, content, styles, links, newlines, `Height` | trailing whitespace past the limit counted (/8); wide graphemes at limit 1 |
| `TabStopsFollowTheModel` | interval-8 stops vs the set model through random ops | columns beyond the width (/5); other intervals pinned (/4) |
| `CellConstructorsFollowRunewidth` | widths/contents, `Clone`/`Blank`/`Equal`/`Empty`/`Clear`, `Line.String`/`At` | ASCII-based combining clusters (/9) |
| `ScreenRendersWhatTheEmulatorShows` | 1–6 frames of `SetContent`/`PrintAt`/`SetCell`/`FillRect`/`ClearRect`/line shifts on an alt-screen `Screen` (xterm, 256color, linux, screen, alacritty, vt100; cursor/hard-tab/backspace options; both width methods) replayed into `vt` | orphans in the screen (/2), the `clearBottom` shape (/12), the `transformLine` hang shape (/13), scrolls of two or more lines without SU (/17), blanks inheriting the pen (/11), a wide cell blanked on the terminal (/14), REP after Latin-1 (/15), frames emitting DCH/ICH (the emulator's own wide-cell bug, see below), frames switching insert mode on (the emulator has no IRM; /18 is pinned through a small IRM-aware line replay) |
| `Examples` | fixed examples including one emulator replay | — |

Each `TestHegelPin…` reproduces one bug and is an expected failure. `CELLBUF_COLLECT=1` turns
failures into a tally per property. The `Render` hang (/13) is reproduced in a child process
with `-test.timeout 5s`, so the pin itself cannot take the suite down. The `Screen` gates for
/13 and /17 come from a replay of `Render`'s line loop (scroll optimisation, `clearBottom`,
`transformLine` in order) on a deep copy of the screen: the code's own arithmetic, run before
the real `Render`, since the hang cannot be recovered from once it starts.

## Bugs

| id | severity | title |
| --- | --- | --- |
| cellbuf/1 | high | `InsertLine`/`DeleteLine`/`DeleteCell` destroy every wide cell they move |
| cellbuf/2 | medium | a wide cell over another wide head leaves an orphan placeholder (columns shift on screen) |
| cellbuf/3 | low | `Buffer.Resize` cuts through wide cells |
| cellbuf/4 | medium | `TabStops` only work for interval 8 (aliasing, panic for 16) |
| cellbuf/5 | low | `TabStops.Set`/`Reset` panic beyond the width; `IsStop` answers from stale bits |
| cellbuf/6 | medium | `DiffSequence` drops bold/faint or a blink when turning off the sibling (SGR 22/25) |
| cellbuf/7 | low | `NewCell` appends every rune, contrary to its documentation |
| cellbuf/8 | low | `Wrap` lets a trailing space push a line past the limit |
| cellbuf/9 | medium | a separately decoded combining mark is attached to the *next* cell (trigger: x-ansi/5) |
| cellbuf/10 | medium | shift operations panic for rectangles beyond the buffer |
| cellbuf/11 | medium | blanks after a styled cell are painted with its style and hyperlink |
| cellbuf/12 | high | `clearBottom` erases the row above the blank region; it is never redrawn |
| cellbuf/13 | high | `Render` loops forever for a wide cell in column 0 over a one-cell row |
| cellbuf/14 | high | the overwrite cursor move prints a space over a wide cell's placeholder |
| cellbuf/15 | low | REP used for Latin-1 characters despite the ASCII-only intent |
| cellbuf/16 | low | `DiffSequence` of two equal non-empty styles is the reset sequence |
| cellbuf/17 | high | scrolling up by two or more lines on a terminal without SU writes its newlines at the top row; the terminal never scrolls |
| cellbuf/18 | medium | on terminals without ICH, inserting before a wide cell writes it twice in insert mode and loses the cell after it |

## Not bugs (or not cellbuf's)

- The `vt` emulator blanks a wide cell that `DCH`/`ICH` shift (`" 中"` + `CSI P` → blank): the
  same `Line.Set` logic as cellbuf/1, but in `ultraviolet`'s buffer. Frames that emit DCH/ICH
  are excluded from the differential rather than blamed on cellbuf.
- The `vt` emulator ignores insert mode (`CSI 4 h`), which cellbuf uses instead of ICH on
  terminals without that capability; those frames are excluded too, and cellbuf/18 is pinned
  against a ten-line replay that implements IRM.
- x/ansi's decoder splits grapheme clusters starting with an ASCII byte (x-ansi/5); cellbuf/9
  is what cellbuf then does with the stray mark. Generators use precomposed `é`/`ñ` and a
  Thai cluster instead.
- `DiffSequence` of two *empty* styles is the reset sequence (`Sequence()` of an empty style),
  by design; for equal non-empty styles it is cellbuf/16.
- `Ascii.Convert`-style profile downsampling (`ConvertStyle`) is not exercised: the screen
  runs with profile 0.
- 2026-09-20: base bumped c615ff2f7805 → 53e2afe73ae5 (2026-09-20, "chore(powernap): update lsp configs from nvim-lspconfig"; v0.0.15+); 18 bug(s) still reproduce. 9 tests pass.
