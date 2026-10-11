# go/cellbuf — charmbracelet/x/cellbuf

The cell buffer and screen-diffing layer under Bubble Tea v2 and lipgloss v2: a 2-D `Buffer`
of cells (wide characters occupy a head cell plus zero-width placeholders), `Render`/`SetContent`
between buffers and ANSI text, cell `Style`s with SGR sequences and diffs, `Wrap`, `TabStops`,
and `Screen`, an ncurses-style optimiser that turns buffer changes into the shortest terminal
output (hashing lines for scroll detection, ECH/REP/ICH/DCH, cursor-movement optimisations).
Monorepo `charmbracelet/x`, `subdir = "cellbuf"`, pinned at c615ff2 (2026-09-13, after
cellbuf/v0.0.15). MIT; no CONTRIBUTING/AGENTS policy (checked in turn 128 for `go/x-ansi`).
The test lives in package `cellbuf` to read `Screen`'s two internal buffers.

## Build

Ten test files in the package, beside the upstream tests: `hegel_idioms_test.go` (the
generator idioms of the series' harness — the fair-bit dice, `hzUnless`, `hzOnly`, `hzShaped`,
the halving helpers), `hegel_test.go` (the harness: the collector, the switches `known`, the
judge, `checks`, the classifier), `hegel_buffer_test.go` (the grid model taking the switch
set, the Buffer and Render cases, models and properties), `hegel_style_test.go` (the SGR table
model, the sequence model, the replica of `DiffSequence`, the two style properties),
`hegel_wrap_test.go` (`Wrap` transcribed, the Wrap property), `hegel_tabs_test.go` (the tab-stop
word-array model, the TabStops property), `hegel_cells_test.go` (the cell constructors),
`hegel_shapes_test.go` (eleven narrow properties), `hegel_screen_test.go` (the Screen family: the
frame records, the predictors replayed on a copy of the screen, the emulator comparison, the
property), `hegel_screen_shapes_test.go` (eight narrow properties of the Screen family, the
child process for the hang) and `hegel_pins_test.go` (the nineteen pins and the fixed
examples). `go test -count=1 -timeout 20m -run TestHegel -v .`.

## Oracles

- **A grid model** with the terminal's wide-cell semantics: a cell written over any column of
  a wide cell blanks that cell (style kept); a wide cell that does not fit becomes blanks;
  shifts move cells as units within the rectangle, clipped to the buffer; a shrink blanks a
  cut wide cell. Compared cell by cell (content, width, style, link), plus `String()` and
  `Bounds()` and the structural invariant (placeholders belong to a head, heads fit). The model
  takes the switch set: with a switch on it reproduces the library's rule for that bug
  (`Line.set` cell by cell for the shifts, the placeholders written over a neighbouring head,
  the cut head kept by `Resize`, the unclipped reads that panic) as a replica of `buffer.go`.
- **The monorepo's own terminal emulator** (`charmbracelet/x/vt`, same commit, pulled in as
  a test dependency): `Screen`'s output is replayed into `vt.NewEmulator(w, h)` after every
  `Render`+`Flush`, and the emulator's cells (content, width, attributes, underline, colours,
  hyperlink) must equal `Screen`'s new buffer; the current buffer must equal the new one too.
  A differential cannot state a bug's picture, so the Screen family's classifier is a set of
  predictors: replicas of `Render`'s decisions (`scrollOptimize`, `clearBottom`,
  `transformLine`'s branches, `emitRange`, the overwrite cursor move) run on a deep copy of the
  screen before the real `Render` of each frame, with a content-level model of the emulator
  that tells which predicted shapes show (an orphan or a scroll the next rows redraw does not).
- **Round trips**: `Render(buffer)` → `SetContent(new buffer)` restores every cell (the model
  of `RenderLine`'s writes read back by `printString`'s rules); `ReadStyle(s.Sequence())`
  restores `s`; `o.Sequence()` then `s.DiffSequence(o)` yields `s` (the diff's effect modelled
  through the SGR table).
- **The SGR table** for `ReadStyle` (attributes, 22–29, 30–37/40–47/90–97/100–107,
  `38;5;n`, `38;2;r;g;b`, colon forms with a colour-space id, `4:k` underline styles, 39/49/59).
- **`Wrap`**: every output line fits the limit; the non-whitespace graphemes, their order, and
  the style and link in force at each are preserved; explicit newlines survive. With the
  switch of cellbuf/8 on, `wrap.go`'s line breaking is transcribed and names the lines that
  overflow by committed spaces.
- **A set model for `TabStops`** at any interval: `IsStop`, `Find`/`Next`/`Prev` saturating at
  the edges, `Set`/`Reset`/`Clear`/`Resize`; beside it the word array of `tabstop.go`, which
  under the switches reproduces the `col >> 3` indexing, the unchecked `Set`/`Reset` and the
  stale bits a `Resize` leaves.
- **go-runewidth / uniseg** for `NewCell`, `NewCellString`, `NewGraphemeCell`, with
  `NewCellString`'s documented rule (the first rune and the zero-width runes after it) for
  `NewCell` too.

## Properties

Cases are records drawn from package-level generators (a buffer size and a list of steps, a
list of SetCells, a style pair, an SGR parameter list, a list of wrap pieces with a limit, a
tab width with its interval and operations, a grapheme), every weight carrying the rate it
realises over three thousand cases. Each family has a model `xExpected(case, known)` that
states every value the property checks with every switch off and, with a switch on, the
library's rule for that bug; the classifier runs the model per switch before the library is
called and names the shape (sufficiency first, then necessity, holes counted: none), and a
case that fails names its bug in the message. Under `HEGEL_NO_KNOWN=1` the shapes are not
drawn (an interval other than 8, a column beyond the width, a rectangle past the buffer, an
ASCII-based cluster, a width-adding pair, an equal pair are alternatives of weight zero), are
filtered out by the classifier (an orphan or a lossy diff among the Render SetCells, a lossy
or equal style pair, a trailing-space wrap: 6–14 % of the cases), or their steps and checks
are dropped from the case (the Buffer property drops the shaped steps in the state the
documented model reaches, the TabStops property the probes at columns beyond the width, the
Screen property the frames from the first predicted one on; all counted) — and every property
passes there.

| Test | What it checks | Shapes drawn |
| --- | --- | --- |
| `BufferFollowsTheGridModel` | 1–25 random `SetCell`/`FillRect`/`ClearRect`/`Insert*Rect`/`Delete*Rect`/`Resize` steps vs the model after every step, the structural invariant | wide cells in shifted regions (/1), a wide cell over another wide head (/2), shrinking through a wide cell (/3), rectangles past the buffer (/10, a tenth of them) |
| `RenderRoundTripsThroughSetContent` | Render → SetContent restores cells; `RenderLine` width and plain text | orphan placeholders (/2), styles `DiffSequence` loses (/6), clusters with an ASCII base (/9) |
| `StyleSequencesRoundTrip` | `Sequence`/`ReadStyle`, `DiffSequence` on top of the old style, empty styles | the SGR 22/25 sibling shapes (/6), equal styles (/16, a tenth of the pairs) |
| `ReadStyleFollowsTheSGRTable` | random parameter lists vs the table; `CSI m` resets | — |
| `WrapKeepsContentAndStyles` | widths, content, styles, links, newlines, `Height` | spaces committed past the limit before a breakpoint or a sequence (/8); a wide grapheme at limit 1 is noted, not a failure |
| `TabStopsFollowTheModel` | stops vs the set model through random ops | intervals other than 8 (/4, a fifth), columns beyond the width (/5, a tenth) |
| `CellConstructorsFollowRunewidth` | widths/contents, `Clone`/`Blank`/`Equal`/`Empty`/`Clear`, `Line.String`/`At` | graphemes whose later runes add width (/7, a tenth) |
| `ScreenRendersWhatTheEmulatorShows` | 1–6 frames of `SetContent`/`PrintAt`/`SetCell`/`FillRect`/`ClearRect`/line shifts on an alt-screen `Screen` (xterm, 256color, linux, screen, alacritty, vt100; cursor/hard-tab/backspace options; both width methods) replayed into `vt` | orphans in the screen (/2), a blank ending a written range under a visible pen (/11), the `clearBottom` row (/12), the `transformLine` hang (/13, judged in a child process), the overwrite move over a placeholder (/14), REP after Latin-1 (/15), a scroll of two or more lines without SU (/17), a shortened line ending with a wide cell (/19); frames that emit DCH/ICH or switch IRM on end the case as exclusions (the emulator's own limits), which keeps /18 for its narrow property |
| `Examples` | fixed examples including one emulator replay | — |

The wide properties fail by the shape they draw most often, measured over forty rounds at a
hundred cases: Buffer by cellbuf/1 (intermittent; 36 of 40 rounds failed, 16 by cellbuf/1, 15
by cellbuf/3, 4 by cellbuf/10, 1 by cellbuf/2), Render by cellbuf/9 (40 of 40), Style by
cellbuf/16 (40), Wrap by cellbuf/8 (intermittent; 39), TabStops by cellbuf/4 (40, one of them
by cellbuf/5), Cells by cellbuf/7 (intermittent; 39); the SGR table property passes. Screen
fails by cellbuf/12 (intermittent; over eighty rounds, the first forty having tied cellbuf/11
and /12 at 16 each: 78 failed, 32 by cellbuf/12, 28 by /11, 6 by /2, 5 by /14, 3 by /15, 2 by
/13, 2 by /19).

Nineteen narrow properties draw one bug's shape each with random surroundings and fail every
run; under `HEGEL_NO_KNOWN=1` each draws the region past the shape and passes:
`ShiftedWideCellsSurvive` (/1), `WideCellsOverWideHeadsLeaveNoOrphan` (/2),
`ShrinkingBlanksCutWideCells` (/3), `TabIntervalsOtherThanEightWork` (/4),
`TabColumnsBeyondTheWidthAreNotStops` (/5), `DiffSequencesKeepSiblingAttributes` (/6),
`NewCellTakesOnlyTheFirstCombiningRune` (/7), `WrappedLinesFitWithTrailingSpaces` (/8),
`CombiningMarksStayOnTheirCell` (/9), `ShiftRectsBeyondTheBufferClip` (/10),
`DiffSequencesOfEqualStylesAreEmpty` (/16); and for the Screen family
`BlanksAfterStyledCellsStayPlain` (/11), `ClearedBottomRowsKeepTheRowAbove` (/12),
`WideCellsInColumnZeroRender` (/13), `CursorMovesKeepWideCells` (/14),
`RepeatedLatin1CharactersAllShow` (/15), `ScrollsOfSeveralLinesReachTheTerminal` (/17),
`InsertsBeforeWideCellsKeepTheRow` (/18, judged on a one-row line model that honours IRM,
since the emulator ignores it) and `ShortenedLinesKeepTheirLastWideCell` (/19).

Each `TestHegelPin…` reproduces one bug and is an expected failure. `ZOO_COLLECT=1` turns
failures into a tally per property. The `Render` hang (/13) cannot be recovered from once it
starts: the pin reproduces it in a child process with `-test.timeout 5s`, and the Screen
property and its narrow property judge a frame the predictor marks as hanging by re-executing
the test binary on the case (as JSON in the environment) with a 200 ms deadline, a timeout
being the failure that names cellbuf/13.

## Modelled as recorded

`known` holds nineteen switches, one per bug, off by default. In this part eleven are read
by the models: /1 (`Line.set` cell by cell, left to right, for `InsertLineRect`,
`DeleteLineRect` and `DeleteCellRect`; `InsertCellRect` copies right to left and is spared),
/2 (`Line.set` splits the wide cell at the target column only), /3 (`Resize` truncates the
line slices), /10 (the four shift loops read the rectangle unclipped: which rectangles panic
follows each loop's reads, see the note), /4 (`col >> 3` and `1 << (col & (interval-1))`
whatever the interval), /5 (`Set`/`Reset` unchecked past the last word; `IsStop` from the
last word's stale bits), /6 (`DiffSequence`'s attribute loop: 22 and 25 without re-sending
the sibling), /16 (an empty `ansi.Style` renders as the reset), /7 (`NewCell` appends every
rune and sums the widths), /8 (`addSpace` before the fit check), /9 (`printString` starts the
next cell with a mark decoded on its own, and sets a mark pending at the end as a zero-width
cell of its own). The Screen family does not read its switches (the emulator is the oracle);
its predictors name /2 (`hasOrphan` on the new buffer), /11 (`emitRange`'s raw `line[0]` for
the last cell of a range), /12 (`clearBottom`'s `move(0, top-1)`), /13 and /19 (the insert
and delete branches of `transformLine`), /14 (the overwrite move passing a placeholder), /15
(REP after a Latin-1 run), /17 (the scroll optimisation without SU); /18 lives behind the IRM
exclusion and is found by its narrow property alone.

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
| cellbuf/19 | high | a shortened line ending with a wide cell is erased from that cell's placeholder, blanking it on the terminal |

## Not bugs (or not cellbuf's)

- The `vt` emulator blanks a wide cell that `DCH`/`ICH` shift (`" 中"` + `CSI P` → blank): the
  same `Line.Set` logic as cellbuf/1, but in `ultraviolet`'s buffer. Frames that emit DCH/ICH
  are excluded from the differential rather than blamed on cellbuf.
- The `vt` emulator ignores insert mode (`CSI 4 h`), which cellbuf uses instead of ICH on
  terminals without that capability; those frames are excluded too, and cellbuf/18 is pinned
  against a ten-line replay that implements IRM.
- x/ansi's decoder splits grapheme clusters starting with an ASCII byte (x-ansi/5); cellbuf/9
  is what cellbuf then does with the stray mark. The Screen generators still use precomposed
  `é`/`ñ` and a Thai cluster; the Render and cell generators draw the ASCII-based clusters as
  the shape of cellbuf/9.
- The Screen generators leave faint and rapid blink out of their styles by design: with them
  in, the lossy diff of cellbuf/6 would be the most frequent shape of the differential; it is
  drawn and named by the Render and Style properties and has its narrow property.
- The `vt` emulator keeps a stale zero-width cell where cellbuf holds an orphan placeholder,
  so an orphan (cellbuf/2) shows on the terminal only when the content around it differs;
  and a scroll without SU (cellbuf/17) heals when the rows below are redrawn with newlines.
  The predictors name only the instances that show.
- `DiffSequence` of two *empty* styles is the reset sequence (`Sequence()` of an empty style),
  by design; for equal non-empty styles it is cellbuf/16.
- `Ascii.Convert`-style profile downsampling (`ConvertStyle`) is not exercised: the screen
  runs with profile 0.
- 2026-09-20: base bumped c615ff2f7805 → 53e2afe73ae5 (2026-09-20, "chore(powernap): update
  lsp configs from nvim-lspconfig"; v0.0.15+); 18 bug(s) still reproduce. 9 tests pass.
- 2026-10-11: part 1 of the rewrite to the known-shape standard (the seven non-Screen
  properties, eleven narrow properties); the notes of cellbuf/8 (a zero-width sequence before
  whitespace commits the spaces too) and cellbuf/10 (which rectangles panic) corrected after
  standalone checks. The old model's shift paths blanked a moved wide cell through the stale
  head when they filled the vacated columns, a latent model bug fixed.
- 2026-10-11: part 2, the Screen property on the predictors with eight narrow properties;
  cellbuf/19 found by the delete-branch predictor and recorded; the notes of cellbuf/11 (the
  blank must end the written range), 15 (a run of five or more), 17 (the rows below must stay
  blank) and 18 (two spare columns) narrowed after standalone checks.
