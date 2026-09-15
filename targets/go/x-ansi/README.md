# x-ansi

[charmbracelet/x/ansi](https://github.com/charmbracelet/x/tree/main/ansi) (module
`github.com/charmbracelet/x/ansi`, `subdir = "ansi"` of the charmbracelet/x monorepo) is the ANSI
escape-sequence library under Bubble Tea, Lip Gloss and Glamour: a DEC-style state-machine
`Parser` with handlers, a `DecodeSequence` tokenizer, `Strip` and the cell widths (grapheme
clusters through displaywidth, or wcwidth-style through go-runewidth), `Truncate`/`TruncateLeft`/
`Cut`, `Hardwrap`/`Wordwrap`/`Wrap`, the SGR `Style` builder and `ReadStyleColor`, `XParseColor`
and the xterm palette conversions, plus constructors for hundreds of sequences. Pinned at
c615ff2f7805 (2026-09-13, past `ansi/v0.11.8`). MIT. No CONTRIBUTING.md, AGENTS.md or AI policy
in the repository; not archived, active. Checked 2026-09-15. The harness lives in
`ansi/hegel_test.go` (package `ansi_test`).

## Oracles

- **A token grammar of ECMA-48**: every generated document is a list of tokens — grapheme
  clusters of known width (ASCII, é, 日, 😀, a family ZWJ sequence that is 2 cells by cluster
  and 6 by wcwidth, the no-break space), C0 controls, CSI sequences (private marker, parameters
  with sub-parameters and leading zeros, intermediates, final), ESC sequences, OSC strings
  (number, payload, BEL/ESC \\/0x9C), DCS with parameters and payload, APC/PM/SOS strings, with
  8-bit C1 introducers now and then. `DecodeSequence` (both methods), `Parser.Advance` with
  every handler, `Strip`, `StringWidth`/`StringWidthWc` are compared with the list they were
  built from: pieces, widths, commands, packed parameters, OSC numbers and payloads, events.
- **Models from the documentation** for `Truncate`, `TruncateLeft`, `Cut` (a cluster straddling
  the left cut is kept whole, as upstream's own cases have it; sequences are kept in place;
  controls after the cut dropped) and for `Hardwrap` (greedy; spaces dropped at the start of a
  wrapped line unless `preserveSpace`).
- **An SGR model** for `Wordwrap` and `Wrap`, where the algorithm is not specified to the
  character: every non-whitespace rune of the output carries the style (SGR sequences since the
  last reset) it had in the input, the sequences appear in order, no newline is lost, and every
  line is within the limit unless it holds a breakpoint, ends in a word at least as wide as the
  limit (Wordwrap never splits a word) or falls under one of the pinned shapes; `Wrap` of a text
  without whitespace or breakpoints equals `Hardwrap`.
- **The SGR parameter table** for the `Style` builder (each method's parameters, then back
  through the decoder and `ReadStyleColor`), **ITU T.416** for `ReadStyleColor` (colon and
  semicolon forms, colour-space ids, 6th parameter, tolerance, CMY/CMYK/RGBA, transparent),
  **X11's XParseColor scaling** for `rgb:`/`rgba:`/`#` colours, and **the xterm palette** for
  `Convert256`/`Convert16` (every palette entry converts to its own index).
- **Arbitrary text** over an alphabet of sequence bytes and clusters: decoding makes progress,
  joins back to the input and never panics; nor do the parser, the widths, truncation or the
  wrappers.

## Properties

- `TestHegelDecodeSequenceFollowsTheGrammar` — clean (two private markers included: the decoder
  keeps the last).
- `TestHegelParserReportsTheGrammarsEvents` — clean with one private marker (x-ansi/20) and
  ASCII payloads in SOS/PM/APC strings (x-ansi/18); ESC \ after a string is reported as an
  ESC sequence of its own, as a VT parser does.
- `TestHegelStripAndWidthsFollowTheTokens` — clean (same payload restriction).
- `TestHegelTruncateFollowsItsModel` — clean; `Cut` under WcWidth with `left > 0` not judged
  (x-ansi/7); under WcWidth the ZWJ sequence is left out of the alphabet (x-ansi/6).
- `TestHegelHardwrapFollowsTheGreedyModel` — clean; a cluster wider than the limit (x-ansi/12)
  not judged; no no-break space in the input (x-ansi/13).
- `TestHegelWordwrapKeepsWordsAndStyles`, `TestHegelWrapKeepsLinesWithinTheLimit` — clean;
  not judged for width: lines with a breakpoint or followed by one (x-ansi/8, /9), lines ending
  in a word at least as wide as the limit (x-ansi/10), inputs with a line starting with a space
  (x-ansi/19) or with whitespace followed by sequences and whitespace (x-ansi/21), clusters
  wider than the limit (x-ansi/12); `Wrap` = `Hardwrap` only without the no-break space.
- `TestHegelStylesRoundTripThroughTheDecoder`, `TestHegelReadStyleColorFollowsT416` — clean
  (components 0–255; x-ansi/15 pinned).
- `TestHegelXParseColorFollowsX11` — clean for two-digit `rgb:`/`rgba:` components, invalid
  components and `#rgb`/`#rrggbb`; the other digit counts are x-ansi/14.
- `TestHegelPaletteConversionsRoundTrip` — clean; basic colours 7 and 8 not judged (x-ansi/17).
- `TestHegelArbitraryTextIsDecodedWithoutLossOrPanic` — clean; inputs with 31 or more CSI
  parameter separators skipped (x-ansi/1).

## Bugs

| id | severity | title |
|----|----------|-------|
| x-ansi/1 | high | DecodeSequence panics on a CSI sequence with more parameters than the parser's buffer |
| x-ansi/2 | low | A CSI sequence with exactly as many parameters as the buffer loses its last one |
| x-ansi/3 | medium | A 0x9C byte inside a UTF-8 character terminates an OSC, DCS, SOS, PM or APC string (upstream #848) |
| x-ansi/4 | low | A private marker after the parameters: the Parser dispatches the sequence, DecodeSequence rejects it and prints the rest |
| x-ansi/5 | medium | A grapheme cluster that starts with an ASCII character is split off after its first byte, so Truncate returns a keycap wider than the length |
| x-ansi/6 | low | TruncateWc decides whether the text fits with grapheme widths |
| x-ansi/7 | high | CutWc truncates to `left` cells instead of removing them |
| x-ansi/8 | medium | Wrap writes a breakpoint, and the whitespace before it, onto a full line (upstream #785) |
| x-ansi/9 | medium | Wordwrap writes a breakpoint without checking the limit |
| x-ansi/10 | low | Wordwrap never moves a word as wide as the limit to its own line |
| x-ansi/11 | low | Wordwrap measures whitespace in bytes |
| x-ansi/12 | low | Hardwrap and Wrap start with an empty line when a cluster is wider than the limit |
| x-ansi/13 | low | Hardwrap drops a non-ASCII space at the start of the text, but keeps an ASCII one |
| x-ansi/14 | medium | XParseColor scales rgb: components as if they always had two digits, and reads invalid hex as zero |
| x-ansi/15 | low | ReadStyleColor truncates colour components modulo 256 |
| x-ansi/16 | low | ByteToGraphemeRange counts escape-sequence bytes and control characters as cells, unlike Cut |
| x-ansi/17 | low | Convert16 does not return the basic colour for the exact RGB of colours 7 and 8 |
| x-ansi/18 | medium | A UTF-8 character inside an SOS, PM or APC string ends the string in the table-driven parser, and is printed |
| x-ansi/19 | medium | Leading spaces confuse Wrap and Wordwrap: an empty first line, or a line one space too wide |
| x-ansi/20 | low | With two private markers the Parser keeps the first and DecodeSequence the last |
| x-ansi/21 | low | Whitespace followed by an escape sequence is flushed past the limit by Wordwrap and Wrap |
| x-ansi/22 | medium | MouseX10 encodes its payload bytes as runes: coordinates from 95 upwards become two UTF-8 bytes |

## Not bugs

- `Hardwrap` emits an empty line when a trailing space overflows just before a newline
  (`"ab \nc"` at 2 → `"ab\n\nc"` without `preserveSpace`): the space starts a line, the newline
  ends it; the model follows the code.
- The wrappers count a tab as one cell where `StringWidth` counts none; tabs are kept out of
  the wrap inputs.
- `TruncateLeft` keeps a cluster that straddles the cut (`TruncateLeft("on👋", 3, ".")` =
  `".👋"` is upstream's own case), so `Cut` can return a span one cell wider than asked.
- A tail wider than the length makes `Truncate` return `""`; the documentation does not say
  otherwise.
- `#rgb` colours are read with CSS scaling (`#fff` is white), not X11's high-order-bits rule;
  the documentation lists the formats and says "similar" to XParseColor.
- `ESC \` after an ESC-terminated string is dispatched by the `Parser` as an escape sequence;
  that is how a VT parser sees the 7-bit String Terminator.
