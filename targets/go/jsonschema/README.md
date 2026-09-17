# jsonschema — Hegel properties for `github.com/santhosh-tekuri/jsonschema/v6`

[santhosh-tekuri/jsonschema](https://github.com/santhosh-tekuri/jsonschema)
validates JSON against JSON Schema drafts 4, 6, 7, 2019-09 and 2020-12,
with `$ref`/`$id`/anchors/`$dynamicRef`, format and content assertions, and
the flag/basic/detailed output formats. Pinned at `ec6106e` (v6.0.3, the
`boon` default branch).

## Build

The patch adds `go.mod` changes and six test files: `hegel_test.go`
(plumbing, the `Known` gates), `hegel_gen_test.go` (random schemas valid by
construction for their draft, guided and random instances, a schema
mutator), `hegel_oracle_test.go` (the Python oracle process),
`hegel_props_test.go` and `hegel_refs_test.go` and `hegel_more_test.go` (the
seven properties) and `hegel_pins_test.go` (seven pins). `go get
hegel.dev/go/hegel` raises the `go` directive to 1.26; the tests run with
`GOWORK=off` because the repository's `go.work` pins an older Go.
**Needs `python3` with the `jsonschema` package (4.x, with `referencing`)**;
the CI Go job installs `jsonschema>=4.26` in a venv put first on `PATH` (the runner image's own copy is too old: no `referencing`, `$recursiveRef` ignored, so `check_schema` accepts `additionalProperties: []` in 2019-09). The oracle greets with its version and the tests refuse anything below 4.18. The whole run takes about a second at
the default case count; `HEGEL_TEST_CASES=2000` about 5 s.

## Oracles

- **Python `jsonschema`** (differential): random schemas in a random draft
  — every core keyword of the draft, `$ref` by JSON pointer (escaped and
  percent-encoded), by `$anchor` / `$id: "#a"` / `id: "#a"`, by embedded
  `$id` resources in relative and absolute forms, `$dynamicRef`, boolean
  schemas, `unevaluated*`, `dependentSchemas`/`dependencies`, `if/then/else`
  — validated on guided and random instances; and the same schemas damaged
  in one place (wrong-typed keyword values, negative counts, invalid regex,
  duplicate types, unresolvable `$ref`) must be rejected by `Compile`
  exactly when `check_schema` rejects them.
- **Reference transparency** (library-internal): a schema reached through
  `$ref` by pointer, by anchor, by embedded id (`sub.json`, `dir/sub.json`,
  `../up.json`, `sub.json#`, absolute and root-relative forms), through a
  chain of refs, through `$dynamicRef` with and without a dynamic anchor,
  `$recursiveRef`, with ignored siblings (drafts ≤ 7), or through a
  one-armed `allOf`/`anyOf`/`oneOf`/`not not`/`if` accepts exactly what the
  plain schema accepts, at the root and one property down.
- **Output well-formedness**: for every failing validation the flag, basic
  and detailed outputs have `valid: false` throughout, an
  `instanceLocation` that resolves in the instance, a `keywordLocation`
  that resolves in the schema when its `$ref` tokens are followed, an
  `absoluteKeywordLocation` that resolves in the document, an error on
  every leaf, and marshal to JSON.
- **Exact arithmetic** (`math/big`): minimum/maximum/exclusive*/multipleOf/
  const/enum/`type: integer`/uniqueItems on decimal texts from `1e-400` to
  `1e400` and 30-digit integers, for every Go representation of the same
  number (`json.Number`, `int64`, `int`, `int8`, `uint64`, `float64`,
  `float32`), including arrays above 20 items (the hashed uniqueItems path).
- **Format grammars**: with `AssertFormat`, `date`, `time`, `date-time`
  (RFC 3339 with leap seconds and offsets), `duration` (RFC 3339 appendix A
  ABNF), `ipv4`, `ipv6` (RFC 4291 text forms), `uuid`, `json-pointer`,
  `relative-json-pointer` and `hostname` against models of the grammars, on
  generated valid strings, their mutations and hand-written edge cases.

## Properties

| Test | Checks |
|---|---|
| `TestHegelValidationMatchesPython` | validity equals Python's jsonschema for random schema + instances in every draft |
| `TestHegelSchemaCheckMatchesPython` | `Compile` accepts exactly the schemas `check_schema` accepts (mutated schemas) |
| `TestHegelReferencesAreTransparent` | reaching a schema through refs/anchors/ids/applicators changes nothing |
| `TestHegelOutputsAreWellFormed` | flag/basic/detailed outputs: locations resolve, leaves carry errors, JSON marshals |
| `TestHegelNumbersAreExact` | numeric keywords follow exact rational arithmetic for every Go number type |
| `TestHegelFormatsFollowTheirRFCs` | ten formats against grammar models |

(The Python differential is two tests; seven properties in six test
functions plus the format table.)

## Bugs (7)

| id | severity | summary |
|---|---|---|
| jsonschema/1 | medium | drafts 6/7: `const` beside `$ref` is enforced (all siblings must be ignored) |
| jsonschema/2 | low | count keywords beyond int64 wrap: `maxLength: 1e19` rejects every string, `minItems: 2^63` accepts `[1]` |
| jsonschema/3 | low | `time`/`date-time`/`ipv4` accept signed fields (`+1:00:00Z`, `1.2.3.-0`) |
| jsonschema/4 | low | output `keywordLocation` is percent-encoded (`/properties/a%20b/type`) |
| jsonschema/5 | low | a `propertyNames` failure is reported at `.../propertyNames/propertyNames` |
| jsonschema/6 | low | a `dependencies` failure is reported at `/dependency/<prop>` |
| jsonschema/7 | medium | a `propertyNames` failure's `instanceLocation` aliases the path buffer and points at a sibling |

Each bug has a `Known` gate that keeps its input shape out of the
properties and a pin in `hegel_pins_test.go` asserting the correct
behaviour; the pins fail while the bugs exist (`[expected_failures]`).

## Not bugs (accepted differences, modelled in the tests)

- Up to draft 7 a root-level `$ref` silences the root's `$id` (the letter of
  the spec; Python keeps the id), so `"/sub.json"` and absolute references
  to embedded resources resolve differently there; the generator uses only
  relative forms in those drafts and the transparency wrappings put the
  `$ref` under `allOf`.
- `multipleOf` is exact decimal arithmetic (`0.3` is a multiple of `0.1`);
  Python divides floats. The differential uses exact binary divisors.
- Draft 4 reads `2.0` as an integer here (Python: not an integer, per the
  draft's wording); the draft-4 pool has no integral numbers written with a
  fraction or exponent.
- A float64 instance is read as the JSON number it would be written as
  (its shortest round-tripping decimal), so `float64(1<<64)` is
  `18446744073709552000`, not `2^64`; the exact-arithmetic property feeds
  floats only when the two agree.
- In 2019-09 `contains` does not mark items evaluated for
  `unevaluatedItems` (2020-12 does); Python treats both drafts alike.
- `dependencies` is still evaluated in 2019-09/2020-12 (the specs allow
  keeping it); Python ignores it there. Not generated in those drafts.
- `$defs` entries are compiled lazily: an unresolvable `$ref` inside an
  unreferenced definition is not a compile error; the mutator puts the bad
  `$ref` at the root. Duplicate anchors in a resource and reference cycles
  without progress (`{"$ref": "#"}`) are errors here (Python recurses).
- `format` is asserted by default in drafts ≤ 7 and Python asserts nothing
  without a format checker; the differential omits `format`, the format
  property uses `AssertFormat` explicitly. Duration is matched
  case-sensitively (`p1d` invalid) as in the test suite.
- Python's own jsonschema (4.26) raises `AttributeError` crawling some legacy
  schemas (`"$id": "#anchor"` anchors in drafts 6/7, array-form
  `dependencies` inside embedded `id` resources in draft 4); those cases are
  skipped.
- Regex dialects: patterns come from a pool valid in both RE2 and Python
  `re`, and test strings contain no trailing newline (`$` differs).

## History

- 2026-09-17: created at ec6106e (v6.0.3), seven bugs.
