# fast-json-stringify

[fast-json-stringify](https://github.com/fastify/fast-json-stringify) compiles a JSON Schema (draft 7
plus OpenAPI's `nullable`) into a `stringify` function, "significantly faster than `JSON.stringify()`
for small payloads", and is the serializer behind fastify's response schemas. Pinned at 7.0.1,
367c8e0 (2026-09-18), MIT.

The library is plain CommonJS with no build; the tests `require('../index.js')`, so the runtime
dependencies are installed and Hegel goes under `.hegel/`. Tests: `hegel/hegel.test.mjs`, run with
`node --test`. `ZOO_FULL=1` widens the generators to the shapes that hit known bugs (odd property
names, string/array unions, tuples with type-less, nullable, union or const items, `additionalItems`
schemas, BigInts); `ZOO_COLLECT=1` prints mismatch statistics.

## Oracle

There is no second implementation of exactly this behaviour, so the oracle is the README's own
description of the output, written down as a model (`hegel/model.mjs`): supported types and the
coercions of non-conforming values (`null` to `0`/`""`/`false`/`{}`/`[]`, floats to integers with
the `rounding` option, `Date` to `toISOString()`, `RegExp` to its source, BigInt to its digits,
`format: date`/`time`/`date-time`), `required` and `default`, undeclared properties dropped unless
`patternProperties`/`additionalProperties` say otherwise (additional ones at the end), tuples and
`additionalItems`, `anyOf`/`oneOf` tried in order with ajv, `allOf` merged, `if`/`then`/`else`,
`const`, `nullable`, multi-type `type` arrays, `$ref` to `definitions` and to `options.schema`.
Branch selection uses ajv with ajv-formats and the library's own rewrite of `type: string` into
"string or object with `toJSON`", so the model picks the same anyOf option the library does. The
generators (`hegel/gen.mjs`) build a random schema together with a generator of values that conform
to it; a second oracle is ajv itself, validating the output against the schema.

## Properties

| Test | Checks |
| --- | --- |
| `TestHegelConformingValuesSerializeAsTheSchemaSays` | a conforming value serializes to the model's output (parsed and compared as JSON); when the model finds no matching anyOf option the library throws too |
| `TestHegelObjectKeyOrderIsRequiredDeclaredAdditional` | object keys come out required first, then the other declared properties in schema order, then pattern/additional ones |
| `TestHegelRefsAreTransparent` | moving every property schema into `definitions` (`#/definitions/x`) or an external schema (`options.schema`, `ext#/definitions/x`) gives byte-identical output |
| `TestHegelDebugRestoreAndStandaloneReproduceTheSerializer` | `mode: 'debug'` + `build.restore`, and `mode: 'standalone'` code (with and without `inlineValidators`) loaded with `require` rewritten to the checkout, give the same output as the direct build (in the default run, Dates under anyOf/if are skipped for the non-inline variant: bug 13) |
| `TestHegelBuildLeavesTheSchemaUnchanged` | `build()` does not modify the schema object (in the default run, modulo the known type sorting/inference of bug 2) |
| `TestHegelDocumentedCoercionsApply` | the README's coercions: `null` per type, `rounding` for floats, numeric strings and BigInts as integers, truthiness as boolean, numbers/booleans/`Date`/`RegExp` as strings; at the top level and inside an object |
| `TestHegelOutputValidatesAgainstTheSchema` | the output, parsed, validates against the schema with ajv (`nullable` rewritten to a `null` type union) |

Pins (`TestHegelPin*`) reproduce the bugs in `bugs.toml` and are listed as expected failures.

## Not tested

- `format: 'unsafe'`, `maxDepth`, the `ajv` option, `compileValidators`, the `largeArrayMechanism`
  mechanisms on arrays of 20000+ items (only their leak between builds, bug 1).
- Schema keywords the library documents as ignored (`enum`, `minimum`, `pattern`, ...): only used
  for type inference.
- `toJSON` on objects, `Symbol`/function values, circular `$ref`s.

## History

- 2026-09-20: created (turn 319); 13 bugs recorded.
