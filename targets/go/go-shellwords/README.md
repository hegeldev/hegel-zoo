# go-shellwords

[mattn/go-shellwords](https://github.com/mattn/go-shellwords) splits a command line into words
the way a shell does — quotes, backslash escapes, comments — with optional `$NAME`/`${NAME}`
expansion (`ParseEnv`, through `Getenv`), optional backtick and `$(…)` command substitution
(`ParseBacktick`, run through `$SHELL -c` in `Dir`), a `Position` that reports where an
unquoted `;`, `&`, `|`, `<` or `>` stopped the parse, `SetExcludeSeparators` to make chosen
runes ordinary, and `ParseWithEnvs` to peel leading `NAME=value` words off. It is a port of
Perl's `Parse::CommandLine` and is used by many Go tools that take a "command" string from a
config file. Pinned at f40666a (v1.0.15, 2026-09-12), MIT, no AI policy.

## Oracle

bash, held open per case: the line is evaluated as the body of an array assignment,
`a=( <line> )`, with `set -f` (no globbing) and `set +B` (no brace expansion), and the elements
are printed NUL-separated behind an explicit count (an empty array and a single empty word
print the same NUL sequence otherwise). Variables reach bash through the environment and
go-shellwords through a `Getenv` map with the same contents; substitution commands are POSIX
`printf`/`echo`/`true` so `$SHELL` does not matter. The generators stay inside the grammar the
two implementations share (see "Not bugs" for what is left out, and the bug notes for what is
kept out because it is pinned).

## Properties

- `TestHegelParseAgreesWithBash` — lines of 0–6 words made of bare text (ASCII, `-_./:=@%^+,{}*?!`,
  non-ASCII letters, an emoji), backslash escapes, single- and double-quoted pieces (with
  `\"`, `\\`, `\$`, `` \` `` inside double quotes), blanks/tabs/newlines, comments
  (`ParseComment`), unquoted, braced, double-quoted and escaped expansions of set, empty and
  unset variables whose values include blanks (`ParseEnv`), and backtick/`$(…)` substitutions
  glued to text (`ParseBacktick`) give exactly bash's words with `Position == -1`;
  `ParseWithEnvs` on the same line returns the same words.
- `TestHegelQuotedWordsRoundTrip` — arbitrary words (every rune but NUL) single-quoted, and
  words double-quoted with the four special characters escaped, come back unchanged from both
  parsers.
- `TestHegelPositionMarksTheFirstMetacharacter` — a prefix from the grammar above followed by
  `;`, `&`, `|`, `<`, `>`, `&&`, `||`, `>>`, `>&`, `|&`… and an arbitrary (even unparseable)
  tail gives the prefix's words, and `Position` is the rune index of the metacharacter — or of
  the bare digits before `>` (`2>x` drops the `2` and points at it).
- `TestHegelParseWithEnvsSplitsLeadingAssignments` — the leading run of `NAME=value` words
  (NAME an ASCII identifier; quoted `'a=b'` counts, `=x`, `1a=b`, `a-b=c`, `é=1` do not) goes
  to envs, the rest to args, both non-nil.
- `TestHegelExcludedSeparatorsAreOrdinaryCharacters` — with `SetExcludeSeparators(S)` for S
  drawn from blanks, newline, metacharacters, quotes, `#`, parentheses and backtick, parsing
  equals parsing the line with each excluded rune replaced by a private-use rune and mapped
  back (words, error, `Position`); `ExcludedSeparators()` returns S.

All general properties pass at 1000 cases × 3 (a few seconds per run, bash dominated). Six
pinned expected failures.

## Bugs (6)

| id | title | severity |
|----|-------|----------|
| go-shellwords/1 | ParseEnv expands and un-escapes after quote removal: `'$FOO'` is expanded, `$FOO"x"` reads `$FOOx` | medium |
| go-shellwords/2 | ParseEnv re-parses expanded words as command lines: metacharacters in a value truncate the line, quoted blanks split, `(` errors | medium |
| go-shellwords/3 | ParseBacktick leaves command substitutions inside double quotes as literal text | low |
| go-shellwords/4 | ParseBacktick keeps a substitution's output as one word, whatever whitespace it contains | low |
| go-shellwords/5 | ParseEnv variable names accept any Unicode letter or digit, so `$é` disappears | low |
| go-shellwords/6 | ParseBacktick rejects `\\$(cmd)`: the escaped-dollar check reads the buffer after un-escaping | low |

/1 and /2 are two faces of one design: expansion runs on the finished token (quotes and
escapes already gone) and its result is re-tokenised. Upstream's tests assert two consequences
(`"echo \\$FOO"` → `echo $FOO`; a value containing an unmatched quote is a parse error), so a
fix has to keep those; the pins use the cases no test covers. /6 is the same "look at the
buffer instead of remembering the escape" pattern in the substitution code. /1, /2 and /6 came
out of the differential property at 1000 cases (three separate generator restrictions were
needed before the property held); /3–/5 from the hand probe that preceded it.

## Not bugs (documented, asserted upstream, or Perl heritage)

- `\t` and `\n` are tab and newline escapes even unquoted or inside double quotes (asserted by
  upstream's `sh -c "printf 'Hello\tworld\n'"` case); a backslash inside double quotes escapes
  any character (`"a\b"` → `ab`, a shell keeps the backslash); `\r` is whitespace (a shell
  treats it as a word character); a backslash before a newline gives a newline in the word (a
  shell's line continuation deletes both); a trailing backslash is an error. All kept out of
  the generators.
- Unquoted expansions are re-parsed as shell syntax on purpose to the extent that
  `TestEnvArgumentsFail` asserts: FOO=`bar '` makes `$FOO` fail. (/2 covers the untested
  consequences.)
- `${FOO` (unterminated brace) is left literal; `$` followed by a non-name character is
  literal (`$@x`, `$#`, `$?`, `$1`: there are no special or positional parameters); `${}`
  expands to nothing. Special parameters are kept out of the generators.
- Nested `$(…)` inside `$(…)` is "invalid command line string"; `$(printf ')')` fails because
  the scan for the closing `)` does not respect quotes inside the substitution (the backtick
  form works); a substituted command exiting non-zero (`` `false` ``) fails the parse where a
  shell ignores the status. Limitations, not recorded; the generator uses successful commands
  without `)` in the `$(…)` form.
- Metacharacters `;&|<>` end the parse rather than erroring (the documented `Position`
  protocol); an all-digit *quoted* word before `>` (`"2">x`) is dropped like a bare fd number,
  and `Position` then points inside the quotes. Left unrecorded; the generator uses bare digits.
- `#` starts a comment only with `ParseComment` and only at the start of a word (`a#b`, `''#c`
  are words, as in a shell).
- Under `ParseBacktick` the command runs through `$SHELL -c` (default `/bin/sh`); the tests
  only use POSIX commands, and `Dir` is not exercised.
- `Position` is 0 for a metacharacter at index 0 and -1 for none; upstream's own
  `TestHaveMore` compares it with 0, which is its problem to have.

## Conventions

External test package with a dot import; `HEGEL_TEST_CASES` via `hegelOpts`; `property()`
turns panics into test-case failures. Upstream's `shellwords_test.go` fails `go vet` under Go
1.26 (non-constant format strings), so the run command uses `-vet=off`.
