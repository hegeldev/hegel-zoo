# pako

[nodeca/pako](https://github.com/nodeca/pako) (npm `pako`, ~40M weekly downloads): a port of
zlib to JavaScript — `deflate`/`deflateRaw`/`gzip`, `inflate`/`inflateRaw`/`ungzip`, the
streaming `Deflate`/`Inflate` classes and the low-level `zlib*` calls. Pinned at 3.0.2
(32be8f8e, 2026-09-12). The tests are `test/hegel.test.mjs` with the zoo's small harness
`test/hegel-zoo.mjs`; they import `../src/index.ts` directly, as pako's own tests do (Node 22
strips the types), so there is no build step.

## What is tested

- **TestHegelDeflateMatchesZlibByteForByte** — data of four textures (random bytes, text from
  a small vocabulary, long runs, mixtures; up to 20 KB, sometimes 300 KB) with random options
  (level, strategy, windowBits, memLevel, chunkSize, a dictionary; zlib, raw or gzip wrapper).
  pako's output must equal Node's `zlib.deflateSync`/`deflateRawSync`/`gzipSync` byte for byte
  (pako's documented claim for its default hash), pushing the data in random pieces must give
  the same bytes, and both pako and Node must inflate it back to the data.
- **TestHegelInflateAgreesWithZlib** — Node's compressed output, whole or damaged (truncated,
  one bit flipped, trailing bytes or zero padding, a second gzip member), inflated one-shot and
  pushed in random pieces with a random output `chunkSize`: pako must succeed exactly when
  zlib does and produce the same bytes; `toText` must give the UTF-8 decoding.
- **TestHegelFlushPointsAreDecodable** — the data pushed in pieces with random flush modes
  (`Z_NO_FLUSH`, `Z_PARTIAL_FLUSH`, `Z_SYNC_FLUSH`, `Z_FULL_FLUSH`, `Z_BLOCK`): after every sync
  or full flush the bytes so far must decode (Node, `finishFlush: Z_SYNC_FLUSH`) to exactly the
  input so far; after the last full flush the remainder must decode on its own as a raw stream;
  the whole must decode on both sides.
- **TestHegelGzipHeadersRoundTrip** — random gzip header fields (name, comment, time incl.
  values past 2^31, os, extra bytes, hcrc, text) set with `zlibDeflateSetHeader` in `onStart`:
  Node must gunzip the stream to the data and pako's `zlibInflateGetHeader` must give the
  fields back.

Each pinned bug has a pin (`TestHegelPin…`, listed in `target.toml`) that fails while the bug
is present; the two hangs are pinned through a child process with a time and heap limit.

## Oracles

Node 22's bundled zlib (Chromium's fork; pako's default ANZAC++ hash is documented to match its
output, its `legacyHash` option matches canonical zlib instead). The zoo's own probe found the
byte-equality claim to hold on 13 200 option combinations before the properties were written.

## Not tested

- `legacyHash: true` (canonical zlib output) — no canonical zlib on hand as an oracle.
- Byte equality of stored blocks (level 0) across buffers: zlib's `deflate_stored` cuts
  blocks to the output buffer and the input pieces at hand, so Node is given pako's
  `chunkSize` (both default to 16 KiB; Node's minimum is 64, below which the comparison is
  skipped as `limit/stored-blocks-follow-the-buffer`) and the pushed-in-pieces comparison is
  skipped at level 0; the round trips are still checked.
- windowBits 8 with raw or gzip: zlib rejects it and so does pako; Node's own layer maps raw
  windowBits 8 to 9 instead, so the generators use 9–15 there.
- The browser bundles, the benchmark, `Z_TREES` (rejected with `Z_STREAM_ERROR` by design).

Documented behaviour that is not counted: trailing bytes after a zlib or raw stream are
ignored (as zlib does); bytes after a gzip member that are not a further member or zero
padding are an error (Node's gunzip agrees); a truncated stream pushed with `Z_FINISH` is
`Z_BUF_ERROR`; `inflate` of empty input is an error on both sides.

## Bugs

Five, pako/1–5 in `bugs.toml`: `chunkSize: 0` (or a fraction) makes `inflate` loop forever and
`deflate` exhaust the heap (/1); an empty gzip `extra` field sets FEXTRA without its length and
nothing can read the stream (/2); a header name or comment character outside Latin-1 is
truncated or mangled (/3); a sync or full flush with `chunkSize` below 7 loops forever (/4); the
streaming `Inflate` ignores every push after a gzip member that ended exactly at a chunk
boundary, so a second member is dropped and trailing garbage goes unreported (/5). Two came from
the probe file (/2, /3), three from the properties — /1 from a probe of the option edges, /4 by
killing the test process the first time the flush property ran, /5 from the inflate property
once its damage and cut points were one generator.

## History

- 2026-09-15: created at 32be8f8e (3.0.2); 4 bugs.
- 2026-09-23: generators rewritten in combinator style (STYLE.md): the data textures, options, damage, flush plan and gzip header are generator values (`weighted`, `record`, `arrays`, `binary`, `text`), the harness lost `n`/`pick`/`chance`/`word` and collect mode; same properties and pins. The rewrite surfaced pako/5 (`Inflate` ignores every push after a gzip member that ended exactly at a chunk boundary: trailing garbage accepted, a second member dropped), pinned and gated by `Known.inputAfterStreamEndIgnored` in the property.
