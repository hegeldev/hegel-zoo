# go-cmp

[google/go-cmp](https://github.com/google/go-cmp) is the equality package most Go test suites
reach for when `reflect.DeepEqual` is not enough (about 4,700 stars): `cmp.Equal` and `cmp.Diff`
with a rule set (Ignore, Transformer and Comparer options after path and value filters, then
an `Equal` method, then the kinds), the `cmpopts` helpers (`EquateEmpty`, `EquateApprox`,
`EquateNaNs`, `EquateErrors`, `EquateApproxTime`, `IgnoreFields`, `IgnoreTypes`,
`IgnoreUnexported`, `IgnoreInterfaces`, `IgnoreSliceElements`, `IgnoreMapEntries`,
`SortSlices`, `SortMaps`, `AcyclicTransformer`), a `Reporter` interface with typed path steps,
and documented panics on misuse. The pin is `b133f1f` (2026-06-18, three commits after
`v0.7.0`).

The repository has LICENSE (BSD 3-clause); CONTRIBUTING.md (a CLA) and the README say nothing
about AI-written code and carry no agent instructions. The zoo keeps its tests in its own
patch and files nothing upstream.

## Build

`go test -count=1 -vet=off -run TestHegel -v ./cmp/` in the module root. The patch adds, in
`cmp/` as the external package `cmp_test`, `hegel_test.go` (harness, the `Known` switches),
`hegel_deepequal_test.go`, `hegel_diff_test.go`, `hegel_options_test.go` (the document type,
the option generator and the model), `hegel_reporter_test.go`, `hegel_misuse_test.go` and
`hegel_pins_test.go` (one plain test per bug), and requires `hegel.dev/go/hegel v0.6.33` in
go.mod, which raises the `go` directive from 1.21 to 1.26. `-vet=off` because with that
directive `go test`'s vet pass rejects unkeyed struct literals in upstream's own
`compare_test.go`.

## Oracles

- **`reflect.DeepEqual`** on values with exported fields only, no `Equal` methods and no
  cycles, where the package documents no difference ("much like reflect.DeepEqual"); the two
  disagree only on a value compared with itself when it holds a NaN or a function (reflect's
  identity shortcut), which the property allows for.
- **The documented meaning of each option**, restated as a model over one document type
  (an embedded struct, string, int and float fields, a slice and a map of strings, a pointer
  to a nested struct, a `time.Time`, an `error`, a struct with an `Equal` method, an unexported
  field): `EquateEmpty` equates nil with empty, `EquateNaNs` NaN with NaN, `EquateApprox` is
  `|x-y| <= max(fraction*min(|x|,|y|), margin)`, `EquateApproxTime` a window on non-zero
  times, `EquateErrors` is `errors.Is`, `IgnoreFields` (plain, dotted, embedded and unexported
  names), `IgnoreTypes`, `IgnoreInterfaces`, `IgnoreUnexported`/`AllowUnexported`/`Exporter`,
  `IgnoreSliceElements` and `IgnoreMapEntries` drop what their predicate selects, `SortSlices`
  compares slices sorted, `SortMaps` compares maps as sorted `{K, V}` lists on which the string
  and int rules apply to keys and values, a `Transformer` (`strings.ToLower`) and a `Comparer`
  (ints modulo 3) replace the string and int rules everywhere they reach, and the `Equal`
  method decides for the type that has one.
- **The Equal/Diff contract**: `Diff` is empty iff `Equal`, and otherwise every line carries a
  two-character prefix with at least one `-` or `+` line; `Equal` is symmetric and reflexive
  except on NaNs and functions.
- **The Reporter contract**: with a recording `Reporter`, every leaf the model says differs is
  reported unequal at the documented path (`.Name`, `.Base.ID`, `.Sub*.X`, `.Attrs["k"]`,
  `.Err.(cmp_test.Code).C`), nothing else is, ignored fields are reported `ByIgnore` at their
  path, `Equal`-method fields `ByMethod`, and `Equal` is true iff nothing unequal was reported.
- **The documented panics**: invalid function shapes for `Comparer`, `Transformer`,
  `FilterValues`, `SortSlices`, `IgnoreSliceElements`, `IgnoreMapEntries`, bad transformer
  names, unfiltered and ambiguous options, unexported fields without an option, non-struct
  arguments, negative tolerances, NaN map keys, a non-total `SortMaps` order; and the
  `IgnoreFields` selector grammar (segments naming fields of the struct reached, embedded
  fields visible on the parent, one leading dot harmless).

## Method

| Property | Checks |
|---|---|
| EqualFollowsDeepEqual | `Equal` on pairs of generated values (identical, cloned, independent, wrapped in `[]any`) against `reflect.DeepEqual`; symmetry; `Diff` empty iff `Equal`, otherwise prefixed lines with a `-` or `+`; reflexivity |
| DiffTextIsCoherent | `Diff` on multi-line texts, byte slices, slices of lines and structs holding a text against an edited copy: empty iff `Equal`, otherwise prefixed lines (the line and byte diffing of the reporter) |
| OptionsFollowTheModel | `Equal` and `Diff` with a random combination of the options above (some nested in `cmp.Options`) on a document and a mutated or independent one, against the model; symmetry; `Equal(x, x)` |
| ReporterSeesTheDifferences | the set of unequal and ignored paths a `Reporter` receives against the model's, the `ByMethod`/`ByIgnore` flags, and the `Equal` result |
| MisusePanicsAsDocumented | a table of 70 valid and invalid constructions (panic or not, with the documented message), and generated `IgnoreFields` selectors accepted exactly when the grammar says |

Mismatches are classified before they count: a `Known` switch per recorded bug gates the input
shape (`IgnoreMapEntries` is not combined with `SortMaps`; a nil slice is not put against a
longer one when `SortSlices` and an element ignore are both on); the pins assert the correct
behaviour and fail while the bug exists. `ZOO_COLLECT=1` records mismatches instead of failing
and prints the class counts.

## Accepted differences

- `reflect.DeepEqual(x, x)` is true for a slice, map or pointer holding a NaN or a non-nil
  function (identity shortcut) where `cmp.Equal(x, x)` is false; cmp documents functions as
  unequal unless both nil and compares NaNs with `==`.
- Cyclic values: cmp documents its own rule (pointed-at values equal only if both addresses
  were visited in the same path step), which differs from reflect's on rings of different
  lengths; the generator makes no cycles.
- `EqualValues`-style conversions do not exist here: `cmp.Equal(1, int64(1))` is false by
  design (different types are wrapped in `any` and compared as interfaces).
- `SortSlices` with a `Transformer` on the elements sorts by the original values and compares
  the transformed ones in that order, so `[]string{"B", "a"}` and `[]string{"A", "b"}` are
  unequal under `SortSlices(less)` plus `strings.ToLower`; the model follows the
  implementation order (sort, then transform), which is what "sorts all []V" and "transform the
  current values" together imply.
- `IgnoreFields(Doc{}, "secret")` and `"When.wall"` are accepted (the selector code resolves
  unexported names deliberately); the grammar model treats them as valid.

## Bugs found

Two, in bugs.toml: `IgnoreMapEntries` has no effect on a map that `SortMaps` flattens (the
discarded entries are compared); with `SortSlices`, a nil slice equals a non-nil slice whose
elements are all ignored when that slice is unsorted and not when it is sorted (the sort
transform turns nil into an empty slice).

## History

- 2026-09-21 (turn 336): target added at b133f1f (v0.7.0+3) with five properties, 2 pins.
