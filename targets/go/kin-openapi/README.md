# go/kin-openapi

[getkin/kin-openapi](https://github.com/getkin/kin-openapi) (v0.149.0, 6 commits after): the Go
OpenAPI 3 toolkit: the `openapi3` document model with its schema validator (a hand-written one
for OpenAPI 3.0 and, behind `EnableJSONSchema2020`, a translation to
santhosh-tekuri/jsonschema for 3.1), `openapi3filter`'s request validation with the parameter
decoding of the OpenAPI styles, and the two routers (`routers/legacy`, `routers/gorillamux`).
Tested here: schema validation in both modes, the parameter decoding, the routers.

## Build

The patch adds `hegel.dev/go/hegel` to `go.mod` and a `hegel/` package of test files that drive
the public API: `go test -count=1 -run TestHegel -v ./hegel`. `TestHegelSchema` needs `python3`
with the `jsonschema` package (4.x) on PATH (the zoo's venv in CI).

## Oracles

The Python `jsonschema` package (Draft 2020-12) over a JSON-lines subprocess, given the
generated schema translated by the OpenAPI 3.0.3 rules: `nullable` adds `"null"` to the type,
the boolean `exclusiveMinimum`/`exclusiveMaximum` turn `minimum`/`maximum` into numeric
exclusive bounds, the formats the library enforces by default (`date`, `date-time`, `byte` as
their regular expressions; `int32`/`int64` as ranges where the type requires an integer)
become patterns and bounds, and, for the built-in validator's 3.0 reading, a schema that does
not permit null rejects it (a schema without type leaves null to its oneOf/anyOf/allOf, a
nullable branch counting). The JSON Schema 2020-12 mode is read as OpenAPI 3.1, where `{}`
accepts null. The OpenAPI 3.0.3 "Style Examples" table for parameter serialization, with the
decoded value observed through format validators registered under private names. The Path
Templating and Paths Object rules for the routers (a template matches a path of the same
number of segments, literal segments equal, a variable taking one non-empty segment, concrete
paths before templated ones; RFC 3986: `%2F` inside a segment is data). And the library against
itself: the two validation modes, `MultiErrors()` and `FailFast()`, the JSON round trip of a
schema, the two routers.

## Generator

Schemas of depth 0 to 3 over the 3.0 keywords (type, the string/number/array/object constraints,
enum, `nullable`, `oneOf`/`anyOf`/`allOf`/`not`, `additionalProperties` in its three forms,
formats known and unknown) and, in 40% of cases, the 3.1 spellings the built-in validator also
implements (type lists, numeric exclusive bounds, `const`); values shaped by the schema with
deviations (values at and next to bounds, multiples and non-multiples, duplicates, missing and
extra properties, astral-plane strings) or free. Parameters: location, style and explode from
the table (including the defaults), a primitive, an array or a flat object of strings,
integers, numbers and booleans, values with reserved and non-ASCII characters (never a
delimiter of their own style), empty strings, absent parameters, and malformed texts for the
numeric and boolean types. Documents of 1 to 4 path templates (literal and variable segments,
distinct shapes) with 1 to 5 methods each, with or without a server (base path or bare host);
requests instantiating a template with plain and percent-encoded segment values, or random.

## Properties

- `TestHegelSchema`: the built-in validator agrees with the oracle on the 3.0 reading, the
  JSON Schema 2020-12 mode on the 3.1 reading; `MultiErrors()` and `FailFast()` give the same
  verdict; the schema survives `json.Marshal`/`Unmarshal`; `Validate` does not panic (its
  verdict is counted, not judged: a generated `required` name may be absent).
- `TestHegelParameters`: `openapi3filter.ValidateParameter` accepts the serialized value and
  decodes exactly it; an absent required parameter is rejected, an absent optional one
  accepted; a malformed integer, number or boolean text is rejected.
- `TestHegelRouters`: the legacy and gorillamux routers find the route the rules give, with the
  path parameters' values, or report a missing path or method (ambiguous documents, several
  templated matches with no concrete one, are skipped).
- Eighteen narrow properties in `hegel_zoo_shapes_test.go`, one per recorded bug, each a
  generator over the bug's shape region with random contents judged by the same oracle
  (`TestHegelConstNullSchema`, `TestHegelParamBoolSpellings`, `TestHegelLegacyTrailingVariable`,
  ...): the deterministic expected failure of each bug.
- `TestHegelPin…`: one pin per recorded bug (expected failures).

The generators are combinator values (`hegel_zoo_test.go` holds the idioms: `weighted`, `chance`,
`maybe`, `pairs`, `many`, `deferred`, `positions`, `shaped`/`known`): schemas from a memoised
grammar per dialect with keyword fragments merged into a node, values guided by the node,
parameters as a record of layout, value, presence and malformation, documents as lists of path
items with requests rendered against the live document.

## Bugs

Eighteen, recorded in `bugs.toml`. Validator: `const: null` is lost (kin-openapi/1); the JSON
Schema 2020-12 mode falls back to the built-in validator, silently, for every nullable schema
(2), loses `nullable` on a type list (3), applies the integer formats to number-typed values
(6) and lets 1e300 pass `format: int64` (7); the built-in validator lets a nullable schema
accept null without applying enum, const, not or the combinators (4), lets a nullable branch
of a combinator override the parent's type for null (5), accepts 2^53 as a multiple of 10 (8),
and treats `{"not": {}}` and `{"oneOf": [{}, {}]}` as empty schemas (9). Parameters: integer,
number and boolean parameters accept Go literal syntax and the `strconv.ParseBool` spellings
(10, 11, 12). Routers: the legacy router gives path-not-found instead of method-not-allowed on
templated paths (13), falls through from a concrete path to a templated one for a missing
method (14), matches paths lacking the trailing variable segments with empty parameters (15),
splits after percent-decoding so `%2F` separates segments (16), and returns encoded parameter
values when the document has servers (18); the gorillamux router returns encoded values always
(17).

## Known shapes

The shapes of the recorded bugs are drawn by default (STYLE.md rule 11): `const: null`, nullable
schemas compared in the 2020 mode, enum/const/not/combinators beside `nullable`, integer formats
on number-typed values, 2^53 against `multipleOf`, 1e300 against `format: int64`, empty `not` and
`oneOf` schemas, the Go-syntax and ParseBool texts, encoded parameter values compared as decoded,
the legacy router compared on every request. A mismatch names the bug whose shape it has (the
`Known` switches keep the shape tests) and the property fails: `TestHegelRouters` every run
(bugs 15 and 17 are the most frequent shapes), `TestHegelSchema` and `TestHegelParameters` in
most runs (their shapes are a few percent of cases), and each narrow property on its own bug.
`HEGEL_NO_KNOWN=1`, read once, switches the known shapes off: the narrow properties skip, the
wide ones skip a mismatching case only when it has a known shape (measured at a fraction of a
percent of cases), the 2020 comparison is left out for schemas holding `nullable` (8.7% of
cases) and requests the legacy router would mishandle are reshaped rather than skipped (`%2F` to
`%20`, trailing slashes dropped, a method the item has for a templated path), so the test passes
and shows what the library gets right beside the recorded bugs.

## Not judged

Python's `$` matches before a trailing newline, so patterns are sent with `\Z`; `nullable:
true` without a type is not generated (3.0.3 says nullable needs a type, the library permits
null); a schema without type whose combinator permits null accepts null with enum/const/not
skipped (the same behaviour as kin-openapi/4, not generated); the legacy router's tolerance of
a trailing slash (`GET /a/b/` routes to `/a/b`) is in bug 15's notes but not pinned; `Validate`'s
verdict on generated schemas; the routers' error texts; documents with two templated matches and
no concrete one (undefined by the specification); the gorillamux router accepts documents with
duplicate template shapes that the legacy router's validation rejects.

## Not tested

Loading documents from files and `$ref` resolution, `openapi2conv`, `openapi3gen`, request and
response body decoding (JSON, form, multipart), `ValidateRequest`/`ValidateResponse` end to
end, security requirements, `readOnly`/`writeOnly` in request/response mode, defaults setting,
discriminators, `Content`-typed parameters, the 3.1-only keywords in the 2020 mode
(`patternProperties`, `dependentRequired`, `if`/`then`/`else`, `prefixItems`, `$ref` inside a
schema), server variables and per-path servers in the routers.

## History

- 2026-09-22: new target, three properties, 18 bugs.
- 2026-09-26: generators rewritten in combinator style; the known shapes are drawn by default
  and eighteen narrow properties, one per bug, are the expected failures beside the pins.
