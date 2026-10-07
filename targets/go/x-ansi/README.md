# x-ansi

[charmbracelet/x/ansi](https://github.com/charmbracelet/x/tree/main/ansi) (module
`github.com/charmbracelet/x/ansi`, `subdir = "ansi"` of the charmbracelet/x monorepo) is the ANSI
escape-sequence library under Bubble Tea, Lip Gloss and Glamour: a DEC-style state-machine
`Parser` with handlers, a `DecodeSequence` tokenizer, `Strip` and the cell widths (grapheme
clusters through displaywidth, or wcwidth-style through go-runewidth), `Truncate`/`TruncateLeft`/
`Cut`, `Hardwrap`/`Wordwrap`/`Wrap`, the SGR `Style` builder and `ReadStyleColor`, `XParseColor`
and the xterm palette conversions, plus constructors for hundreds of sequences. Pinned at
c615ff2f7805 (2026-09-13, past `ansi/v0.11.8`). MIT. No CONTRIBUTING.md, AGENTS.md or AI policy
in the repository; not archived, active. Checked 2026-09-15. The test lives in
`ansi/` (package `ansi_test`): `hegel_test.go` (harness, the `Known` switches), `hegel_gen_test.go`,
`hegel_model_test.go`, `hegel_props_test.go`, `hegel_shapes_test.go` (one narrow property per bug)
and `hegel_pins_test.go`.

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

The wide properties draw the shapes of the recorded bugs by default and fail on them (see
below); each is mapped in `target.toml` to the bug it most often shrinks to.

- `TestHegelDecodeSequenceFollowsTheGrammar` and `TestHegelParserReportsTheGrammarsEvents` —
  parameter lists up to and beyond the parser's buffer (x-ansi/1, /2), a 0x9C byte inside a
  UTF-8 character of a control string (x-ansi/3, the usual basin), a private marker after the
  parameters (x-ansi/4), two private markers (x-ansi/20), UTF-8 payloads in SOS/PM/APC strings
  (x-ansi/18); `ESC \` after a string is reported as an ESC sequence of its own, as a VT parser
  does.
- `TestHegelStripAndWidthsFollowTheTokens` — the same documents; UTF-8 payloads in SOS/PM/APC
  strings are its basin (x-ansi/18).
- `TestHegelTruncateFollowsItsModel` — `Cut` under WcWidth with `left > 0` (x-ansi/7, the
  basin), the ZWJ sequence under WcWidth (x-ansi/6), clusters starting with ASCII (x-ansi/5).
- `TestHegelHardwrapFollowsTheGreedyModel` — clusters wider than the limit (x-ansi/12, the
  basin), the no-break space at the start (x-ansi/13).
- `TestHegelWordwrapKeepsWordsAndStyles`, `TestHegelWrapKeepsLinesWithinTheLimit` — lines with
  a breakpoint or followed by one (x-ansi/8, /9), a word as wide as the limit after a leading
  space (x-ansi/10), the ideographic space (x-ansi/11), clusters wider than the limit
  (x-ansi/12, Wrap's basin), lines starting with a space (x-ansi/19, Wordwrap's basin),
  whitespace followed by sequences and whitespace (x-ansi/21); a line ending in a word wider
  than the limit is tolerated (it fits nowhere); `Wrap` = `Hardwrap` without whitespace or
  breakpoints.
- `TestHegelStylesRoundTripThroughTheDecoder` — clean.
- `TestHegelReadStyleColorFollowsT416` — components beyond 255 (x-ansi/15).
- `TestHegelXParseColorFollowsX11` — one-, two-, three- and four-digit `rgb:`/`rgba:`
  components and invalid ones (x-ansi/14), `#rgb`/`#rrggbb`.
- `TestHegelPaletteConversionsRoundTrip` — every palette entry, basic colours 7 and 8 included
  (x-ansi/17).
- `TestHegelArbitraryTextIsDecodedWithoutLossOrPanic` — CSI parameter lists of any length
  (x-ansi/1), clusters starting with ASCII (x-ansi/5, the basin); three disagreements between
  the decoder's widths and `StringWidth` that are not recorded yet are counted, not judged
  (`candidate/go/x-ansi-1`: a C0 control inside an ESC sequence, `"\x1b\a["`; `-2`: an
  introducer after an intermediate, `"\x1b ]abc"`; `-3`: ESC inside a DCS, `"\x1bP\x1bPé"`).
- Twenty-two narrow properties in `hegel_shapes_test.go`, one per recorded bug and named after
  what it tests (`TestHegelDecodeSequenceKeepsTheBufferOnLongParameterLists`,
  `TestHegelBufferSizedParameterListIsKeptWhole`,
  `TestHegelControlStringsKeepCharactersWithAnSTByte`,
  `TestHegelPrivateMarkerAfterParametersIsOneSequence`,
  `TestHegelClustersStartingWithASCIIDecodeWhole`, `TestHegelTruncateWcFitsByWcWidth`,
  `TestHegelCutWcRemovesTheLeftCells`, `TestHegelWrapKeepsBreakpointLinesWithinTheLimit`,
  `TestHegelWordwrapKeepsBreakpointLinesWithinTheLimit`,
  `TestHegelWordwrapMovesAWordAsWideAsTheLimitToItsOwnLine`,
  `TestHegelWordwrapMeasuresWhitespaceInCells`,
  `TestHegelWrappersStartWithTextWhenAClusterIsWiderThanTheLimit`,
  `TestHegelHardwrapKeepsTheNoBreakSpaceAtALineStart`, `TestHegelXParseColorScalesByDigitCount`,
  `TestHegelReadStyleColorRejectsComponentsBeyond255`, `TestHegelByteToGraphemeRangeCountsCells`,
  `TestHegelConvert16ReturnsTheBasicGreys`, `TestHegelStringsKeepUTF8Payloads`,
  `TestHegelWrappersKeepLeadingSpaces`, `TestHegelParserAndDecoderAgreeOnTwoPrivateMarkers`,
  `TestHegelWrappersKeepWhitespaceBeforeASequenceWithinTheLimit`,
  `TestHegelMouseX10PayloadIsThreeBytes`): each draws its bug's shape region with random
  contents and is the deterministic expected failure beside the pin.

## Known shapes drawn by default

A `Known` struct in `hegel_test.go` has one switch per bug shape, every one off by default:
the generators draw the shapes (`shaped(Known.x, on, off)` at the generator) and `mismatch`
names the bug whose shape the failing case has. Properties that fail every run are mapped
plain to their most frequent basin (Decode and Parser to x-ansi/3, Truncate to /7, Hardwrap
and Wrap to /12, Wordwrap to /19, XParseColor to /14); those a 100-case run misses now and
then are intermittent (Strip /18, ReadStyleColor /15, Palette /17, the arbitrary text /5).
`HEGEL_NO_KNOWN=1`, read once, turns every switch on: the shapes are left out at the
generators, the narrow properties draw the neighbouring region, and every property passes
except the pins.

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
- 2026-09-20: base bumped c615ff2f7805 → 53e2afe73ae5 (2026-09-20, "chore(powernap): update lsp configs from nvim-lspconfig"; v0.11.8+); 22 bug(s) still reproduce. 13 tests pass.
- 2026-10-07: generators rewritten in combinator style (package-level generator values, the
  token grammar as a `OneOf` of `Composite` token kinds, documents as lists of tokens, parameter
  lists and colours as records rendered by pure functions) and the file split in six; the known
  shapes drawn by default with twenty-two narrow properties; the model's `lastWordWidth` now
  measures by the method under test and the 8-bit introducers are raw C1 bytes; three
  decoder/parser disagreements surfaced as candidates (above), to be judged and recorded.
