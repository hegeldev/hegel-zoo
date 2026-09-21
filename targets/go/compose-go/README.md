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
Templates are generated as text over a mapping with set, empty, unset and dollar-containing
values, with literal runs including braces, quotes, backslashes and newlines outside words
(inside words bare braces are left out, since the specification says nothing about them and
bash and compose-go read them differently), one of twelve invalid forms now and then, and
nesting to depth two. bash is the second oracle: on templates without invalid forms or
backslashes, `printf '%s' "<template>"` with `$$` written `\$` must give the same string and
fail exactly when compose-go reports a required variable.

## Properties

- `TestHegelSubstitute`: `Substitute`/`SubstituteWithOptions` give the model's value, or the
  model's error class (invalid template; required variable with the same name and expanded
  message).
- `TestHegelBash`: on the shared subset, compose-go and bash agree.
- `TestHegelEscape`: doubling every `$` of any string makes a template that substitutes to
  that string.
- `TestHegelExtractVariables`: the variables reported for a configuration holding the
  template are the model's, required when any occurrence is, with the default and presence
  value when one occurrence defines them.

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
