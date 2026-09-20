# gocsv

[gocarina/gocsv](https://github.com/gocarina/gocsv) marshals slices of Go structs to CSV and
back (about 2,200 stars, used by many CLI tools and importers), on top of `encoding/csv`: `csv`
struct tags with alternative keys, `omitempty`, `default=`, `partial` and `-`, nested and
inline (`csv:"."`) structs with dotted headers, `csv[]` tags expanding slices and arrays into
indexed columns, JSON for other slices, `TypeMarshaller`/`TypeUnmarshaller`, `TextMarshaler`
and `Stringer`, header matching with a normalizer, duplicate-header alignment, the
`FailIf...` switches, a streaming `Unmarshaller`, channel and callback variants, headerless
variants and the `CSVToMap(s)` helpers. The pin is `9ab82d6` (2026-09-08, master; the
repository has no tags).

The repository has LICENSE (MIT) and README; no CONTRIBUTING, no agent instructions, nothing
about AI-written code. The zoo keeps its tests in its own patch and files nothing upstream.

## Build

`go test -count=1 -vet=off -run TestHegel -v .` in the module root. The patch adds
`hegel_test.go` (harness, the column and cell model, the types under test, the Marshal and
round-trip properties), `hegel_columns_test.go` (header matching, cell conversions, `csv[]`
columns, the map helpers) and `hegel_pins_test.go` (one plain test per bug), and requires
`hegel.dev/go/hegel v0.6.33` in go.mod (the `go` directive moves from 1.13 to 1.26.0 for it).
`-vet=off` because under that directive `go test`'s vet fails the build on upstream's own
`fmt.Errorf(nonConstant)` calls; gocsv has no dependencies and needs no external tool.

## Oracles

- **The documented column layout and cell conversions, as a model.** Four struct types (every
  primitive kind and renamed kinds, an untagged field, `-`, an unexported field, a
  `TypeMarshaller` type and `time.Time`; pointers with `omitempty` and `default=`; nested,
  pointer-nested, inline, anonymous and two-level structs; `csv[]` slices of primitives and of
  structs, a `csv[]` array, JSON slices) have their headers written by hand. A reflection model
  gives the cells (strconv formatting, `""` for nil, `MarshalCSV`/`MarshalText`, JSON) and reads
  them back (pointers allocated, `omitempty` leaving an empty pointer nil, `default=` filling
  an empty cell, `csv[]` slices grown to the highest index, the lenient conversions: trimmed,
  empty is zero, yes/no, an integer cell's fraction dropped, a decimal comma) with the field's
  own width, so a cell that does not fit is an error.
- **encoding/csv** writes the modelled cells (quoting, CRLF normalisation) and is the reader
  behind every gocsv path; the header-matching rules (exact, trimmed, zero-width characters
  removed, `partial`, alternative keys, the normalizer, duplicate alignment) and the map helpers
  are modelled directly.
- **gocsv against itself**: the twelve Unmarshal entry points (string, bytes, `CSVReader`,
  `Decoder`, array target, channel, callback, callback with error, the `Unmarshaller`, and the
  headerless slice, reader and channel variants) must agree on one text, and each column of a
  row must decode as it does alone.

## Method

| Property | Checks |
|---|---|
| MarshalWritesTheModelCells | `Marshal` of a `[]T`, `[]*T` (nil elements included) or `[k]T`, by value or pointer, is the hand-written header and the modelled cells written by `encoding/csv`; `MarshalWithoutHeaders` and `MarshalBytes` agree |
| UnmarshalInvertsMarshal | every entry point reads that text back to the model's rows or fails at the modelled row and column (`csv.ParseError`); the headerless family reads the headerless text positionally; an empty text is `ErrEmptyCSVFile`; a longer pre-filled slice is replaced |
| HeadersMatchTheModel | random headers (keys, alternatives, padded, BOM and zero-width prefixed, partial superstrings, other case, unrelated, duplicates) under either normalizer and the three switches: the mapping, `default=`, `ErrDoubleHeaderNames`, `ErrUnmatchedStructTags`; the `Unmarshaller`'s rows, `MismatchedHeaders`, `MismatchedStructFields` and `ReadUnmatched` |
| CellsDecodeLikeTheModel | random numeric-looking cells (signs, long digit strings, fractions, exponents, decimal commas, yes/no and the `ParseBool` words, NaN/Inf, garbage) into every bool, integer and float kind and pointers to them: value or error as the model; a whole row errors at its first failing column |
| SliceColumnsFollowTheTags | `csv[]` columns of a slice, a slice of structs and an array in any order and with columns missing: the slice grows to the highest index present, gaps are zero, absent fields stay nil |
| MapsFollowTheModel | `CSVToMaps`, `CSVToChanMaps`, `CSVToMap` and `UnmarshalCSVToMap` (string and int values) against `encoding/csv` and the model |

Mismatches are classified before they count: a `Known` switch per recorded bug gates the input
shape (out-of-order `csv[]` columns beyond the growth, integer cells wider than the field, uint
cells with a dot, float32 cells out of range, headers matched only after trimming, a longer
target slice, extra columns on the headerless channel path, `default=` without headers, the
off-by-one line). With everything gated the properties run clean; `ZOO_COLLECT=1` prints
class counts and the first 25 mismatches instead of failing.

## Accepted differences (not bugs)

- `encoding/csv` normalises a CRLF at the end of a physical line to LF, inside quoted fields
  too, so a string with `\r\n` reads back with `\n`; a lone `\r` survives. Its writer quotes a
  leading space and `\.`. The model applies the same transport.
- CSV has no null: a nil pointer is an empty cell, read back as an allocated zero value unless
  the field is `omitempty`; a nil `*time.Time` without `omitempty` therefore fails to read (an
  empty cell is not a time), and nested pointer structs are allocated on read (README:
  "allocates the pointers needed to reach each field").
- A `csv[]` slice is fixed-width: elements beyond the tag's count are not written, and reading
  grows the slice to the highest column present, zero-filled.
- Duplicate headers map to the same field, the later column winning, unless
  `ShouldAlignDuplicateHeadersWithStructFieldOrder`; an unprefixed key in a tag such as
  `csv:"a,"` includes the empty key.
- `.5` is not an integer cell (`0.5` is 0): the integer rule drops the fraction and parses what
  is left. `1,5` is 1.5 for a float field. `on`/`off` are not booleans.
- The headerless slice paths return `ErrEmptyCSVFile` for an empty text; the headerless channel
  path sends nothing.

## Bugs found

Fifteen, recorded in `bugs.toml` with a pin test each. Four medium: `csv[]` columns out of
order or with a gap panic in reflect `SetLen` because the slice growth never checks the index
against the new capacity (**gocsv/1**); `Unmarshal` into a struct with an `interface{}` field
panics on `Elem()` of the interface type, though `Marshal` accepts it (**gocsv/2**);
`UnmarshalToChanWithoutHeaders` panics on a row with more columns than fields, where
`UnmarshalWithoutHeaders` ignores them (**gocsv/3**); an integer cell wider than the field wraps
silently, 300 into an `int8` is 44 (**gocsv/4**). Low: uint cells containing a dot go through
`ParseFloat` and a float-to-uint conversion, so `-1.5` is 2^64-1 and `1.5e2` is 150 where the
int rule gives 1 (gocsv/5); float32 cells are parsed at 64 bits, so out of range is +Inf without
error (gocsv/6); several keys on a nested struct field produce `q.p.a` instead of `q.a`
(gocsv/7); an array field without `csv[]` is written as JSON that `Unmarshal` rejects (gocsv/8);
a map field is written as an empty cell without error and rejected on read (gocsv/9);
`FailIfUnmatchedStructTags` and the `Unmarshaller`'s mismatch lists compare headers exactly
while the mapping trims spaces and a BOM (gocsv/10); `Unmarshal` into a longer slice keeps the
stale elements (gocsv/11); `CSVToMaps` panics on a ragged row under a permissive reader
(gocsv/12); `Marshal` writes `Stringer` output (`time.Duration`: `1.5s`) that `Unmarshal`
cannot read (gocsv/13); the headerless paths ignore `default=` (gocsv/14) and the headerless
channel path reports errors one line too far (gocsv/15). All found on 2026-09-20 (turn 331).
The header layout, the write/read round trip through every entry point, header matching with
its switches and the map helpers otherwise agreed with the model throughout.

## History

- 2026-09-20 (turn 331): target created at `9ab82d6` (master, untagged); 15 bugs.
