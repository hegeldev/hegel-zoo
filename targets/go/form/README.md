# form

[go-playground/form](https://github.com/go-playground/form) decodes `url.Values` (an HTML
form, a query string) into Go values and encodes Go values into `url.Values`, by reflection:
dot paths for struct fields (`Address.Name`), `[index]` for slices and arrays (`Phone[0]`,
or plain repeated values), `[key]` for maps, nested without limit; `form` tags with `-` and
`omitempty`, `ModeExplicit` (tagged fields only), a tag name and namespace prefix/suffix of
one's choice, `AnonymousEmbed`/`AnonymousSeparate` for embedded structs, `time.Time` as
RFC3339, custom type functions, a maximum array size against index bombs, errors collected
per field in `DecodeErrors`. The package (`github.com/go-playground/form/v4`, about 1 600
lines of Go, no dependencies) is used by go-playground's web frameworks and many others. MIT;
the pin is the tag `v4.5.0` (`5b6e41f`, 2026-09-20), the release that added
`Decoder.SetAnonymousMode`. `.github/CONTRIBUTING.md` (2026-09-20) welcomes AI-assisted
contributions provided they are attributed (a `Co-Authored-By` trailer, a note in pull
requests and issues); `CLAUDE.md` is guidance for Claude Code. Nothing forbids AI-written
tests or use.

## Build

`go test -count=1 -run TestHegel -v ./hegel` in the module root. The patch adds the package
`hegel/` (the type universe and generator, one file per oracle, and `hegel_pins_test.go` with
one plain test per bug) and requires `hegel.dev/go/hegel v0.6.33` in go.mod (the module's
`go` directive is already 1.26).

## Oracles

- **The Encode -> Decode round trip** over generated values of a type universe covering every
  supported kind: every scalar kind, `time.Time`, pointers, slices, arrays, maps with string,
  integer, bool and float keys, `interface{}`, nested structs directly, behind pointers, in
  slices, arrays and maps, nested slices and maps, embedded structs by value and by pointer,
  tags (`-`, a name, `omitempty`, a second tag name); and non-struct roots (slices, maps,
  arrays, a string, an int, a time). The Encoder and Decoder share generated settings (mode,
  tag name, namespace prefix and suffix, anonymous mode). The decoded value must equal the
  original up to what the encoding does not carry (nil and empty alike; a value that encodes
  to nothing, such as an empty slice or a pointer to a struct with nothing to write, and the
  trailing such elements of a slice, are not there), times by `Equal`; and encoding the
  decoded value must give the same `url.Values`.
- **A model of the documented encoding**: dot paths, `[index]` only where a plain repeated
  value cannot do (pointers, nested containers, structs, times), `[key]`, `omitempty` and `-`,
  `ModeExplicit`, the two anonymous modes, RFC3339 times, `strconv` formatting; compared with
  `Encode` exactly.
- **strconv, the documented boolean vocabulary and time.Parse** on generated tokens (valid,
  empty, out of range, signed, hexadecimal, exponent, NaN and infinities, every boolean
  spelling, dates in several shapes) for every scalar field of a pre-filled struct, pointers
  and a nested struct included: the value each field ends with, and the set of field
  namespaces in `DecodeErrors`.
- **A model of the documented key semantics** for slices, arrays and maps: plain repeated
  values, `[index]` (valid, invalid, beyond the array, beyond `SetMaxArraySize`), the two
  mixed ("array/slice then array[idx]/slice[idx]"), `[key]` for string and integer keys,
  structs in slices and maps, nested slices with plain and indexed inner values, bare element
  keys, unrelated keys; the decoded struct and the error namespaces.
- **A model of Decode over the whole universe into a pre-filled destination**: the values are
  the encoding of another value of the same type under the same settings, some tokens
  replaced by arbitrary ones, plus unrelated keys of every shape; fields present are set,
  nested structs (also behind non-nil pointers) field by field, a slice's plain values
  appended after its existing elements and its indexed values set in place, arrays in place,
  map entries added or replaced, an unparsable value leaving its field alone with an error
  under its namespace. Both anonymous modes, tag names, `RegisterTagNameFunc` variants.
- **Custom type functions** on both sides (a string type, a struct type written as one or two
  values, `time.Time` as a date; failing on a chosen text) for fields in every position:
  direct, behind pointers, in slices and arrays (indexed), as map keys (the first value) and
  values, in nested structs and slices and maps of structs; `Encode` against the encoder model
  with the functions as hooks (values and error namespaces), the round trip, and the decoder
  model on a pre-filled destination.

## Properties

`TestHegelRoundTrip`, `TestHegelEncodeModel`, `TestHegelScalars`, `TestHegelIndexed`,
`TestHegelDecodeModel`, `TestHegelCustomTypes`; seven narrow properties in
`hegel_shapes_test.go`, one per recorded bug, each a generator over the bug's shape region with
random contents judged by the same oracle (`TestHegelStrayBracketKeysAreIgnored`,
`TestHegelNilInterfaceElementsKeepTheirPositions`, `TestHegelBracketMapKeysRoundTrip`, ...);
the pins `TestHegelPin*`.

The generators are combinator values (`hegel_test.go` holds the idioms: `absentOr` with nil
first, `many`, `pairs`, `weighted`, `chance`, `maybe`, `shaped`): values of the type universe
come from a memoised, reflection-driven `valuesOf(type, depth)`, the options are a record, the
indexed keys a choice of entry generators per key form, and edits are drawn lists applied at
positions taken modulo the live size. The universe gained `Anys`, a struct of interface slices.

## Bugs

Seven, in `bugs.toml`: two panics on input (a key with a stray `]` or an unclosed `[`; an
`interface{}` field that already holds a value), nil elements of a slice of interfaces losing
the positions of the others, an unparsable time zeroing its field, map keys with brackets
written unescaped so that they cannot be read back, and two panics on custom type functions
used for map keys (an encoder function returning no values, a decoder function returning
nil).

## Known shapes

The shapes of the recorded bugs are drawn by default (STYLE.md rule 11): keys the decoder
panics on, pre-filled `interface{}` fields, nil elements before values in a slice of
interfaces, unparsable times, map keys with brackets, custom functions returning no values or
nil for a map key. The models say what should happen (the stray key ignored, the held value
replaced, the positions kept, the field left alone, the key read back, the entry skipped, an
error), a mismatch names the bug whose shape it has (the `Known` switches keep the shape
tests) and the property fails: `TestHegelScalars` (bug 4, bug 2 in a fifth of its hits),
`TestHegelEncodeModel` (3), `TestHegelDecodeModel`, `TestHegelRoundTrip` and
`TestHegelCustomTypes` (5, or 2, 3 and 4 in some runs) every run, `TestHegelIndexed` (1) in
most runs, its panic keys being a fifth of the junk keys of 40% of cases; and each narrow
property on its own bug. `HEGEL_NO_KNOWN=1`, read once, switches the known shapes off: the
generators draw the neighbouring regions instead (a junk key for a panic key, a value after a
nil, a value-returning custom function), nothing is skipped, and every property passes.

## Not tested

`json.Unmarshaler` or `TextUnmarshaler` destinations (unsupported by design), custom
functions returning a value of the wrong type or given no values (a user error: `vals[0]`
in the documented example panics on a key present with no values), `SetMaxArraySize` against
a pre-filled slice with spare capacity (deliberately unchecked), the exact error messages,
concurrency of the shared struct cache, the warning printed for values beyond an array's
length. Two quirks are recorded here rather than as bugs: with lower-case field names and an
empty namespace prefix, `In.S` and `Ins` both become `ins` (an inherent collision, so the
generator avoids it); a decoder custom function for the element type of a slice given plain
repeated values receives the values from its element to the end, not just its own.

## History

- 2026-09-21: new target at v4.5.0; four properties, five bugs.
- 2026-09-21: the decoder model on pre-filled destinations, custom type functions and
  `RegisterTagNameFunc`; two more bugs (6, 7).
- 2026-09-26: generators rewritten in combinator style; the known shapes are drawn by default
  and seven narrow properties, one per bug, are the expected failures beside the pins. A latent
  model bug fixed (the decode model descended into a held interface and set its unaddressable
  element; it now replaces the held value).
