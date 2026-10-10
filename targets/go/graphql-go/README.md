# go/graphql-go

[graphql-go/graphql](https://github.com/graphql-go/graphql) (v0.8.1 plus 67 commits): the GraphQL
implementation for Go (parser, validator, executor with the new query planner). Tested here:
`graphql.NewSchema` on generated type systems (objects, interfaces, unions, enums, input objects,
lists and non-nulls, arguments and input fields with default values, descriptions and
deprecations) and `graphql.Do` with generated operations (aliases, literal and variable arguments,
variable defaults, `__typename`, inline fragments with and without type conditions, fragment
spreads, `@skip`/`@include`, a second operation selected by name) against generated root data.

## Build

The patch adds `hegel.dev/go/hegel` to `go.mod` and a `hegel/` package of fourteen
`hegel_zoo_*_test.go` files that drive the public API. `go test -count=1 -run TestHegel -v ./hegel`
needs `python3` with the `graphql-core` package (3.2+) on the PATH.

## Oracle

graphql-core (the python port of graphql-js), one process per test: it builds the same schema
from SDL (each object type checks the `__typename` of its values, as the Go side's `IsTypeOf`
does), executes the same operation with the same variables and root data, and answers with its
data and errors. The data (numbers normalised) and the sorted error paths must agree; when both
sides return no data, the error paths must agree too unless both are request errors. Fields named
`echo…` resolve to the canonical JSON of their coerced arguments on both sides (integers plain,
floats with four decimals, null-valued entries left out), so argument coercion and default values
are compared as well.

## Properties

- `TestHegelExecute`: a type system of 1-2 enums, 0-2 input objects, 0-2 interfaces, Query and
  2-3 objects, an optional union; root data with values of the right kind (a few of the wrong
  kind, nulls in non-null positions, non-lists for lists, wrong `__typename`s); an operation of
  up to 25 field selections with the features above. Classes counted: ok, errors agree, both
  reject (request errors), both reject with agreeing paths. Expected failure: the operations
  and the root data carry the shapes of graphql-go/1 to 14 and 19 at their natural rates (a
  null literal and a non-null variable with a default each in one case of four, a twin
  selection with a variable-driven `@skip` on the first copy in one of fifteen, a transitive
  field conflict in one of forty, a wrong-kind leaf value of a recorded kind drawn in a sixth
  of the cases and selected in a tenth of those), and the shrunk one is the twin selection
  (7): `query($v1: Boolean!) { __typename @skip(if: $v1) __typename }`, the fewest draws (a
  null literal needs a field with an argument).
- `TestHegelIntrospection`: graphql-core's introspection query (without the newer fields) on the
  same type system; the results must agree after normalisation (introspection types and
  directives left out, lists sorted by name, built-in scalar descriptions and an interface's own
  interfaces not judged, a `= null` default - which the Go API cannot express - counted as none,
  an integer-like ID default the same quoted or bare). Expected failure: nearly every type
  system has a description missing somewhere (graphql-go/16), and the shrunk one has nothing
  else.
- `TestHegelValidate`: the generated operation with one or two text mutations aimed at the
  validation rules (unknown field/argument/directive/type, undefined or unused fragments and
  variables, duplicate names, variables of non-input types or in the wrong position, leaf and
  object selection errors, fragments on scalars and inputs, impossible spreads, cycles, anonymous
  and duplicate operations, missing root operation types, SDL in the document, conflicting
  aliases and arguments, unknown and duplicate input fields, a directive twice on one
  selection); `ValidateDocument`'s verdict must equal graphql-core's `validate`. Intermittent
  expected failure: the two mutations graphql-go misses (17, 18) are one entry each of the
  table's thirty-six, and reach the bug only when no other mutation beside them makes both
  sides reject, and the transitive field conflict (19) is drawn in one operation of forty
  (36 of forty runs at a hundred cases fail; the shrunk failure is 17 in twenty-one of them and 18
  in fifteen, never 19, whose chain of fragments the shrinker trades for a mutation).
- Nineteen narrow properties, one per recorded bug, each a generator over the bug's shape with
  random contents and the wide property's judge, failing every run:
  `TestHegelIntrospectionDefaultsAreLiterals` (15), `TestHegelIntrospectionMissingDescriptionsAreNull`
  (16), `TestHegelValidateDirectivesAreUniquePerLocation` (17), `TestHegelValidateDefinitionsAreExecutable`
  (18), `TestHegelValidateTransitiveFragmentConflictsAreCaught` (19), `TestHegelExecuteNullLiteralsParse`
  (1), `TestHegelExecuteDefaultedNonNullArgumentsAreOptional` (2), `TestHegelExecuteNonNullVariablesTakeDefaults`
  (3), `TestHegelExecuteNullVariablesStayNull` (4), `TestHegelExecuteVariablesOfTheWrongKindAreRejected`
  (5), `TestHegelExecuteIntLiteralsAre32Bit` (6), `TestHegelExecuteSkippedSelectionsMergeWithTheirTwins`
  (7), `TestHegelExecuteInlineFragmentsNeedNoCondition` (8), `TestHegelExecuteEnumsSerializeOnlyNames`
  (9), `TestHegelExecuteLeafSerializationErrorsAreReported` (10), `TestHegelExecuteIntsDoNotTruncate`
  (11), `TestHegelExecuteBooleansAreStrict` (12), `TestHegelExecuteStringsAreStrict` (13),
  `TestHegelExecuteRootErrorsAreAllReported` (14).
- `TestHegelPin…`: one pin per recorded bug (expected failures).

## Bugs

Nineteen, recorded in `bugs.toml`. The language and validation: the `null` literal is a syntax
error (graphql-go/1); a non-null argument or input field with a default must still be provided
(2); a non-null variable with a default is rejected (3); an inline fragment without a type
condition under a list or non-null field is rejected (8); an Int literal outside 32 bits is
accepted (6). Coercion: a variable given null takes its default or the argument's (4); variable
values of the wrong kind are coerced instead of rejected (5). Execution: a field selected twice
is dropped when the first selection is excluded by a variable-driven `@skip`/`@include` (7); a
leaf value that cannot be serialized becomes null without a field error (10); Int serialization
truncates fractional floats (11); Boolean serialization turns strings into true (12); String and
ID serialization print slices, maps, booleans and floats with fmt (13); `Enum.Serialize` of a
slice or map panics (9); when a non-null root field is null the other root fields' errors are
dropped (14). Introspection: enum, list and input object defaults printed as quoted fmt strings
(15); an empty string instead of null for a missing description (16). Validation: the same
directive twice on one selection accepted (17); a type definition in an executable document
accepted (18); a field conflict reached only through a fragment spread inside a fragment passes
validation and executes (19: the rule's recursion compares the nested fragments with the
enclosing fragment instead of the selection set).

## Drawn shapes

The properties draw the shapes of the recorded bugs by default and name them before the library
is called (DESIGN.md decision 3, STYLE.md rule 11); `HEGEL_NO_KNOWN=1` switches the shapes off
and every property then passes. The type system is a package-level generator (`schemas`) whose
descriptions are missing at 75 % (the shape of 16; zero under NO_KNOWN, when enum values get
descriptions too) and whose arguments and input fields of enum, list or input-object type get
default values at the natural rate (15; scalar types only under NO_KNOWN); `introShape` names
15 where such a default is present and 16 where a description is missing (nearly every case by
default; the shrunk failure is a description-less schema). The validation cases draw one or
two mutations from the table with the duplicate-directive and type-definition mutations in it at
their natural weight (left out under NO_KNOWN); `validateShape` names 17 or 18 when the
unmutated document is valid by graphql-core's verdict, a mutation graphql-go misses was applied,
and every other mutation applied is one both sides accept (an operation of a kind the schema has
no root type for), and 19 where graphql-core's only errors on the unmutated document are field
conflicts and a replica of graphql-go's rule on the operation tree misses them (19 before 17
and 18: graphql-go accepts the document whatever the mutation, unless one makes both sides
reject). The narrow properties draw a type system with every description present and one
deliberate enum, list or input-object default (15); one description blanked in a drawn place,
with scalar defaults only (16); a valid generated document plus `@skip` or `@include` two or
three times on a drawn placement (a root field, `__typename`, a fragment spread, an inline
fragment with or without a condition; on the operation or a fragment definition both sides
reject it as misplaced) (17); a valid generated document plus a drawn type, interface, union,
enum, input, scalar, schema, directive or `extend type` definition before or after the
operation (`extend` of the other kinds is a syntax error to graphql-go, so both reject) (18).

The operation is a drawn tree of records (selections, variable and fragment definitions)
rendered to text by pure functions, with the shapes of graphql-go/1 to 8 as weights of its
choices (`operationShapes`; zero under NO_KNOWN, and zero for the validation properties, whose
base document must be valid on both sides): a null literal at a nullable literal position at
15 % (1); a non-null argument or input field with a default left out at the nullable ones'
rate (2); a default on a non-null variable at 30 % (3); a null runtime value where a default
of the variable's or the argument's or an input field's applies and an echo field shows the
substitution, at 15 % (4); a runtime value of a kind graphql-go coerces instead of rejecting
(an Int from "3", 1.5 or true; a Float from "1.5" or true; a String or an ID from a number, a
boolean or a list; a Boolean from a string, a number or a list) at 4 beside 92 strict and 8
both sides reject, where wrong kinds are drawn (5); an Int literal outside 32 bits the same
way (6); a selection twice with a variable-driven `@skip`/`@include` on the first copy and
none on the second, the variable excluding it three times in four, at 5 % of the selections
(7; a variable condition then also goes on any selection, where under NO_KNOWN it goes only on
a freshly aliased field, which nothing merges with); the type condition left off an inline
fragment directly under a list or non-null field at 20 % (8). `executeShape` names the bug
from the operation record and graphql-core's reply before graphql-go is called: where
graphql-core rejects the request, 5 then 6 unless something makes graphql-go reject too; where
it executes, 1, 2, 3, 8 in that order; else a replica of graphql-go's query plan (`plan.go
collectInto`: the first selection with a response key keeps its predicates, later ones merge
into it and lose theirs) is walked beside graphql-core's collection over graphql-core's data
for a key one side includes and the other drops (7), then for an echo field showing a
substituted default (4). 5 and 6 are named in few cases of the wide property (an operation
with a wrong-kind draw nearly always carries a null literal or a left-out default too, which
makes graphql-go reject for its own reasons); their narrow properties reach them every case.
The narrow execution properties add one field to Query for the shape (`zn(n: T)`, `zd(n: T! =
v, in: InD)`, `zv`, `echoZ`, `zk`, `zi`, `zt`, `zw: Query!`), draw the shape at the root of an
otherwise clean operation (no shape, no value both sides reject) and are judged by
`judgeExecute` like the wide property.

The root data is a drawn record too (`hzData`, the value resolved for each field as a sum
type: null, a leaf value, a wrong-kind leaf value with the bug it reaches, a list, a non-list,
an object, an object of a type not possible for the abstract type, left out), rendered to the
map both sides resolve from; of the wrong-kind leaf values, the kinds both sides serialize
alike (an Int from "3", 4.0 or true, a String from a number, a Boolean from a number, an ID
from an int) are four draws in five and the recorded shapes one in five (`dataShapes`; none
under NO_KNOWN): an enum from a slice or a map (9), an Int from a non-numeric string, a slice
or an int outside 32 bits, a Float from a non-numeric string, a slice or a map, an enum from
an unknown or lowercased name, a number or a bool (10, named in a nullable position only: in a
non-null one both sides report and propagate alike), an Int from a fractional float (11), a
Boolean from a string, a slice or a map (12), a String from a slice or a map, an ID from a
bool, a fractional float, a slice or a map (13). The plan replica walks the data beside
graphql-core's reply and names the shape of a wrong value at a path graphql-core reported an
error for, 9 to 13 before 7 and 4; 14 (a non-null root field null beside another root field's
error, graphql-go dropping the other) is named last, from graphql-core's data being null with
two field errors; it has no generator switch of its own (it is plain data), so under NO_KNOWN
the judge skips its rare instance (about one case in three thousand). The transitive field
conflict (19) is an alternative of a selection set at one in fifty: a leaf field or
`__typename` under a fresh alias beside a chain of two or three fragments ending in a field
of a different name under the same alias; the replica of graphql-go's
OverlappingFieldsCanBeMerged rule (`hegel_zoo_conflict_test.go`, run as graphql-go has it and
with step (E) corrected) decides in the generator and the classifiers whether the document has
a conflict graphql-go catches (both reject) or one it misses (the shape, confirmed by
graphql-core's verdict); under NO_KNOWN the operations are filtered by it. The narrow
properties of 9 to 13 resolve one added leaf field of Query to a value of the shape in
otherwise plain data; 14's resolves an added `zl: [Int]` to an Int and `zn: Int!` to null; 19's
puts the conflicting chain at the root of a valid document.

Design notes:

- Default values reach graphql-go as Go values and graphql-core as SDL literals, so the Go
  values are what literal coercion gives (an Int literal is a float64 for Float and a string
  for ID; absent input fields with defaults are filled in), as graphql-js's `defaultValue` is an
  internal value too.
- graphql-go leaves null-valued arguments and input fields out of a resolver's Args map, so the
  canonical form treats absent and null as equal; the difference is not judged.
- graphql-core cannot build a self-referencing input field with a default value, so the
  generated input objects give none there.
- The mutations are inserted at the first brace outside the variable definitions (a variable's
  default may be an input object literal with braces of its own).
- A variable's default value is drawn like an argument literal (strict at 90 %), where the old
  generator drew it strict always, so that the shape of graphql-go/6 reaches variable defaults.
- The lowercased enum value of the wrong-kind pool is the first value with a capital in lower
  case; the old pool lowercased the first value, which for an enum like `beta` was a valid
  value.

## Not tested

Mutations and subscriptions, custom scalars (`DateTime`), the introspection of directives
(graphql-go has neither `@specifiedBy` nor `@oneOf` and its `@deprecated` lacks the 2021
locations), `ResolveType` functions, resolver errors and thunks, `Plan`/`PlanQuery`/`ExecutePlan` and the
plan cache directly, extensions, `Schema.AppendType`/`AddImplementation`, error messages and
locations, the printer.

## History

- 2026-09-21: new target, one property, 14 bugs.
- 2026-09-21: introspection and validation properties, 4 more bugs.
- 2026-10-09: rewrite part 1 of two: the type system as a combinator generator, the
  introspection and validation properties drawing the recorded shapes, four narrow properties;
  graphql-go/19 found on an unmutated document.
- 2026-10-10: rewrite part 2a: the operation as a drawn tree, the execution property drawing
  the shapes of the operation bugs 1 to 8, eight narrow properties.
- 2026-10-10: rewrite part 2b, the series complete: the root data as a drawn record, the
  execution property drawing the serialization bugs 9 to 14 and the transitive field conflict
  19, seven more narrow properties, the old switches removed.
