# uuid

[google/uuid](https://github.com/google/uuid) generates and inspects UUIDs (RFC 9562: versions
1, 3, 4, 5, 6, 7 and the DCE version 2): `Parse`/`ParseBytes`/`Validate` on the four documented
spellings, `String`/`URN`, `Version`/`Variant`/`Time`/`ClockSequence`/`NodeID`, the constructors,
`Compare`, and the `encoding` (text, binary, JSON), `database/sql` (`Scan`/`Value`, `NullUUID`)
glue. Pinned at 2d3c2a9cc518 (2024-11-14, past v1.6.0; adds `NewV6WithTime`). BSD-3-Clause.
CONTRIBUTING.md asks for Conventional Commits and Google's CLA for pull requests, nothing about
AI; not archived. Checked 2026-09-15. Upstream has fuzz targets for `Parse`/`ParseBytes`/
`FromBytes` (crash-only).

## Oracle

Python 3's `uuid` module, one child held open over JSON lines: `UUID(str)` for the spellings
Python shares with `Parse` (hyphenated, `urn:uuid:` lower-case, `{…}`, 32 hex digits),
`UUID(bytes=…)` for the field accessors (`version`, `variant`, `time`, `clock_seq`, `node`,
`str`, `urn`, `int`), `uuid3`/`uuid5` for the name-based versions. In-process models: the
documented `Parse`/`Validate` grammar (lengths 32/36/38/45, the error kinds `ErrInvalidLength`,
`ErrInvalidURNPrefix`, `ErrInvalidUUIDFormat`, `ErrInvalidBracketedFormat`), the RFC 9562 bit
layouts of versions 1, 6 and 7 (with the RFC's example values as a sanity test), `NewHash`'s
documented definition, and round trips.

## Properties

- `TestHegelParseAgreesWithPython` — every documented spelling (random hex case, the `urn:uuid:`
  prefix in any case, braces or any other 38-byte wrapper) parses through `Parse`, `ParseBytes`,
  `UnmarshalText`, `Scan` (string and bytes), `MustParse` and `json.Unmarshal` to the same bytes,
  `Validate` accepts exactly the documented ones, and `String`/`URN`/`MarshalText`/`Value` are
  Python's spellings. Clean.
- `TestHegelParseFollowsTheDocumentedGrammar` — near-valid text (mutations, junk of plausible
  lengths): `Parse`/`ParseBytes`/`Validate` accept exactly the grammar and return the documented
  error kinds; whatever `Parse` accepts, Python parses to the same value. Clean.
- `TestHegelFieldsAgreeWithPython` — arbitrary 16 bytes (all versions and variants, Nil, Max, the
  name spaces): `Version`, `Variant`, `Time` (v1 layout for versions other than 6/7, the v6/v7
  layouts otherwise), `ClockSequence`, `NodeID`, `UnixTime` inverting the tick count, `Compare`
  as Python's integer order and as the string order, the `String()` names. Clean.
- `TestHegelNameBasedAgreeWithPython` — `NewMD5`/`NewSHA1` are `uuid3`/`uuid5` for arbitrary name
  spaces and byte names; `NewHash` with MD5/SHA-1/SHA-256 and any version is the documented
  truncation with the bits set, resets the hash, and is deterministic. Clean.
- `TestHegelTimeBasedLayoutsFollowTheRFC` — `SetClockSequence`/`SetNodeID` (one node in ten
  all zeros) then `NewUUID` (v1: fields, wall-clock bracket), `NewV6WithTime` at a drawn instant
  (exact `Time()`, the clock sequence advancing for a repeated instant; 15% of the instants lie
  outside 1678–2262), a v1 re-laid as v6 keeping its `Time()`, `NewV7FromReader` (our random
  bits, the wall clock in ms, strictly increasing). Finds /5 (and /6).
- `TestHegelDCEFieldsRoundTrip` — `NewDCESecurity(domain, id)`: version 2, `Domain()`, `ID()`,
  node, `Domain.String()`. Clean.
- `TestHegelEncodingsRoundTrip` — a struct with a `UUID`, a `NullUUID` and a `UUIDs` through
  `encoding/json` both ways (null included), `NullUUID.MarshalJSON`/`UnmarshalJSON`, text and
  binary of the UUID and of a `NullUUID` valid or null, `FromBytes`, `Value`→`Scan` on fresh
  and on prefilled destinations, `Scan` of NULL as nil, `""` and an empty `[]byte`, wrong
  binary lengths rejected. Finds /4 (and /2, /3).
- `TestHegelRandomVersionsSetOnlyTheirBits` — `NewRandomFromReader`/`NewV7FromReader` keep the
  reader's bits and set only the version/variant, short readers are errors, `New`/`NewRandom`/
  `NewString` are v4. Clean.

The generators draw the shapes of the six recorded bugs and the properties that meet them are
the expected failures mapped to the bugs (STYLE.md rule 11); every mismatch names the shape it
has. One narrow property per bug in `hegel_shapes_test.go` draws the bug's shape region with
random contents: `ConcurrentNewV6WithTimeCallsAreDistinct` (/1, two to four goroutines calling
`NewV6WithTime` at one instant, intermittent like the pin), `ScanOfNullResetsTheDestination`
(/2), `NullUUIDScanOfEmptyIsNull` (/3), `NullUUIDTextAndBinaryRoundTrip` (/4),
`NewV6WithTimeRejectsUnrepresentableInstants` (/5) and `SetNodeIDKeepsTheZeroNode` (/6).
`HEGEL_NO_KNOWN=1` switches the shapes off (instants inside 1678–2262, non-zero nodes, fresh
destinations, a valid `NullUUID` through text and binary, one goroutine) and all fifteen
properties pass.

## Bugs

| id | severity | title |
|----|----------|-------|
| uuid/1 | high | `NewV6WithTime` updates the shared clock state without the mutex, so concurrent callers get duplicate UUIDs |
| uuid/2 | medium | `UUID.Scan` of a NULL, an empty string or an empty `[]byte` leaves the previous value in place |
| uuid/3 | low | `NullUUID.Scan` of an empty string or empty `[]byte` reports `Valid = true` |
| uuid/4 | low | `NullUUID`'s null value marshals to text `null` and to an empty binary, neither of which unmarshals |
| uuid/5 | low | `NewV6WithTime` encodes a garbage timestamp for instants it cannot represent instead of returning an error |
| uuid/6 | low | `SetNodeID` of six zero bytes returns true but the node is replaced by the hardware address on the next use |

uuid/1 is marked `intermittent` in target.toml: the pin fails whenever one of eight rounds of
12 000 concurrent calls yields a duplicate, and the narrow property whenever one of twelve rounds
of its drawn calls does; on this two-core machine the goroutines often run in streaks and a
race is not a certainty.

## Not bugs

- `Parse` accepts any 38-byte string whose middle 36 bytes are a UUID (`(…)`, `[…]`, `x…y`):
  documented ("Only the middle 36 bytes are examined"); `Validate` insists on `{…}`, also
  documented, and the properties expect exactly that.
- `Parse` takes the `urn:uuid:` prefix in any case (`strings.EqualFold`); Python's constructor
  does not. RFC 9562 says the URN prefix is case-insensitive.
- `Time()` of a version-7 UUID has millisecond resolution (the `rand_a` sub-millisecond bits the
  library itself fills are not read back): the RFC leaves `rand_a` to the implementation.
- For instants before 1970 with a nanosecond count that is not a multiple of 100, the timestamp
  is truncated toward zero rather than floored (one tick late); the generator uses multiples of
  100 there. Sub-100 ns and pre-1970 — not recorded.
- `NewUUID`/`NewV6` bump the clock sequence whenever the instant is not later than the last one
  used (RFC 9562 §6.1), including after a `NewV6WithTime` in the future: expected, so the
  property re-sets the clock sequence (with a changed value, which resets the "last time") before
  each `NewUUID`.
