# pflag

[spf13/pflag](https://github.com/spf13/pflag) is the POSIX/GNU-style command-line flag
package behind cobra: a drop-in replacement for the standard library's `flag` with `--long`
options, one-letter shorthands that bundle (`-abc`, `-n1234`, `-abcs hello`), no-option
defaults (`--flag` with `NoOptDefVal`), interspersed positional arguments, `--` as the
terminator, thirty-odd typed values (slices, maps, IPs, durations, times, bytes) with
`FlagSet.GetX` accessors, name normalisation, deprecation and hidden flags, and a usage
printer that wraps to a column width. About 6 000 lines plus example-based tests per value
type; the pinned commit is the September 2026 head, v1.0.10 plus one wrapping fix.
BSD-3-Clause. No CONTRIBUTING or AI policy in the repository; not archived. Checked
2026-09-15.

## Oracle

Four, by property. (1) The standard library's `flag` package on the syntax the two share:
`--name`, `--name=value`, `--name value`, `--bool`, `--`, positionals after the flags, with
`bool/int/int64/uint/uint64/float64/string/duration` flags and identical defaults; pflag runs
with `SetInterspersed(false)` so both stop at the first non-flag. (2) A model of the README's
"Command line flag syntax" section plus the doc comments of the unknown-flag handling modes
(`IgnoreUnknownFlag`, `PassUnknownFlagToArgs`): long options, shorthand bundles where every
letter but the last must take no argument, `-f=arg`/`-farg`/`-f arg`, no-option defaults for
bools, counts and flags with `NoOptDefVal`, `--help`/`-h`, `--` and `ArgsLenAtDash`, and the
typed error classes (`NotExistError`, `ValueRequiredError`, `InvalidValueError`,
`InvalidSyntaxError`). (3) The parsers behind each typed value (`strconv`, `time`, `net`,
`encoding/csv`, `encoding/hex`, `encoding/base64`) for the value a flag should hold, and the
flag's own bound variable for what its `GetX` accessor should return. (4) The documented
usage layout: `  -s, --name type   usage (default X)`, words preserved, no line wider than the
column count unless it is one word, greedy filling, and `(default …)` only for non-zero
defaults.

## Properties

- `TestHegelSharedSyntaxAgreesWithStdlibFlag` — 1–5 flags of the eight shared kinds, random
  command lines in the shared syntax (including bad values, unknown flags and `--help`): a
  plain pflag `FlagSet`, one built with `AddGoFlagSet` and a `flag.FlagSet` filled by
  `CopyToGoFlagSet` all agree with `flag` on success/failure, `ErrHelp`, every value, `Args()`,
  `NFlag()` and the flags `Visit` sees. Clean over 60 000 cases — pflag really is a drop-in.
- `TestHegelParseFollowsTheDocumentedGrammar` — 1–5 flags of eight kinds (bool, count, string,
  int, stringSlice, stringArray, string and int with `NoOptDefVal`) with optional shorthands,
  interspersed on or off, the three unknown-flag modes, command lines of long options,
  bundles, positionals, unknown flags, `--help`, syntax errors and `--`: the error class,
  `Args()`, `ArgsLenAtDash()`, every value, `Changed()` and `NFlag()` equal the model's.
- `TestHegelTypedValuesRoundTripThroughGet` — one flag of one of 23 kinds, 0–3 occurrences with
  valid text: the bound variable equals the parsers' value (last wins for scalars, append for
  slices, merge for maps, `+1` for counts), the `GetX` accessor equals the bound variable, and
  for scalars `Set(Value.String())` on a fresh flag reproduces the value. Lands on pflag/3 (an
  `ipMask`/`ipNet` flag left at its nil default, 2 % of cases; pflag/2 and /1 at 1.3 % and
  0.4 %; intermittent at 100 cases).
- `TestHegelUsageFollowsTheDocumentedLayout` — 1–4 flags of 14 kinds with zero or non-zero
  defaults, random ASCII usage text with backquoted names, `cols` 0 or 10–120: one entry per
  flag with the README's column, the words of `UnquoteUsage` plus `(default X)` iff the default
  is non-zero, no line wider than `cols` unless it is a single word, greedy filling (`wrap`'s
  five-column slop and its 16-column fallback modelled), and `Value.String()` stable across
  calls. Lands on pflag/4 (an empty collection default shown as `(default [])`, a third of the
  cases; pflag/5 and /7 are in its region too).
- `TestHegelNormalizedNamesAreInterchangeable` — a normaliser folding `_`/`.`/case to `-`
  installed before or after the flags are defined, flags defined and used under random
  spellings: parse results, `Lookup`, `Changed`, `Args` and `FlagUsages` equal the canonical
  spelling's.

## Known bugs

The generators draw the shape of every recorded bug (STYLE.md rule 11): the two wide properties
above are expected failures mapped to the bug they land on, and each bug has a narrow property
over its own shape region in `hegel_shapes_test.go`, the deterministic expected failure beside
the pin: `TestHegelGetStringArrayReturnsTheBoundElements` (pflag/1),
`TestHegelGetFloat64SliceKeepsEveryDigit` (/2), `TestHegelGetMaskAndNetReturnTheDefault` (/3),
`TestHegelEmptyCollectionDefaultsAreNotShown` (/4), `TestHegelUsageWrapsByColumnWidth` (/5),
`TestHegelStringToStringSinglePairKeepsItsValue` (/6) and `TestHegelStringToIntDefaultTextIsSorted`
(/7). `HEGEL_NO_KNOWN=1` (read once) switches the shapes off: `stringSlice`/`stringArray` texts
contain no lone empty element or CR, `float64Slice` texts are values `%f` renders exactly, the
accessor check is skipped by name on an `ipMask`/`ipNet` flag left at its nil default, the usage
property gives `boolSlice`/`durationSlice`/`stringToString` flags a non-empty default and ASCII
usage text, map values carry no quotes and only `stringToString` (which sorts) appears with a
multi-key default; every property then passes at 1000 cases with no skips. The pflag/7 shape
(a map default rendered in Go's map order) made a case's verdict random, which Hegel's final
replay could pass and so swallow the counterexample; the usage property's stability check makes
it deterministic. In ignore-unknown mode a bundle gets glued text only after a letter that
consumes it: an unknown shorthand followed by more letters strips (or not) the next argument by
rules the README does not state.

## Bugs

| id | severity | title |
|----|----------|-------|
| pflag/1 | low | `GetStringArray` re-parses the CSV rendering and loses an empty element or a CR |
| pflag/2 | medium | `GetFloat64Slice` rounds every element to six decimals |
| pflag/3 | low | `GetIPv4Mask`/`GetIPNet` fail on a flag left at its nil default |
| pflag/4 | low | Usage shows `(default [])` for empty boolSlice, durationSlice, float64Slice, ipSlice and map flags |
| pflag/5 | low | `FlagUsagesWrapped` counts bytes, not columns |
| pflag/6 | low | A single `key="value"` pair keeps its opening quote |
| pflag/7 | low | `stringToInt`/`stringToInt64` render in map order, so `DefValue` changes between runs |

## Not bugs

- `-sb` where `s` is a string flag sets `s` to `b`: the README says every shorthand but the last
  must take no argument.
- `--flag value` for a flag with `NoOptDefVal` sets the default and leaves `value` positional
  (README table).
- `--unknown arg` in `IgnoreUnknownFlag` mode drops `arg` (the flag might have taken it); the
  doc comment says so. `-x arg` behaves the same, but `-xc arg` with a known `c` keeps `arg`
  — a quirk of re-reading the original argument list per letter, not documented either way.
- A `stringSlice` element written as `"a\r\nb"` comes back as `a\nb`: that is `encoding/csv`'s
  documented treatment of a quoted CRLF, and a string *slice* is CSV by contract.
- `-test.v`-style shorthands are silently skipped (README, "Using pflag with go test").
- pflag's `int` accepts `1_000` and `0b101`, and so does `flag` (both use base 0).
