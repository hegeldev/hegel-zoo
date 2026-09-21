# go/go-pretty

Hegel property tests for [jedib0t/go-pretty](https://github.com/jedib0t/go-pretty), the
table/list/progress renderer: its `text` package, the ANSI-aware string utilities the renderers
are built on (widths, trimming, wrapping, alignment, case conversion, colours, the escape
sequence parser, the transformers).

## Build

The patch adds a `hegel/` package; `go test -count=1 -run TestHegel -v ./hegel` needs nothing
beyond the module.

## Oracle

A model of the documented behaviour over strings holding escape sequences. A scanner splits a
string into sequences and visible runes by ECMA-48 (a CSI sequence ends at its final byte, an
OSC sequence at BEL or ESC \); the visible text and its width (`text.RuneWidth` per rune, the
package's own definition) follow. An SGR state (foreground, background, the attributes 1-9,
set by their codes and cleared by 22-29, 39, 49 or 0) is tracked through the sequences, so
that the state in force at every visible rune can be compared between input and output. On
these: the documented rules of Trim, Snip, Pad, RepeatAndTrim, Widen, InsertEveryN, ProcessCRLF,
Align (trimming, padding, justification, the numeric test of AlignAuto), VAlign, Format
(sequences untouched), Escape (the sequence applied from the start and after every reset), the
parser's restored sequence (must denote the state), and for the wrap functions the invariants:
every line fits the width, the visible non-space runes and their escape state are preserved in
order, a wrapped output leaves no state open, WrapSoft keeps words that fit, a string that fits
is returned as it is. The transformers are checked against `fmt.Sprintf` with the documented
sign colours and against `time.Format` with the documented unit detection.

## Properties

- `TestHegelWidth`: `StripEscape`, `StringWidthWithoutEscSequences`, `RuneCount`,
  `LongestLineLen`, `Trim`, `Pad`, `Snip`, `Widen`, `RepeatAndTrim`.
- `TestHegelInsert`: `InsertEveryN`, `ProcessCRLF`.
- `TestHegelAlign`: `Align.Apply` (all six alignments), `VAlign.Apply`, `VAlign.ApplyStr`.
- `TestHegelFormat`: `Format.Apply`.
- `TestHegelEscape`: `Escape`, `Colors.Sprint`, `EscSeqParser.ParseString/Sequence/IsOpen`.
- `TestHegelWrap`: `WrapHard`, `WrapSoft`, `WrapText`.
- `TestHegelTransform`: `NewNumberTransformer`, `NewTimeTransformer`,
  `NewUnixTimeTransformer`.

## Bugs

Twenty-four, in `bugs.toml`. Sequences: a CSI sequence is terminated only by `m`, so the
package's own cursor and erase sequences swallow the text after them (1, medium); an OSC
sequence terminated by BEL is recognised only for OSC 8 (2); the parser reads a 24-bit colour
as five attributes (9, medium), restores colours in numeric order rather than the last set
(10, medium), ignores 28 (11), and applies 256-colour codes before the other codes of the same
sequence, so `ESC[0;38;5;31m` loses its colour (23, medium). Wrapping: a reset leaves the
earlier sequence to be re-opened on later lines (5, medium); a word broken across lines
restarts with the raw sequence found in the word, losing the other attributes (6, medium); a
hyperlink's parameters are read as SGR codes so the following lines are concealed (7, medium)
and the hyperlink word is never wrapped (8); the state is dropped at a paragraph break and, in
WrapText, at a line break (20, medium); a wide rune straddling the width makes the line one
column too wide (21, medium). Strings: Format.Apply ends every sequence at `m`, case-changing
a hyperlink's URL and label (3, medium); FormatTitle upper-cases instead of title-casing (16);
Escape with an empty sequence removes every reset (4) and removes the input's own
sequence+reset pair, leaving the output open (24); AlignAuto reads the number from the raw
text (15); AlignJustify panics on a blank text and a negative length (22); RepeatAndTrim counts
runes but trims by width (17); Snip neither pads as documented nor keeps the length with a wide
indicator (18); ProcessCRLF lets escape sequences take columns (19). Transformers: negatives
are formatted as `-` plus the format of the negated value, breaking widths and MinInt64 (12);
times at or before the epoch render as "" (13, medium); unix times are accepted as int64 and
string only (14).

## Modelled as recorded, not counted

- Widths are `text.RuneWidth` per rune (runewidth with the box-drawing rule): a combining mark
  is 0, an emoji 2, a ZWJ sequence the sum of its parts; the model uses the same function.
- Align trims spaces on the padded side only when the raw string has a space at that end (a
  sequence at the end prevents it); Justify splits the raw text on spaces, so a sequence
  standing alone is a word and a blank text loses its sequences.
- WrapSoft pads the lines it ends early with spaces to the width (the package's tests assert
  it); a string that fits is returned with its line breaks and space runs, while a longer one is
  re-flowed; tabs become four spaces first.
- ProcessCRLF overwrites rune by rune, so a wide rune is one column; Pad appends characters,
  not columns; Trim drops the visible runes after the first that does not fit.
- NewUnixTimeTransformer reads a value >= 10^10 as milliseconds, >= 10^13 as microseconds,
  >= 10^16 as nanoseconds; float32 values are formatted after conversion to float64.
- BeEquivalent-like conversions and the `table`, `list` and `progress` packages are not
  exercised.
