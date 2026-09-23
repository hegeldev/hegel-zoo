# ulid

[oklog/ulid](https://github.com/oklog/ulid) v2 (Apache-2.0), pinned at `75921a73` (v2.1.2,
2026-07-23): Universally Unique Lexicographically Sortable Identifiers - a 48-bit millisecond
timestamp and 80 bits of entropy, Crockford base32 text, binary, SQL and JSON encodings, and
monotonic entropy sources.

The patch adds `hegel_test.go` (package `ulid_test`) and the `hegel.dev/go/hegel` requirement to
`go.mod`. The inputs are `Generator` values built from the binding's combinators (STYLE.md):
`ids` is a `weighted` choice of the zero ULID, all ones and `Binary(16, 16)` (with edge-value
timestamp bytes from a `Lists` three times in ten), `millis` a `weighted` choice of the timestamp
corners, `parseInputs` a `OneOf` of valid-or-overflowing, substituted (`Lists` of position/byte
pairs), truncated-and-padded and `Binary` strings, `idRuns` a `Lists` of ULIDs with same-time and
duplicate flags folded by `Map`, and the monotonic tests draw a printable `entropySource` (fast
path, plain reader, or a reader started 1-200 below 2^80) and a `Lists` of millisecond steps up
front instead of drawing inside the read loop. The text encoding is checked against a
`math/big` Crockford base32 model; parsing
against the documented error contract (`ErrDataSize`, `ErrInvalidCharacters`, `ErrOverflow`, and
"undefined ULIDs" for lenient parsing of bad characters); ordering against `(time, entropy)`; the
monotonic sources against the documentation of `Monotonic`.

## What is tested

- `TestHegelTextEncodingIsCrockfordBase32` - `String`, `MarshalText[To]`, `Parse`, `ParseStrict`,
  `UnmarshalText`, `Scan` (string, 16- and 26-byte slices, nil, other types), `Value`,
  `MarshalBinary[To]`, `UnmarshalBinary`, `Bytes`, JSON, `Entropy`/`SetEntropy`, `IsZero` on
  random, zero and all-ones ULIDs, in upper, lower and mixed case.
- `TestHegelParsingReportsTheDocumentedErrors` - valid strings, strings with substituted bytes
  (invalid letters I L O U, punctuation, control and high bytes), wrong lengths and random bytes:
  strict and lenient parsing, `UnmarshalText`, `Scan` and `MustParseStrict` give the documented
  errors and values.
- `TestHegelOrderIsLexicographicAndChronological` - `Compare` equals byte order, string order and
  `(time, entropy)` order; sorting ULIDs sorts their strings and their times.
- `TestHegelTimestampsRoundTrip` - `New`, `SetTime`, `Time`, `Timestamp`, `MaxTime`, `ErrBigTime`,
  `MustNew`, entropy readers of exact and short length, `Make`/`MustNewDefault`/`Now`.
- `TestHegelMonotonicEntropyIncreasesWithinAMillisecond` - `Monotonic` (with a `*rand.Rand` and
  with a plain reader, optionally behind `LockedMonotonicReader`) over sequences of same, later
  and earlier milliseconds: strictly increasing entropy within a millisecond, increments at most
  `inc` (exactly 1 for `inc == 1`), fresh entropy on a new millisecond, overflow only when there is
  no room.
- `TestHegelMonotonicIncrementsCoverTheDocumentedRange` - the increments of both paths against
  "a random number between 1 and inc inclusive": every value appears for small `inc`, and the low
  bytes are spread for large `inc`.
- `TestHegelPin...` - one plain test per recorded bug.

## Bugs

See `bugs.toml`: the `io.Reader` path of `MonotonicEntropy` increments by 2..inc, never 1 (1);
after `ErrMonotonicOverflow` the wrapped entropy stays, so the next read in the same millisecond
returns a lower ULID (2); `random()` masks the little-endian low byte instead of the most
significant one, so reader-fed increments are heavily biased (16 values for `inc = 1000`) and
reject most candidates (3).

## Notes

- `Parse` on invalid characters is documented to produce undefined ULIDs; the property only
  requires that it does not panic and agrees with `UnmarshalText` and `Scan`.
- The three findings are all in `MonotonicEntropy.random`/`increment`; the default entropy
  (`math/rand` through the fast path) is not affected by 1 and 3.
