# kaptinlin-jsonschema

[kaptinlin/jsonschema](https://github.com/kaptinlin/jsonschema) (MIT), pinned at `cde5e24`
(v0.9.10, 2026-09-13): a JSON Schema validator for drafts 4, 6, 7, 2019-09 and 2020-12 with
exact JSON numbers, `$ref`/`$id`/anchors/`$dynamicRef`, format assertion on request, a
meta-schema check (`ValidateSchema`), defaults-aware `Unmarshal`, schema serialization, and
hierarchical/flat result lists.

The patch adds the `hegel.dev/go/hegel` requirement to `go.mod` and eight test files (package
`jsonschema_test`): `hegel_test.go` (plumbing, the `Known` gates), `hegel_gen_test.go` (random
schemas valid by construction for their draft, guided and random instances, a schema mutator),
`hegel_oracle_test.go` (the Python oracle process), `hegel_props_test.go`, `hegel_refs_test.go`,
`hegel_more_test.go`, `hegel_defaults_test.go` (the ten properties) and `hegel_pins_test.go`
(eight pins). The generator, the oracle and the format and number models are those of the
`go/jsonschema` target (santhosh-tekuri), adapted to this API. **Needs `python3` with the
`jsonschema` package (4.26, with `referencing` and `jsonschema_specifications`) on PATH**: it
is the validation oracle, and the 2019-09 and 2020-12 meta-schemas that `ValidateSchema` loads
over HTTP are served offline from `jsonschema_specifications`' files (the compiler's `http`
and `https` loaders are replaced). The whole run takes about four seconds; the library's own
tests run in the same `go test`.

## Properties

| Test | Checks |
|---|---|
| `TestHegelValidationMatchesPython` | Random schemas in a random draft (every core keyword, `$ref` by pointer/anchor/embedded `$id`, `$dynamicRef`, boolean schemas, `unevaluated*`, `dependentSchemas`/`dependencies`, `if/then/else`) on guided and random instances: `ValidateJSON` agrees with Python's `jsonschema`, and `Validate` on the decoded value and `ValidateMap` agree with `ValidateJSON`. |
| `TestHegelSchemaCheckMatchesPython` | The same schemas, three quarters of the time damaged in one place: `ValidateSchema` accepts them exactly when `check_schema` does; an unresolvable `$ref` or an invalid `pattern` is a `Compile` error; `Compile` accepts what Python accepts. |
| `TestHegelReferencesAreTransparent` | Reaching a schema through `$ref` (pointer, anchor, embedded id in its URI forms, chains, `$dynamicRef`, `$recursiveRef`, ignored siblings up to draft 7) or a one-armed applicator accepts exactly what the plain schema accepts, at the root and one property down. |
| `TestHegelSerializedSchemaIsEquivalent` | `json.Marshal` of a compiled schema compiles to a schema with the same verdicts, and marshals again to the same JSON. |
| `TestHegelUnmarshalAppliesDefaults` | `Unmarshal` into a map returns the instance with property defaults filled in (through `properties`, `items`, `$ref`) and nothing else changed, from JSON and from a map alike; schemas whose defaults sit under other applicators are not judged. |
| `TestHegelOutputsAreWellFormed` | For a failing validation: the flag is invalid, and under the library's output convention (see below) every unit's instance location resolves in the enclosing instance, its evaluation path names an applicator of the enclosing schema with the key or index the library appends, its schema location ends in that path, invalid units carry errors or details, messages are non-empty, both lists marshal and `DetailedErrors` is non-empty. |
| `TestHegelNumbersAreExact` | `minimum`/`maximum`/`exclusive*`/`multipleOf`/`const`/`enum`/`type: integer`/`uniqueItems` follow exact rational arithmetic on decimal texts from `1e-400` to `1e400` and 30-digit integers, for every Go representation of the same number (`json.Number`, `int64`, `int`, `int8`, `uint64`, `float64`, `float32`), including arrays above 20 items. |
| `TestHegelFormatsFollowTheirRFCs` | With `SetAssertFormat(true)`: `date`, `time`, `date-time`, `duration`, `ipv4`, `ipv6`, `uuid`, `json-pointer`, `relative-json-pointer` and `hostname` against models of their grammars on generated strings, their mutations and hand-written edge cases. |
| `TestHegelPin...` | One plain test per recorded bug. |

## Bugs

Eight, see `bugs.toml`: a plain-name fragment `$id` (`"#A"`, drafts 4-7) breaks the references
inside its subschema (1); output paths name the normalised keywords for legacy tuple `items`,
`additionalItems` and `dependencies` (2); `schemaLocation` reads `...schema##/...` when the
resource id ends in `#` (3); `ipv4`, `time` and `date-time` accept a signed field (4); `duration`
rejects `P1Y1D` and `PT1H1S` (5); `maxLength`/`minLength`/`maxContains`/`minContains` at or
beyond 2^63 are misread (6); output locations do not escape `~` and `/` in property names (7);
a missing required property produces a `properties/<name>` unit located at the absent member (8).

## Notes

- The library's result lists follow a convention of its own rather than the specification's
  output format: every unit's `evaluationPath`, `schemaLocation` and `instanceLocation` are
  relative to the enclosing unit; per-member applicators append the instance key or index
  (`/properties/p`, `/patternProperties/<name>`, `/additionalProperties/<name>`,
  `/propertyNames/<name>`, `/items/<i>` also for a single `items` schema, `/prefixItems/<i>`,
  `/dependentSchemas/<name>`, whose details are nevertheless evaluated against the whole object,
  and `/propertyNames/<name>`, evaluated against the name); the subschema reached through `$ref`,
  `then` or `else` is an intermediate unit with empty paths. The well-formedness property models
  that convention.
- Accepted differences with Python noted from the santhosh-tekuri target still hold here:
  Python crashes on some legacy-anchor schemas (no verdict), and only notices an unresolvable
  `$ref` when validation reaches it.
