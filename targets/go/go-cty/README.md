# go/go-cty

[zclconf/go-cty](https://github.com/zclconf/go-cty) — the dynamic type system of Terraform and
HCL: types (primitives, lists, maps, sets, objects, tuples, the DynamicPseudoType placeholder),
values with null and unknown, conversions (`cty/convert`), JSON and msgpack serializations, and
a standard library of functions (`cty/function/stdlib`). Pinned at `a918e11` (main, 2026-08-21,
two commits after v1.19.0). MIT.

## Oracle

The documentation in `docs/` (types.md, convert.md, json.md, functions.md) and the doc comments
and `Description` fields of the stdlib functions, evaluated over generated types (depth up to
three, with placeholders where allowed) and values (with nulls and unknowns):

- a value marshalled with its type unmarshals to an equal value when the same type is given; the
  type serialization round-trips; without placeholders the implied type reads the document back
  and converts to the original type; `SimpleJSONValue` agrees;
- the conversion charts: a safe conversion implies an unsafe one, a conversion that exists gives
  the requested type and keeps nullness, `Convert` fails exactly when no unsafe conversion
  exists, a safe conversion (to a set-free type) is reversible; `Unify` gives one conversion per
  type, each landing on the unified type;
- the stdlib functions against Go models: strings by runes (Upper, Lower, Reverse, Strlen,
  Substr, Chomp, Indent, Title, Trim family, Replace, Split/Join, Sort), collections (Length,
  Element, HasIndex/Index, Contains, Distinct, Compact, ReverseList, Slice, Chunklist, Concat,
  Flatten, Coalesce, CoalesceList, Keys, Values, Lookup, Merge, Zipmap), sets (SetHasElement,
  union, intersection, subtraction, symmetric difference, SetProduct), numbers (Absolute,
  Negate, Signum, Int, Floor, Ceil, comparisons, Min/Max, exact integer Add/Subtract/Multiply/
  Modulo/Divide/Pow, ParseInt), Range, Format (verbs s d v t q f x o b X with width, `-`, `0`,
  `+`, precision; null and unknown arguments), Regex/RegexAll/RegexReplace against Go's regexp
  with the documented result shapes, JSONEncode/JSONDecode, CSVDecode against encoding/csv,
  FormatDate against Go's time layouts and TimeAdd against time.Duration.

## Properties

- `TestHegelJSONRoundTrip`, `TestHegelMsgpackRoundTrip`: the codec round trips above.
- `TestHegelConversionRules`, `TestHegelUnification`: `cty/convert`.
- `TestHegelStringFunctions`, `TestHegelCollectionFunctions`, `TestHegelSetFunctions`,
  `TestHegelNumberFunctions`, `TestHegelRange`, `TestHegelFormat`, `TestHegelRegex`,
  `TestHegelJSONFunctions`, `TestHegelCSVDecode`, `TestHegelFormatDate`: the stdlib.

## Known shapes drawn by default

The test lives in `hegel/` (package `hegel`): `hegel_test.go` (harness, the generator idioms
`choice`/`weighted`/`chance`/`maybe`/`many`/`shaped`, the `ZOO_COLLECT` collector, the `Known`
struct), `hegel_gen_test.go` (types as a depth-indexed generator memoised per depth, values as a
generator derived from the type, numbers and strings as weighted choices over tables),
`hegel_codec_test.go`, `hegel_stdlib_test.go` (one record and `Composite` per property, the
models as pure functions shared with the narrow properties), `hegel_pins_test.go` (one plain test
per bug) and `hegel_shapes_test.go` (one property per bug). `Known` has one switch per recorded
bug, every one off by default: the models state the documented behaviour, the generators draw the
bugs' shapes and `mismatch` names the shape of the failing case. The wide properties reach the
shapes at their natural rates: NumberFunctions shrinks to `Modulo(0, 0)` (go-cty/8),
JSONFunctions to a trailing `]` (go-cty/7) and Format to `%.0v` of `a` (go-cty/9; go-cty/6's
`%.0s` is in reach but loses the shrink) every round; JSONRoundTrip and MsgpackRoundTrip reach
go-cty/1 (a null under a dynamic element type, the unmarshal panic recovered and named) about
half and a quarter of the rounds, StringFunctions go-cty/2 (`Substr("a", -1, 0)`; go-cty/3 is in
reach but never wins the shrink) and Range go-cty/5 some rounds, so those four are mapped
intermittent. The narrow properties `DynamicElementTypesKeepNullElements`,
`SubstrNegativeOffsetsWithZeroLength`, `TitleAfterUnderscores`, `ComparisonsAgainstDescriptions`,
`RangeRejectsZeroSteps`, `FormatStringPrecision` (`%s` with a precision of 0),
`JSONDecodeRejectsTrailingBrackets`, `ModuloByZero`, `FormatDefaultVerbPrecision` (`%v` with a
precision of 0 to 4 and a width over strings and numbers, judged as the `%s` or `%g` it stands
for) and `UnifiedTuplesConvertThroughTheirListForm` (a tuple or object of two or three
collections or tuples over different primitive types beside a list or map of lists or sets of a
third, in both modes, judged as the Unification property judges) each draw one bug's region and
fail every run. The Unification property names the shape of go-cty/10 (`unifyWrapShape`: tuples
beside lists, or objects beside maps, whose elements unify to one collection type that the
collection beside moves again, with an element the first conversion has to move) and recovers
the conversion's panic itself, but reaches it about once in twelve thousand cases of
`unifyCases` and fails on it about once in twenty thousand (the `cousinsOf` alternatives for a
tuple or object — a list or set of a cousin or a swap of one element, three times in ten for
tuples, a map of one, one time in six for objects — and an unrelated `freshTypes` list of lists
are what reach it; the rest of the rate is the base type's: a tuple or object of two or more
collections or tuples that unify to a type a cousin can still move is under two percent of
`plainTypes2`, and the shape also needs every type beside it to be a list or map, a non-empty
element the first conversion has to move, and for objects the unsafe mode), so it passed 17 of
17 default rounds and is not mapped. `HEGEL_NO_KNOWN=1`
(read once) turns the switches on: the models reproduce the recorded behaviour, the codec
generators give the collections of go-cty/1 known non-empty elements, the Unification property
skips the shape of go-cty/10 and counts it, and the narrow properties draw the neighbouring
region (for `%v`: no precision, or the `%s`/`%g` it stands for with one; for the unified tuples,
elements over one primitive type); every property then passes.

## Bugs

Ten, in bugs.toml: a null, unknown or empty element under a dynamic element type loses its
type in JSON and msgpack and the unmarshal panics beside a known element (1); Substr with a
negative offset and length 0 returns the rest of the string (2); Title's description does not
match strings.Title's separators (3); the comparison functions' descriptions name the operands
backwards (4); Range's zero-step check is pointer equality with cty.Zero (5); Format ignores a
precision of 0 on %s (6); JSONDecode accepts a stray `]` or `}` after the value and the typed
Unmarshal accepts any trailing data (7); Modulo by zero returns the dividend though Value.Modulo
documents an infinity (8); Format's `%v` ignores every precision where the documentation has it
format a string as `%s` and a number as `%g` (9); the conversion Unify hands back for a tuple it
unified as a list (an object as a map) beside a list (map) that moved the element type again
applies the second conversion to the original tuple instead of the first conversion's result,
so it fails, panics or gives the wrong type on a value Convert converts (10).

Modelled as documented, not recorded: Chunklist with size 0 returns one chunk holding the whole
list (the implementation says so); Range with two arguments steps by -1 when the end is below
the start though the doc comment says the step defaults to 1; a null argument to Format's `%v`
prints `null`. A conversion `Unify` returns for a source type containing `DynamicPseudoType`
may fail at run time (convert.md: a run-time type check): `Unify([Map(String), Object{Z: String,
a: Dynamic}])` is `Map(Dynamic)`, and `{Z: null String, a: null Number}` does not convert
("attribute types must all match for conversion to map"); the Unification property counts it.

## History

- 2026-09-21: target created at `a918e11`; 8 bugs.
- 2026-10-07: generators rewritten in combinator style; known shapes drawn by default; eight narrow properties.
- 2026-10-07: go-cty/9 recorded (`%v` ignores every precision; the candidate the rewrite's FormatStringPrecision property had gated); ninth narrow property FormatDefaultVerbPrecision and its pin; the Format property now shrinks to go-cty/9 every round.
- 2026-10-07: go-cty/10 recorded (Unify's wrapped tuple and object conversions convert the original value twice; found by the Unification property at 1000 cases); tenth narrow property UnifiedTuplesConvertThroughTheirListForm and its pin; the Unification property names the shape and recovers the conversion's panic.
