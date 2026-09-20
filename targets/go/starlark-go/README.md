# starlark-go

[google/starlark-go](https://github.com/google/starlark-go), the Go implementation of Starlark
(`go.starlark.net/starlark`), against Python 3: generated programs in the subset of Starlark that is
also Python, with the same meaning by the Starlark specification, run in both and must print the same
lines and fail or succeed alike.

## What is tested

**`hegel/hegel_props_test.go`** (needs `python3`, 3.11 or later)
- `TestHegelMatchesPython`: a generated program (typed variables of int, str, bool, list, dict and
  tuple types; arithmetic, bitwise and comparison operators with minimal parentheses by the shared
  precedence table; string methods, `%`-formatting and `str.format`; list and dict methods; slices;
  comprehensions; `if`/`elif`/`else`, `for` over ranges, lists, dicts, `enumerate`, `zip` and `items`,
  bounded `while`, `break`/`continue`; functions with defaults and keyword calls; tuple unpacking;
  `print`) runs in starlark-go (`starlark.ExecFileOptions` with `TopLevelControl`, `GlobalReassign`
  and `While`, a step limit, `Print` captured) and in python3 (`hegel/oracle.py`, one JSON line each
  way, `print`/`str`/`repr` replaced by versions spelling values the Starlark way: double-quoted
  strings, Go-style escapes). Judged: same status (ok, error, static error) and the same printed
  lines up to the end or the error. Error messages are not compared.
- `TestHegelOracle`: the oracle is there and spells a sample the Starlark way.

**`hegel/hegel_pins_test.go`**: one deterministic reproducer per recorded bug.

## Oracles

python3 (3.12 here and on CI), through `hegel/oracle.py`. Python is not a Starlark reference: the
generator stays inside the subset where the two agree by design, and the following deliberate
Starlark differences are kept out of the programs (documented in `doc/spec.md`):

- bools are not numbers (`True + 1`, `1 == True`, bools as dict keys next to ints);
- no chained comparisons (`a < b < c`), no chained assignment, no `**`, no `lambda`, `set`, `del`,
  slice assignment, `while` only under the option, no recursion;
- strings are not iterable and index bytes: only ASCII strings are generated;
- a dict literal with two equal keys is an error (Python keeps the last): literal keys are distinct;
- `int()` rejects surrounding spaces and underscores; shift counts are limited to 511;
- indexes and slice bounds must fit a machine int (Python clamps): computed indexes are reduced;
- `"".find("", 5)`, `startswith("", 1, 0)`: Python finds no empty substring in an empty or inverted
  range, Starlark does (as in the slice `S[start:end]`): ranged searches use a non-empty literal;
- `splitlines` splits on `\n` only; `\x1c`-`\x1f` are whitespace for Python only: `chr()` and the
  string pool avoid those characters;
- `%`-formatting with widths, flags or precision and `str.format` specifiers are unsupported;
  `%s`/`{}` take only scalars (a container would need Python's repr);
- mutating a list while iterating it is an error in Starlark, tolerated by Python: loops over a
  variable make no mutations, loops over an expression iterate a copy, functions mutate nothing;
- Python's C-sized limits (`"" * (1 << 70)`, `len(range(1 << 70))`) are counted, not judged.

## Known bugs (gated)

Two bugs (`bugs.toml`): a negative repeat count below -2**31 is an error (spec: like zero; the gate
is on the error message, and repeat counts are now kept small anyway, since a 64-bit count times a
list is minutes of work in Python), and `strip`/`lstrip`/`rstrip` with an empty cutset strip
whitespace (the generator gives them non-empty literal cutsets while the bug is open).

## Not tested

Floats (formatting differs by design), `set`, `lambda`, `hash`, `type`, `getattr`, `load`, freezing,
the `starlarkstruct`, `starlarkjson` and `lib` packages, `syntax` and `resolve` as APIs, error
messages, non-ASCII strings.

## History

- 2026-09-20: written against 89a6a09411d5c7a33409dc050c2fecdf8f4eca8f (2026-09-08, "Add
  Struct.Entries (#658)") with hegel.dev/go/hegel v0.6.33; 2 bugs.
