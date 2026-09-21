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
`TestHegelDecodeModel`, `TestHegelCustomTypes`; the pins `TestHegelPin*`.

## Bugs

Seven, in `bugs.toml`: two panics on input (a key with a stray `]` or an unclosed `[`; an
`interface{}` field that already holds a value), nil elements of a slice of interfaces losing
the positions of the others, an unparsable time zeroing its field, map keys with brackets
written unescaped so that they cannot be read back, and two panics on custom type functions
used for map keys (an encoder function returning no values, a decoder function returning
nil).

## Modelled as recorded

- The round trip skips values with a map key containing `[` or `]` (bug 5) and expects nil
  elements of a slice of interfaces to be dropped (bug 3); the encoder model writes such
  slices as the encoder does (bug 3).
- The scalar model zeroes a time field on a parse error (bug 4) and does not pre-fill the
  `interface{}` field (bug 2).
- The key model skips cases with a key the decoder panics on (bug 1); the decoder model
  clears the pre-filled interface fields (bug 2) and skips map keys with brackets (bug 5).
- Bugs 6 and 7 have pins only: the custom functions of the property always return a value.

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
