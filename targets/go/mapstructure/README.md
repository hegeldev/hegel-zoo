# mapstructure

[go-viper/mapstructure](https://github.com/go-viper/mapstructure) (v2) is the maintained fork
of mitchellh/mapstructure: `Decode`/`WeakDecode`/`DecodeMetadata` and `NewDecoder(config)`
turn one Go value into another through reflection — typically a `map[string]any` from JSON
or YAML into a struct, or a struct into a map — with field tags (rename, `squash`, `remain`,
`omitempty`, `omitzero`, `-`), a weak-typing conversion table, decode hooks, metadata of used,
unused and unset keys, and the options ErrorUnused, ErrorUnset, AllowUnsetPointer, ZeroFields,
IgnoreUntaggedFields, MatchName, MapFieldName, DecodeNil, DisableUnmarshaler. About 3 000 lines
without tests; the pinned commit is the January 2026 head (v2.5.0 plus dependabot merges;
the last code change is v2.5.0 of January 12). MIT. No CONTRIBUTING or AI policy; not archived
(the fork's README says it is the blessed successor); 483 stars. Checked 2026-09-15.

## Oracle

`encoding/json` on a struct universe tagged identically for both packages (`Big`, embedding
`Base` with `,squash`, nested `Inner`, pointers, slices, maps, an `any`, `omitempty`,
`omitzero`, a renamed and an ignored field, an unexported one): the map a struct decodes to
must equal the JSON object of the struct, and a JSON-derived generic value must decode to what
`json.Unmarshal` gives for the struct. A model of the documented weak conversion table
(`DecoderConfig.WeaklyTypedInput`) for eight target kinds. A model of `Metadata.Keys`/
`Unused`/`Unset`, `ErrorUnused`, `ErrorUnset`, `AllowUnsetPointer` and `,remain` on a flat
struct. The standard library parsers behind the string decode hooks.

## Properties

- `TestHegelStructToMapAgreesWithJSON` — `Decode(struct, &map)` equals `json.Marshal(struct)`
  once both are read back as generic JSON values.
- `TestHegelStructMapStructRoundTrips` — struct → map → struct is the identity.
- `TestHegelJSONMapDecodesLikeEncodingJSON` — the generic value of the struct's JSON decodes
  to what `json.Unmarshal` produces, into a fresh struct and (30 %) into a pre-filled one with
  `ZeroFields`.
- `TestHegelWeakDecodeFollowsTheConversionTable` — one field of eight kinds (int, int8, uint,
  float64, bool, string, `[]string`, `map[string]int`) from an input of a random kind (ints,
  integral and fractional floats, bools, 29 strings with prefixes, underscores, spaces and
  out-of-range values, `[]any`, `[]byte`, maps, nil): value per the table or an error exactly
  when the table has no row.
- `TestHegelMetadataAccountsForEveryKey` — random subsets of a flat struct's keys (20 %
  upper-cased), extras and nil values: `Keys` (with `tags[i]` per element), `Unused`, `Unset`,
  `ErrorUnused`/`ErrorUnset` firing exactly then, and a `,remain` map taking the extras.
- `TestHegelDecodeHooksMatchTheirParsers` — `StringToTimeDurationHookFunc`,
  `StringToSliceHookFunc(",")` and `StringToBasicTypeHookFunc` vs `time.ParseDuration`,
  `strings.Split` and `strconv`.

Twenty thousand cases per property before saving, plus three plain runs. The generators avoid
the pinned shapes: integers stay within their target's range and floats integral when they
meet an integer field (mapstructure/1, /2); no float32 is converted to a string (/4); the
pre-filled struct for `ZeroFields` has a nil `any`, a nil pointer field and zero in every
field an `omitempty`/`omitzero` key can omit — a key that is absent is never written, by
design (/5, /6); the Metadata struct has no unexported field (/3).

## Bugs (6; details in bugs.toml)

| id | severity | shape |
|----|----------|-------|
| mapstructure/1 | medium | `Decode(300 → int8)` = 44, `256 → uint8` = 0, `MaxUint64 → int64` = −1, `1e300 → float32` = +Inf, all without error |
| mapstructure/2 | medium | `Decode(1.7 → int64)` = 1 and `1e30 → int64` = MinInt64 in strict mode, without error |
| mapstructure/3 | medium | `ErrorUnset` fails on "unset fields: priv" for an unexported field the decoder skips |
| mapstructure/4 | low | `WeakDecode(float32(0.1) → string)` = "0.10000000149011612" (formatted as a float64) |
| mapstructure/5 | medium | `ZeroFields` does not zero an `any` field: `true` into an `any` holding 1.5 is "unconvertible type 'bool'" |
| mapstructure/6 | medium | `{"p": nil}` into a pre-filled `*Inner` field leaves the pointer set (dereferenced as if embedded) |

## Not bugs (documented or design)

- `Metadata.Keys` lists slice elements as `tags[0]`, `tags[1]`, …, and a typed nil slice
  counts as decoded (it is a valid slice value); an untyped nil value is neither decoded nor
  unused nor unset.
- Weak strings: `""` is 0 and false for numbers and bools (the doc says "anything else is an
  error" for bools, the code special-cases the empty string); `"017"` is 15 and `"1_000"` is
  1000 (`strconv.ParseInt(s, 0, …)`, "base implied by prefix"); a negative int into a uint
  wraps ("negative numbers to overflowed uint values").
- With `ZeroFields`, a key absent from the input leaves the field as it was: only fields being
  written are zeroed.
- `Separators`-style identity: `DecodeHook` sees the whole input once per squashed struct
  (documented).
