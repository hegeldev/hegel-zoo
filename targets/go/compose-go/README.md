# go/compose-go

[compose-spec/compose-go](https://github.com/compose-spec/compose-go) is the reference Go
library for the Compose specification. This target covers its `template` package: the
interpolation of `${VAR}`, `${VAR:-default}`, `${VAR-default}`, `${VAR:?err}`, `${VAR?err}`,
`${VAR:+alt}`, `${VAR+alt}`, `$VAR`, `$$`, nested forms, and `ExtractVariables`, which lists
the variables a configuration uses. Pinned at `f18e211` (13 commits after v2.15.0,
2026-09-18, Apache-2.0; no AI policy in README, CONTRIBUTING, AGENTS.md — agent build
instructions — or `.github`).

## Build

The tests live in a new package directory `hegel/` of the upstream module; `go.mod` gains
`hegel.dev/go/hegel`. The run command is `go test -count=1 -run TestHegel -v ./hegel`.
`TestHegelBash` runs `bash` from `PATH` (present on CI's Ubuntu image).

## Oracle

A model of the specification's interpolation section (12-interpolation.md, plus the `:+`/`+`
forms Docker documents): a recursive parser of the bash-like syntax — a word extends to the
matching brace with nested `${...}` counted, `$$` is a literal dollar, a `$` followed by
anything else is preserved, `${` followed by anything but a name and an operator is an
invalid template — evaluated lazily (a default is expanded only when used, an error message
only when the variable is missing) with the first error in evaluation order reported.
Templates are generated as data — a list of one to six pieces (a literal run, `$$`, `$NAME`,
`${NAME}`, `${NAME op word}` with the word a nested list of pieces, to depth two, or one of
twelve invalid forms), a weighted choice with the literal run first so counterexamples shrink
towards plain text — and rendered to a string by a pure function that keeps a name character
after `$NAME` apart with a space; the model parses the rendered text. The mapping has set,
empty, unset and dollar-containing values; literal runs include braces, quotes, backslashes
and newlines, inside words too (bare braces are left out of words, since the specification
says nothing about them and bash and compose-go read them differently). Three variants of the one generator serve the
properties: everything, without the invalid forms (`ExtractVariables`), and without the
invalid forms and backslashes (bash). bash is the second oracle: on that last subset,
`printf '%s' "<template>"` with `$$` written `\$` must give the same string and fail exactly
when compose-go reports a required variable.

## Properties

- `TestHegelSubstitute`: `Substitute`/`SubstituteWithOptions` give the model's value, or the
  model's error class (invalid template; required variable with the same name and expanded
  message).
- `TestHegelBash`: on the shared subset, compose-go and bash agree.
- `TestHegelEscape`: doubling every `$` of any string makes a template that substitutes to
  that string.
- `TestHegelExtractVariables`: the variables reported for a configuration holding the
  template are the model's, required when any occurrence is, with the default and presence
  value of the first occurrence that defines them.
- One narrow property per recorded bug, drawing its shape region with random contents and
  judged by the same oracles: `TestHegelNewlineInWordSubstitutes` (a word with a newline in a
  literal run), `TestHegelMessageVariablesExtracted` (a `?` or `:?` message containing a
  reference to a name used nowhere else) and `TestHegelFirstDefaultOccurrenceKept` (two forms
  of one name with distinct defaults or presence values). Each fails every run.

The generators draw the recorded bugs' shapes by default: literal runs inside words include a
newline (about 10% of cases), `?` messages contain variables (17%), and a name may occur with
distinct defaults in one string (5%). So `TestHegelSubstitute` and `TestHegelBash` fail while
bug 1 is open (shrinking to `${A:-\n}`), and `TestHegelExtractVariables`, which reaches all
three, fails every run and is mapped to bug 2, the shape it shrinks to in most 100-case runs
(`${A:?$B}`; sometimes `${A:-\n}` or `${A:-1}${A:-2}`); a mismatch the model attributes to a
recorded bug names it in the failure. The pins are regression examples beside the properties.
`HEGEL_NO_KNOWN=1` switches the shapes off for a run that looks past the bugs: no newline in
words, literal-only `?` messages, the default kept among several distinct candidates not judged
(the shape is still drawn in 8% of cases, so it is skipped per name rather than assumed away);
every property then passes with nothing else discarded.

## Bugs

Three, see `bugs.toml`: a newline inside a default, alternative or message makes the
template invalid (1); `ExtractVariables` misses the variables used in a `?` message (2) and
keeps the last rather than the documented first default/presence value within one string,
with a map-order-dependent result across keys (3).

## Modelled as recorded, not counted

- A bare `{` inside a default counts as an opening brace for compose-go (`${U:-x{}y}` gives
  `x{}y`) but not for bash (`x{y}`); the specification is silent, so the generators avoid
  bare braces in words.
- `${A:x}` (bash substring expansion) and `${1}` are invalid templates; `$1`, `$ ` and a
  trailing `$` are preserved, as the specification says.
- Values are never re-expanded (`D="$X"` substitutes to `$X`), as in bash.
- The default and presence value of `${A:-}` is the empty string, indistinguishable from
  none in the `Variable` struct.
- `ExtractVariables` of an invalid template (`${U:?}a${`) also reports a variable with an
  empty name for the stray `${`; the property skips invalid templates, which `Substitute`
  rejects first.
- `Substitute` logs a warning for every unset variable; the tests silence logrus.

## History

- 2026-09-24: unsteered (STYLE.md rule 11): the known shapes are drawn by default, the three
  wide properties and three narrow ones are the expected failures, `HEGEL_NO_KNOWN=1` switches
  the shapes off; the `Known` struct is gone.
