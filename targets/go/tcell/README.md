# go/tcell

Hegel property tests for the `terminfo` and `terminfo/dynamic` packages of
[gdamore/tcell](https://github.com/gdamore/tcell) v2 (the v3 line dropped terminfo for a
built-in emulation): `TParm`, the evaluator of parameterized strings, and
`dynamic.LoadTerminfo`, which builds a `Terminfo` from `infocmp -1` output.

## Build

The patch adds a `hegel/` package. `go test -count=1 -run TestHegel -v ./hegel` needs `tic`,
`infocmp` and `tput` from ncurses on the PATH (Ubuntu's `ncurses-bin`) and reads the installed
database under `/usr/share/terminfo` for `TestHegelDatabase` (skipped when absent).

## Oracle

ncurses, in both directions, as for go/terminfo: `tic -x` compiles a generated terminfo source
into a temporary database, `infocmp -1 -x -A <db>` reads the compiled entry back, and
`TERMINFO=<db> tput -T <name> <cap> p1..p9` evaluates a parameterized string. The generator's
own values are compared with infocmp too, so a mismatch is attributed (class `Source` is a
generator or ncurses quirk, `Load` and `Mismatch` are the package's). A model of tparm written
from terminfo(5) (C ints, non-zero is true, `%c` writes the low byte) validates tput on every
case; under `HEGEL_NO_KNOWN=1` its switches emulate the recorded deviations (`flatSkip`,
`literalFlags`, `literalLogic`, `strictFlagOrder`) so that the rest of the language stays
tested; by default it predicts what terminfo(5) says and the property fails on the bug, naming
which single switch reproduces the output. The model of
`LoadTerminfo` is the package's documented rules applied to what infocmp prints: the named
fields, `Colors` zeroed below 8 or without `setaf`, the pad character, `Tc`/`RGB`, the composed
`SetFgBg`, and an error without `cup`.

## Properties

- `TestHegelLoad`: a generated entry (aliases, description, standard bools/nums/strings with
  cancellations, extended caps including `Tc` and `RGB`, `cup` most of the time, strings of
  arbitrary bytes rendered with terminfo(5)'s escapes chosen at random) compiled by tic loads to
  what infocmp prints for it. Lands on tcell/3 (an entry with `Tc` or `RGB`; 2-40 % of cases
  from run to run, intermittent).
- `TestHegelDatabase`: random entries of the installed database load to what infocmp prints.
  Lands on tcell/3 (26 of the 2869 installed entries carry `Tc` or `RGB`; intermittent).
- `TestHegelTParm`: a generated parameterized string (parameters, constants, arithmetic,
  bitwise, comparison and logical operators, `%i`, dynamic variables, printf-style formats,
  nested `%? %t %e %;`) compiled into an entry evaluates through `TParm` with nine int
  parameters to what tput prints for it. Lands on tcell/2 (a format flag without the colon,
  its shrunk form; tcell/1, /5 and /6 are reached at 16 %, 13 % and 1 % of cases).

## Known bugs

The generators draw the shape of every recorded bug (STYLE.md rule 11): the three properties
above are expected failures mapped to the bug they land on, and each bug has a narrow property
over its own shape region in `hegel/hegel_shapes_test.go`, the deterministic expected failure
beside the pin: `TestHegelNestedConditionalInSkippedBranchIsSkipped` (tcell/1),
`TestHegelFormatFlagsWorkWithoutTheColon` (/2), `TestHegelTrueColorFlagsAreRead` (/3),
`TestHegelXorOperatorLoadsUnchanged` (/4), `TestHegelLogicalOperatorsAreEvaluated` (/5) and
`TestHegelFormatFlagsComeInAnyOrder` (/6). `HEGEL_NO_KNOWN=1` (read once) switches the shapes
off: the tparm model absorbs the deviations, the Load model is blind to `Tc`/`RGB`, `%^` is
respelled, and the narrow properties draw the neighbouring region; every property then passes
at 3000 cases (the ncurses specifics below stay assumed away, under 5 % of the TParm cases).

## Bugs

Six, in `bugs.toml`: a skipped conditional branch ends at the first `%e`/`%;` whatever the
nesting (1, high; 99 installed entries nest); `%#`, `% ` and `%.` formats need the colon (2,
low); `LoadTerminfo` runs infocmp without `-x`, so `Tc`/`RGB` are never seen (3, medium);
`unescape` reads the `^` of `%^` as a control prefix, breaking dm2500's `cup` (4, medium);
`%A`/`%O` are not implemented (5, medium; 13 installed entries use them); a flag after the `0`
flag ends the format (6, low).

## Modelled as recorded, not counted

- tcell keeps a NUL where terminfo has the byte 0200 (`\0` in infocmp output, ncurses' spelling
  of NUL inside a string), and `%c` of zero writes a NUL where ncurses writes 0200: both are a
  deliberate reading of the same convention; the Load model maps 0200 to NUL and the TParm
  property leaves `%c` of zero out.
- ncurses specifics left out of the TParm comparison, as in go/terminfo: `%i` applied at most
  once per evaluation (the renderer keeps only the first `%i`), two's-complement `%x`/`%o` of negatives, `%c` of a multiple of 256
  (NUL truncates the C string), int32 overflow, `%#x` of zero (C prints 0, Go 0x0), and the
  Go-vs-C printf differences the format generator leaves out (`%#0`, `% .0d`, `%#.0o`, `%:+`).
- tic and infocmp quirks the generators leave out (see go/terminfo): `%'c'` rewritten as `%{n}`
  and back, control characters after `%`, a backslash after a caret, 0200 before an octal digit,
  two-letter extended names, `box1`, cancelled booleans, extended numbers above 32767; and a
  string ending in `% ` as the entry's last capability, which infocmp prints without the space
  (respelled as `%x`).
- An entry whose last name field is an alias rather than a description: tcell, like ncurses'
  `longname()`, takes the last field as the description; the model does the same.
