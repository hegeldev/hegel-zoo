# brotli

[andybalholm/brotli](https://github.com/andybalholm/brotli) is the pure-Go Brotli
implementation: the reference encoder and decoder translated from C with c2go (`Writer`
at qualities 0–11 with window sizes 10–24, `Reader`), a newer encoder built from the
`matchfinder` package (`NewWriterV2`, the LZ77 stages M0, M4, Pathfinder, Bargain1–3, Trio,
ZFast, ZDFast, ZM, and the entropy stages `Encoder` and `FastEncoder`), a `flate` package
that puts the same matchfinders behind DEFLATE and gzip encoders, and `HTTPCompressor`, a
content-negotiating response writer. About 30 000 lines, MIT, pinned at `eede312` (v1.2.4,
2026-09-10). README and LICENSE are the only project documents and say nothing about
AI-written code.

## Build

`go test -count=1 -run TestHegel -v .` in the module root, with the `brotli` command-line
tool (1.1.0, the `brotli` package of Ubuntu) installed: it is the reference implementation
and the tests fail without it. The patch adds `hegel_test.go` (the models and the properties)
and `hegel_pins_test.go` (one plain test per bug) and requires `hegel.dev/go/hegel v0.6.33`
in go.mod.

## Oracles

- **The reference implementation**: the `brotli` tool decodes every stream the `Writer`,
  `NewWriterV2`, the hand-assembled `matchfinder.Writer`s, `Encoder` and `FastEncoder`
  produce, and its streams (qualities 0–11, windows 10–24) must be read by the `Reader`.
  Damaged streams are judged by it too: bytes it rejects the library must reject, bytes it
  decodes the library must decode to the same content.
- **RFC 7932**: the stream header's WBITS code, parsed independently, must be in range and
  within the configured window.
- **LZ77**: a match sequence is valid when the matches cover the block exactly, every copy
  has a positive distance no further back than the bytes before it and within the finder's
  window, the copied bytes equal the bytes at that distance (checked against the history the
  finder was fed since its last Reset), and only the last match may have length 0. Every
  `MatchFinder` is held to it, and generated valid sequences (literal runs, overlapping
  copies, copies into earlier blocks, lengths from the format's minimum to thousands of
  bytes, distances up to the window) are what the encoders must accept.
- **The standard library**: `compress/flate` and `compress/gzip` decode the `flate`
  package's streams.
- **RFC 9110 section 12.5.3** for `HTTPCompressor`: content codings compared
  case-insensitively, an explicit listing sets a coding's weight, `*` the weight of every
  coding not listed, the highest non-zero weight wins, `br` (offered first) wins ties, and
  the body must decode with the coding announced.
- **The documented contracts**: Flush makes the bytes so far decodable, Write/Flush/Close
  after Close fail, Reset revives a Writer or Reader, a Reader at the end returns `io.EOF`,
  `FindMatches` and `Encode` append to `dst`, level and window values outside the documented
  ranges are clamped.

## Properties

| Property | Checks |
|---|---|
| WriterStreamsDecode | `Writer` with random quality (−3–20) and LGWin (0, 5–30) via `NewWriter`, `NewWriterLevel` or `NewWriterOptions`, data of 0–128 KiB in seven characters (random, text, runs, repeats, zeros, sparse, mixed) written in chunks with Flushes: after every Flush the bytes so far decode to everything written and then want more input; the header's WBITS is 10–24 and within LGWin; the reference tool and the `Reader` (random source chunking, `(n, EOF)` sources, buffers from 1 byte to 128 KiB) decode the stream; Write, Close and Flush after Close fail; Reset gives a second decodable stream with the same WBITS |
| ReaderDecodesReferenceStreams | streams from the tool at random quality and window, one to three per case through one `Reader` (fresh or Reset), read with fixed buffers, `io.Copy` or `io.ReadAll`: the content is right, then `(0, io.EOF)` and a harmless `Read(nil)` |
| DamagedStreams | a tool or `Writer` stream with a bit flipped, a byte replaced, deleted or inserted, truncated, followed by extra bytes, empty, or replaced by garbage: the `Reader` never panics, never reports a clean EOF for damage, agrees with the tool on rejection and on the decoded content when accepted, and is reusable after Reset |
| MatchFindersAreValidLZ77 | every `MatchFinder` (random parameters: window, minimum length, hash length, table bits, chain length, distance cost, lazy, skip, `AutoReset`) on one to four blocks, some echoing earlier data, with `dst` empty, pre-filled or accumulated, and occasional Resets: the matches are valid LZ77 against the bytes, appended to `dst` |
| EncodersAcceptAnyMatches | `Encoder`, `FastEncoder`, `flate.NewEncoder` and `NewGZIPEncoder` on one to four blocks of generated valid matches (lengths from the format's minimum up to 20 000, distances up to the window, into earlier blocks), appended or not, after a Reset or not: the tool and the `Reader`, or the standard library, decode the stream to the blocks |
| MatchfinderWritersRoundTrip | `NewWriterV2` (levels −1–12), `flate.NewWriter`, `NewGZIPWriter` and `matchfinder.Writer`s assembled from a random finder, `Encoder` or `FastEncoder` and block size (0–65 536), fed in chunks: the stream decodes with the reference decoders and the `Reader`; Reset and reuse |
| HTTPCompressorNegotiates | generated Accept-Encoding headers (zero to two lines of up to four codings among br, gzip, `*`, identity, deflate, zstd and others, in either case, with valid, absent or malformed weights, random separators) at levels 0–11 with and without a preset Vary: Content-Encoding is the RFC's choice, Vary is set unless preset, the body decodes with the announced coding |

## Known bugs

The generators draw the shape of every recorded bug (STYLE.md rule 11), so five of the wide
properties are expected failures mapped to the bug they land on: DamagedStreams on brotli/7
(the Reset check after trailing bytes), MatchFindersAreValidLZ77 on brotli/5 (M4 with an
accumulated `dst`; brotli/8 in some runs, a pass in others: intermittent),
EncodersAcceptAnyMatches on brotli/6 (two- and three-byte matches into `FastEncoder`; on
brotli/1 nearly as often), MatchfinderWritersRoundTrip on brotli/1 (flate matches over 258
bytes) and HTTPCompressorNegotiates on brotli/2 (mixed-case codings; brotli/4 now and then).
Three of the eight bugs surface as panics, which the harness recovers and names. Each bug also
has a narrow property over its own shape region in `hegel_shapes_test.go`, the deterministic
expected failure beside the pin: `TestHegelFlateWritersSplitLongMatches` (brotli/1),
`TestHegelContentCodingsMatchInAnyCase` (/2), `TestHegelStarDoesNotOutweighAListedBr` (/3),
`TestHegelGzipOnlyClientsGetGzipAtHighLevels` (/4),
`TestHegelMatchFindersIgnoreThePreviousMatchesInDst` (/5),
`TestHegelFastEncoderEncodesTwoAndThreeByteMatches` (/6),
`TestHegelReaderResetRecoversFromTrailingBytes` (/7) and
`TestHegelShortBlocksStayInTheFindersHistory` (/8). `HEGEL_NO_KNOWN=1` (read once) switches
the shapes off: flate matches no longer than 258 bytes and random data for the flate writers,
lowercase codings, no `*` beside a listed br or gzip, levels up to 9 for the HTTP helper, an
empty `dst` for M4, matches of at least four bytes for `FastEncoder` and no Bargain finder in
front of it, no block under 20 bytes before another for Trio and ZM, and the Reset check after
trailing data skipped (11.6 % of the damaged streams, too many for an assume); every property
then passes at 1000 cases in under a minute, most of it the tool's round trips.
`BROTLI_COLLECT=1` records mismatches instead of failing and prints them shortest-first with
the case's description; `HEGEL_VERBOSE=1` turns on the engine's log.

## Bugs (8; details in bugs.toml)

| id | summary | severity |
|----|---------|----------|
| brotli/1 | the `flate` encoder panics ("match too long") on a match over 258 bytes instead of splitting it, so `flate.NewWriter` and `NewGZIPWriter` panic at every level on any input with a long repeat (1000 zero bytes) | high |
| brotli/2 | `HTTPCompressor` matches Accept-Encoding codings case-sensitively (`BR` gets no compression) | low |
| brotli/3 | an Accept-Encoding `*` overrides the weight of an explicitly listed coding (`br;q=0.5, *` and `br;q=0, *` get brotli, not gzip) | low |
| brotli/4 | `HTTPCompressorWithLevel` at level 10 or 11 sends gzip-only clients an uncompressed response (`gzip.NewWriterLevel` rejects the level and the error falls through to identity) | low |
| brotli/5 | `M4` takes the last entry of `dst` for its previous match: accumulating matches across blocks yields distance-0 matches (corrupt streams), a far stale distance panics | medium |
| brotli/6 | `FastEncoder` writes a corrupt stream for a length-3 match and panics for a length-2 or -3 match after six or more literals (its fixed histograms give those codes no code word); a `matchfinder.Writer` pairing it with a Bargain finder fails on ordinary text | medium |
| brotli/7 | `Reader.Reset` after a stream with trailing bytes ("excessive input") leaves the Reader unable to decode the next stream (the leftover input is kept) | medium |
| brotli/8 | `Trio` and `ZM` leave a block under 20 (16) bytes out of their history, so later matches into earlier data copy from the wrong place: a `matchfinder.Writer` with one block per Write silently corrupts the data | high |

How they were found: brotli/1 by the first round of the writers property (260 zero bytes
through `flate.NewWriter` level −1) and independently by the generated-matches property;
brotli/2, 3 and 4 by the negotiation property's model (case, `*` beside a listed coding,
levels 10–11 with gzip-only clients); brotli/5 by the LZ77 property with a pre-filled `dst`,
then reduced by probes to the accumulate-across-blocks shape and the far-distance panic;
brotli/6 by the generated-matches property (short matches at small distances), reduced by a
grid of insert and copy lengths; brotli/7 by the damaged-streams property's Reset check
(every "append" case); brotli/8 by the LZ77 property (a block echoing earlier data after a
two-byte block), reduced by probes to three blocks and confirmed through a `Writer`. The
`Writer`, the `Reader` (apart from Reset), `NewWriterV2`, `Encoder` and the other nine
matchfinders came out clean: every stream agrees with the reference tool both ways, damaged
streams are judged as the tool judges them, and the matches are valid LZ77 on every block.

## Accepted differences (not bugs)

- Quality and window values outside the documented ranges are clamped silently
  (`NewWriterLevel(w, 20)` compresses at 11, LGWin 5 becomes 10, 30 becomes 24), as the
  reference library does.
- The `Reader` does not read "large window" streams (`brotli --large_window`, WBITS code
  0x11, outside RFC 7932); the tool decodes them without being told. The library has no way
  to ask for them, so the properties never make them.
- A stream followed by extra bytes is an error for both the `Reader` (`brotli: excessive
  input`) and the tool; the `Reader` returns the content read so far with the error.
- Malformed Accept-Encoding weights (`q=1.5`, `q=abc`) are accepted or skipped without a
  verdict from the RFC; the properties only require a decodable body then.
- Without an Accept-Encoding header the helper sends identity, which the RFC allows.
- `Match.Distance` beyond a finder's `MaxDistance` is checked only when the parameter was
  set; the defaults differ between finders (65 535 for M4, 65 536 for ZFast, 1 MiB for the
  writers) and are not part of the check.

## Not tested

Compression ratios and speed, the `corpus-test` program, the static dictionary and the
context modelling beyond decoding whatever the encoders produce, `TextEncoder` (a debugging
aid), and concurrent use of one Writer or Reader.
