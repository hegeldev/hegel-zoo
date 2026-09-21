# go/terminfo

[xo/terminfo](https://github.com/xo/terminfo) reads compiled terminfo files in pure Go and
evaluates their parameterized strings (`Printf`, the equivalent of `tparm`). Pinned at
`c203b35` (v1.2.0, 2026-09-14, MIT; no AI policy in README or `.github`, no CONTRIBUTING).

## Build

The tests live in a new package directory `hegel/` of the upstream module; `go.mod` gains
`hegel.dev/go/hegel`. The run command is `go test -count=1 -run TestHegel -v ./hegel`. They
run ncurses' `tic`, `infocmp` and `tput` from `PATH` (ncurses-bin, essential on Debian and
Ubuntu) and sample `/usr/share/terminfo` when it exists.

## Oracle

ncurses, the reference implementation of terminfo. Entries are generated as values (names
and aliases, a description, standard and extended boolean, numeric and string capabilities,
cancellations, numbers up to 2^31-1 so that both the 16-bit and the 32-bit file format
occur, strings of arbitrary bytes rendered in terminfo source syntax with the escapes
terminfo(5) allows chosen at random), compiled with `tic -x`, read back with
`infocmp -1 -x` and compared with what `Open` decodes; the generator's own values are
compared with infocmp too, so a mismatch is attributed. Parameterized strings are generated
over the whole language (`%p1`..`%p9`, `%{n}`, `%'c'`, arithmetic, bitwise, comparison and
logical operators, `%i`, dynamic variables, `%d %o %x %X %c` with printf flags, width and
precision, nested `%? %t %e %;`), compiled into an entry and evaluated by `tput` with nine
integer parameters; a model of `tparm` written from terminfo(5) checks tput (it never
disagreed) and, with the recorded typing bugs switched on, predicts the package's output so
that the rest of the language stays under test.

## Properties

- `TestHegelDecode`: a tic-compiled entry decodes to what infocmp prints (names, every
  capability, cancellations, extended capabilities by name).
- `TestHegelDatabase`: the same for random entries of the installed database.
- `TestHegelPrintf`: `Printf` of a compiled string with int parameters gives tput's output.

## Bugs

Six, see `bugs.toml`: `Decode` panics on an odd-length `acsc` (1); the parameter
interpreter keeps Go-typed values, so a number is never true for `%t`, `%!`, `%A`, `%O` and
a comparison prints as 0 (2), `%'c'` constants are 0 in arithmetic and `%c` of a number
writes NUL (3); an entry without `acsc` decodes with an empty one (4); `%:` followed
directly by the conversion swallows the following text (5); the canonical `acsc` keeps the
first mapping of a repeated key where ncurses' repair, which it cites, keeps the last (6).

## Modelled as recorded, not counted

- ncurses specifics the generators avoid or the property leaves out: `%i` increments at most
  once per evaluation in ncurses (the package increments at every `%i`); `%o`/`%x`/`%X` of a
  negative value print two's complement in C and `-N` in Go; `%c` of a non-zero multiple of
  256 truncates the C string; int32 overflow; `%#x` of zero and `%#0` (Go's `fmt` differs
  from C's printf); the `+` flag, which ncurses 6.4 does not implement after `%:`; `%s` and
  `%l`, which tput cannot be given; static variables (`%PA`), which persist across `Printf`
  calls but not across tput processes.
- tic rewrites `%{n}` with a printable n as `%'c'`, keeps `%^X` literal (the xor operator),
  drops a cancelled boolean, stores an extended number above 32767 as cancelled unless a
  standard number forces the 32-bit format, derives `acsc` from `box1`, and rejects
  aliases that are not filenames and names starting with `_`; infocmp prints the character
  after `%` and a backslash after a caret raw. The generators avoid these.
- `tput` evaluates a string only when it refers to a parameter, so the property appends
  `%p1%Pa` to strings without one.
