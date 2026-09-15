# go/ultraviolet — charmbracelet/ultraviolet (input decoder)

The terminal primitives under Bubble Tea v2: this target covers the input side —
`EventDecoder` (bytes → key, mouse, paste, focus and report events; the successor of
charmbracelet/x/input's parser), `eventScanner` (the read loop behind `TerminalReader` and
`Terminal`: whole-read key-table lookup, bracketed paste, waiting for incomplete sequences
across reads), the key table (`buildKeysTable`, built-in and terminfo keys) and the `Key`
methods programs match on (`Keystroke`, `String`, `MatchString`). Pinned at 6c9e17d
(2026-09-10, untagged main). MIT; no CONTRIBUTING/AGENTS/AI policy (checked 2026-09-15). The
test lives in package `uv` to reach `eventScanner`, `buildKeysTable` and the legacy flag
constants. The cell buffer, renderer and layout solver are open slices.

## Oracles

Encoders for every protocol the decoder decodes, each returning the bytes and the events they
mean — the x-input harness carried over and extended:

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
| `Examples` | fixed examples from the protocols, and the x-input bugs fixed here (/2 event types, /3 num lock, /4 buffer mutation, alt+`[`) | — |

Each `TestHegelPin…` reproduces one bug and is an expected failure. `UV_COLLECT=1` turns
failures into a tally per property. Pin /12 needs the `tmux`, `screen` and `xterm` terminfo
entries (ncurses-base); it fails either way.

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

Fixed here relative to charmbracelet/x/input (held as examples): x-input/2 (event types on
`CSI n;mod:ev ~`), x-input/3 (num lock text), x-input/4 (URxvt `$` rewrote the caller's
buffer — now `slices.Clone`), x-input/7's alt+`[` (now `Code '['`).

## Not bugs (or not ultraviolet's)

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
- Win32 input mode (`CSI vk;sc;uc;kd;cs;rc _`) and the Windows console path are not covered
  (no encoder written; open slice).
