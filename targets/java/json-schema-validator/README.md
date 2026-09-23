# json-schema-validator

[networknt/json-schema-validator](https://github.com/networknt/json-schema-validator) (Apache-2.0),
pinned at `2575a025` (3.0.7, 2026-09-18): a JSON Schema validator for Jackson 3 covering drafts 4,
6, 7, 2019-09 and 2020-12, with output formats, fail-fast, type-loose mode, format assertions and a
schema walker.

The patch adds `hegel/` (its own Maven module; `setup` installs the checkout's artifact into the
local repository first). The oracle is Python's `jsonschema` package (4.26+, with `referencing`),
driven as a child process speaking one JSON request per line (`Oracle.java`), with an exact
`multipleOf` (its float division is inexact beyond 2^53). `Gen.java` holds the generators as
values: a schema per draft is `lists` of keyword fragments (small `ObjectNode`s from `weighted`/
`oneOf` choices over types, enum/const, numeric bounds, string bounds/pattern/format, items/
prefixItems/additionalItems/contains/min-maxContains/uniqueItems/unevaluatedItems, properties/
required/additionalProperties/patternProperties/propertyNames/dependencies/dependentRequired/
dependentSchemas/unevaluatedProperties, allOf/anyOf/oneOf/not/if-then-else, `$ref` into
`$defs`/`definitions`, boolean subschemas) merged in order by a pure function, recursion through
`schema(depth)`/`sub(depth)` generator-returning methods with a depth bound; `guided(schema, depth)`
turns a drawn schema into a generator of instances shaped by its hints (const, enum, a combinator
branch, the type and its keywords, each with its own weight) or arbitrary values; the meta-schema
test draws a list of `Mutation` records (object position modulo the live count, keyword, remove or
a value) applied afterwards. `weighted`/`chance`/`maybe` are the zoo's stand-ins for weighted
choice, shrinking towards the first (simplest) alternative.

## What is tested

- `hegelValidationAgreesWithPythonJsonschema` - valid/invalid across the five drafts, with format
  assertions on or off (mirrored to the oracle's format checker).
- `hegelErrorLocationsMatchTheFailingInstances` - for schemas without combinators or references,
  the set of (instance location, keyword) pairs of the errors equals python's.
- `hegelOutputFormatsAgree` - `validate(JsonNode)` against the BOOLEAN, FLAG, DEFAULT, LIST,
  HIERARCHICAL and RESULT output formats, fail-fast (same verdict, at most one error),
  `validate(String, JSON)` and `validate(String, YAML)`.
- `hegelMetaSchemaValidationAgreesWithCheckSchema` - random schema documents with random
  mutations, validated against the draft's meta-schema, agree with python's `check_schema`; the
  accepted ones compile and validate.
- `hegelTypeLooseAndNarrowingFollowTheirDocs` - `typeLoose` as documented (numeric/boolean
  strings, scalars as one-element arrays) and the draft-4 versus draft-6+ reading of `integer`.
- `hegelPin...` - one plain test per recorded bug.

## Bugs

See `bugs.toml`: `contains` with `maxContains` below `minContains` rejects every non-array
instance, twice when both bounds are explicit (1); `unevaluatedProperties` ignores `failFast` and
reports every offending property (2); `uniqueItems` iterates the members of any instance, so an
object with two equal values is rejected (3, found by the 2026-09-23 rewrite of the generators in
combinator style: `{"uniqueItems": true}` against `{"a": null, "b": null}`).

## Notes

- Representational differences folded into the comparison: python reports one error for all the
  extra items/properties of `items: false`/`additionalProperties: false` (the library one per
  offender), attributes property-name failures to the inner keyword (here `propertyNames`), too
  few `contains` matches to `contains` or `minContains` depending on the count, and a `false`
  subschema's error at the parent location with no keyword (a quirk of its `descend`), so such
  errors are left out on both sides.
- Oracle limits: python's vendored draft-06/07 meta-schemas lack the `enum` minItems/uniqueItems
  constraints of the published ones (the library's copies match the published ones; as `items` and
  `dependencies` values are an `anyOf` there, the library also reports the other branch's `type`
  error at the parent of such an enum, which the meta-schema property drops as well); its draft
  2019-09 `unevaluatedProperties` (a `_legacy_keywords` copy) does not count the properties an
  object-valued `additionalProperties` evaluates, unlike its 2020-12 one, so such 2019-09 schemas
  are skipped in the validity comparison; its `check_schema` accepts a relative `$id` such as
  `"string"` or `""`, which the library's default `SchemaIdValidator` refuses because no base URI
  makes it absolute (the spec requires that), so the meta-schema property tolerates that
  `SchemaException` as it does the non-string `$ref` (all three found by the 1000-case runs of
  2026-09-23); its `date`
  checker rejects year 0; `additionalItems` next to a boolean `items` crashes it (such cases are
  skipped); formats are restricted to those both sides check (ipv4, ipv6; date from draft 7; uuid
  from 2019-09).
- `anyOf`/`oneOf` validate their branches without fail-fast and report every branch's errors when
  the keyword fails; the at-most-one-error check skips schemas containing them.
