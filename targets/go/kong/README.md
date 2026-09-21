# go/kong

[alecthomas/kong](https://github.com/alecthomas/kong) (v1.16.1 plus 9 commits, incl. the new
`lastwins` groups): a command-line parser driven by struct tags, with a hand-written
token scanner and tracer (`scanner.go`, `context.go`): long and short flags with values by
space or `=`, short-flag tails, aliases, negatable bools, `--`, flags inherited by
subcommands, subcommands with aliases, hidden and default commands, positional arguments,
slice and map values, counters, `required`, xor/and/lastwins groups, enums, passthrough.
Tested here: `Kong.Parse` over generated grammars and argument lists.

## Build

The patch adds `hegel.dev/go/hegel` to `go.mod` and a `hegel/` package of three
`hegel_zoo_*_test.go` files that drive the public API: a grammar struct type built with
`reflect.StructOf` from a generated spec (tags written as kong documents them), `kong.New`
with `NoDefaultHelp` and `Parse`, then `Context.Command()` and the struct's fields read back.
`go test -count=1 -run TestHegel -v ./hegel`

## Oracles

- A model of the command-line grammar as the README (Flags, Commands, Positional arguments,
  Slices, Maps, Pointers, Supported tags) and the doc comments describe it: a flag by its
  name, short or alias with one or two dashes, its value after a space or `=` (bool flags
  take one only after `=`), short-flag tails (`-abc`, `-nvalue`), `--no-x` and `--no-x=false`
  for negatable flags, `--` ending the parsing, a subcommand's flags plus its ancestors',
  subcommands by name or alias, positionals in declaration order (required first, a slice or
  map last taking the rest), slice values split at `,` (escapable) and appended across
  occurrences, map values `k=v;k=v`, counters incremented per occurrence or set with `=N`,
  defaults, `required`, xor (at most one), and (all or none), lastwins (the last occurrence
  wins, the others revert), enums, default commands (`default:"1"` at the end of the line,
  `withargs` also for unmatched arguments), passthrough commands and positionals (all and
  partial), the package's error messages incl. "did you mean" suggestions. The model
  reimplements this over the same spec; values are parsed with the same `strconv`/`time`
  calls.
- The result compared: the error text, or `Command()` and every field of the grammar struct
  (nil kept apart from empty for slices, maps and pointers).

## Properties

- `TestHegelRun`: a grammar of 1-3 levels (root, 0-3 subcommands, sub-subcommands), 0-3
  flags per command from 15 kinds (bool, negatable bool, string, int, int8, uint16, float64,
  duration, []string, []int, map[string]string, map[string]int, counter, *int, enum string)
  with shorts, aliases, `required`, `hidden`, defaults (mostly valid), xor/and/lastwins groups;
  1-3 positionals (string, int, int8, or a slice/map last, required or optional, sometimes
  passthrough), subcommands with aliases, hidden and default commands, passthrough commands;
  an argument list of up to 8 tokens, mostly a walk towards one command with its flags (all
  forms, values fit for the kind and not, combined short tokens, `-s=v`) and its positionals,
  with `--` and odd tokens (`-`, `-1`, `""`, unknown flags, whitespace) around; against the
  model.
- `TestHegelPin…`: one pin per recorded bug, asserting the documented behaviour (expected
  failures).

## Bugs

Six, recorded in `bugs.toml`: a short flag declared as a non-ASCII rune can never be given
(kong/1); a flag with a default counts as used in its xor group, so the other member cannot
be given (kong/2), and in its and group, so an empty command line fails (kong/3); `--` after
the first value of a cumulative positional ends it and the rest is rejected (kong/4); a
required flag alone in its xor or lastwins group is not required at all (kong/5); a counter
with a default increments from zero (kong/6).

## Modelled as recorded

kong/2 and kong/3 are in the model behind the `HZKnown` switch `defaultsCountInGroups`,
kong/4 behind `dashDashStopsCumulative`, kong/5 behind `requiredChoiceMemberOptional`, kong/6
behind `counterIgnoresDefault`; `ZOO_KNOWN_OFF=name` turns a switch off and the property then
fails. kong/1 is not reached (the generated shorts are ASCII).

Design notes the model follows (undocumented, taken from the code):

- A short-flag token is split by bytes: `-s=v` gives the string flag `s` the value `=v`, an
  int flag fails on `"=5"`, a bool flag `-b=true` fails with "unknown flag -=".
- A value-taking flag rejects a following token that looks like a flag (`--s --t`: "expected
  string value but got "--t" (long flag); perhaps try --s="--t"?") but takes `-` and `--x=v`'s
  value; a missing value reads `expected string value but got "EOL" (<EOL>)`.
- A slice flag's value is one token split at `,`: `--l a,-b` fails on `-b` while `--l=a,-b`
  is fine (the pieces keep the token's type); `a,` drops the empty tail while `,a` keeps the
  empty head; the first given value replaces the default, later ones append.
- Integers parse with base 0 (`0x10`, `1_0`); a bool value is `true/1/yes/false/0/no`,
  case-insensitively; a negated flag's `=value` is inverted.
- A subcommand named right after `--` is dispatched; a command alias equal to a sibling's name
  is ignored, an alias shared by two commands goes to the first; hidden commands are matched
  but not suggested; suggestions are the candidates with the token as prefix or within
  Levenshtein distance 2, hidden flags included.
- `required` flags of the root are checked before the subcommand's; a required flag with a
  default is never missing; an and group with one required member makes all its members
  required; a default command's flags are checked even when it was selected implicitly.
- Enum defaults are checked at parse time ("--e must be one of "a","b" but got "c""); a
  default that fails to parse is an error only when its command is on the selected path.

## Not tested

Help output and the help flag, env vars, resolvers and configuration files, hooks and
`Run()`, branching positional arguments (`arg` structs), embedded structs and prefixes,
plugins and dynamic commands, variable interpolation, `time.Time`, `*os.File`, `*url.URL`,
the path/file named mappers, custom mappers, `Validate()`, `AllowHyphenPrefixedParameters`.

## History

- 2026-09-21: new target, one property, 6 bugs.
