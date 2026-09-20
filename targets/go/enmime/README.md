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
  is counted.
- **`hegel/hegel_build_test.go`** `TestHegelBuildReadByPython`: `Builder` with From, To, Subject,
  text, HTML, attachments and inlines (text and binary, file names with specials and non-ASCII),
  `Build` and `Encode`; Python reads the leaves (type, file name, content), Subject and addresses
  as given; enmime reads back its own Subject, Text and HTML.

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
line ends); raw 8-bit headers; enmime's charset detection.

## Known bugs (gated)

Five bugs (`bugs.toml`): a part without Content-Type losing its disposition and file name;
RFC 2231 file names in non-UTF-8 charsets dropped; body lines starting with the boundary taken as
delimiters or terminators; encoded words with a language tag not decoded; a comment before an
address breaking the list. `hegel/known.go` gates them by generated shape (a disposition on a part
without Content-Type; a non-UTF-8 RFC 2231 file name; a boundary-like content line; a language tag;
a comment before an address); `HEGEL_NO_KNOWN=1` lifts the gates.

## Not tested

`Envelope.Text`/`HTML`/`Attachments`/`Inlines`/`OtherParts` selection rules beyond the round trip
(text parts gathered into `Text` are enmime's design), charset detection, `html2text` down-
conversion, `DecodeHeaders`, DSN parsing, `Part.Encode` of parsed trees, the `mediatype` package's
repairs of malformed headers (nothing malformed is generated), errors and warnings.

## History

- 2026-09-20: written against 6c69c1c37bf7d273337b7d568f971013aa4b38d6 (2026-09-05, v2.5.0) with
  hegel.dev/go/hegel v0.6.33; 5 bugs.
