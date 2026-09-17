# lz4

[pierrec/lz4](https://github.com/pierrec/lz4) v4 is the pure-Go LZ4 implementation: the block
format (`CompressBlock`, `CompressBlockHC`, `UncompressBlock`, with an optional dictionary)
and the frame format (`Writer`, `Reader`, `CompressingReader`, legacy Linux-kernel frames,
skippable frames, block and content checksums, concurrency, options), about 7 000 lines,
BSD-3-Clause, pinned at `e692a9f` (2026-09-15, after v4.1.9). README and LICENSE are the
only project documents and say nothing about AI-written code.

## Build

`go test -count=1 -run TestHegel -v .` in the module root, with the `lz4` command-line tool
(1.9.4, the `lz4` package of Ubuntu) installed: it is the reference implementation and the
tests fail without it. The patch adds `hegel_test.go` (the format models and the properties)
and `hegel_pins_test.go` (one plain test per bug) and requires `hegel.dev/go/hegel v0.6.33`
in go.mod.

## Oracles

- **The LZ4 block format** (lz4_Block_format.md), written in the test as an independent
  decoder (tokens, length extensions, offsets into the output and the dictionary, the final
  literal sequence; it also reports whether a block follows the encoder restrictions: five
  trailing literals, last match twelve bytes before the end) and an independent sequence
  encoder that builds compliant blocks of any shape (long literal runs, overlapping matches,
  matches into a dictionary, length extensions of 15 + 255 k).
- **The LZ4 frame format** (lz4_Frame_format.md), written as an independent parser (magic
  numbers, descriptor flags and their reserved bits, block size index, content size, header
  checksum, block sizes and the raw-block flag, block checksums, the end mark, the content
  checksum, dependent blocks with the 64 KiB window, skippable frames, legacy frames) and an
  independent builder, with an xxHash32 of their own (checked against the specification's
  test vectors).
- **The reference implementation**: the `lz4` tool decodes every block and frame the library
  produces, and its frames (all levels, standard and custom block sizes, dependent blocks,
  block checksums, content size, no frame checksum, legacy) must be read by the library.
- **The documented contracts**: `CompressBlockBound`, the destination-size rules of the
  compressors, determinism, the options and their `String`s, the named errors, the state
  machine of Writer and Reader, `OnBlockDone`, `Size`, `ValidFrameHeader`, `Reset`.

## Properties

| Property | Checks |
|---|---|
| BlockCompressionRoundTrips | `CompressBlock`, `Compressor`, `CompressBlockHC` and `CompressorHC` at every level on compressible data (repeats at offsets up to and beyond 64 KiB, runs, small alphabets, random bytes, 0–70 000 bytes): a bound-sized destination always succeeds; the block decodes by the format and follows the encoder restrictions; `UncompressBlock` and the reference decode it; deterministic; a source-sized destination gives a valid block or 0; a destination one byte short gives 0 |
| SpecBlocksDecode | blocks built by the sequence encoder, with and without a dictionary: `UncompressBlock`/`UncompressBlockWithDict` into exact and larger buffers; a short buffer gives `ErrInvalidSourceShortBuffer`; the reference decodes them; damaged blocks never panic, are never accepted when the format rejects them, decode to the format's result when accepted, and compliant blocks are never rejected |
| WriterFramesFollowTheSpec | `Writer` with random options (block size, block and content checksums, content size, level, concurrency, legacy) and write patterns (one Write, chunks, chunks with Flush, ReadFrom): the frame parses by the specification with the configured flags, content and content size, blocks within the block size and never larger than their data, the expected block count, `OnBlockDone` once per block; the reference and the `Reader` (Read with random buffer sizes, WriteTo, ReadAll, concurrency) read it back; `ValidFrameHeader`; Close twice |
| ReaderAcceptsSpecAndReferenceFrames | concatenations of frames built by the specification builder (random flags, raw and compressed blocks, dependent blocks, legacy) and by the reference tool (random options), with skippable frames: the `Reader` returns the content in every mode and concurrency; `Size` after the first Read; `OnBlockDone` in WriteTo sums to the content; `ValidFrameHeader` |
| CorruptFramesAreRejected | frames with bytes flipped, inserted, deleted or truncated: the Reader never panics or hangs; bytes that are still a valid frame are read to the parser's content; bytes the specification rejects are rejected, with the named error for header, block and content checksums and the magic number; block damage the format rejects is never accepted |
| CompressingReaderMatchesTheWriter | `CompressingReader` with the same options as a `Writer` produces the same bytes, read with random buffer sizes (including one byte); `Source`, `Close` closes the source, `OnBlockDone` once per block |
| OptionsAndStatesFollowTheContract | `Option.String`; invalid block sizes and levels; inapplicable options on a Reader; Apply after the first Write or Read; Write and ReadFrom after Close; Close twice; Reset writes the same frame again with the same options; Reader Reset and Apply; empty, truncated and garbage inputs give `io.EOF`, `io.ErrUnexpectedEOF` and `ErrInvalidFrame` |

`Known` switches gate the fourteen recorded bugs (the generators avoid the shapes: options
applied in one call, ReadFrom only on a fresh Writer, frames ordered so that WriteTo keeps its
buffer, no legacy frame before another kind, handler checks on non-concurrent Writers). With
them on, the seven properties run clean at 1000 cases in about six seconds (`LZ4_COLLECT=1`
records mismatches instead of failing and prints them shortest-first with the case's
description; `HEGEL_VERBOSE=1` turns on the engine's log).

## Bugs (14; details in bugs.toml)

| id | summary | severity |
|----|---------|----------|
| lz4/1 | `Writer.Apply` and `Writer.Reset` zero the content size but keep the size flag: the header says 0 bytes | medium |
| lz4/2 | `Writer.ReadFrom` calls the `OnBlockDone` handler twice per block (compressed and uncompressed size) | low |
| lz4/3 | `Reader.Read` calls the `OnBlockDone` handler once per Read call with the bytes copied, not per block | low |
| lz4/4 | the `Reader` accepts frames with a version other than 1 and with reserved bits set (the reference rejects them) | low |
| lz4/5 | the `Reader` does not check the frame's content size against the content (the reference does) | low |
| lz4/6 | a stream cut off after a block (no end mark) or right after the magic number is accepted as complete | medium |
| lz4/7 | a legacy block whose compressed size equals the content read so far is taken for the kernel size trailer: the stream is cut short | medium |
| lz4/8 | `Writer.ReadFrom` fails with `ErrInternalUnhandledState` unless it is the first operation (so `io.Copy(w, r)` after a Write fails) and leaves the Writer unusable | high |
| lz4/9 | a legacy frame followed by a standard or skippable frame fails with `ErrOptionInvalidBlockSize` | medium |
| lz4/10 | with concurrency, the `OnBlockDone` handler is called from other goroutines, after Close has returned | low |
| lz4/11 | `Reader.WriteTo` silently drops every block of a following frame whose block size is larger than the first frame's, or whose blocks are dependent when the Reader started concurrently | high |
| lz4/12 | `Reader.WriteTo` returns `io.EOF` as an error on an empty or skippable-only stream (`io.Copy` fails) | medium |
| lz4/13 | a failed `Apply` (invalid option, or after the first Write/Read) leaves the Writer or Reader in its error state for good; the frame stays unfinished | medium |
| lz4/14 | `Reader.Size` is 0 once a Read has reached the end of the frame, so a frame read in one call never reports its size | low |

How they were found: lz4/1, 2, 3, 4, 5 and 14 by hand probes while writing the Writer and
Reader properties (the first Writer property applied its options in two calls and produced
size-0 headers; the reference tool showed the version, reserved-bit and content-size
stances); lz4/6 and 7 by reading the reader's end-of-stream handling and confirming with
constructed frames, lz4/6 also by the corrupt-frames property's truncations; lz4/8, 9, 10, 12
and 13 by the first collect rounds of the Writer, Reader and options properties (write then
ReadFrom, legacy then standard, handler counts under concurrency, skippable-only streams, Close
failing after a late Apply); lz4/11 by the Reader property losing a legacy frame after a
standard one and a frame with dependent blocks under concurrency, then reduced by probes to
the block-size rule. The block properties found nothing: the compressors and the decoder agree
with the format and the reference on every generated block.

## Accepted differences (not bugs)

- The block decoder rejects some non-compliant blocks the reference accepts (a final token
  with a non-zero match nibble) and accepts some the reference rejects (a long block ending
  right after a match); the format leaves malformed blocks to the decoder, and the properties
  only require agreement on compliant blocks.
- `UncompressBlock` of an empty input returns 0 bytes without error (the reference reports
  an error); the format has no empty block.
- The block compressors return `(0, nil)` for incompressible data when the destination is
  smaller than `CompressBlockBound`, as documented; the properties only check that a non-zero
  result is a valid block.
- The `Reader` ignores the dictionary-ID flag (frames with a dictionary ID fail the header
  checksum); the reference tool never writes one and the generators do not either.
- In legacy mode the reader also accepts the Linux-kernel variant with a trailing size, which
  the reference does not; only the coincidence of lz4/7 is a defect.
- `Reader.Size` is 0 before the first Read, as the size is read from the stream.

## Not tested

The `cmd/lz4c` command, `internal/` packages directly, the frozen `--favor-decSpeed` levels of
the reference beyond decoding its output, and performance.
