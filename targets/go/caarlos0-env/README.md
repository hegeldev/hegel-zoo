# caarlos0-env

[caarlos0/env](https://github.com/caarlos0/env) (v11) parses environment variables into
structs by tags: `env:"NAME,required,notEmpty,expand,file,unset,init"`, `envDefault`,
`envPrefix`, `envSeparator`, `envKeyValSeparator`, with `Options` for a custom environment,
prefix, tag names, `RequiredIfNoDef`, `UseFieldNameByDefault`, `SetDefaultsForZeroValuesOnly`,
`OnSet` and `FuncMap`; nested structs, pointers, slices, maps and slices of structs. The pin is
`fb64035` (2026-09-03, eight commits after `v11.4.1`).

The repository is MIT (LICENSE.md); there is no CONTRIBUTING.md, the README says nothing about
AI-written code, and there are no agent instructions. The zoo keeps its tests in its own patch
and files nothing upstream.

## Build

`go test -count=1 -run TestHegel -v .` in the module root. The patch adds, as the external
package `env_test`, `hegel_test.go` (harness, the `Known` switches), `hegel_model_test.go`
(the configuration struct and the model), `hegel_props_test.go` (generators and properties)
and `hegel_pins_test.go` (one plain test per bug), and requires `hegel.dev/go/hegel v0.6.33`
in go.mod (the `go` directive rises to 1.26). The properties never touch the process
environment; the `unset` pin uses a unique variable name, the expand-cycle pin re-runs the test
binary as a child process (a stack overflow is fatal).

## Oracle

The README's semantics, restated as a model over one fixed struct (`Config`, 31 fields:
string, every int width, float64, bool, `time.Duration`, `url.URL`, a `TextUnmarshaler`,
pointers, slices with separators, maps with both separators, `required`, `notEmpty`, `expand`,
defaults, an `init` pointer, a nested struct, an anonymous struct, a pointer to a struct, a
slice and a pointer to a slice of structs, an untagged field, an ignored field, an unexported
field). The model is driven by a hand-written table of the fields' tags: key = prefix +
tag (or the converted field name under `UseFieldNameByDefault`); a set-but-empty variable falls
back to `envDefault` (the README's caveat); `required` is satisfied by a default and fails on
an absent variable; `notEmpty` fails on an empty value after the default; `expand` resolves
names through the fields processed so far, then the environment, recursively; an empty value
sets nothing; `SetDefaultsForZeroValuesOnly` ignores a default for a non-zero field; scalars
parse with `strconv` at the type's width, `time.ParseDuration`, `url.Parse`; slices split on
the separator, maps on both; nested structs and `init` pointers recurse with their prefix; a
slice of structs is sized by the contiguous indices present (at least its initial length) and
untouched when no variable under its prefix exists. Errors are compared as a multiset of kinds
(`required:KEY`, `notEmpty:KEY`, `parse:Field`, `noParser:Field`) through the package's error
types; `OnSet` calls as the set of keys a value was set for.

Generators draw an environment over some fifty variable names (each field's key, nested and
indexed keys, a few extra names such as `PATH`, `HOST`, `SCHEME` and the nested fields' own
names) with values from per-type pools of valid, boundary and invalid strings and 10% empty;
options at random (prefix `APP_` or none, the three booleans); and an initial struct that is
zero or partly filled (scalars, pointers, maps, nested structs, one or two slice items).

## Method

| Property | Checks |
|---|---|
| ParseFollowsTheReadme | `ParseWithOptions` on a copy of the initial struct: every exported field equals the model's, the errors are the model's, `OnSet` fired for the fields set |
| FieldParamsFollowTheTags | `GetFieldParamsWithOptions` reports each keyed field's key, default and options as the tags say (nested and `init` fields included) |

Mismatches are classified before they count: a `Known` switch per recorded bug gates the input
shape (32-bit ints, non-zero fields under `SetDefaultsForZeroValuesOnly`, `url.URL` under
`UseFieldNameByDefault`, nested structs under `UseFieldNameByDefault` with `RequiredIfNoDef` or a
variable of their name, `OnSet` calls, pre-initialized `*[]struct`, parse errors on nil
pointers, parse errors inside slices of structs; the generator never builds an expansion
cycle); the pins assert the documented behaviour and fail while the bug exists. `ZOO_COLLECT=1`
records mismatches instead of failing and prints the class counts.

## Accepted differences

- `TextUnmarshaler` wins over a `FuncMap` entry for the same type; undocumented, not judged.
- `os.Expand` semantics for malformed references (`${A`, a trailing `$`, `$$`) are Go's; the
  model uses `os.Expand` too.
- Slice items must be indexed contiguously from 0 (`IT_0_`, `IT_1_`...); a gap ends the slice.
- Nested struct fields without `envPrefix` share the parent's namespace; the README says so.
- `file` is not exercised (it reads the filesystem).

## Bugs found

Eleven, in bugs.toml: `int`/`uint` parsed with a 32-bit range; `UseFieldNameByDefault` does not
separate a trailing uppercase letter; `SetDefaultsForZeroValuesOnly` ignores environment values
for non-zero fields; parser-handled struct types (`url.URL`) are recursed into, so under
`UseFieldNameByDefault` a URL's Path is replaced by `$PATH` and under `RequiredIfNoDef` its
fields are required; nested structs are processed as values under `UseFieldNameByDefault`;
`unset` unsets the process variable when the value came from `Options.Environment`; `OnSet`
fires when nothing is set; a pre-initialized `*[]struct` loses its items; a nil pointer is
allocated before a failing parse; an expansion cycle is a fatal stack overflow; a parse error in
one slice item discards all items and the other items' errors.

## History

- 2026-09-21 (turn 340): target added at fb64035 (v11.4.1+8) with two properties, 11 pins.
