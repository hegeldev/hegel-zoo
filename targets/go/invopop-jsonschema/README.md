# go/invopop-jsonschema

[invopop/jsonschema](https://github.com/invopop/jsonschema) (v0.14.0 plus one commit): JSON
Schema 2020-12 generation from Go types by reflection, driven by `json`, `jsonschema`,
`jsonschema_description` and `jsonschema_extras` struct tags and the `Reflector` options. Tested
here: `Reflector.ReflectFromType`/`Reflect` on generated types (anonymous structs built with
`reflect.StructOf` over scalars, slices, arrays, maps, pointers, `time.Time`, `net.IP`,
`url.URL`, `json.RawMessage`, byte slices, `any`, and a pool of named struct, slice, map, byte
slice and integer types including a recursive one), with generated tags and options, and the
schemas' behaviour on the JSON `encoding/json` writes for values of those types.

## Build

The patch adds `hegel.dev/go/hegel` to `go.mod` and a `hegel/` package of five
`hegel_zoo_*_test.go` files that drive the public API. `go test -count=1 -run TestHegel -v ./hegel`
needs `python3` with the `jsonschema` package (4.18+) on the PATH.

## Oracles

- A model of the reflection: the package's documented mapping of Go types and tag keywords to
  JSON Schema (README, the `Reflector` doc comments), with `encoding/json`'s rules for property
  names (tag name or Go name, `-` drops, `-,` names the key `-`), for required (no
  `omitempty`/`omitzero`, or the `required` tag with `RequiredFromJSONSchemaTags`), for embedding
  (an untagged embedded struct or pointer to struct contributes its fields; the shallower field
  wins a duplicate key, then the tagged one), for unexported fields and for the `,string`
  option; named slice, map and struct types become `$defs` entries with `$ref`s (inline under
  `DoNotReference`), `ExpandedStruct` moves the root's definition into the root, `Anonymous`
  drops the `$id` (`https://<package path>/<dashed type name>` otherwise), `AssignAnchor` adds
  `$anchor`, `AllowAdditionalProperties` drops `additionalProperties: false`.
- python-jsonschema (`Draft202012Validator`, format assertions on): the generated schema must be
  a valid schema (`check_schema`), and the JSON `encoding/json` writes for a value of the type
  must validate against it. The model's schema with every switch off (the correct schema) must
  accept the value too; the package's schema and the model's with the switches on must agree.

## Properties

- `TestHegelSchema`: a root type (mostly a struct of 0-5 fields, two levels deep, also a named
  type, a pointer or a slice/map) and `Reflector` options; the schema's JSON (numbers as
  `json.Number`, `required` sorted) must equal the model's.
- `TestHegelValidate`: the same draw plus a value of the type honouring its tags (bounds,
  `multipleOf`, `enum`, lengths, patterns, item counts, uniqueness, non-empty when `required`
  meets `omitempty`; nil pointers only under `nullable`, embedded pointers non-nil): `check_schema`
  and validation as above, with counts of the values the recorded bugs reject.
- `TestHegelPin…`: one pin per recorded bug (expected failures); the fatal one runs in a child
  process.

## Bugs

Fourteen, recorded in `bugs.toml`. Schemas that reject the package's own JSON: `url.URL` as a
string with format `uri` while `encoding/json` writes an object (invopop-jsonschema/1); signed
integer map keys under `^[0-9]+$`, so negative keys fail (2); `json:"-,"` fields dropped (3); a
later field with the same key replacing an earlier one, so an embedded struct's field overrides
the outer field's type (4); the yaml `inline` option honoured on json tags (5); an unexported
embedded non-struct type as a required property (6); `net.IP` always `ipv4` (9); `nullable` as
`oneOf`, rejecting null for `any`/`json.RawMessage` fields (14). Tags: `uniqueItems=false` is
true (7); `jsonschema_extras` `maximum=5` a string, an invalid schema (8); type-specific tags on
named slice fields dropped (10); array `default=` values always strings (11). Options:
`ExpandedStruct` on a recursive type leaves dangling `$ref`s (12); `DoNotReference` on a
recursive type overflows the stack (13).

## Modelled as recorded

Twelve are in the model behind `HZKnown` switches (`urlIsString`, `intKeysNonNegative`,
`dashNameIgnored`, `sameKeyOverwrites`, `inlineOptionEmbeds`, `uniqueItemsAlwaysTrue`,
`extrasMaximumString`, `ipAlwaysV4`, `refTagsDropped`, `arrayDefaultsAreStrings`,
`expandedDanglingRef`, `nullableOneOfRejectsNull`); `ZOO_KNOWN_OFF=name` turns a switch off and
the properties then fail. Bug 6 is pinned only (`reflect.StructOf` cannot embed an unexported
type) and bug 13 too (the generated types exclude the recursive type under `DoNotReference`).

Design notes the model follows (undocumented, taken from the code):

- Nil slices, maps and pointers are `null` in JSON, which the schemas reject unless the field is
  `nullable`; the values generated are non-nil except under `nullable`. Likewise a nil embedded
  pointer to struct drops its promoted fields, which the schema requires.
- Keyword tags parse as the code does: numeric keywords take valid JSON numbers only (else the
  keyword is dropped), `minLength`/`maxItems`... take unsigned integers, `readOnly`/`writeOnly`
  take `strconv.ParseBool`, `default`/`example`/`enum` are typed by the property's schema type
  (strings for `string`, numbers for `integer`/`number`, `true`/`false` for `boolean`), array
  tags other than `minItems`/`maxItems`/`uniqueItems`/`default`/`format`/`pattern` go to the
  items when the items have a scalar type, `,string` turns integer, number and boolean types into
  `string` before the type-specific keywords. Extras go last and overwrite the keyword of the
  same name; a repeated key collects strings.
- `map[string]any` has no `additionalProperties`; unsigned integer keys have none of the signed
  keys' pattern. A slice of `uint8` under any name is a base64 string, an array of bytes an
  array of integers.
- Only struct, slice, array and map named types get definitions; named integers are inline.
  `time.Time`, `url.URL`, `net.IP` and `json.RawMessage` never do.

## Not tested

`JSONSchema()`/`JSONSchemaExtend`/`JSONSchemaAlias`/`JSONSchemaProperty` methods, `Mapper`,
`Lookup`, `Namer`, `KeyNamer`, `AdditionalFields`, `IgnoredTypes`, `FieldNameTag`, comments
(`AddGoComments`, `CommentMap`, `LookupComment`), the `oneof_*`/`anyof_*`/`type=`/`anchor=`
tags, `Schema.UnmarshalJSON`, `ID` methods, `inline` on `url.URL`/`time.Time` fields (it inlines
their fields).

## History

- 2026-09-21: new target, two properties, 14 bugs.
