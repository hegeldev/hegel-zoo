# testify

[stretchr/testify](https://github.com/stretchr/testify) is the assertion library most Go test
suites use (about 26,000 stars): the `assert` package's `Equal`, `EqualValues`, `Exactly`,
`Same`, `Empty`, `Zero`, `Nil`, `Len`, `Contains`, `Subset`, `ElementsMatch`, `Greater` and the
ordering family, `InDelta`/`InEpsilon`, `WithinDuration`, `Panics`, the error assertions,
`JSONEq`/`YAMLEq`, `EqualExportedValues`, each with a `Not` twin and an optional message, plus
`require` (the same with `FailNow`), `mock` and `suite`. The pin is `435c07b` (2026-09-02, twelve
commits after `v1.12.1`).

The repository has LICENSE (MIT); CONTRIBUTING.md, the README and the `.github` templates say
nothing about AI-written code and carry no agent instructions. The zoo keeps its tests in its
own patch and files nothing upstream.

## Build

`go test -count=1 -vet=off -run TestHegel -v ./assert/` in the module root. The patch adds, in
`assert/` as the external package `assert_test`, `hegel_test.go` (harness, the `Known`
switches, a recording `TestingT` and the `check`/`expect` helpers), `hegel_equal_test.go`
(equality, `EqualValues`, `EqualExportedValues`), `hegel_compare_test.go` (ordering, time
windows, deltas), `hegel_collections_test.go`, `hegel_contract_test.go` (the shared contract
and `JSONEq`/`YAMLEq`), `hegel_shapes_test.go` (one narrow property per bug) and
`hegel_pins_test.go` (one plain test per bug), and requires
`hegel.dev/go/hegel v0.6.33` in go.mod, which raises the `go` directive from 1.17 to 1.26.
`-vet=off` because with that directive `go test`'s vet pass rejects two non-constant format
strings in upstream's own `assertion_compare_test.go`.

## Oracles

- **The documented meaning of each assertion**, restated as a model: `Equal` is
  `reflect.DeepEqual` with the documented `[]byte` rule (content, nil distinct from empty) and
  nil equal to nil only; `EqualValues` on two numbers is exact mathematical equality (computed
  with `math/big`), on a string and a `[]byte` content equality, on a named integer value
  equality, on a slice and an array of the same length element equality; `Empty`, `Zero`, `Nil`
  and `Len` from their doc comments; `Contains` is membership (keys of maps, substrings of
  strings), `Subset` set containment (pairs for two maps, keys for a map against a list),
  `ElementsMatch` multiset equality; `Greater` & co are the Go ordering of the kind (`bytes`,
  `strings`, `time.Before`); `InDelta` is `|a-b| <= delta` and `InEpsilon` `|a-b|/|a| <= eps`
  with NaN equal to NaN only; `WithinDuration`/`WithinRange` from `time`.
- **Laws between assertions**: `NotX` is the negation of `X` for every pair; `Exactly` is
  `Equal` plus a type check; `Equal` implies `EqualValues`; `Equal`, `EqualValues`, `InDelta`,
  `WithinDuration`, `ElementsMatch` and `EqualExportedValues` are symmetric; `ElementsMatch`
  is invariant under permutation; `Zero` implies `Empty`; `Positive` is `Greater` than the zero
  value.
- **An independent exported-fields copy** for `EqualExportedValues` (a struct with exported and
  unexported fields nested through pointers, maps, slices and interfaces).
- **A generated JSON document serialised twice** (random key order and whitespace) for
  `JSONEq` and `YAMLEq`, and once more after a mutation that changes its value.
- **The shared contract**, checked on every call through a recording `TestingT`: the returned
  bool is true exactly when nothing was reported, at most one report per assertion, no panic,
  and the caller's message (a plain string or a format with arguments) appears verbatim on the
  `Messages:` line exactly once.

## Method

| Property | Checks |
|---|---|
| EqualityFollowsTheModel | `Equal`, `NotEqual`, `ObjectsAreEqual`, `Exactly`, `IsType`, `IsNotType`, `Same`, `NotSame` on pairs from a dozen types (equal, cloned or independent), and `Empty`, `Zero`, `Nil`, `Len` with their `Not` twins on one value |
| EqualValuesFollowsTheModel | `EqualValues`, `NotEqualValues`, `ObjectsAreEqualValues` on two numbers of any of the twelve numeric types (both orders), a string and a `[]byte`, a named int, a slice and an array |
| EqualExportedValuesFollowsTheModel | a nested struct against a copy with unexported fields changed, exported fields changed, or an independent value; by value and by pointer; both orders |
| OrderingFollowsTheModel | `Greater`, `GreaterOrEqual`, `Less`, `LessOrEqual` on ints, uints, floats, a named int, durations, strings, `[]byte` and times (and across kinds), `Positive`/`Negative` on the numbers, `IsIncreasing`/`IsNonIncreasing`/`IsDecreasing`/`IsNonDecreasing` on slices and arrays |
| TimeWindowsFollowTheModel | `WithinDuration` (both orders) and `WithinRange` |
| DeltasFollowTheModel | `InDelta` (both orders, a string operand), `InEpsilon`, `InDeltaSlice`, `InEpsilonSlice`, `InDeltaMapValues` over ints, uints, float32, float64, durations and NaN |
| CollectionsFollowTheModel | `Contains`, `NotContains`, `Len`, `Subset`, `NotSubset`, `ElementsMatch` (both orders, a permutation), `NotElementsMatch` on int slices and arrays |
| MapAndStringCollectionsFollowTheModel | `Contains` on maps and strings, `Subset` map/map, map/list and list/map |
| AssertionsKeepTheContract | some 50 assertions on generated arguments with a random message: result vs report, one report, no panic, the message verbatim once |
| JSONEqFollowsTheModel | `JSONEq` (both orders) and `YAMLEq` on two serialisations of one document, a mutated document, and invalid text on either side |

The generators are combinator values (`hegel_test.go` holds the idioms: `weighted`, `chance`,
`maybe`, `pairs`, `many`, `tape`, `shuffled`, `shaped`): each property draws one case record
(the two values and the model's verdict, the document and its serialisations, the assertion
and its arguments) rendered by pure methods.

The shapes of the recorded bugs are drawn by default (STYLE.md rule 11): negative signed
against unsigned, fractional floats against integers, int/string pairs, slices against arrays of
every length, nil to the collection assertions, NaN deltas, big integers in documents, `NotSame`
on non-pointers, and so on. A mismatch names the bug whose shape it has (the `Known` switches
keep the shape tests) and the property fails: the wide properties fail on the shape they reach most
often (`EqualValues` on 65 against "A", `Positive("a")`, ...): `Equality`, `EqualExportedValues`,
`Ordering` and `Deltas` every run, `EqualValues`, `JSONEq`, `Collections`,
`MapAndStringCollections` and `AssertionsKeepTheContract` in most runs (their shapes are a few
percent of cases, and hegel-go's case sequence differs per test binary, so a run on another
machine can miss them), and the nineteen narrow properties of `hegel_shapes_test.go`
(`TestHegelEqualValuesKeepsSignedAndUnsignedApart`, `TestHegelInDeltaRejectsANaNDelta`, ...) each
on its own bug: they are the deterministic expected failures beside the pins. `HEGEL_NO_KNOWN=1`,
read once, switches the known shapes off: the generators draw the neighbouring regions instead
(the narrow properties then check the library where it is right, next to the bug), a
mismatching case with a known shape is skipped (measured at under one percent of cases), and
the test passes. `ZOO_COLLECT=1` records mismatches instead of failing and prints the class
counts.

## Accepted differences

- `EqualValues([]int{}, [0]int{})` passes and `EqualValues([0]int{}, []int{})` fails: Go
  converts a slice to an array but not an array to a slice; the model puts the slice first and
  does not check that pair both ways.
- `Regexp` with an invalid pattern string panics through `regexp.MustCompile` (a programming
  error in the test, as the doc example suggests); patterns are valid.
- `InDelta(+Inf, +Inf, 0)` passes (the difference is NaN, which is neither below -delta nor
  above it) while `InEpsilon(+Inf, +Inf, eps)` fails with "relative error is NaN"; infinities
  are not generated.
- `EqualExportedValues` treats every `time.Time` (and any struct with only unexported fields)
  as equal to any other, by the letter of "exported fields only, applied recursively"; the
  generated structs have no such fields.
- `Empty(-0.0)` is false (reflect's `IsZero` compares the bits) while `Zero(-0.0)` is true;
  negative zero is not generated.
- `IsIncreasing([]any{1, 2})` fails with "can not compare": the element kind is Interface.
- Assertions whose misuse the documentation implies (a nil `Implements` interface, a nil
  `ErrorAs` target, a non-string first message argument) are not exercised.

## Bugs found

Nineteen, in bugs.toml: `EqualValues` equates a negative integer with the unsigned one it
wraps to, truncates floats to integers (1 equals 1.5), is not symmetric on rounding, converts
65 to "A", panics on a slice against a longer array and passes a slice against a shorter array
holding its first elements (`[]int{1, 2, 3}` against `[2]int{1, 2}`, bug 19, found once every
slice/array length was drawn); `Contains` on a string looks for
"<int Value>"; `Subset`, `ElementsMatch`, `IsIncreasing`, `Positive` panic on nil;
`ElementsMatch` passes two empty non-lists; `PanicsWithValue` panics on an uncomparable value;
`InDelta` accepts a NaN delta; `InDeltaSlice` ignores the lengths; `Greater` panics on two
structs or slices of different types; `EqualExportedValues` drops nil-interface map entries and
panics on nil-interface elements; `JSONEq`/`YAMLEq` compare big integers as float64; `NotSame`
returns true after failing; `NotElementsMatch` mangles the message and reports twice;
`Positive("a")` passes; `ElementsMatch([1]int{0}, []int{})` passes (a zero array is "empty").

## History

- 2026-09-21 (turn 335): target added at 435c07b (v1.12.1+12) with ten properties, 18 pins.
- 2026-09-26: generators rewritten in combinator style; the known shapes are drawn by default and
  nineteen narrow properties, one per bug, are the expected failures beside the pins; testify/19
  found by the freed slice/array pairs. Two latent model bugs fixed (2^63-1 and 2^64-1 rounded to
  powers of two by a 53-bit `big.Float`; the big-integer test off by one).
