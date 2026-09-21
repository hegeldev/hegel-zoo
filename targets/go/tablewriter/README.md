# go/tablewriter

Hegel property tests for [olekukonko/tablewriter](https://github.com/olekukonko/tablewriter),
the ASCII/Unicode table renderer: its helper packages `pkg/twwidth` (display widths of strings
holding ANSI escape sequences, truncation, the tab width), `pkg/twwarp` (word splitting and
minimum-raggedness wrapping) and `tw` (padding, header title formatting, camel-case splitting,
break points).

## Build

The patch adds a `hegel/` package; `go test -count=1 -run TestHegel -v ./hegel` needs nothing
beyond the module. The tests fix the tab width at 4 (`SetTabWidth` after a first `TabWidth()`,
see bug 1) and set the East Asian and narrow-border options per test case.

## Oracle

A model of the documented behaviour. Escape sequences are found by ECMA-48 (a CSI sequence is
`ESC [`, parameters, intermediates and a final byte; an OSC sequence is `ESC ]` up to BEL or
`ESC \`); the visible text's width is the sum of `displaywidth`'s rune widths (the package's
own primitive) with the tab width and the narrow box-drawing rule applied, and, when the
per-rune switch is off, `displaywidth`'s grapheme-aware string width. `Truncate` is modelled
case by case from its doc comment: negative width, visually empty input, zero width, a string
that fits (a reset appended after sequences), and the truncation walk keeping the sequences
met and the visible prefix that fits the budget left by the suffix. Wrapping: the words are
`strings.FieldsFunc(unicode.IsSpace)`; the partition returned by `WrapWords` must keep the
words, end in a line that fits (or a single word), cost the brute-force optimum of the
raggedness the package minimises (the squared slack of every line but the last, plus a penalty
for an overflowing line) and equal an independent statement of the dynamic programme;
`WrapString` and `WrapStringWithSpaces` add the limit adjustment, the special cases for blank
input and the preserved leading and trailing spaces. The `tw` helpers are modelled from their
comments (`Title`'s dot rule, `SplitCamelCase`'s classes and the upper-run lending its last
rune, `IsNumeric` as `Atoi`/`ParseFloat`, `BreakPoint` over the visible width, the `Pad`
family by gap).

## Properties

- `TestHegelWidth`: `Width`, `WidthNoCache`, `WidthWithOptions`, `Filter`, `SetOptions`,
  `SetTabWidth` (with the cache switch off).
- `TestHegelTruncate`: `Truncate` with and without a suffix, both East Asian settings.
- `TestHegelWrap`: `SplitWords`, `WrapWords`, `WrapString`, `WrapStringWithSpaces`.
- `TestHegelFn`: `tw.Title`, `tw.SplitCamelCase`, `tw.IsNumeric`, `tw.BreakPoint`, `tw.Pad`,
  `tw.PadLeft`, `tw.PadRight`, `tw.PadCenter`.

## Bugs

Eight, in `bugs.toml`. Tab width: a width set before the first `Size()` is overwritten by the
detection (1, medium); `Width`'s cache is not purged when the tab width changes (2, medium).
Widths: emoji sequences (VS16, ZWJ, flags, modifiers) are measured rune by rune (3).
`Truncate`: an ESC inside a sequence restarts the scan, so an `ESC \`-terminated OSC (a
hyperlink) swallows the rest of the string (4, medium); at width 0 the documented suffix is not
returned (5). Wrapping: `WrapStringWithSpaces` splits a multi-byte last rune, mis-measuring the
last word and returning a limit its lines exceed (6, medium). `tw`: `BreakPoint` counts the
characters of escape sequences, so `WrapBreak` cuts coloured text inside its sequence (7,
medium); `SplitCamelCase` keeps groups of several underscores (8).

## Modelled as recorded, not counted

- `Width` strips only CSI and OSC sequences (as `Filter` documents): a two-character escape
  such as `ESC 7` leaves its final character visible; an OSC holding a newline is not a
  sequence. The generators produce neither.
- `Truncate` appends a reset after a string that fits when it holds ESC and does not end in
  `ESC[0m`; the East Asian setting returns the bare suffix when exactly the suffix fits, the
  other setting the sequences met plus a reset plus the suffix.
- `WrapString(" ")` is `[" "]` but two spaces are `[""]`; a newline or a tab is a word
  separator; `WrapStringWithSpaces` of blank input returns its width as the limit (smaller than
  the input limit) and truncates a blank wider than the limit; its leading spaces are not
  counted in the limit, so a line with them may be wider than the limit returned.
- `IsNumeric` accepts whatever `ParseFloat` accepts: `inf`, `NaN`, `1_000`, hexadecimal floats.
- The `Pad` family repeats the padding string by characters, not columns (a wide padding
  character over-pads), and `Pad` with an unknown alignment pads right.
- The table itself (`tablewriter.Table`, the renderers) is not yet exercised.
