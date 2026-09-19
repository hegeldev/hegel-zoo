# gqlparser

[vektah/gqlparser](https://github.com/vektah/gqlparser) (MIT), pinned at `5d4af16` (v2.5.37 plus
two commits, 2026-09-07): the GraphQL parser and validator behind gqlgen - lexer, parser for
executable and type system documents, schema loading (`LoadSchema` with the built-in prelude) and
the query validation rules, ported from graphql-js. The readme targets the September 2025 spec on
the basis of graphql-js v16.13.2.

The patch adds the `hegel.dev/go/hegel` requirement to `go.mod` and five test files at the module
root (package `gqlparser_test`): `hegel_test.go` (plumbing, the `Known` gates),
`hegel_gen_test.go` (generators), `hegel_oracle_test.go` (the graphql-core child process),
`hegel_props_test.go` (the properties and the canonical dumps) and `hegel_pins_test.go` (twenty-four
pins). **Needs `python3` with the `graphql-core` package on PATH**: graphql-core 3.2 (the Python
port of graphql-js) is the second implementation, one process per `go test`, batches of documents
as JSON lines. The whole run takes about a minute.

## Properties

| Test | Checks |
|---|---|
| `TestHegelParseAgreesWithGraphQLCore` | A generated executable document (operations with variable definitions, defaults and directives, fragments, inline fragments, aliases, arguments, every value kind, block strings, comments, commas, `\r\n`, a BOM) is accepted or rejected by both parsers alike, and accepted documents have the same AST in a canonical form (operations, variables with type strings, selections, arguments, directives, values with their kind). A document with a deliberately malformed token (`01`, `1.`, `\x`, an unterminated string, `T!!`, `{}`, `...on`, a stray `}`) must be rejected by both. |
| `TestHegelSchemasAgreeWithGraphQLCore` | A generated SDL document (scalars, objects, interfaces implementing interfaces, unions, enums, input objects, directive definitions with locations and `repeatable`, descriptions, applied directives incl. `@deprecated`, `@specifiedBy`, `@oneOf`, a `schema` definition, extensions of every kind) loads as the same schema in `LoadSchema` and in graphql-core's `build_schema` + `validate_schema` - or is rejected by both. The canonical schema: root types, description, directives, every non-builtin type with kind, description, directives, interfaces, fields with type strings, arguments, defaults and directives, union members, enum values, input fields, and every custom directive definition. Interface implementors mostly copy the interface's fields (with covariant tweaks); occasionally a field, an argument or a transitive interface is left out, a type referenced but undefined, a kind used where another is required. |
| `TestHegelValidationAgreesWithGraphQLCore` | Against a fixed schema (interfaces, a union, an enum, input objects, a custom scalar, a repeatable directive, root types for all three operations), a type-directed query with faults injected at random (unknown fields and arguments, wrong-typed literals, missing required arguments, misdeclared or undeclared or unused variables, incompatible fragment spreads and type conditions, unused fragments and fragment cycles, misplaced and duplicated directives, conflicting aliases, multi-field subscriptions, deep introspection) is valid for `validator.Validate` exactly when graphql-core's `validate` reports no error. |
| `TestHegelOracleVersion` | The oracle is graphql-core 3.x. |
| `TestHegelPin...` | One plain test per recorded bug. |

Not judged, because the oracle is lenient where the spec is not: control characters inside
strings and comments (graphql-core 3.2 accepts them, gqlparser rightly does not), `1e400` as a
Float literal, the values of custom directives' arguments in SDL and `null` for a non-null
directive argument (neither implementation checks the former, only gqlparser the latter), a
directive definition applying itself to its own arguments, `scalar String` redeclared, a default
value on an input field whose type reaches back to the containing input object (`input B { b: B
foo: B = {} }`: graphql-core recurses without end coercing it, so such fields get no default). Also
not judged: the prelude's `@defer` directive (gqlparser's own extension), and cases where
graphql-core raises while validating a subscription whose `@skip`/`@include` argument is a variable
or a bad literal (its SingleFieldSubscriptions rule collects fields and coerces the directive
arguments on the way) - those are skipped.

## Bugs

Twenty-four, see `bugs.toml`. Lexer and parser: lone surrogate escapes accepted as U+FFFD (1),
surrogate pairs not combined (4), the variable-width `\u{...}` escape rejected (2), a block string
closed by the last three of four or more quotes (3), the dedent of block strings counting the
first line (17), no lookahead after a number so `[1a]` is two values (5), variables allowed in the
const directives of a variable definition (20). Schema loading: directive argument values (6),
duplicate directive arguments (7) and duplicate keys in object values (8) unchecked in SDL;
duplicate (9) and self (10) interface implementation; extending an undefined type defines it (11);
duplicate (12), missing (13) and non-object (15) query root; `@oneOf` constraints (14);
`@deprecated` on required arguments and input fields (16); enum values named `__x` (18); duplicate
argument definitions (19); a non-repeatable directive twice on a type, or in a type and its
extension (22). Query validation: `{}` accepted as a value of any type (21), the single-field
subscription rule counting field names instead of response keys (23), list and object argument
values never compared when merging fields (24). The other validation rules agreed with graphql-core
on every generated document.
