# go/x-input — charmbracelet/x/input

The terminal input parser under Bubble Tea v2: bytes from the terminal become key, mouse,
paste, focus and report events. It understands VT100/VT220 and xterm PC-style function keys,
SS3 keypad keys, URxvt's odd sequences, the Kitty keyboard protocol (CSI u with alternate
keys, event types and associated text), xterm's modifyOtherKeys, X10 and SGR mouse reports,
bracketed paste, cursor/mode/device-attribute/window reports, OSC colour and clipboard
replies, XTGETTCAP and XTVERSION. Monorepo `charmbracelet/x`, `subdir = "input"`, pinned at
c615ff2 (2026-09-13, after input/v0.3.7). MIT; no CONTRIBUTING/AGENTS policy (checked for the
sibling packages in turns 128–130). The test lives in package `input` to reach
`Parser.parseSequence` and `buildKeysTable`.

## Oracles

Encoders for every protocol the parser decodes, each returning the bytes and the events they
mean:

- **x/ansi's own encoders** for what it has them: `EncodeMouseButton` + `MouseSgr` (X10 is
  encoded by hand, see below), `CursorPositionReport`, `ReportMode`,
  `PrimaryDeviceAttributes`, `WindowOp`, `SetClipboard`.
- **Hand-written encoders from the specifications** for the rest: the Kitty keyboard protocol
  (`CSI code[:shifted[:base]] ; mods[:event] ; text u`, functional keys 57344+, lock
  modifiers), xterm's `CSI 1;mod[:event] F`, `CSI n;mod[:event] ~`, `SS3 mod F`,
  `CSI 27;mod;code ~`, URxvt's `CSI n ^ / @ / $`, OSC 10/11/12 `rgb:` replies, `DCS 1+r`
  hex pairs, `DCS >|` versions, `CSI 200~`/`201~`, plain text (single runes, clusters, C0
  controls) and ESC-prefixed alt keys.
- **The package's own key table** (`buildKeysTable`, built-in and terminfo keys for the
  terminals present in the system terminfo database): the Reader consults it for a whole read
  and the parser otherwise, so the two must agree.
- **The Kitty and modifyOtherKeys encodings of the same key** must decode to the same event.

## Properties

| Test | What it checks | Lands on |
| --- | --- | --- |
| `SequencesDecodeToTheirEvents` | every encoded event decodes to itself, consuming exactly its bytes, leaving the buffer untouched, with a non-empty `String()` | bug 6 (an ASCII-led cluster); the shapes of bugs 1, 2, 3 and 4 are drawn too |
| `StreamsSplitIntoTheirEvents` | 1–6 encoded events back to back parse (via `parseSequence` and via `Reader.ReadEvents`) into the concatenated event lists; a lone ESC, `ESC ESC`, `ESC` + introducer and `CSI n $` only as the last event (ambiguous with a follower by nature); `CSI 1;mod R` alone skips the Reader check (whole-buffer table lookup gives F3 only, by design) | bug 6 |
| `KittyAndModifyOtherKeysAgree` | `CSI code;mod u` and `CSI 27;mod;code ~` give the same code and modifiers (shift/alt/ctrl), and the same text without shift | clean |
| `KeyTableAgreesWithTheParser` | every built-in and terminfo table entry for random flags and terminals decodes to the same key (F3/CPR ambiguity allowed) | bug 10 in most runs (about four cases in a thousand; bug 9's shape is rarer), passing a default run now and then |
| `ReaderPastesRoundTrip` | bracketed paste of random text (including ESC, `[`, digits, `~`, controls) through the Reader, between other events; pastes containing the end marker and reads over 250 bytes (the Reader's buffer is 256) are not drawn | bug 6 or 1 through the neighbouring events, passing a default run now and then |
| `GraphemesAreOneKey` | a multi-rune grapheme cluster is one `KeyExtended` press with the whole text | bug 6 |
| `Examples` | fixed examples from the protocols | clean |

One narrow property per bug draws its region with random contents and is the deterministic
expected failure mapped to it: `KittyAlternateKeysKeepTheShiftedKey` (1),
`TildeKeysHonourEventTypes` (2), `NumLockKeepsTheKeyText` (3),
`URxvtDollarKeysLeaveTheInputUntouched` (4), `InvalidUTF8BytesAreReportedRaw` (5),
`ASCIILedGraphemeClustersAreOneKey` (6), `AltIntroducerKeysLookLikeOtherAltKeys` (7),
`CSIWithManyParametersIsConsumedWhole` (8), `CtrlOpenBracketFlagAppliesToALoneEscape` (9),
`TerminfoKeysParseLikeTheTable` (10). A failure names the shape it hit. `HEGEL_NO_KNOWN=1`
(read once) looks past the recorded bugs: the pools are built without the shapes and the narrow
properties draw the neighbouring region (caps lock for 3, C1 bytes for 5, `] _ ^` introducers
for 7, up to 32 parameters for 8, ...); every property then passes.

Each `TestHegelPin…` reproduces one bug and is an expected failure. `XINPUT_COLLECT=1` turns
failures into a tally per property. Pin /10 needs the `screen`, `vt220` and `tmux` terminfo
entries (ncurses-base); it fails either way, so it is a stable expected failure.

## Bugs

| id | severity | title |
| --- | --- | --- |
| x-input/1 | high | Kitty alternate keys: the base-layout key overwrites the shifted key — shift+a on AZERTY types "q" |
| x-input/2 | medium | release/repeat event types ignored for `CSI n;mod:event ~` keys (Insert, Delete, PgUp, PgDn, F5–F20) |
| x-input/3 | medium | a num-lock modifier removes the key's text while caps lock keeps it |
| x-input/4 | low | URxvt `CSI n $` keys are parsed by rewriting `$` to `~` in the caller's buffer |
| x-input/5 | low | an invalid UTF-8 byte is reported as the UTF-8 encoding of the rune with that value |
| x-input/6 | medium | grapheme clusters starting with an ASCII byte are split into separate key presses |
| x-input/7 | medium | alt+`[` has no code and keeps its text (`String()` is "["); alt+O/P/X have odd shapes |
| x-input/8 | low | a CSI with more than 32 parameters is cut short and its tail becomes key presses |
| x-input/9 | low | `FlagCtrlOpenBracket` ignored for a lone ESC and ESC ESC, unlike the key table |
| x-input/10 | medium | terminfo keys the parser also recognises are honoured only when the key arrives alone |

## Not bugs (or not input's)

- `CSI 1;mod R` is both a modified F3 and a cursor position report on row 1; the parser
  returns both (documented), the generators expect both.
- `CSI 1 R` alone is unknown (`CSI 1 P/Q/S` are F1/F2/F4): it is also a cursor report with the
  column omitted; left alone.
- Kitty reports shift+1 as `CSI 49;2u`; without alternate keys no parser can know the text is
  "!", and the derived "1" is what the protocol allows for. Lock modifiers are not reported for
  text keys without "report all keys as escape codes" (kitty spec), which limits /3's reach.
- xterm's meta bit (8) is `ModMeta`, the Kitty super bit (8) is `ModSuper` — documented in
  `mod.go`; the cross-protocol property only compares shift/alt/ctrl.
- `ansi.MouseX10` in x/ansi encodes the three payload bytes with `string(byte)`, i.e. as runes,
  so coordinates from 95 upwards become two UTF-8 bytes; the input parser is right to read
  three raw bytes. Recorded against `go/x-ansi` (x-ansi/22); the X10 generator here encodes
  the bytes itself.
- `ansi.XParseColor` keeps a four-digit channel whole when its high byte is zero (`00c0` →
  0xc0): x-ansi's bug (x-ansi/20-class, XParseColor scaling); the colour generator avoids that
  shape.
- A stream ending in ESC, or `ESC ESC` followed by a key, is ambiguous (Escape then alt+key,
  or alt+esc then key) in the protocol itself; the stream generator keeps them last.
- 2026-09-20: base bumped c615ff2f7805 → 53e2afe73ae5 (2026-09-20, "chore(powernap): update lsp configs from nvim-lspconfig"; v0.3.7+); 10 bug(s) still reproduce. 7 tests pass.
