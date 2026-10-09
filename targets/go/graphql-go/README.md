# go/graphql-go

[graphql-go/graphql](https://github.com/graphql-go/graphql) (v0.8.1 plus 67 commits): the GraphQL
implementation for Go (parser, validator, executor with the new query planner). Tested here:
`graphql.NewSchema` on generated type systems (objects, interfaces, unions, enums, input objects,
lists and non-nulls, arguments and input fields with default values, descriptions and
deprecations) and `graphql.Do` with generated operations (aliases, literal and variable arguments,
variable defaults, `__typename`, inline fragments with and without type conditions, fragment
spreads, `@skip`/`@include`, a second operation selected by name) against generated root data.

## Build

The patch adds `hegel.dev/go/hegel` to `go.mod` and a `hegel/` package of eleven
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
  reject (request errors), both reject with agreeing paths.
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
  sides reject (29 of forty runs at a hundred cases fail; 18 more often than 17 under the
  engine's draw).
- Four narrow properties, one per introspection and validation bug, each a generator over the
  bug's shape with random contents and the wide property's judge, failing every run:
  `TestHegelIntrospectionDefaultsAreLiterals` (15), `TestHegelIntrospectionMissingDescriptionsAreNull`
  (16), `TestHegelValidateDirectivesAreUniquePerLocation` (17), `TestHegelValidateDefinitionsAreExecutable`
  (18).
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

## Drawn shapes (the introspection and validation properties; the execution property follows)

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
no root type for). A field conflict graphql-core reports on the unmutated document and
graphql-go accepts (19) is skipped and counted until part 2 of the rewrite draws that shape on
purpose. The narrow properties draw a type system with every description present and one
deliberate enum, list or input-object default (15); one description blanked in a drawn place,
with scalar defaults only (16); a valid generated document plus `@skip` or `@include` two or
three times on a drawn placement (a root field, `__typename`, a fragment spread, an inline
fragment with or without a condition; on the operation or a fragment definition both sides
reject it as misplaced) (17); a valid generated document plus a drawn type, interface, union,
enum, input, scalar, schema, directive or `extend type` definition before or after the
operation (`extend` of the other kinds is a syntax error to graphql-go, so both reject) (18).

`TestHegelExecute` still keeps its generators away from the fourteen execution bugs behind
`HZKnown` switches (no null literals, non-null arguments with defaults always provided, no
defaults on non-null variables, no null variable values, only wrong-kind variable values both
sides reject, no out-of-range Int literals, variable-driven directive conditions only on
freshly aliased fields, no condition-less inline fragments under wrapped fields, no wrong-kind
leaf values of the recorded kinds; with `rootPropagationDropsErrors`, graphql-go's error paths
need only be among graphql-core's when both data are null); the collector counts the
avoidances, and `ZOO_KNOWN_OFF=name` turns a switch off. Part 2 of the rewrite replaces that
with drawn shapes and fourteen narrow properties.

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
