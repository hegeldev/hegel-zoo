# go/cobra

[spf13/cobra](https://github.com/spf13/cobra) (main after v1.10.2): the most used Go
command-line framework (40k stars; kubectl, hugo, docker, gh), with pflag for the flags and
its own hand-written dispatch (`command.go`): `Find` walks from the root to the command named
by the first positional argument, skipping the flags and their values (`stripFlags`,
`argsMinusFirstX`); with `TraverseChildren`, `Traverse` parses each parent's flags on the way;
prefix and case-insensitive matching (`EnablePrefixMatching`, `EnableCaseInsensitive`),
aliases, the automatic `help` command and `--help`/`--version` flags, the `Args` validators
(`args.go`), required flags, flag groups (`flag_groups.go`), suggestions and the Run hooks.
Tested here: `Command.ExecuteC` over generated command trees and argument lists.

## Build

The patch adds `hegel.dev/go/hegel` to `go.mod` and a `hegel/` package of three
`hegel_zoo_*_test.go` files that drive the public API (a `cobra.Command` tree built from a
spec, `ExecuteC` with `SilenceErrors`/`SilenceUsage`, the output writers on buffers, the help
and usage functions replaced by recorders, the default completion command disabled).
`go test -count=1 -run TestHegel -v ./hegel`

## Oracles

- A model of the command-line grammar as the user guide ("Working with Flags", "Positional
  and Custom Arguments", "PreRun and PostRun Hooks", "Suggestions"), the doc comments of
  `Command`, `args.go` and `flag_groups.go` describe it, and pflag's grammar for the flags
  themselves (`--flag value`, `--flag=value`, `-f value`, `-fvalue`, `-f=value`, combined
  short letters with the last one taking a value, bool and count flags taking none, `--`,
  interspersed positionals, pflag's error texts): the first positional argument names the
  subcommand and the walk goes on from there (or, with `TraverseChildren`, the parents' flags
  are parsed on the way); exact names and aliases first (case-insensitively with
  `EnableCaseInsensitive`), then a unique prefix with `EnablePrefixMatching`; a root with
  subcommands and no `Args` rejects a positional argument as an unknown command, with the
  suggestions within Levenshtein distance 2 (or `SuggestionsMinimumDistance`), by prefix or
  `SuggestFor`; the final command parses its own, its persistent and its ancestors' persistent
  flags plus `--help`/`-h` (and `--version`/`-v` when `Version` is set); help wins over
  everything after a successful parse, a non-runnable command shows its help; then `Args`,
  the persistent pre-run hooks (the nearest one, or all of them with
  `EnableTraverseRunHooks`), `PreRun`, the required flags, the flag groups (each enforced
  where every flag of the group is defined; required-together, then one-required, then
  mutually exclusive), `Run`/`RunE`, `PostRun`, the persistent post-run hooks; the `help`
  command finds its topic from the root. Values are parsed with the same `strconv` calls.
- The result compared: the command `ExecuteC` returns, the error text, the ordered log of
  hooks (with the positional arguments, `CalledAs` and `ArgsLenAtDash` at `Run`), the help
  and usage requests, the output (deprecation and version messages, unknown help topics), and
  for a run without error the value and `Changed` of every flag the command sees.

## Properties

- `TestHegelExecute`: a tree of 1-3 levels (root, 0-3 subcommands, 0-2 sub-subcommands) with
  aliases, `SuggestFor`, hidden and deprecated commands, `Run`/`RunE` (some failing), the four
  hooks in their plain, `E` and failing forms, 0-3 flags per command from six kinds (bool,
  string, int, count, string slice, string array) with shorthands, persistent or local,
  some required, flag groups of the three kinds over the flags a command sees, an `Args`
  validator from the documented ones (and two `MatchAll` combinations) with `ValidArgs`,
  `Version` on the root, `DisableSuggestions`/`SuggestionsMinimumDistance`, and the four
  global options; an argument list of up to 12 tokens, mostly a walk towards one command with
  flags around the names (long and short forms, `=` values, attached values, combined short
  tokens, fit values and not) and odd tokens (`-`, `--`, `""`, `-1`, `---x`, `--=x`, unknown
  flags, `--help`, `-hv`), prefixes, case variants and typos of the names, `help` topics; and
  dedicated shapes for the corners (a combined short token with a value before a command
  name, `--` before a command name, a valid argument then a typo, an empty argument, a help
  flag before a command name, the `help` command, a case variant of a prefix, a `SuggestFor`
  word); against the model.
- `TestHegelPin…`: one pin per recorded bug, asserting the documented behaviour (expected
  failures).

## Bugs

Ten, recorded in `bugs.toml`: the dispatcher does not see that the last letter of a combined
short token takes the next argument, so `root -af x sub` is an unknown command (cobra/1);
with `TraverseChildren`, `--` is taken for a flag with a value and `root -- x sub` runs sub
without x (cobra/2); with `TraverseChildren` a root with subcommands accepts an unknown
command as an argument (cobra/3); `OnlyValidArgs` computes its suggestions for the first
argument (cobra/4); with prefix matching and `TraverseChildren` an empty argument dispatches
a command's only subcommand (cobra/5); with `TraverseChildren` a help flag on a parent
followed by an argument and a command name is the error `pflag: help requested` (cobra/6);
the `help` command is refused when a required persistent flag or a flag group of the root is
not satisfied (cobra/7); the dispatcher takes the argument after `--help`/`-h`/`--version`/`-v`
for the flag's value, so `root --help sub child` is an unknown command (cobra/8); prefix
matching ignores `EnableCaseInsensitive` (cobra/9); a command matched by distance and by
`SuggestFor` is suggested twice (cobra/10).

## Modelled as recorded

All ten are in the model behind `HZKnown` switches (`combinedShortKeepsValue`,
`traverseDashDashValue`, `traverseSkipsUnknownCheck`, `validArgsSuggestFirst`,
`emptyPrefixDispatch`, `traverseHelpFlagError`, `helpCommandChecksFlags`,
`helpFlagSwallowsNext`, `prefixCaseSensitive`, `duplicateSuggestions`); `ZOO_KNOWN_OFF=name`
turns a switch off and the property then fails.

Design notes the model follows (undocumented, taken from the code):

- The dispatcher assumes an unknown `--flag` or `-x` takes the next argument as its value
  (`root --unknown sub` runs root and fails on the flag); a bool or count flag it knows does
  not. A lone `-` names no command: `Find` skips it and goes on (`root - sub` runs sub with
  `-`), `Traverse` stops at it (`root - sub` runs root with `- sub`).
- A parent's local flag before the subcommand name is an unknown flag for the subcommand
  (`root --local x sub`: `unknown flag: --local` from sub); the user guide says such flags are
  "ignored".
- The `help` command runs the root's persistent pre- and post-run hooks like any subcommand;
  `root help --bogus` is an unknown-flag error, `root help extra` (extra names no command) is
  "Unknown help topic" with the root's usage.
- Flag groups are annotations on the flags, so a group marked on a subcommand over persistent
  flags of the root is also enforced on the root and on every other command that sees all of
  them (the user guide: "only enforced on commands where every flag is defined").
- `PreRun` runs before the required flags and flag groups are checked; a deprecation message
  is printed before the flags are parsed; the version flag is honoured before the runnable
  check, so a non-runnable root with `Version` prints it.

## Not tested

Shell completion (`__complete`, `ValidArgsFunction`, `RegisterFlagCompletionFunc`, the
completion command), help and usage text, `DisableFlagParsing`, `FParseErrWhitelist`,
`SetGlobalNormalizationFunc`, a subcommand's flag shadowing a parent's persistent flag,
`Command.Context`, `OnInitialize`/`OnFinalize`, documentation generation.

## History

- 2026-09-22: new target, one property, 10 bugs.
