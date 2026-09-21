# go/cli

[urfave/cli](https://github.com/urfave/cli) v3 (v3.13.0): the most used Go command-line
framework (23k stars), with a hand-written argument parser (`command_parse.go`): flags with
values by space or `=`, bool flags, aliases, single- and double-dash forms, `--`, combined
short options (`UseShortOptionHandling`), persistent and `Local` flags, subcommands with
aliases, slice and map flags, `OnlyOnce`, `Required`, mutually exclusive groups,
`StopOnNthArg`, and typed positional `Arguments`. Tested here: `Command.Run` over generated
command trees and argument lists.

## Build

The patch adds `hegel.dev/go/hegel` to `go.mod` and a `hegel/` package of three
`hegel_zoo_*_test.go` files that drive the public API (a `cli.Command` tree built from a
spec, `Run` with the help hidden and `OnUsageError` returning the error, Actions recording
what ran). `go test -count=1 -run TestHegel -v ./hegel`

## Oracles

- A model of the command-line grammar as `docs/v3/examples/flags/*.md`,
  `arguments/advanced.md`, `subcommands/basics.md` and the doc comments of `Command` and
  `FlagBase` describe it: a flag by any of its names with one or two dashes, its value after
  a space or `=` (bool flags take no value unless `=`), last value wins, slice flags append
  (values split at `,`), map flags take `key=value` items, `OnlyOnce` makes a repetition an
  error, `--` ends the parsing, `StopOnNthArg` stops it after N positionals, the first
  positional that names a subcommand hands the rest to it, a subcommand sees its own flags and
  its ancestors' non-`Local` flags (unless it defines the same name), combined short options
  are several bool letters with the last letter allowed a value, an unknown flag or a missing
  value is an error with the package's message, mutually exclusive groups are checked at each
  command on the way down and `Required` flags at the command that runs, typed arguments
  consume positionals in declaration order (single ones optional unless `Required`, multi
  ones between `Min` and `Max`), the rest is `Args()`. The model reimplements this over the
  same spec as the real tree; values are parsed with the same `strconv`/`time` calls.
- The result compared: the command that ran, its `Args()` and typed argument values, and for
  every flag of the tree its `Get()`, `IsSet()` and `Count()`; or the error text.

## Properties

- `TestHegelRun`: a tree of 1-3 levels (root, 0-3 subcommands, sub-subcommands), 0-4 flags per
  command from 11 kinds (bool, string, int, int8, uint16, float, duration, string slice, int
  slice, string map, `BoolWithInverseFlag`) with aliases, `Local`, `OnlyOnce`, `Required`
  and defaults, mutually exclusive groups, `Arguments`, `UseShortOptionHandling` and
  `StopOnNthArg`; an argument list of up to 8 tokens, mostly a walk towards one command with
  its flags (long and short forms, `=` values, combined short tokens, values fit for the kind
  and not) and odd tokens (`-`, `--`, `-1`, `""`, unknown flags, whitespace) around the
  command names; against the model.
- `TestHegelPin…`: one pin per recorded bug, asserting the documented behaviour (expected
  failures).

## Bugs

Eight, recorded in `bugs.toml`: a lone `-` ends the parsing and drops every argument after it
(cli/1); in a combined short token a value-taking flag that is not last is silently ignored
(cli/2); a `BoolWithInverseFlag` in a combined short token is set to false (cli/3); a parent's
`Local` flag is set from a subcommand through its short form (cli/4); a subcommand named right
after `--` is dispatched and the rest parsed as its flags (cli/5); a subcommand name that is
not the first positional stops the parsing but is not run (cli/6); two forms of one flag are
documented as an error but accepted (cli/7); `BoolWithInverseFlag.Get` panics before a run
(cli/8).

## Modelled as recorded

cli/1, cli/3, cli/4, cli/5 and cli/6 are in the model behind `HZKnown` switches
(`dashDropsRest`, `combinedInverseSetsFalse`, `combinedShortsSeeLocalFlags`,
`dashDashDispatches`, `commandNameStopsParsing`); cli/8 behind `inverseGetPanics` (the state
reader reports the default); `ZOO_KNOWN_OFF=name` turns a switch off and the property then
fails. cli/2 is modelled as the code does (the letter dropped) and counted; cli/7 is a
documentation mismatch the model follows the code on.

Design notes the model follows (undocumented, taken from the code):

- A token whose first character after a single dash is not a letter (`-1`, `-.5`) is not a
  flag: it and everything after it are positional.
- Arguments are classified after `strings.TrimSpace` (`" --lang"` is the flag), but positional
  arguments and `=` values keep their whitespace; an argument that is only whitespace is
  positional.
- Integer flags parse with base 0 (`0x10`, `010`, `1_0` accepted); int slice elements are
  trimmed, string slice elements are not; a slice flag's first value replaces the default.
- A value-taking flag takes the next argument whatever it is (`--lang --verbose` sets lang to
  `--verbose`); `--flag=` sets the empty string.
- `--no-x=false` sets an inverse flag to false; setting both forms is an error; the required
  check counts an inverse flag whose Set failed as set.
- `Required` flags of every command on the path are checked at the innermost command (after
  the mutually exclusive groups of each level, before the arguments); the message quotes the
  names of one command joined by `, `.
- Only `ArgumentBase` arguments count as required in the positional precheck (index against
  the number of positionals); `Args` with `Max: 0` or `Min > Max` are errors at parse time.

## Not tested

Help and version output, shell completion, `DefaultCommand`, `PrefixMatchCommands` and
suggestions, `ReadArgsFromStdin`, value sources (env, files, maps), flag `Action`/`Validator`,
`Before`/`After`, timestamp flags and arguments, `AllowExtFlags`, `SkipFlagParsing`.

## History

- 2026-09-21: new target, one property, 8 bugs.
