# xz

[ulikunitz/xz](https://github.com/ulikunitz/xz) is the pure-Go implementation of the .xz
container, LZMA2 and the classic .lzma format (560 stars, about 1 000 importers: archivers,
package managers, backup tools). It has no C dependency and its README says it "cannot compete
with the xz tool regarding compression speed and size" and that "there might be bugs". The pin
is v0.5.16 (`024f909`, 2026-07-20, the latest stable tag; a v2 is in development on another
branch). BSD-3-Clause; README.md, SECURITY.md, TODO.md and LICENSE say nothing about AI-written
code; the zoo keeps its tests in its own patch and files nothing upstream.

## Build

`go test -count=1 -run TestHegel -v .` in the module root (upstream's own tests are not the
zoo's business). The patch adds `hegel_test.go` (properties) and `hegel_pins_test.go` (one plain
test per bug) and requires `hegel.dev/go/hegel v0.6.33` in go.mod. The `xz` command-line tool
(XZ Utils 5.4 here; GitHub's ubuntu runners ship it) is the external oracle, found on PATH or
through `HEGEL_XZ`.

## Oracles

- **`xz`** — a stream written by the Go Writer must decode with `xz -dc`, and `xz --robot -l
  -v -v` must list one stream, no padding, the configured check (None/CRC32/CRC64/SHA-256), the
  block count ⌈len/BlockSize⌉ and every block's uncompressed size; a stream written by
  `xz -c` with random options (presets 0–6 with `-e`, or `--lzma2=dict=…,lc=,lp=,pb=,mode=,mf=,
  nice=`, any `--check=`, `--block-size=`) must decode with the Go Reader; the same for the
  classic format (`--format=lzma --lzma1=…`) with lzma.Writer/lzma.Reader and for raw LZMA2 chunk
  sequences (`--format=raw --lzma2=dict=…`) with lzma.Writer2/lzma.Reader2. For a mutated
  stream, `xz -dc`'s verdict is the reference: what xz decodes the Reader must decode, and what
  xz refuses the Reader may accept only if the data comes out intact.
- **Round trips** — Writer→Reader under random configurations (Properties with lc+lp ≤ 4 for
  LZMA2 and up to lc 8 for the classic format, DictCap from 4 KiB to 8 MiB, BufSize, BlockSize,
  every check, both matchers), random write chunking (including empty writes) and random read
  chunking behind `iotest.OneByteReader`/`HalfReader`/`DataErrReader`; concatenated streams with
  4-byte padding between and after them; `SingleStream`; lzma.Reader's `Header()`/`EOSMarker()`
  against what was written; `ReaderConfig.DictCap` as a limit (`*ErrDictSize`).
- **Documented rules** — `Verify` on every config struct against the documented ranges (zero
  values default; `NoCheckSum` overrides `CheckSum`; lc+lp ≤ 4 for LZMA2), io.Reader/io.Writer
  contracts (empty reads, `io.Copy`, `io.ReadAll`, write after close, error from the sink).

## Properties

| Property | Checks |
|---|---|
| WriterOutputRoundTripsThroughTheReader | any config, any chunking, 1–3 concatenated streams with padding; `ValidHeader`; EOF stays EOF; SingleStream stops after the first stream |
| XzToolDecodesTheWriterOutput | `xz -dc` equality; `xz --robot -l` streams, padding, check name, block count and block sizes |
| ReaderDecodesTheXzToolOutput | xz-written streams with random options, concatenated with padding, through random reader wrappers |
| ClassicLzmaRoundTrips | lzma.Writer in the four size modes → lzma.Reader (Header, EOSMarker, ErrDictSize) and `xz --format=lzma -dc`; `xz --format=lzma -c` → lzma.Reader, `lzma.ValidHeader` |
| Lzma2ChunkSequencesRoundTrip | Writer2 with Flush calls → Reader2 (`EOS()`) and `xz --format=raw -dc`; xz's raw LZMA2 → Reader2 |
| CorruptStreamsAreRejected | one flip/zero/truncate/delete/insert/append/short-padding/padding mutation of a Go- or xz-written stream: no panic, no wrong data with a clean EOF, verdict agrees with `xz -dc` (unchecked streams: both decoders must agree) |
| ConfigsAreVerified | Verify/NewWriter/NewReader accept exactly the documented ranges; accepted configs round-trip |
| WritersReportTheirSinksErrors | a failing underlying writer surfaces from Write or Close; Write/Close after Close fail |
| ReadersAreIOReaders | empty reads, `io.ReadAll`, `io.Copy` through a one-byte reader |

A `Known` switch per recorded bug gates the input shape while the bug is open (truncations
that decode cleanly are not counted; DictCap under 64 KiB is raised for data longer than the
dictionary; every Writer uses HashTable4 only; an explicit size of 0 is not written; the
Writer2 sink checks and the lzma.Writer after-Close checks are skipped; the classic Reader is not
given empty buffers). With everything gated the nine properties run clean at 300 cases (about
2 minutes, most of it xz processes); `XZ_COLLECT=1` records mismatches instead of failing and
prints them shortest-first, `HEGEL_VERBOSE=1` turns on the engine's log. Hegel's too-slow health
check is suppressed: the xz-forking properties take over a second per case on a loaded machine,
and the check then fails the run (hegel-go reports a run-level error with no message — the first
clean `zoo test` failed that way while five bumps were building in parallel).

## Bugs (8; details in bugs.toml)

| id | summary | severity |
|----|---------|----------|
| xz/1 | a truncated stream decodes with a clean `io.EOF` when the cut falls in a block header, between blocks, or (no check) inside block data — 66 of 299 prefixes of a 3-block stream; also reached by a flip that turns the index indicator into a block-header size byte | high |
| xz/2 | Writer/Writer2 fail with "insufficient space" on incompressible data when DictCap < 64 KiB (uncompressed chunk copied from a dictionary that no longer holds it) | medium |
| xz/3 | `Matcher: BinaryTree` writes undecodable streams, classic and LZMA2 ("distance out of range" in lzma.Reader, "corrupt" for xz); known in upstream's TODO | medium |
| xz/4 | `SizeInHeader` with `Size: 0` writes an unknown-size header without an EOS marker: the empty stream is unreadable | medium |
| xz/5 | `Writer2.Close` returns nil when the flush fails | medium |
| xz/6 | lzma.Writer accepts Write and Close after Close, appending to the finished stream | low |
| xz/7 | `lzma.Reader.Read` with an empty buffer returns `io.EOF` while output is still buffered | low |
| xz/8 | an LZMA2 chunk's compressed-size field is never verified: overstated, the stream decodes as if correct (xz: "Compressed data is corrupt"); understated on an unchecked stream, a clean EOF with the data missing | medium |

How they were found: the first round (150 cases) showed "insufficient space" in the xz-tool and
LZMA2 properties (xz/2, isolated by a probe over write sizes: 65552 bytes pass, 65553 fail with
DictCap 4096), the corruption property's clean EOFs on truncated streams (xz/1; the pin then
showed the boundary and unchecked-data cases too), the config property's `NoCheckSum` overriding
an invalid `CheckSum` (documented, not a bug) and the sink property's Writer2 and lzma.Writer
contracts (xz/5, xz/6; the lzma.Writer "sink" cases were the harness — the output was smaller
than the failure limit). The classic property's early clean EOFs (11 of 512 bytes, 77 299 of
97 081) resisted hand probes until Hegel shrank one to a 40-byte stream read through
`HalfReader` with buffer sizes 7, 32, 0 — the empty read (xz/7); the probes meanwhile found the
BinaryTree matcher (xz/3; a 300-case round then showed it in the .xz path too) and the empty
explicit size (xz/4). The round-trip property first hung
for minutes: `BlockSize: 1` with the default 8 MiB dictionary builds a fresh dictionary and
BinaryTree per one-byte block (the generator now keeps blocks ≤ 64; see below). xz/8 came from CI (2026-09-17): the corruption
property failed on the runner on a flip the local runs had not drawn; a local hunt of the
property alone (≈10 s a run) reproduced it in the second run, and a probe over the
compressed-size bytes of a single-block stream showed both directions.

## Accepted differences (not bugs)

- liblzma refuses lc+lp > 4 in every format, so `xz` cannot decode a classic stream the Go
  Writer produces with, say, lc 7 (`File format not recognized`); the property expects that
  failure and checks such streams with lzma.Reader only. The `--lzma1` oracle options keep
  lc+lp ≤ 4.
- `SingleStream` reports an error for anything after the first stream, including padding;
  `xz --single-stream` silently ignores trailing data. Documented as "assume that the underlying
  stream contains only a single stream"; only the decoded data is compared.
- `WriterConfig{NoCheckSum: true}` ignores an invalid `CheckSum` (fill sets CheckSum to None
  first) — documented as "Forces NoChecksum".
- `Size` alone cannot express an explicit size of 0 (`Size: 0` is the zero value): the Writer
  falls back to an EOS marker, and `Header()` reports -1; only `SizeInHeader: true` claims 0
  (xz/4).
- Every block allocates a new dictionary and matcher of `DictCap` bytes, so many small blocks
  with a large dictionary are slow (64 KiB in one-byte blocks with the default 8 MiB
  dictionary and BinaryTree: minutes). A performance shape, not recorded; the generator keeps
  the block count within 64.
- `DictCap` up to `MaxDictCap` (4 GiB − 1) is valid and allocates a dictionary and hash table
  of that size at once (a 2 GiB value ran the test process out of memory); the config property
  draws dictionaries up to 8 MiB.
- Block header padding of more than 3 bytes is accepted on purpose (comment in
  `blockHeader.UnmarshalBinary`, upstream #11/#15); the mutations never produce it.

## Not tested

Filters other than LZMA2 (the package supports none), multi-threading (none), the `gxz` and
`xb` commands, `internal/*`, Writer2 output concatenated after a Flush without Close, dictionary
sizes above 8 MiB, streams above 256 KiB.
