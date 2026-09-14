# compress

[klauspost/compress](https://github.com/klauspost/compress) is the Go compression toolbox: drop-in
replacements for `compress/flate`, `compress/gzip` and `compress/zlib` (faster, with a stateless
deflater and custom windows), a pure-Go zstandard encoder and decoder, the S2 extension of Snappy
and a Snappy-compatible package, plus Huffman/FSE primitives. About 70 000 lines; it is the zstd
implementation behind much of the Go ecosystem (Docker, Prometheus, Kubernetes…). The pinned
commit is the September 2026 head, a few commits past v1.20.0. BSD-3-Clause; no CONTRIBUTING.md
and no AI policy at the pinned commit (SECURITY.md only). The project has a large fuzz corpus of
its own, which is why the interoperability oracles below matter more than round trips.

## Oracles

- The standard library's `compress/flate`, `compress/gzip` and `compress/zlib`, in process: a
  stream written by one side must decode byte-for-byte on the other, at every level, with and
  without dictionaries, with random chunking and sync flushes, through the stateless deflater and
  custom-window writer, and gzip headers must survive with all their fields.
- The reference `zstd` command-line tool (v1.5.5 here; `[run] setup` checks it is installed): a
  frame from klauspost's `Encoder` under random options must decode with `zstd -d`, and a frame
  from `zstd -1`…`--ultra -22` (with `--no-check`, `--long`, `--single-thread`, `--block-size`,
  `--no-content-size`, trained and raw-content dictionaries, several frames concatenated) must
  decode with klauspost's `Decoder` through `DecodeAll`, `Read` and `WriteTo`.
- For S2/Snappy there is no second implementation on the machine, so the properties are the
  format's own invariants: every encoder mode against both decoders, `DecodedLen`,
  `MaxEncodedLen`, `ConcatBlocks`, dictionaries, streams with random block sizes/padding/flushes,
  and Snappy-compatible S2 streams read by the Snappy reader.

Caveat on the oracle: Go 1.27.1's `compress/flate` writer at levels 7–9 with a short dictionary
(1 and 26 bytes seen; 300 not) emits the dictionary bytes inside its first stored block, and its
own reader then returns dict+data. That is the standard library's bug, not klauspost's; the
properties cap the standard writer at level 6 when a dictionary is used (`stdLevel`).

## Properties

- `TestHegelFlateInteroperatesWithStdlib` — random data (empty, random bytes, tiny alphabets,
  words, repeated patterns with mutations, runs, mixtures; up to 300 KB to cross the 32 KiB window
  and 64/128 KiB block sizes), a random level −2…9 and an optional dictionary sharing material with
  the data: klauspost writer (also `StatelessDeflate`, `NewWriterWindow`) → `compress/flate`
  reader, and `compress/flate` writer → klauspost `NewReaderDict`/`NewReaderOpts(WithDict)`.
- `TestHegelGzipInteroperatesWithStdlib` — one to three members with random headers (Latin-1
  names and comments, `Extra`, `ModTime`, `OS`) and levels, both directions; header fields must
  match; `Multistream(false)` stops after the first member.
- `TestHegelZlibInteroperatesWithStdlib` — levels and dictionaries both directions; a stream
  needing a dictionary is refused without it by both sides.
- `TestHegelZstdEncoderOutputDecodesWithReferenceTool` — `Encoder` with a random level, CRC on/off,
  zero frames, single segment, window size 1 KiB–4 MiB, no-entropy / all-literal-entropy, padding,
  low memory, trained or raw dictionary; `EncodeAll` or a streaming writer with `Reset`/
  `ResetContentSize`, chunks and flushes: `zstd -d` reproduces the input, klauspost's own
  `Decoder` agrees, and the frame header (`Header.Decode`, re-encoded by `AppendTo`) is
  consistent with the options (checksum flag, single-segment flag, content size).
- `TestHegelReferenceToolOutputDecodesWithKlauspost` — one to three frames from the tool with
  random flags, concatenated, decoded by `DecodeAll` and by the streaming reader (`Read` or
  `WriteTo`, random concurrency and low-memory mode); `Header` reports the checksum flag and the
  frame content size the flags imply and re-encodes to the same bytes.
- `TestHegelCorruptStreamsGetTheSameVerdictAsStdlib` — a flate/gzip/zlib stream (either writer)
  with one bit flip, byte change, insertion, deletion or truncation: klauspost's reader and the
  standard library's must both accept (same output) or both reject.
- `TestHegelCorruptFramesAcceptedByKlauspostAreAcceptedByReferenceTool` — the same corruptions on
  a zstd frame from either side: whatever klauspost accepts the reference tool accepts with the
  same output, and `DecodeAll` agrees with the streaming reader.
- `TestHegelS2AndSnappyBlocksRoundTrip`, `TestHegelS2AndSnappyStreamsRoundTrip` — as above.

The generators avoid the pinned shapes and say where: a zero `ModTime` in gzip headers (/1, /2),
the truncated-raw-deflate verdict (/3, recognised and skipped in the corruption property), the
checksum flag of the empty `EncodeAll` frame (/4). All nine pass at 1000 cases (about 30 s,
mostly `zstd` process launches); the four pins are expected failures. `COMPRESS_COLLECT=1` makes
the properties record mismatches instead of failing and print them shortest-first.

## Bugs (4; details in bugs.toml)

| id | summary | severity |
|----|---------|----------|
| compress/1 | gzip: a zero `ModTime` is written as MTIME 2288912640 (2042-07-14) instead of 0 | low |
| compress/2 | gzip: MTIME 0 is read as 1970-01-01 instead of the zero `time.Time` | low |
| compress/3 | flate: a raw stream cut off inside a match ends with `io.EOF`, not `ErrUnexpectedEOF` | medium |
| compress/4 | zstd: the empty `EncodeAll` frame has no checksum although `WithEncoderCRC` is on | low |

How they were found: the gzip property's first collect run (every case with a zero `ModTime`
differed on the read-back header; the reader half fell out of the source while confirming the
writer); the corruption property's first run (`stdlib rejected (unexpected EOF), klauspost
accepted` on 5- and 9-byte deflate streams, then reproduced by truncating a 21-byte stream at every
offset); the frame-header probe written before the zstd properties (the canned zero frame
`28b52ffd2000010000` against the tool's `28b52ffd240001000099e9d851`).

## Not bugs (documented, allowed by the specification, or the oracle's fault)

- Go 1.27.1 `compress/flate` levels 7–9 with a short dictionary write the dictionary into the
  stream (see above). Not klauspost's; the standard writer is capped at level 6 with dictionaries.
- `ResetContentSize` with a size below 256 produces a frame without `Frame_Content_Size`: the
  format can only store such sizes with the single-segment flag, which the streaming encoder does
  not set (the tool does, because it knows the input is small). Not recorded.
- `EncodeAll` of 1–255 bytes without `WithSingleSegment` likewise writes no content size; sizes of
  256 and above do. Asserted only from 256 up.
- The reference tool accepts some damaged frames klauspost rejects: reserved bits set in the
  sequences header (`corrupt block: reserved bits not zero`), non-zero padding bits (`N extra bits
  on block, should be 0`), a `Window_Descriptor` asking for gigabytes when the content is tiny
  (`window size exceeded`; klauspost applies its documented `WithDecoderMaxWindow` first), and a
  block whose regenerated size disagrees with the frame content size. The specification says
  those must be zero / may be rejected, so klauspost's strictness is not recorded; the corruption
  property only requires that klauspost never accepts what the tool rejects.
- Empty input: `DecodeAll(nil)` and the streaming `Decoder` return no data and no error (like the
  standard library's readers on an empty reader); the tool reports an unexpected end of file. Not
  compared.
- A raw-content dictionary must be registered with ID 0 to interoperate (the tool has no other ID
  for raw content); other IDs fail on both sides, as they should.
- S2's Snappy-compatible writer limits block sizes to 4 KiB–64 KiB (documented); the generator
  stays inside.
- Error messages and types differ; only the presence of an error is compared.
- Not covered: the `huff0`/`fse` primitives, `zip`, `zstd`'s skippable frames and `BuildDict`,
  S2's index and `--long`-style options, the `flate.NewReaderOpts` callbacks (`WithEobCallback`,
  `WithResumeFrom`, `WithPartialBlock`).
