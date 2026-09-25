# enmime

[jhillyerd/enmime](https://github.com/jhillyerd/enmime), a MIME parser and builder, against
Python's `email` package: for a generated message, enmime's leaf parts (media type, charset,
disposition, file name, decoded content) and decoded Subject, From and To must be Python's; a
message built with `Builder` and written with `Encode` must be read by Python as built.

## What is tested

**`hegel/hegel_mime_test.go`** (needs `python3`; `hegel/oracle.py` is the child process, one
request per line)
- `TestHegelReadMatchesPython`: a message with From, To (one to three addresses, display names
  plain, quoted or RFC 2047 encoded in UTF-8 or ISO-8859-1, B or Q; folded lists; groups; a comment
  before an address), Subject (up to nine words, encoded words split and folded, with a language
  tag), optional MIME-Version, and a body that is a leaf or a multipart/mixed, alternative or
  related tree of depth up to two with one to three children each: text parts (plain, html, csv,
  calendar) in UTF-8, ISO-8859-1, latin1, windows-1252 (its 0x80-0x9F range too), US-ASCII or with
  no charset or no Content-Type or no headers at all, in 7bit, 8bit, quoted-printable (lower-case
  hex too) or base64 (lines of 4 to 1000, unpadded); binary parts (octet-stream, pdf, gif, jpeg)
  in base64 or quoted-printable; dispositions and file names as quoted values, RFC 2231 encoded,
  in continuations (split inside a multi-byte character too), in a non-UTF-8 charset, or as a
  `name` parameter; media types, encodings and dispositions in any case; folded parameters;
  boundaries with specials, quoted, with trailing white space; preamble, epilogue, body lines that
  start with the boundary; LF or CRLF. Python's reading (leaf parts in document order; Subject,
  From, To decoded) must be enmime's, with `DisableCharacterDetection`; a message Python rejects
  is counted. The property draws every recorded shape and lands on enmime/5 (a comment before
  an address, 7 % of cases; the other shapes are 0.2-6 %, met first in some runs).
- **`hegel/hegel_build_test.go`** `TestHegelBuildReadByPython`: `Builder` with From, To, Subject,
  text, HTML, attachments and inlines (text and binary, file names with specials and non-ASCII),
  `Build` and `Encode`; Python reads the leaves (type, file name, content), Subject and addresses
  as given; enmime reads back its own Subject, Text and HTML.

**`hegel/hegel_shapes_test.go`**: one narrow property per recorded bug, the wide generators with
one leaf (drawn by position modulo the leaf count) replaced by the bug's shape region.

**`hegel/hegel_pins_test.go`**: one deterministic reproducer per recorded bug.

## Oracles

Python 3.12's `email.message_from_bytes` with `policy.default` (RFC 2047 and RFC 2231 decoding,
address parsing, `get_payload(decode=True)`); text contents are decoded with the declared charset
and re-encoded as UTF-8, as enmime does. Normalisations: addresses compared as display name and
`username@domain` (Python re-quotes a quoted local part, enmime does not); a part without a
Content-Type header is compared by content only (Python applies the text/plain default, enmime
leaves a child's type empty with a warning and gives the root text/plain; charset=us-ascii).
Not generated, because the parsers differ by design: comments after an address (Go's net/mail makes
them the display name, Python drops them); `message/*` parts (Python nests a message); unpadded
base64 in encoded words (Python decodes, enmime keeps the word, as RFC 2047 allows); a missing
closing boundary and multiparts without a boundary (both parsers recover, with different trailing
line ends); raw 8-bit headers; enmime's charset detection. A part with no charset anywhere and
100 or more runes of content can still get a detected charset (`MinCharsetDetectRunes`;
`DisableCharacterDetection` only keeps a declared one: a 109-rune body of digits comes back
`ISO-8859-1`), so the charset of such a part is counted and not compared, the content still is.

## Known bugs

Five bugs (`bugs.toml`): a part without Content-Type losing its disposition and file name;
RFC 2231 file names in non-UTF-8 charsets dropped; body lines starting with the boundary taken as
delimiters or terminators; encoded words with a language tag not decoded; a comment before an
address breaking the list. The generators draw every shape (STYLE.md rule 11): the wide property
is the expected failure mapped to enmime/5, and each bug has a narrow property in
`hegel/hegel_shapes_test.go`, the deterministic expected failure beside the pin:
`TestHegelDispositionSurvivesMissingContentType` (enmime/1), `TestHegelRFC2231FileNamesDecodeInLatin1`
(/2), `TestHegelBoundaryLikeBodyLinesStayInTheContent` (/3), `TestHegelLanguageTaggedEncodedWordsDecode`
(/4) and `TestHegelCommentsBeforeAddressesParse` (/5). `HEGEL_NO_KNOWN=1` (read once in
`hegel/known.go`) switches the shapes off (no disposition on a part without Content-Type, RFC 2231
file names in UTF-8 only, no boundary-like content line, no language tag, no comment before an
address); every property then passes at 3000 cases. Until 2026-09-25 the switch had the inverse
meaning (the gates were on by default and `HEGEL_NO_KNOWN=1` lifted them).

## Not tested

`Envelope.Text`/`HTML`/`Attachments`/`Inlines`/`OtherParts` selection rules beyond the round trip
(text parts gathered into `Text` are enmime's design), charset detection, `html2text` down-
conversion, `DecodeHeaders`, DSN parsing, `Part.Encode` of parsed trees, the `mediatype` package's
repairs of malformed headers (nothing malformed is generated), errors and warnings.

## History

- 2026-09-20: written against 6c69c1c37bf7d273337b7d568f971013aa4b38d6 (2026-09-05, v2.5.0) with
  hegel.dev/go/hegel v0.6.33; 5 bugs.
- 2026-09-25: generators rewritten in combinator style; the properties draw the known shapes and
  five narrow properties were added; the NO_KNOWN switch flipped to the zoo's meaning; the
  charset-detection tolerance above added.
