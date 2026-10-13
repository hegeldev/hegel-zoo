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
package `envconfig_test`, `hegel_zoo_idioms_test.go` (the generator idioms shared with the
other rewritten Go targets: weighted choices, fair-bit dice, halving helpers),
`hegel_zoo_test.go` (the harness, the collector, the `known` switch set, the judge and the
classifier), `hegel_zoo_model_test.go` (the configuration struct, the model `processExpected`
with the switch set threaded, the comparison), `hegel_zoo_cases_test.go` (the case records and
their generators), `hegel_zoo_process_test.go` (the wide property), `hegel_zoo_lookupers_test.go`
(the lookuper tree and its property), `hegel_zoo_shapes_test.go` (one narrow property per
switched bug) and `hegel_pins_test.go` (one plain test per bug), and requires
`hegel.dev/go/hegel v0.6.33` in go.mod. `HEGEL_TEST_CASES`, `HEGEL_SEED` and `HEGEL_VERBOSE`
are passed through to the engine; `HEGEL_COLLECT=1` records mismatches instead of failing and
prints the counts per class; `HEGEL_NO_KNOWN=1` switches the known shapes off (below). The
tests never touch the process environment: a `MapLookuper` is always given.

## Oracle

The README's and the godoc's semantics, restated as a model over one fixed struct (`Cfg`, 38
fields: string, `int`/`int8`/`uint16`/`int64`, `float64`, `bool`, `time.Duration`, `time.Time`,
`url.URL` and `*url.URL`, pointers with and without `noinit`, a default with a `$STR` reference
and one with an escaped `\$` and a comma, slices with a field delimiter, `[]byte`, `Base64Bytes`,
`HexBytes`, maps with the default and with field-level delimiter and separator, `required`,
`overwrite` with and without a default, a `Decoder`-typed string with and without `decodeunset`,
a nested struct by value, by pointer and by pointer with `noinit`, each with its prefix, an
untagged nested struct sharing the namespace, a `[]Plain` and a `map[string]Plain` where
`Plain` is a struct without a decoder (the two fields added at the rewrite for
go-envconfig/10), an untagged field and a private one). The model is driven by a hand-written
table of the fields' tags, walked in struct order; the first error ends the walk as `Process`
returns its first error. Rules: key = lookuper prefix + nested prefixes + tag key; a
set-but-empty variable is a value; a default applies to an unset variable only and is expanded
(`$NAME`, `\$`, `\\`) against the plain environment; an existing non-zero value (or non-nil
pointer) is kept unless `overwrite` and the variable is set; a Config default marks fields
required, but a field with a default is never missing; `noinit` leaves an unset field alone,
otherwise nil pointers are allocated; decoders run when the variable is set, a default applies
or `decodeunset` holds; mutators run in order on set, defaulted or `decodeunset` values, with
`resolvedKey` the full key, a `stop` ending the chain; scalars parse with `strconv` (base 0 for
integers), `time.ParseDuration`, `url.Parse`, `time.Time.UnmarshalText`; slices split on the
delimiter with items trimmed, maps on the delimiter then the separator (a missing separator is
`ErrInvalidMapItem`); an element kind without a decoder that the package does not handle is an
error; nested structs inherit the resolved defaults and their prefix; a nil struct pointer is
walked detached and attached unless `noinit` and nothing was set. The model's statement of a
case is a set of checks: the error (none, or its kind - `missingRequired`, `requiredAndDefault`,
`mapItem`, `mutator`, `parse`, through the package's sentinels - and the field path of its
message) and the exported top-level fields' values (time by `Equal`, NaN equal to NaN, pointers
by nil-ness then target); on an expected error the fields before the failing one in walk order,
which `Process` has set by then, are checked and the failing field and those after it are not
(a failed decode leaves its field partial: a zeroed `time.Time`, a `Base64Bytes` prefix).

Cases are records drawn from package-level generators: the `Config` choices (a prefix lookuper
at 25 %, the delimiter and separator defaults at 25, `DefaultNoInit` 20, `DefaultOverwrite`
30, `DefaultDecodeUnset` 15, `DefaultRequired` 5, zero to three of five mutators in a drawn
order at 40: one rewrites `~x` to `x!`, one stops the chain on the original value `stop`, one
refuses `muterr`, one is a `LegacyMutatorFunc` doubling a leading `L`, one fills an empty
current value with `filled`), the lookup map as an ordered list of optional entries over fifty
keys (every field's key, the nested and prefixed ones, a few stray names, each present at 15 to
92 percent with a value from its kind's pool of valid, boundary and invalid strings, empty 8 % of
the time - 2 for time and url -, the `T` key at 90 under `decodeunset`, three unprefixed names
under a prefix) and the initial struct as a record of pre-set choices (zero half the time,
otherwise each of 26 fields pre-set at a quarter), built into a fresh `*Cfg` on each side. The
pools are the old ones byte for byte plus the values the mutators act on in the url and time
pools (`~http://a/b`, `stop`, `muterr`, `Lx`; `~2020-01-02T03:04:05Z`, `stop`), without which
the shape of go-envconfig/5 was never drawn. Every weight is drawn through the fair-bit dice of
the idioms and the realised rate measured over 3000 cases in context stands beside it; a share
moves by up to five points between seeds at the same weight. A case costs about 600 draws,
under a thousand at most.

## Method

| Property | Checks |
|---|---|
| ProcessFollowsTheDocs | `ProcessWith` on a fresh copy of the initial struct ends with the model's error kind and field path, or no error, and with the model's field values (all of them without an error; those before the failing field with one) |
| LookupersCompose | a random tree of `MapLookuper`, `PrefixLookuper` and `MultiLookuper` resolves each key as the godoc says: prefix prepended before the wrapped lookup, first hit wins |
| eleven narrow properties | one per switched bug (below): the bug's shape forced, the rest of the case drawn as in the wide property, judged by the same model |

## Accepted differences

- A default's `$NAME` is resolved against the unwrapped lookuper, so under a prefix `$X` reads
  `X`, not `PREFIX_X`; the code does this on purpose and the model follows.
- A set-but-empty variable is passed to decoders (a `time.Time` cannot decode it: an error) and
  ignored by the built-in kinds; a design choice the model follows.
- `Base64Bytes`/`HexBytes` keep the partial result of a failing decode (the field is assigned
  before the error is checked), and a failing `time.Time` decode zeroes the field
  (`UnmarshalText` assigns on error); harmless, as `Process` fails anyway, and the failing field
  is not checked.
- Integers parse with base 0 (`0x10`, `010`, `1_000`); slice and map items are trimmed; an empty
  item is the zero value; `decodeunset` has no effect under `noinit` (processField returns
  first).
- A field marked `required` is not checked when it already holds a non-zero value.

## Bugs found

Twelve, in bugs.toml: an unset `url.URL` field ends with an initialized `User` and prints as
`//@`; decoders of non-struct types run on unset variables without `decodeunset`; `overwrite`
does not apply an empty value; `DefaultRequired` rejects every field with a default; mutators
skip struct-typed decoder fields; struct-typed decoder fields ignore the overwrite rule;
`LegacyMutatorFunc` stops the chain; the README's escaped-backslash example does not give the
value it shows; a struct decoder error lacks the field name; unsupported element kinds decode
silently to zero values; `DefaultDecodeUnset` is not inherited by nested structs; mutators are
not called on unset variables under `decodeunset` although the Mutator doc says they are
(go-envconfig/12, found at the rewrite by a standalone check of the doc's sentence).

## Properties and the recorded bugs

The model states the documented behaviour; the `known` switch set (`type known [12]bool`,
one index per bug id, all off by default) turns a replica of the library's rule on in its place,
each transcribed from the lines of `envconfig.go` and `mutator.go` it follows. The classifier
runs the model per switch on the case before the library is called and names the first bug in
id order whose switch alone changes the expected checks (sufficiency), else the first whose
switch is needed (necessity), else a hole; every mismatch by default is a named shape and no
named shape passes. go-envconfig/8 is a documentation bug (the README's example comment
contradicts the README's general rule, which the code's comment states and the model follows):
a property cannot draw a contradiction in the documentation, so it stays pin only.

Over 3000 default cases the wide property names 2464 shapes (82 %), every one by sufficiency
with the library agreeing with the replica in all of them: go-envconfig/1 in 990, 2 in 611, 3 in
8, 4 in 77, 5 in 15, 6 in 183, 7 in 55, 9 in 279, 10 in 146, 12 in 100; counted alone, the
switches of 1, 2, 6, 9, 10, 11 and 12 change the expected checks in 990, 1503, 371, 443, 781,
201 and 209 cases, the others in under 110. go-envconfig/11 is never the name of a wide case:
whenever its switch matters (an unset nested `T` under `DefaultDecodeUnset`) the error it
produces is also the unprefixed one of go-envconfig/9, which comes first in id order; its narrow
property judges the error's kind alone. The narrow properties force the shape with the rest of
the case drawn as in the wide property, each named as its bug in every case; where the walk
would end in an error before the shaped field, the case is rejected (up to a third for 10 and
11, under a quarter otherwise). A case costs about 600 draws, under a thousand at most; a
default run takes about 45 s on this machine (most of it the eleven failing properties
shrinking), a thousand cases under `HEGEL_NO_KNOWN=1` about 80 s.

Under `HEGEL_NO_KNOWN=1` the shapes are off: the field checks that an unset `url.URL` and the
unset decoder fields change (go-envconfig/1 and 2, in most cases) are dropped from the case and
counted; the `DefaultRequired` and `DefaultDecodeUnset` coins, the `SUBS`/`SUBM` keys, the
mutator-triggering url and time values, the bad and empty time values and the fill mutator are
at weight zero (4, 5, 9, 10, 11, 12); an empty value on a pre-set field under overwrite, a
pre-set struct decoder field with its variable set and the legacy mutator before another are
filtered out by the classifier (3, 6, 7; 18 % of cases rejected). The narrow properties
draw the region past their shape and pass. The pins alone fail there.

## Shrinking

The simplest alternative comes first in every choice: the shrink target is the empty lookup map,
the zero Config and the zero initial struct, which is the shape of go-envconfig/1 and 2 at once
(an unset `U`, unset decoder fields). A shrink here is cheap (no process is spawned), but the
harness bounds it by a budget of failing judgements all the same, since the engine keeps every
attempt in memory.

## History

- 2026-09-21 (turn 341): target added at c883e6f (v1.4.3) with two properties, 11 pins.
- 2026-10-13: rewritten to the standard: the eleven `Known` switches on by default, which made
  the model reproduce the bugs, turned into twelve switches off by default with the classifier
  naming the shape; the generators as records in combinator style with measured rates; the
  struct gained `Subs`/`SubM` for go-envconfig/10 and the url/time pools the mutator-triggering
  values for go-envconfig/5; eleven narrow properties; go-envconfig/12 found and recorded;
  the notes of 2, 3, 4, 5, 6, 7, 9 and 11 widened after standalone checks.
