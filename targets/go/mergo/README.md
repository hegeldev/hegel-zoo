# go/mergo

[darccio/mergo](https://github.com/darccio/mergo) (`dario.cat/mergo`, v1.0.2): a reflection
library that merges same-type structs and maps by filling empty destination attributes from
a source ("useful for configuration default values"), with options to override, append
slices, deep-copy slices, keep pointers, type-check and transform; and `Map`, which maps a
`map[string]interface{}` onto a struct and back. Used by containerd, docker, moby, loki,
goreleaser, sprig and thousands of others. The README declares the library "stable and
frozen": "No new features are accepted. They will be considered for a future v2 that improves
the implementation and fixes bugs for corner cases."

## Build

The patch adds `hegel.dev/go/hegel` to `go.mod` (the module has no other dependency) and the
`hegel/` test package: `hegel_zoo_idioms_test.go` (the harness idioms shared with the other
Go targets), `hegel_zoo_test.go` (the harness, the judge, the collector, the `known`
switches, the comparison), `hegel_zoo_values_test.go` (the type universe and the value
generators), `hegel_zoo_model_test.go` (the options, the transformers, the merge and `Map`
models with the switches threaded, the classifier), `hegel_zoo_merge_test.go` (the merge
cases and the two wide properties on `Merge`), `hegel_zoo_map_test.go` (the `Map` cases and
their wide property), `hegel_zoo_shapes_test.go` (ten narrow properties) and
`hegel_pins_test.go` (twenty pins). `go test -count=1 -run TestHegel -v ./hegel`.

## Oracles

- A model of the documented `Merge`: an empty destination attribute (a zero scalar, a nil or
  empty container, a nil pointer or a pointer to an empty value unless `WithoutDereference`)
  takes the source's, recursively through exported struct fields, pointers and maps; structs
  inside maps are not merged (documented: unaddressable), map and pointer entries are merged
  through; `WithOverride` replaces non-empty attributes with non-empty source values,
  `WithOverwriteWithEmptyValue` with empty ones too (and removes map entries the source lacks),
  `WithOverrideEmptySlice` lets an empty slice override, `WithAppendSlice` appends (an error
  for slices of different types), `WithTypeCheck` makes overriding a slice with one of another
  type an error, `WithSliceDeepCopy` merges elements, `WithTransformers` replaces the merge of
  a type (a `time.Time` transformer as in the documentation, a named string type's transformer
  that can fail); unexported fields are left alone. The model states an outcome and a result:
  the outcome `ok`, or the set of the error messages the merge can hit (the package stops at
  the first, in map order), or a crash where a switched bug reaches one (or a crash or one of
  the errors, whichever map order reaches first); the result compared structurally (nil and
  empty containers alike, times by `Equal`, pointers by their targets).
- Laws that hold whatever the model says: the source is not modified; a zero source changes
  nothing (unless empty values override); merging the same source twice is the same as once
  (unless appending). Each law is also stated on the model, which is how its cases are
  classified (below).
- A model of the documented `Map`: from a `map[string]interface{}` into a struct, a key names
  the field with its initial capitalised, a value of the field's kind is merged in (a pointer
  to one dereferenced first), a nested map maps into a struct field, a value of another kind
  is a "type mismatch" error, other keys are skipped; from a struct into a map, every exported
  field under its name in lower camel case, missing keys added, present ones replaced with
  `WithOverride` when the field is not empty.
- The replicas of the recorded bugs the generators reach (`known`, one switch per bug, off by
  default): with a switch on the model follows the library's rule for that bug, transcribed
  from the source at the point named beside the switch (`isEmptyValue`'s array rule for
  mergo/7, `deepMerge`'s pointer, struct, slice and map cases for 6, 8, 15, 16, 17, 19 and 20,
  `deepMap`'s forced overwrite and interface mismatch for 10 and 9). The classifier runs the
  model with no switch, with each switch alone and with all but each, before the library is
  called, and names a case's shape by the first switch that changes the statement (then by
  the first whose absence does); the library's statement is also compared with the model's
  under every switch (replica agreement, 100 percent over three thousand cases).

The type universe: a `Leaf` of scalars (with a named string type), an `Inner` with a field of
every shape (embedded structs, pointers to scalars and structs, slices and maps of scalars,
structs and pointers, an array, a `map[string]interface{}`, an `interface{}`, a `time.Time`
and a pointer to one, unexported fields) and an `Outer` nesting `Inner` in every container
(with an embedded pointer, a `[]interface{}` and a JSON-like `map[string]interface{}`); the
roots are these structs, maps of interfaces, structs, pointers and slices, and slices of
structs, pointers, ints and interfaces. Interfaces hold nothing, scalars, slices, maps of
interfaces, a `Leaf` or a pointer to one (typed nil included). Empty values are frequent (a
nil pointer two times in five, a nil slice or map one in three, a zero array or time two in
five, zero scalars a quarter). A value is drawn by a generator per type and depth, built once
from the field, element and entry generators and allocating afresh on every draw; the
entries of a map are a counted list set in order (repeated keys collapse, as before); the
figure beside every weight is the share the probe measured in context.

## Properties

- `TestHegelMergeModel`: `Merge` (and the deprecated `MergeWithOverwrite`) against the model,
  every option combination, a value or a pointer as the source, a zero destination sometimes.
- `TestHegelMergeLaws`: the three laws above.
- `TestHegelMapModel`: `Map` (and `MapWithOverwrite`) in both directions against the model.
- Ten narrow properties, one per bug the wide properties reach, each over the bug's shape
  with random surroundings: `TestHegelDeepCopyMergesScalarAndStructElements` (mergo/6),
  `TestHegelZeroArraysAreEmpty` (7), `TestHegelNoDerefOverridesStructPointers` (8),
  `TestHegelKeysOfAnotherDynamicTypeAreLeftAlone` (9),
  `TestHegelEntriesTheSourceMapLacksStay` (10), `TestHegelNilEntriesOfTheSourceMapAreEmpty`
  (15), `TestHegelZeroTimesDoNotOverride` (16),
  `TestHegelDeepCopyOverInterfaceElementsOfDifferentKinds` (17),
  `TestHegelNoDerefOverPointerEntries` (19) and `TestHegelSliceDeepCopyMapEntries` (20).
- `TestHegelPin…`: one pin per recorded bug, asserting the documented behaviour (expected
  failures in `target.toml`); the pins that can panic recover.

The wide properties draw the shape of every switched bug at its natural rate (per three
thousand cases: the merge model names mergo/7 185 times, 6 129, 15 106, 16 73, 8 37, 17 6, 9
and 20 once; the `Map` model 10 235, 7 133, 9 58, 6 33, 8 17, 17 9, 15 3, 19 2; the laws 7
119, 16 29, 19 16, 17 11) and fail by the shape they draw most often; the narrow properties
fail every run. Under `HEGEL_NO_KNOWN=1` the cases the classifier names are not drawn (the
merge model rejects 17 percent of its draws, the `Map` model 18, the laws 6) and the narrow
properties draw the region past their shape; every property then passes. The bugs the
generators keep away from (no nil sources, unexported fields zero, exactly typed `Map`
values, non-nil map destinations, untyped nil for nil pointers in `Map` values,
`map[string]interface{}` sources and destinations, embedded structs by value under `Map`,
interface entries never holding typed maps of different types: mergo/1-5, 11-14 and 18) are
pin-only until the second part of the rewrite draws them.

Shrinking: the engine keeps every attempt of a shrink in memory (a property of three
thousand plain integer draws that always fails reaches 1.6 GB resident on this machine), and
a merge case of an `Outer` is a sequence of thousands of draws, so the harness bounds the
shrink of a failure to a budget of failing judgements (`HEGEL_SHRINK_BUDGET`, 1.5 MB of the
first failure's message by default, between a hundred and three thousand attempts), after
which the next attempt is rejected before it draws, which ends the shrink, and the engine's
replay of the last failure prints it. A default run takes three to six minutes and under a
gigabyte of memory; a shrunk `Outer` case is less minimal than an unbounded shrink would give.

## Bugs

Twenty, recorded in `bugs.toml`: twelve crashes (a typed nil pointer source; an unexported
map field under `WithOverwriteWithEmptyValue`; `Map` values of the field's kind but another
type, in particular a nested `map[string]interface{}` for a typed map field; a nil map
destination; a typed nil pointer value; a map destination or source of another map type; a
promoted field through a nil embedded pointer; `WithSliceDeepCopy` over `[]interface{}`
elements of different kinds (and, with no option, map-of-interfaces entries of different
kinds), and over a map-of-interfaces entry that holds a slice in the source and a scalar,
struct, pointer or non-empty map in the destination; interface entries holding maps of
different types; `WithoutDereference` with `WithOverride` on pointer entries of maps and on
the pointer fields of struct entries) and eight wrong results
(`WithSliceDeepCopy` merges only pointer and map elements; arrays are never empty;
`WithoutDereference` with `WithOverride` leaves struct pointers alone; `Map` into a non-empty
interface field of another dynamic type errors; `Map` removes map entries and pointers the
source lacks; `WithOverride` merges into a pointer's target before replacing the entry; nil
map entries override without being empty for some kinds and never for pointers; a zero
`time.Time` overrides under `WithOverride`).

Design facts mirrored, not recorded: a struct is never empty (only its fields are), so a
struct without exported fields moves only with `WithOverride`, and a pointer to a zero struct
fills a nil pointer; an interface holding an empty scalar is empty when dereferenced, but a
non-nil interface is not replaced without `WithOverride` (its dynamic value is
unaddressable), and two interfaces are merged through only when they hold the same kind; a
nil pointer fills from a pointer to an empty value; in typed maps `WithOverride` never
replaces a pointer entry (it is merged through), in maps of interfaces it replaces everything;
`WithTypeCheck` errors only when the source entry is a slice (a scalar overriding a slice is
also an error, with a message about two slices); `WithAppendSlice` and `WithSliceDeepCopy`
cannot change a slice held in an interface field (unaddressable); a nil map entry is not added
without `WithOverride`; `Map` dereferences a pointer value for a non-pointer field (so a
`*Leaf` for an `interface{}` field lands as a `Leaf`); a `Map` value that is a map for a
non-struct, non-map field is silently ignored; `Map` sets an empty non-nil slice for an empty
source slice; keys are matched by `FieldByName` after capitalising the first letter only
("url" does not find `URL`, "uRL" does; both "value" and "Value" find `Value`).

## Not tested

Cycles and aliasing inside one value (the visited set), transformers on unexported or
unaddressable values beyond the two used, `Map` with sources and destinations of the same
kind (redirected to `Merge` without the type check), channels and funcs, concurrency.

## History

- 2026-09-21: new target, three properties, 19 bugs.
- 2026-09-28: mergo/20 (`WithSliceDeepCopy` over map entries without elements), found by the
  weekly run at a thousand cases.
- 2026-10-13: rewrite, part 1 of two: the nine switches the model reproduced the bugs behind
  turned around (off by default, the properties failing by the shapes they draw), mergo/20
  a tenth switch, the value generators a table per type, ten narrow properties, the shrink
  budget; the notes of mergo/17 and 19 widened after standalone checks.
