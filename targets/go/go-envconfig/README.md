# go-envconfig

[sethvargo/go-envconfig](https://github.com/sethvargo/go-envconfig) populates struct fields from
environment variables (or any `Lookuper`) by `env` tags: `env:"KEY,required,default=...,
prefix=...,overwrite,delimiter=...,separator=...,noinit,decodeunset"`, with a `Config` of
defaults for every option, `Mutators` as middleware on the looked-up values, and decoders
(`Decoder`, `TextUnmarshaler`, `BinaryUnmarshaler`, `json.Unmarshaler`, `GobDecoder`, the
package's `Base64Bytes` and `HexBytes`). The pin is `c883e6f` (2026-07-19, v1.4.3).

The repository is Apache-2.0; `.github/CONTRIBUTING.md` asks for pull-request review only, the
README says nothing about AI-written code, and there are no agent instructions. The zoo keeps its
tests in its own patch and files nothing upstream.

## Build

`go test -count=1 -run TestHegel -v .` in the module root. The patch adds, as the external
package `envconfig_test`, `hegel_test.go` (harness, the `Known` switches), `hegel_model_test.go`
(the configuration struct, the model, the comparison), `hegel_props_test.go` (generators and
properties) and `hegel_pins_test.go` (one plain test per bug), and requires
`hegel.dev/go/hegel v0.6.33` in go.mod. The tests never touch the process environment: a
`MapLookuper` is always given.

## Oracle

The README's and the godoc's semantics, restated as a model over one fixed struct (`Cfg`, 36
fields: string, `int`/`int8`/`uint16`/`int64`, `float64`, `bool`, `time.Duration`, `time.Time`,
`url.URL` and `*url.URL`, pointers with and without `noinit`, a default with a `$STR` reference
and one with an escaped `\$` and a comma, slices with a field delimiter, `[]byte`, `Base64Bytes`,
`HexBytes`, maps with the default and with field-level delimiter and separator, `required`,
`overwrite` with and without a default, a `Decoder`-typed string with and without `decodeunset`,
a nested struct by value, by pointer and by pointer with `noinit`, each with its prefix, an
untagged nested struct sharing the namespace, an untagged field and a private one). The model is
driven by a hand-written table of the fields' tags, walked in struct order; the first error ends
the walk as `Process` returns its first error. Rules: key = lookuper prefix + nested prefixes +
tag key; a set-but-empty variable is a value; a default applies to an unset variable only and is
expanded (`$NAME`, `\$`, `\\`) against the plain environment; an existing non-zero value (or
non-nil pointer) is kept unless `overwrite` and the variable is set; a Config default marks
fields required, but a field with a default is never missing; `noinit` leaves an unset field
alone, otherwise nil pointers are allocated; decoders run when the variable is set, a default
applies or `decodeunset` holds; mutators run in order on set or defaulted values, with
`resolvedKey` the full key, a `stop` ending the chain; scalars parse with `strconv` (base 0 for
integers), `time.ParseDuration`, `url.Parse`, `time.Time.UnmarshalText`; slices split on the
delimiter with items trimmed, maps on the delimiter then the separator (a missing separator is
`ErrInvalidMapItem`); nested structs inherit the resolved defaults and their prefix; a nil struct
pointer is walked detached and attached unless `noinit` and nothing was set. Errors are compared
by kind (`missingRequired`, `requiredAndDefault`, `mapItem`, `mutator`, `parse`, through the
package's sentinels) and by the field path prefix of the message.

Generators draw the lookup map over some fifty keys (every field's key, nested and prefixed
ones, a few stray names) from per-type pools of valid, boundary and invalid strings (a value is
empty 8% of the time), the `Config` (prefix lookuper or none, delimiter and separator defaults,
the four booleans, zero to three of four mutators in random order: one rewrites `~x` to `x!`,
one stops the chain on the original value `stop`, one refuses `muterr`, one is a
`LegacyMutatorFunc`) and an initial struct that is zero or partly filled.

## Method

| Property | Checks |
|---|---|
| ProcessFollowsTheDocs | `ProcessWith` on a copy of the initial struct ends with the model's field values (time by `Equal`, NaN equal to NaN) and the model's error kind and field path, or no error |
| LookupersCompose | a random tree of `MapLookuper`, `PrefixLookuper` and `MultiLookuper` resolves each key as the godoc says: prefix prepended before the wrapped lookup, first hit wins |

The model reproduces a recorded bug while its `Known` switch is on (url.URL User initialized,
decoders on unset values, overwrite with an empty value, DefaultRequired against defaults,
mutators and overwrite on struct-typed decoder fields, the legacy mutator stopping the chain, the
unprefixed struct decoder error, decodeunset not inherited); the pins assert the documented
behaviour and fail while the bug exists. `ZOO_COLLECT=1` records mismatches instead of failing and
prints the agreement classes (about 40% of cases run the whole struct, the rest end at an agreed
error).

## Accepted differences

- A default's `$NAME` is resolved against the unwrapped lookuper, so under a prefix `$X` reads
  `X`, not `PREFIX_X`; the code does this on purpose and the model follows.
- A set-but-empty variable is passed to decoders (a `time.Time` cannot decode it: an error) and
  ignored by the built-in kinds; a design choice the model follows.
- `Base64Bytes`/`HexBytes` keep the partial result of a failing decode (the field is assigned
  before the error is checked); harmless, as `Process` fails anyway.
- Integers parse with base 0 (`0x10`, `010`, `1_000`); slice and map items are trimmed; an empty
  item is the zero value; `decodeunset` has no effect under `noinit` (processField returns
  first).
- A field marked `required` is not checked when it already holds a non-zero value.

## Bugs found

Eleven, in bugs.toml: an unset `url.URL` field ends with an initialized `User` and prints as
`//@`; decoders of non-struct types run on unset variables without `decodeunset`; `overwrite`
does not apply an empty value; `DefaultRequired` rejects every field with a default; mutators skip
struct-typed decoder fields; struct-typed decoder fields ignore the overwrite rule;
`LegacyMutatorFunc` stops the chain; the README's escaped-backslash example does not give the
value it shows; a struct decoder error lacks the field name; unsupported kinds decode silently to
zero values; `DefaultDecodeUnset` is not inherited by nested structs.

## History

- 2026-09-21 (turn 341): target added at c883e6f (v1.4.3) with two properties, 11 pins.
