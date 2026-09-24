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
- `hegel_lang_test.go` - BCP 47 tags composed from known subtags: `Parse`/`String` round trips, variants and
  extensions kept, `TypeForKey`/`SetTypeForKey` in either case, attribute order, `ParseBase`/`ParseScript`/
  `ParseRegion`/`ISO3`/`M49`, `Parent` chains; collators (15 locales, every option subset) as total
  preorders whose keys order like `Compare`, `SortStrings` agreeing with `Compare`, the documented
  equivalences of `IgnoreCase`/`IgnoreDiacritics`/`IgnoreWidth`/`Numeric`; `search` hits being rune-aligned
  spans `Equal` to the pattern; `Matcher.Match` returning a supported tag with the desired `-u` extension
  and `MatchStrings` agreeing; `currency` codes, roundings, `FromRegion`/`FromTag`.
- `hegel_cases_test.go` - `cases.Upper`/`Lower`/`Fold`/`Title` against Python's `upper`/`lower`/`casefold`/`title`
  (title only on words of cased letters), idempotence, `Span` prefixes, streaming; the Turkish/Azeri i rules,
  Dutch `ij`, unsupported languages equal `und`; `width` kinds against `east_asian_width`, `Folded`/`Narrow`/
  `Wide` against each other and NFKC, the three transformers rune by rune and streamed; `bidi` classes against
  `bidirectional`, brackets mirrored, `ReverseString` an involution keeping marks on their base, `Paragraph`
  runs partitioning the first paragraph with strong characters in runs of their direction, `RunAt`;
  `bidirule.Valid`/`Direction`/`Transformer` against RFC 5893 written out on the classes; the four PRECIS
  profiles against RFC 8265/8266 written out (mapping steps, class, Bidi Rule on RTL strings, no empty
  result), `String`/`Bytes`/`Append`, `Compare` as key equality.
- `hegel_misc_test.go` - `runes.Remove`/`Map`/`ReplaceIllFormed`/`If` against their documented models on any
  bytes, `Span`, streaming; `transform.Chain` as the composition of its links with `String`/`Bytes`/`Append`/
  `NewReader`/`NewWriter`, `Nop`, `Discard`, `RemoveFunc`; `number.Decimal`/`Percent`/`PerMille` against the
  CLDR patterns written out (half-even rounding of the exact value, the digit options, grouping, width and
  padding) in English and with the symbols of twelve other locales; `message.Printer` against `fmt` with the
  grouping and the x10 exponent notation undone; catalog messages resolved through the parent chain, `Key`,
  `Languages`, `Matcher`; `plural.Selectf` against `Cardinal.MatchPlural` in fifteen languages.

## Known bugs (45, see bugs.toml)

Normalization: the forms insert a CGJ into runs of more than 30 non-starters, undocumented (1), `Iter`
places it differently from `String` (2), and under NFKC `BoundaryBefore` is true for the compatibility
Hangul letters that compose to the left (45). Encodings: the HZ-GB2312 encoder stays in GB mode after an
unsupported rune (3); GB18030 does not round-trip 2,068 private-use runes (4); `ianaindex` names UTF-32 but
cannot look it up (5); the ISO-2022-JP encoder passes ESC through and its decoder reads it as an escape (44). Language tags: sorted variants followed by an extension corrupt the tag (6); `-t-`
fields after a `tlang` are rejected (7); `SetTypeForKey` is case-sensitive (16); `-u` attributes sort by
three bytes (17); `ParseBase("heb")` is the deprecated `iw` (18); `Match` overwrites an explicit `-u-rg-`
(19); `EncodeM49`'s error loses the code (21); `display` has no name for `az-Arab` (22); `Script`/`Region`
say `Low` for `No` (23). Collation: `-u-ka-shifted` compares everything equal (8); `IgnoreWidth` is a no-op
(9); `Force` is not in the key (10); `fr-u-kb` is ignored, and has no `TypeForKey` (11); `IgnoreDiacritics`
alone leaves the marks' tertiary weights, so `o != ö` (24). Search: `WholeWord` and `Exact` are nil and
panic (12); `Backwards` panics (13); `Equal` is not reflexive on empty or mark-only strings (14); Danish
`Aarhus` is not matched (15). Currency: `FromTag` ignores `-u-rg-` (20). Casing: `Fold` maps the Cherokee capitals to the small letters, so
folding is not idempotent (32); `Lower`/`Title` lose the final-sigma context at a `Transform` call boundary
(33). Bidi: `ReverseString` puts a mark before its base (25); `RunAt` returns the last run (28); `Direction` is
the first run's, never `Mixed`/`Neutral` (29); `Paragraph.Direction` panics before `Order`, and on an empty
paragraph (30); `Order` runs past the paragraph separator (31); the `bidirule.Transformer` fails a valid label
at a chunk ending in ES/CS/ET/ON/BN (34); `bidirule.Valid` accepts surrogates and code points past U+10FFFF
(35). PRECIS: the username profiles accept the empty string (26) and apply the Bidi Rule to non-ASCII strings
without RTL characters while ASCII ones skip it (27). Numbers and messages: `number.Formatter` ignores the
directive's width without a `Pad` option (36); `MinFractionDigits` above the maximum rounds first and pads
zeros (39); the `Printer`'s `%.Ng` prints N+1 digits (37), `%x` on a float is a bad verb (38), `%q` on a
negative int is a bad verb (40), its fmt copy is stale (`%#g` of 0.5, `%#b`, `%O`; 41), and a width leaks into
a later directive with a precision (43); `plural.Selectf` parses `=x` as 16-bit (42). Bugs 6-23 came from a
source review with probe programs (`work/x-text-audit-c.md` in the zoo's notes); the language, collation,
search, matcher and currency properties reach 6, 8-11, 14, 16-20 and 24, the casing, width, bidi and PRECIS
properties 25-29 and 31-35, the number, message and plural properties 36-43, the encoding and normalization properties 44-45 (found
when the generators were rewritten in combinator style, 2026-09-24), the rest are carried by pins.

## Conventions followed, not recorded

`runenames.Name` returns the UnicodeData range label (`<Hangul Syllable>`, `<CJK Ideograph>`, `<Private
Use>`) rather than the derived names Python computes; `Properties.Decomposition` is nil for Hangul syllables
(algorithmic); norm boundaries are shared between NFC and NFD and between NFKC and NFKD but not across
(U+FF9F decomposes to a non-starter only under NFK*); `QuickSpan` may stop short of a normal string; Python's
legacy codecs differ from the WHATWG tables on undefined bytes; the `MIB` index returns MIB names that
`Encoding` (IANA names only) does not accept; both indexes ignore surrounding white space in names.
`language.Tag` values holding a non-compact tag compare by pointer, so equal tags are compared by `String`;
variants come out in the registry's canonical order (`valencia-1994`), not sorted; `posix` is a `-u-va-`
type, not a variant; `MatchStrings` returns the plain default tag when nothing matched (confidence `No`);
`Force` and `-u-ks-identic` undo the `Ignore*` equivalences as documented; `currency.Query` can yield a unit
under another table index than `ParseISO`, so units are compared by code. Go 1.27's tables are Unicode 17: a
case mapping to a rune Unicode 15 lacks (U+0264 -> U+A7CB) and the Tai Xuan Jing symbols' width are counted,
not compared; `Title` is compared with Python only on words of cased letters (Python's `str.title` restarts a
word at every uncased character); the Greek, Lithuanian and Afrikaans casers are not modelled; the casers are
stateful and are `Reset` before `Span` (as `String` does); the won sign U+20A9 is halfwidth by fiat with no
`Folded`; `width.Fold` is the width decomposition alone (a halfwidth Hangul letter folds to the compatibility
jamo, which NFKC decomposes further); ill-formed UTF-8 never conforms to the Bidi Rule; a paragraph that is
just its separator has no runs; PRECIS strings with CONTEXTJ/CONTEXTO runes (RFC 5892 appendix A) are
skipped, since `Allowed()` excludes them while the enforcement accepts them in context. The `Printer`'s `0`
flag becomes a minimum number of (grouped) integer digits, so `%010d` of 12345 is `0,000,012,345` (asserted by
upstream's tests), and an integer's precision is grouped the same way; a message without verbs ignores its
arguments (no `EXTRA` marker); `number.Pad` without `FormatWidth` pads to the pattern's own length (9 for
`#,##0.###`); `Decimal(-0.0)` and a negative value rounding to zero print without the sign; a form the
language's rules never produce is rejected by `Selectf`; the catalog `Fallback` option orders the matcher
only, lookups walk the parent chain to `und` and then render the key. A probe
saw `Collator.SortStrings` retain about 240 bytes per call (`sorter.buf` is never reset), but the same loop
under `go test` retains nothing measurable, so it is not recorded.
