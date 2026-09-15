# gofrs-uuid

[gofrs/uuid](https://github.com/gofrs/uuid) (module `github.com/gofrs/uuid/v5`, the maintained
fork of satori/go.uuid) generates and inspects RFC 9562 UUIDs: versions 1, 3, 4, 5, 6, 7 and 8
through a `Generator` whose clock, random source and hardware address are injectable,
`FromString`/`Parse`/`UnmarshalText` on six input forms, `TimestampFromV1/V6/V7`, `fmt.Formatter`
verbs, and the `encoding`/`database/sql` glue including `NullUUID`. Pinned at 9b67c3bcafbf
(2026-08-10, past v5.5.1). MIT. No CONTRIBUTING.md or AI policy; not archived. Checked
2026-09-15. Upstream has crash-only fuzz targets for the parsers and a large v7 monotonicity
suite.

## Oracle

Python 3's `uuid` module, one child held open over JSON lines: `UUID(str)` for the six input
forms (all of which Python also takes), `UUID(bytes=…)` for the field accessors, `uuid3`/`uuid5`
for the name-based versions. In-process models: the documented parsing grammar with the
package's error values (`ErrIncorrectLength`, `ErrInvalidBraces`, `ErrInvalidURNPrefix`,
`ErrInvalidDashes`, `ErrInvalidFormat`, compared with `errors.Is`), the RFC 9562 bit layouts
(the RFC's example values as a sanity test), and — the main instrument — a generator built with
`WithRandomReader`/`WithEpochFunc`/`WithHWAddrFunc` from drawn bytes, instants and an address,
so that every field of every generated UUID is predicted exactly from the script.

## Properties

- `TestHegelParseAgreesWithPython` — canonical/hash forms, braced, `urn:uuid:`-prefixed, random
  hex case: `FromString`, `FromStringOrNil`, `Parse`, `UnmarshalText`, `Scan` (string and text
  bytes), `json.Unmarshal` into `UUID` and `NullUUID` agree with Python; `String`, `MarshalText`,
  `Value`, `%v %s %x %X %S %q %#v` are Python's spellings. Clean.
- `TestHegelParseFollowsTheDocumentedGrammar` — near-valid text (mutations, wrong-case prefixes,
  other brackets, junk of plausible lengths): the grammar and its error values; `FromStringOrNil`
  is Nil on error; accepted text parses identically in Python. Clean.
- `TestHegelFieldsAgreeWithPython` — arbitrary bytes: `Version`, `Variant`, `TimestampFromV1`
  vs Python's `time` (and the v6/v7 layouts), the version guards (`ErrInvalidVersion`),
  `Timestamp.Time` inverting the tick count, the clock-sequence/node layouts, `SetVersion`/
  `SetVariant` touching only their bits, `IsNil`/`IsZero`/`Bytes`. Clean.
- `TestHegelNameBasedAgreeWithPython` — `NewV3`/`NewV5` (package and generator) are `uuid3`/
  `uuid5` over the bytes of arbitrary names, invalid UTF-8 included. Clean.
- `TestHegelGeneratorsFollowTheRFC` — a scripted generator, 1–6 calls: v1 (time fields, the
  14-bit clock sequence seeded from the stream and stepped when the instant does not advance,
  the node from the address or from the stream with the multicast bit), v6 (reordered timestamp,
  random low half), v4 (the stream with the bits set), v7 (`NewV7` and `NewV7AtTime` mixed: the
  millisecond field, the counter seeded from 11 stream bits and stepped within a millisecond,
  `rand_b` from the stream, clamping for a backwards clock vs honouring an older explicit
  instant, strict ordering otherwise), v8 (custom fields with the bits set; wrong lengths are
  `ErrV8FieldLength`), and streams too short for the request (errors and Nil, never a panic).
  Clean.
- `TestHegelEncodingsRoundTrip` — JSON (struct with `UUID`, `NullUUID` incl. null, a slice),
  `NullUUID.MarshalJSON`/`UnmarshalJSON`, text/binary, `FromBytes`/`FromBytesOrNil`,
  `Value`→`Scan` for strings, 16-byte binaries, text bytes and `UUID` values on fresh
  destinations, `NullUUID.Scan(nil)`, unsupported sources (`ErrTypeConvertError`), wrong binary
  lengths (`ErrIncorrectByteLength`). Clean.

What the general generators avoid (pinned separately): `Scan`/`Parse` into a non-fresh
destination with rejected text (/1, /2), JSON numbers or escapes for `NullUUID` (/3), instants
outside 1678–2262 for `NewV1AtTime`/`NewV6AtTime` (/4).

## Bugs

| id | severity | title |
|----|----------|-------|
| gofrs-uuid/1 | low | `NullUUID.Scan` of a rejected source leaves `Valid = true` |
| gofrs-uuid/2 | low | `Parse`, `UnmarshalText` and `Scan` decode into the receiver byte by byte, so a rejected string leaves a mix of old and new bytes |
| gofrs-uuid/3 | low | `NullUUID.UnmarshalJSON` hands the raw JSON token to the text parser: a 32-digit number is accepted and string escapes are not decoded |
| gofrs-uuid/4 | low | `NewV1AtTime` and `NewV6AtTime` encode a garbage timestamp for instants they cannot represent instead of returning an error |

## Not bugs

- The `urn:uuid:` prefix is accepted in lower case only: the documented forms list it literally
  (google/uuid folds case; RFC 9562 calls the prefix case-insensitive, but this is a spelling
  choice the package documents).
- `UUID.Scan(nil)` is `ErrTypeConvertError`: NULLs belong to `NullUUID`, and upstream tests
  assert the error.
- `fmt` width and precision flags are ignored by the `Formatter` (`%40s` is not padded): the
  `Formatter` contract leaves flag handling to the implementation.
- For instants before 1970 with a nanosecond count that is not a multiple of 100, the timestamp
  is truncated toward zero rather than floored (one tick late); the generator uses multiples of
  100 there.
- `NewV6AtTime` draws its clock sequence from the random stream rather than from the v1 clock
  sequence (RFC 9562 §5.6 allows either) but still steps the shared v1 sequence: an
  implementation choice.
- v7 `Timestamp.Time()` has millisecond resolution; `rand_a` holds the counter, as documented.
