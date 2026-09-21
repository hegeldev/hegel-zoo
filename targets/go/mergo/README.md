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
`hegel/` test package. `go test -count=1 -run TestHegel -v ./hegel`.

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
  that can fail); unexported fields are left alone. Compared structurally (nil and empty
  containers alike, times by `Equal`, pointers by their targets); errors as a set of the
  messages the merge can hit (the package stops at the first, in map order). Recorded crashes
  are expected where the model says the merge reaches them.
- Laws that hold whatever the model says: the source is not modified; a zero source changes
  nothing (unless empty values override); merging the same source twice is the same as once
  (unless appending).
- A model of the documented `Map`: from a `map[string]interface{}` into a struct, a key names
  the field with its initial capitalised, a value of the field's kind is merged in (a pointer
  to one dereferenced first), a nested map maps into a struct field, a value of another kind
  is a "type mismatch" error, other keys are skipped; from a struct into a map, every exported
  field under its name in lower camel case, missing keys added, present ones replaced with
  `WithOverride` when the field is not empty. Map values are generated from the struct type:
  exact types mostly, pointers to scalars, nested maps or struct values for struct fields,
  embedded structs under their own key or through their promoted fields, kind mismatches, nil
  and unknown keys.

The type universe: a `Leaf` of scalars (with a named string type), an `Inner` with a field of
every shape (embedded structs, pointers to scalars and structs, slices and maps of scalars,
structs and pointers, an array, a `map[string]interface{}`, an `interface{}`, a `time.Time`
and a pointer to one, unexported fields) and an `Outer` nesting `Inner` in every container
(with an embedded pointer, a `[]interface{}` and a JSON-like `map[string]interface{}`); the
roots are these structs, maps of interfaces, structs, pointers and slices, and slices of
structs, pointers, ints and interfaces. Interfaces hold nothing, scalars, slices, maps of
interfaces, a `Leaf` or a pointer to one (typed nil included). Empty values are frequent.

## Properties

- `TestHegelMergeModel`: `Merge` (and the deprecated `MergeWithOverwrite`) against the model,
  every option combination, a value or a pointer as the source, a zero destination sometimes.
- `TestHegelMergeLaws`: the three laws above.
- `TestHegelMapModel`: `Map` (and `MapWithOverwrite`) in both directions against the model.
- `TestHegelPin…`: one pin per recorded bug, asserting the documented behaviour (expected
  failures in `target.toml`); the pins that can panic recover.

## Bugs

Nineteen, recorded in `bugs.toml`: eleven crashes (a typed nil pointer source; an unexported
map field under `WithOverwriteWithEmptyValue`; `Map` values of the field's kind but another
type, in particular a nested `map[string]interface{}` for a typed map field; a nil map
destination; a typed nil pointer value; a map destination or source of another map type; a
promoted field through a nil embedded pointer; `WithSliceDeepCopy` over `[]interface{}`
elements of different kinds; interface entries holding maps of different types;
`WithoutDereference` with `WithOverride` on pointer entries of maps) and eight wrong results
(`WithSliceDeepCopy` merges only pointer and map elements; arrays are never empty;
`WithoutDereference` with `WithOverride` leaves struct pointers alone; `Map` into a non-empty
interface field of another dynamic type errors; `Map` removes map entries and pointers the
source lacks; `WithOverride` merges into a pointer's target before replacing the entry; nil
map entries override without being empty for some kinds and never for pointers; a zero
`time.Time` overrides under `WithOverride`).

## Modelled as recorded

The model reproduces the recorded behaviour while a `Known` switch is on (bugs 6, 7, 8, 9,
10, 15, 16, 17, 19); `ZOO_KNOWN_OFF=name` turns a switch off to check that the model then
disagrees (never set in the zoo's runs). The other bugs are pin-only: the generators keep
away from them (no nil sources, unexported fields zero, exactly typed `Map` values, non-nil
map destinations, untyped nil for nil pointers in `Map` values, `map[string]interface{}`
sources and destinations, embedded structs by value under `Map`).

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
