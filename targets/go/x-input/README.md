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

| Test | What it checks | Gates |
| --- | --- | --- |
| `SequencesDecodeToTheirEvents` | every encoded event decodes to itself, consuming exactly its bytes, leaving the buffer untouched, with a non-empty `String()` | the pinned shapes (/1 alternate keys with a base key, /2 event types on `~` keys, /3 num lock) are counted, `CSI n $` is exempt from the immutability check (/4) |
| `StreamsSplitIntoTheirEvents` | 1–6 encoded events back to back parse (via `parseSequence` and via `Reader.ReadEvents`) into the concatenated event lists | a lone ESC or `ESC ESC` only as the last event (alt+esc followed by a key is ambiguous by nature); `CSI 1;mod R` alone skips the Reader check (whole-buffer table lookup gives F3 only, by design) |
| `KittyAndModifyOtherKeysAgree` | `CSI code;mod u` and `CSI 27;mod;code ~` give the same code and modifiers (shift/alt/ctrl), and the same text without shift | — |
| `KeyTableAgreesWithTheParser` | every built-in table entry for random flags and terminals decodes to the same key (F3/CPR ambiguity allowed) | terminfo-sourced entries (/10), `ESC`/`ESC ESC` with `FlagCtrlOpenBracket` (/9) |
| `ReaderPastesRoundTrip` | bracketed paste of random text (including ESC, `[`, digits, `~`, controls) through the Reader, between other events | pastes containing the end marker; reads over 250 bytes (the Reader's buffer is 256) |
| `GraphemesAreOneKey` | a multi-rune grapheme cluster is one `KeyExtended` press with the whole text | clusters starting with an ASCII byte (/6) |
| `Examples` | fixed examples from the protocols | — |

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
