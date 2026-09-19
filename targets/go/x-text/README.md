# golang.org/x/text

[golang.org/x/text](https://github.com/golang/text) (BSD-3-Clause), pinned at `6dcc5b6` (v0.42.0+,
2026-09-18): the Go text-processing packages - Unicode normalization (`unicode/norm`), the legacy encodings
(`encoding/...`), case mapping, East Asian width, bidi, BCP 47 language tags, collation, PRECIS, number
formatting and message catalogs. With Go 1.27 the generated tables are Unicode 17.0.

The patch adds `hegel/`, a test-only package inside the module: `hegel_test.go` (plumbing and the Python
oracle), `hegel_gen_test.go` (rune pools drawn from `rangetable.Assigned("15.0.0")`, and `drive`, a driver
that feeds any `transform.Transformer` by the letter of its contract - pieces of 1..9 bytes, destination
buffers of 1..64 bytes grown only when a call makes no progress), one file per area, `hegel_pins_test.go`
(one plain test per recorded bug) and `known.go` (one switch per bug the properties gate on).

## Oracles

Python 3.12's `unicodedata` (Unicode 15.0.0), spoken to as a JSON-lines subprocess, for normalization,
combining classes, decompositions and character names on the runes both libraries know; Python's legacy
codecs for the single-byte charmaps that share a table; and the packages' own contracts: every
`Transformer` must give the same bytes streamed as in one shot (`Bytes`, `String`, `Transform` in pieces,
`transform.NewReader`/`NewWriter`, `norm.Iter`, `Form.Reader`/`Writer`); encoders and decoders must
round-trip the encoder's repertoire; `rangetable.Merge` must be the union of its tables; boundaries must
split a string into independently normalizable pieces; the UAX #15 identities (`NFC(NFD(x)) = NFC(x)`,
idempotence); the BOM policies of UTF-16/32 as documented; the HTML and IANA name indexes must round-trip
`Name`/`Get`.

## What is tested

- `hegel_norm_test.go` - the four forms against `unicodedata.normalize` (including runs of 20-40
  non-starters and Hangul jamo around the 30-rune limit), `Bytes`/`Append`/`AppendString`/`IsNormal`/
  `QuickSpan`; streaming against one shot on any bytes including ill-formed UTF-8; `FirstBoundary`/
  `NextBoundary`/`LastBoundary`/`Span` and `Properties` (CCC, decomposition, lead/trail CCC,
  `BoundaryBefore`); `rangetable.Merge`/`New`/`Visit`; `runenames.Name`.
- `hegel_encoding_test.go` - every charmap's `DecodeByte`/`EncodeRune` against its `Decoder`/`Encoder`,
  round trips, streaming, Python's codecs; the CJK encodings' round trips, streaming, random-byte decoding,
  `HTMLEscapeUnsupported`/`ReplaceUnsupported`; UTF-16/32 with every endianness and BOM policy, ill-formed
  input; `htmlindex` and `ianaindex` round trips.

## Known bugs (23, see bugs.toml)

Normalization: the forms insert a CGJ into runs of more than 30 non-starters, undocumented (1), and `Iter`
places it differently from `String` (2). Encodings: the HZ-GB2312 encoder stays in GB mode after an
unsupported rune (3); GB18030 does not round-trip 2,068 private-use runes (4); `ianaindex` names UTF-32 but
cannot look it up (5). Language tags: sorted variants followed by an extension corrupt the tag (6); `-t-`
fields after a `tlang` are rejected (7); `SetTypeForKey` is case-sensitive (16); `-u` attributes sort by
three bytes (17); `ParseBase("heb")` is the deprecated `iw` (18); `Match` overwrites an explicit `-u-rg-`
(19); `EncodeM49`'s error loses the code (21); `display` has no name for `az-Arab` (22); `Script`/`Region`
say `Low` for `No` (23). Collation: `-u-ka-shifted` compares everything equal (8); `IgnoreWidth` is a no-op
(9); `Force` is not in the key (10); `fr-u-kb` is ignored (11). Search: `WholeWord` and
`Exact` are nil and panic (12); `Backwards` panics (13); `Equal` is not reflexive on empty or mark-only
strings (14); Danish `Aarhus` is not matched (15). Currency: `FromTag` ignores `-u-rg-` (20). Bugs 6-23 came
from a source review with probe programs (`work/x-text-audit-c.md` in the zoo's notes) and are carried by
pins only so far; the language/collate properties are still to be written.

## Conventions followed, not recorded

`runenames.Name` returns the UnicodeData range label (`<Hangul Syllable>`, `<CJK Ideograph>`, `<Private
Use>`) rather than the derived names Python computes; `Properties.Decomposition` is nil for Hangul syllables
(algorithmic); norm boundaries are shared between NFC and NFD and between NFKC and NFKD but not across
(U+FF9F decomposes to a non-starter only under NFK*); `QuickSpan` may stop short of a normal string; Python's
legacy codecs differ from the WHATWG tables on undefined bytes; the `MIB` index returns MIB names that
`Encoding` (IANA names only) does not accept; both indexes ignore surrounding white space in names. A probe
saw `Collator.SortStrings` retain about 240 bytes per call (`sorter.buf` is never reset), but the same loop
under `go test` retains nothing measurable, so it is not recorded.
