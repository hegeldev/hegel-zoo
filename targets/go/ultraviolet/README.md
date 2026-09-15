# go/ultraviolet — charmbracelet/ultraviolet (input decoder, cell buffer, renderer, layout)

The terminal primitives under Bubble Tea v2, in three slices. **Input**: `EventDecoder` (bytes →
key, mouse, paste, focus and report events; the successor of charmbracelet/x/input's parser),
`eventScanner` (the read loop behind `TerminalReader` and `Terminal`: whole-read key-table
lookup, bracketed paste, waiting for incomplete sequences across reads), the key table
(`buildKeysTable`, built-in and terminfo keys) and the `Key` methods programs match on
(`Keystroke`, `String`, `MatchString`). **Output**: the cell buffer (`Line`, `Buffer`,
`RenderBuffer`, `ScreenBuffer`: wide cells and their placeholders, area fills, IL/DL/ICH/DCH
shifts, resize, clone, draw), `Style.String`/`StyleDiff` and `Line.Render`, and
`TerminalRenderer` (the frame differ that turns a `RenderBuffer` into escape sequences, with its
scroll, hard-tab, backspace, ECH/REP/ICH/DCH optimisations) against the charmbracelet/x/vt
terminal emulator. Pinned at 6c9e17d (2026-09-10, untagged main). MIT; no
CONTRIBUTING/AGENTS/AI policy (checked 2026-09-15). The tests live in package `uv`
(`hegel_test.go`, `hegel_buffer_test.go`) to reach `eventScanner`, `buildKeysTable`, the legacy
flag constants and the renderer's current buffer; the renderer differential is in package
`uv_test` (`hegel_render_test.go`) because x/vt imports ultraviolet, and reaches the harness
through exported `…T` bridges. **Layout**: the `layout` subpackage (a translation of
ratatui's Cassowary-based `Layout`: `Len`/`Percent`/`Ratio`/`Min`/`Max`/`Fill` constraints,
seven `Flex` modes, spacing, padding, the split cache) in `layout/hegel_test.go` (package
`layout_test`), checked against the documented invariants and against ratatui itself. Open
slices: win32 input mode, `Terminal`.

## Oracles

Input — encoders for every protocol the decoder decodes, each returning the bytes and the
events they mean (the x-input harness carried over and extended):

- **x/ansi's own encoders**: `EncodeMouseButton` + `MouseSgr` (X10 by hand: x-ansi/22),
  `CursorPositionReport`, `ReportMode`, `PrimaryDeviceAttributes`,
  `SecondaryDeviceAttributes`, `TertiaryDeviceAttributes`, `WindowOp` (including the 4/6/8/48
  size reports), `SetClipboard`, `LightDarkReport`, `KittyGraphics`.
- **Hand-written encoders from the specifications**: the Kitty keyboard protocol (alternate
  keys, event types, associated text, lock modifiers, functional keys), xterm's
  `CSI 1;mod[:event] F`, `CSI n;mod[:event] ~`, `SS3 mod F`, `CSI 27;mod;code ~`, URxvt's
  `CSI n ^ / @ / $`, OSC 10/11/12 `rgb:` replies, `DCS 1+r`, `DCS >|`, PM/SOS/APC strings,
  `CSI 200~`/`201~`, plain text (runes, clusters, C0 controls) and ESC-prefixed alt keys.
- **The scanner's read loop as the terminal drives it**: the same stream in one read, and cut
  into reads at arbitrary byte offsets (`scanEvents(buf, false)` per read, the remainder
  flushed as expired), must give the same events.
- **The package's own key table** and **the Kitty vs modifyOtherKeys encodings** of one key.
- **`MatchString` against `Keystroke()`/`String()`**: a key must match the string the
  package prints for it, or a binding written from a log line cannot fire.

Output:

- **The grid model** from go/cellbuf (`mgrid`): a width×height array of `{grapheme, width,
  style, link}` with the terminal's rules — writing over any column of a wide cell blanks the
  whole cell keeping its style, a wide cell that does not fit at the right edge becomes styled
  blanks, IL/DL/ICH/DCH move cells whole and a cell they cut in half is erased, resize keeps
  cells and pads with blanks. The `Buffer`/`RenderBuffer` must agree cell by cell (content,
  width, style, link), in `String()` and `Bounds()`, and every changed line of a
  `RenderBuffer` must be touched.
- **An SGR interpreter** written from ECMA-48 and the xterm/kitty extensions (`applySGR`:
  0–9, 22–29, 30–37/90–97, 40–47/100–107, 38/48/58 with `5;n` and `2;r;g;b` in colon or
  semicolon form, `4:n`, 39/49/59) and an OSC 8 reader: `Style.String()` must read back as the
  style, `StyleDiff(from, to)` applied after `from` must give `to`, and `Line.Render()`
  replayed onto a blank row must give the line's cells.
- **The x/vt terminal emulator**: a random sequence of frames (styled text printed into a
  `ScreenBuffer`, cells set, areas filled and cleared, lines inserted and deleted, erases,
  resizes) is rendered through `TerminalRenderer` (fullscreen or inline/relative-cursor, scroll
  optimisation, hard tabs and backspace on or off, 11 TERM values) into the emulator; after
  each frame the emulator's screen must equal the frame, the renderer's current buffer must
  equal the frame, and the renderer's cursor model must agree with the emulator's cursor.

Layout — **ratatui** (the Rust original the package is "roughly a 1:1 translation" of): a
40-line Rust program in `zoo/rtoracle` (ratatui 0.30, `default-features = false`) reads one
layout per line (direction, area, flex, spacing, constraints) and prints
`Layout::split_with_spacers`; `[run] setup` builds it with cargo and the differential skips
itself when it is not there. Padding is applied on the Go side (ratatui has none) and the
inner area handed over. Alongside it, the documented invariants: the segments tile the padded
area in order with the spacers between them; the inner spacers are exactly the spacing in
the fixed modes and the outer ones empty where the mode says so; `Max` is never exceeded;
`Min`, `Len`, `Percent`, `Ratio` and `Max` are honoured (proportional ones within a cell,
since positions are rounded) whenever everything asked for fits in the area; Legacy covers
the area exactly; the cache returns what a fresh solve returns.

## Properties

| Test | What it checks | Gates |
| --- | --- | --- |
| `SequencesDecodeToTheirEvents` | every encoded event decodes to itself, consuming exactly its bytes, leaving the buffer untouched, with a non-empty `String()` | alternate keys with a base key (/1) |
| `StreamsSplitIntoTheirEvents` | 1–6 events back to back parse (via `Decode` and via the scanner) into the concatenated event lists | lone ESC / `ESC ESC` only last; `CSI 1;mod R` alone skips the scanner (whole-read table lookup gives F3 only, by design); URxvt `CSI n $` not in streams (see below) |
| `StreamsSurviveArbitraryReads` | the same stream cut into 2–4 reads gives the same events | cuts inside a cluster (two keys: the decoder cannot know), inside `CSI n $ y` (URxvt prefix), inside an X10 report (/3), between ESC and `\` of ST (/16); `CSI 1;mod R` not in cut streams (a remainder that is exactly a table key is F3 only) |
| `KittyAndModifyOtherKeysAgree` | `CSI code;mod u` and `CSI 27;mod;code ~` give the same code, modifiers and (without shift) text | — |
| `KeyTableAgreesWithTheDecoder` | every table entry for random legacy flags, terminals and terminfo use decodes to the same key | terminfo-sourced entries (/12), `ESC`/`ESC ESC` with CtrlOpenBracket (/11) |
| `PastesRoundTrip` | bracketed paste of random text (ESC, `[`, digits, `~`, controls, clusters) between other events, in one read or cut into several | text with `ESC [` + arbitrary bytes (/18), text ending in ESC or containing `CSI A` when chunked (/17, /19), the stream cut rules for the event before the paste |
| `GraphemesAreOneKey` | a multi-rune cluster is one `KeyExtended` press | ASCII-led clusters (/9) |
| `KeystrokesMatchTheirKeys` | every decoded key event satisfies `MatchString(Keystroke())` and `MatchString(String())` | base key ≠ code (/4), `+` (/5), lock modifiers (/6), modifier keys (/7), keypad keys (/14), lock keys (/15) |
| `BufferFollowsTheGridModel` | 1–25 random `SetCell`/`FillArea`/`ClearArea`/`InsertLineArea`/`DeleteLineArea`/`InsertCellArea`/`DeleteCellArea`/`Resize`/`CloneArea`/`Clone`/`Draw`/`Line` operations on a `Buffer` or `RenderBuffer` (1–10 × 1–5, wide cells, styles, links, out-of-range coordinates) agree with the model after each; changed lines are touched; at the end every placeholder has a head and every head fits | wide cells in ICH/DCH rows (/20), a shrink through a wide cell (/21), a wide cell over a placeholder and a head (/22, also for wide fills), IL/DL areas whose edge cuts a wide cell (/23) |
| `StylesRoundTripThroughSGR` | `Style.String()` reads back as the style; `StyleDiff(o, s)` after `o` gives `s`; `s.Diff(&o)` is `StyleDiff(&o, &s)`; equal styles diff to `""`; the zero style prints `CSI m` | — |
| `LinesRenderWhatTheyHold` | `Buffer.Render()` is the lines' `Render()` joined by `\n`; each replayed onto a blank row gives the line's cells with styles and links; the stripped text is `String()`; the printed width is the line width; `NewCell` follows the width method | orphan placeholders (/22) |
| `RendererDrawsWhatTheEmulatorShows` | 1–6 frames on a 2–16 × 1–6 screen (see Oracles) leave the emulator's screen, the renderer's current buffer and its cursor equal to the frame | frames with an orphan placeholder (/22), a linked cell whose link the emulator lacks after the renderer reset the hyperlink (/24), a mismatch after a scroll sequence when some row was untouched (/25), IRM emitted (the emulator has no insert mode) |
| `Examples` | fixed examples from the protocols, and the x-input bugs fixed here (/2 event types, /3 num lock, /4 buffer mutation, alt+`[`) | — |

Each `TestHegelPin…` reproduces one bug and is an expected failure. `UV_COLLECT=1` turns
failures into a tally per property (`UV_STACK=1` adds stacks to panics). Pin /12 needs the
`tmux`, `screen` and `xterm` terminfo entries (ncurses-base); it fails either way. Bold, faint,
italic, blink and the foreground colour are not compared on blank cells: the renderer erases
runs of such blanks with EL and terminals keep only the background of erased cells.
| `LayoutSplitsTileTheArea` | random layouts (0–6 constraints, 7 flex modes, spacing −3..5, padding, areas up to 60) satisfy the invariants above | Legacy and single-segment SpaceBetween give the surplus to a segment regardless of its constraint (documented); negative spacing makes every segment at least the overlap |
| `LayoutCacheIsTransparent` | the same layout split twice, through `Split` and `SplitWithSpacers`, and with a nudged constraint against a fresh solve, agrees | over-constrained layouts (/26) |
| `LayoutAgreesWithRatatui` | `SplitWithSpacers` equals ratatui's `split_with_spacers` for the same layout | over-constrained layouts and Legacy surplus ties, where equally good solutions exist |

## Bugs

| id | severity | title |
| --- | --- | --- |
| ultraviolet/1 | high | Kitty alternate keys: the base-layout key overwrites the shifted key — shift+a on AZERTY types "q" (x-input/1) |
| ultraviolet/2 | high | `TerminalReader.Legacy`/`UseTerminfo` have no effect; `Terminal` never gives the decoder its legacy options either |
| ultraviolet/3 | medium | an X10 mouse report cut before its payload by a read boundary is lost (UnknownCsiEvent + key presses) |
| ultraviolet/4 | medium | `Keystroke()` prints the base-layout key, `MatchString` compares `Code`: non-US layouts never match their own keystroke |
| ultraviolet/5 | medium | `MatchString` splits on `+`: the `+` key, ctrl++, alt++ cannot be matched |
| ultraviolet/6 | medium | lock modifiers are part of the exact modifier comparison: caps/num lock breaks every binding under Kitty |
| ultraviolet/7 | low | modifier key events (`leftshift` with shift set) do not match their keystroke |
| ultraviolet/8 | low | an invalid UTF-8 byte is reported as the rune with that value (x-input/5) |
| ultraviolet/9 | medium | ASCII-led grapheme clusters are split into key presses (x-input/6) |
| ultraviolet/10 | low | a CSI with more than 32 parameters is cut short, its tail becomes key presses (x-input/8) |
| ultraviolet/11 | low | `CtrlOpenBracket(true)` never produces ctrl+[ (x-input/9; the table is dead for reads ≤ 2 bytes) |
| ultraviolet/12 | medium | terminfo keys the decoder also recognises are honoured only when the key arrives alone (x-input/10) |
| ultraviolet/13 | low | alt+O/P/X lack `ShiftedCode` (x-input/7 remainder; alt+`[` is fixed here) |
| ultraviolet/14 | medium | keypad keys print as "enter", "1", "period"… but `MatchString` knows only "kpenter", "kp1"… |
| ultraviolet/15 | low | the caps/num/scroll lock keys print as "capslock"… which `MatchString` reads as modifiers |
| ultraviolet/16 | medium | ST split across reads (ESC \| `\`) ends the string at the ESC: OSC replies dropped, `\` typed |
| ultraviolet/17 | low | `ESC ESC [` at a read boundary is alt+[ instead of waiting; after a pasted ESC the end marker is lost |
| ultraviolet/18 | low | inside a paste, recognised key sequences are kept verbatim, all other sequences dropped |
| ultraviolet/19 | low | the whole-read table lookup runs before the paste check: a read that is exactly a key sequence during a paste is a key press |
| ultraviolet/20 | medium | `InsertCell`/`DeleteCell` destroy the wide cells they move: head blanked, placeholder orphaned (cellbuf/1's shape) |
| ultraviolet/21 | low | `Buffer.Resize` (and `InsertCell`) leave a wide head in the last column without room for it (cellbuf/3's shape) |
| ultraviolet/22 | medium | a wide cell written over a placeholder and the next head leaves an orphan placeholder: the line loses a column (cellbuf/2's shape) |
| ultraviolet/23 | low | `InsertLineArea`/`DeleteLineArea` tear a wide cell straddling the area's edge |
| ultraviolet/24 | medium | the renderer resets the terminal's hyperlink on a row change but keeps it in its pen: the next linked cell is drawn without its link |
| ultraviolet/25 | high | the scroll optimisation moves a row the new frame did not touch and never paints it back: a blank on the terminal where the frame has the row, and the renderer's record agrees with the terminal |
| ultraviolet/26 | medium | layout: the solver picks among equally good splits at random (Go map iteration in `internal/casso`), so an over-constrained layout changes from call to call |

Fixed here relative to charmbracelet/x/input (held as examples): x-input/2 (event types on
`CSI n;mod:ev ~`), x-input/3 (num lock text), x-input/4 (URxvt `$` rewrote the caller's
buffer — now `slices.Clone`), x-input/7's alt+`[` (now `Code '['`). Fixed here relative to
charmbracelet/x/cellbuf (the renderer differential finds none of them): cellbuf/6 (lossy
SGR 22/25 diffs — `StyleDiff` re-sends the sibling attribute), cellbuf/11 (blank inheriting
the pen), cellbuf/12 (clearBottom's erase row), cellbuf/13 (the transformLine hang — the
placeholder loop now stops at the line end), cellbuf/14 (space printed over a placeholder —
lines with wide cells are repainted whole), cellbuf/16 (equal styles diff to a reset),
cellbuf/17 (multi-line scroll without SU), cellbuf/18 (IRM without the cells).

## Not bugs (or not ultraviolet's)

- Layout, faithful to ratatui: with `FlexSpaceAround` every spacer is at least the spacing
  and the outer two are half the inner ones, so the inner gaps are at least *twice* the
  spacing; `FlexLegacy`, and `FlexSpaceBetween` with a single segment, hand the surplus to
  a segment whatever its constraint (`Max(20)` alone takes the whole area, as documented);
  a negative spacing (overlap) forces every segment to be at least the overlap; and when
  the constraints ask for more than the area holds, several splits are equally good and
  ratatui's choice is one of them (the Go solver's is random — /26).

- `CSI 1;mod R` is both a modified F3 and a cursor position report on row 1; the decoder
  returns both (documented), the generators expect both.
- URxvt's `CSI n $` followed by a final byte (`CSI 34 $ A`) is one ECMA-48 control sequence
  (`$` is an intermediate); the decoder's URxvt reading applies only when the buffer ends at
  the `$`. The protocol's own ambiguity: URxvt keys are kept out of streams, and reads are not
  cut after the `$` of `CSI n $ y` (DECRPM for ANSI modes).
- Keypad keys without associated text get the digit/operator as text (`CSI 57399 u` → "0"),
  under shift too; the oracle adopts the decoder's rule.
- A cluster cut between runes by a read boundary is two keys: the decoder cannot know more is
  coming; no cut inside clusters. `ESC ESC` followed by a key is ambiguous (alt+esc then key,
  or esc then alt+key); the stream generator keeps them last.
- PM, SOS and APC strings end with ST only (ECMA-48); BEL terminates OSC alone — the
  generators use `ESC \` for them.
- `ansi.MouseX10` encodes payload bytes as runes — x-ansi/22; X10 encoded by hand.
  `ansi.XParseColor` keeps a four-digit channel whole when its high byte is zero — x-ansi;
  the colour generator avoids that shape.
- A wide fill cell in `InsertLine`/`DeleteLine`/`InsertCell`/`DeleteCell` is written at every
  column of the vacated region, each write blanking the previous one: the result is styled
  blanks. The model does the same; the generators use narrow fill cells (nobody fills with a
  wide cell).
- `Line.Set` blanks a wide cell it partially overwrites with the wide cell's style — a
  documented choice the model adopts.
- The renderer erases trailing blanks with `EL` even when they carry a foreground colour or
  bold/faint/italic/blink; terminals keep only the background of erased cells. Invisible on a
  blank, so not compared.
- The x/vt emulator has no insert mode (IRM); frames where the renderer uses it (terminals
  without ICH) are not compared.
- Win32 input mode (`CSI vk;sc;uc;kd;cs;rc _`) and the Windows console path are not covered
  (no encoder written; open slice).
