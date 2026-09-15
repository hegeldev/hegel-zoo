# fflate

[101arrowz/fflate](https://github.com/101arrowz/fflate) (npm `fflate`, ~60M weekly downloads;
the DEFLATE/gzip/zlib/ZIP library most bundlers and browser tools ship): `deflateSync`/
`zlibSync`/`gzipSync` and their inflating counterparts, `decompressSync` (format detection), the
streaming `Deflate`/`Zlib`/`Gzip`/`Inflate`/`Unzlib`/`Gunzip`/`Decompress` classes with `flush`,
the UTF-8 helpers `strToU8`/`strFromU8`/`EncodeUTF8`/`DecodeUTF8`, and the ZIP writer and
reader (`zipSync`/`unzipSync`, the streaming `Zip`/`ZipDeflate`/`ZipPassThrough` and
`Unzip`/`UnzipInflate`). Pinned at 0.8.3 (dcb3714a, 2026-05-15). The tests are
`test/hegel.test.mjs` with the zoo's harness `test/hegel-zoo.mjs`, the zipfile bridge
`test/hegel-zip.mjs` and the oracle `test/hegel-zip-oracle.py`.

fflate ships tsc's ES5 output, and its streaming classes rely on it: the `Gzip`, `Zlib`,
`Gunzip`, `Unzlib`, `ZipDeflate` constructors do `Deflate.call(this, …)` and the like, which
throws on a native class. Running the sources through Node's type stripping would therefore
test something upstream never ships, so the setup builds `lib/` with the pinned TypeScript
(fetched by `npx`, without installing the dev tree; `test/tsconfig.hegel.json` drops the
`@types/node` reference) and the tests import `../lib/index.js`.

## What is tested

Data of four textures (random bytes, text from a small vocabulary, long runs, mixtures; up to
20 KB, sometimes 300 KB) and streams cut at random points.

- **TestHegelZlibReadsWhatFflateWrites** — `deflateSync`/`zlibSync`/`gzipSync` with random
  `level`, `mem`, dictionary (raw and zlib), gzip `filename` and `mtime` (number, Date, ISO
  string, 0): Node's zlib must read the output back to the data (with the dictionary), the gzip
  header must carry the fields as given, fflate must read its own output, the streaming class
  pushed in pieces must produce a stream Node reads (whether it equals the one-shot output is
  only counted: it does about 60 % of the time), and after `flush(true)` the bytes so far must
  decode (`finishFlush: Z_SYNC_FLUSH`) to the input so far and the whole stream still decode.
- **TestHegelFflateReadsWhatZlibWrites** — Node's output with random `level`, `strategy`,
  `windowBits`, `memLevel`, dictionary, whole or damaged (truncated, one bit flipped, zero
  padding, trailing garbage, a second gzip member): the one-shot function for the format must
  succeed exactly when Node does and give the same bytes; the streaming class pushed in pieces
  must agree with it; `decompressSync` and the `Decompress` stream must detect the format; a
  preallocated `out` of the right size must work; `strFromU8` must give the UTF-8 text.
- **TestHegelUtf8HelpersAgreeWithTheEncodingApi** — strings of ASCII, Latin-1, BMP, astral
  characters, BOM and lone surrogates: `strToU8`/`strFromU8` must equal
  TextEncoder/TextDecoder (and the Latin-1 mode `Buffer`'s), `DecodeUTF8` pushed in pieces cut
  anywhere in the bytes must give the whole decoding, `EncodeUTF8` pushed in pieces cut between
  code units the whole encoding.
- **TestHegelZipfileReadsWhatFflateZips** — a random `Zippable` tree (nested directories, per-file
  and per-directory options, `level`, `mtime` in each form, `os`, `attrs`, `extra` fields,
  comments, non-ASCII names, empty files) written by `zipSync` and by the streaming `Zip` with
  `ZipDeflate`/`ZipPassThrough` (data descriptors): Python's zipfile must read every entry with
  the same data, method, DOS time, comment, external attributes, creating system, extra bytes
  and UTF-8 flag, `testzip()` must find every CRC right, and `unzipSync` must read it too.
- **TestHegelFflateReadsWhatZipfileWrites** — zipfile's archives (stored, deflated at every
  level, bzip2 and LZMA entries, seekable or streamed with data descriptors, forced zip64
  records, entry and archive comments, non-ASCII names, directories): `unzipSync` and the
  streaming `Unzip` pushed in pieces must return the same entries and bytes; unknown methods
  must be refused with error 14 (and `unzipSync` with a `filter` must still return the rest).

Each bug has a pin (`TestHegelPin…`, listed in `target.toml`) that fails while the bug is
present; the pins for fflate/5 and fflate/7 need the zipfile oracle, the rest only Node.

## Oracles

Node 22's bundled zlib for DEFLATE, zlib and gzip; Python 3's `zipfile` (stdlib, with its
zlib/bz2/lzma) for ZIP, held open as a child process over two FIFOs with one JSON line per
request (`test/hegel-zip-oracle.py`), so an archive is written or read by an independent
implementation in well under a millisecond.

## Not tested

- The asynchronous, worker-backed API (`AsyncDeflate`, `gzip(data, cb)`, `unzip(data, cb)`,
  …): the same code in a worker; the harness runs synchronous bodies.
- `AsyncZipDeflate`/`AsyncUnzipInflate`, `terminate()`, `ondrain`/`queuedSize`
  (backpressure), the `consume` option, `Zip` with files added while earlier ones are still
  being pushed, entries over 4 GiB, archives with more than 65535 entries, encryption (not
  supported by fflate), the browser and UMD bundles.
- Directory options are not inherited by the directory's contents (`fltn` hands the global
  options down, not the merged ones); the tests model that as it is, not as a bug.

Differences from the oracles that are not counted (each skipped with a `limit/…`): bytes after
a gzip member that are neither a member nor zero padding are ignored by fflate, an error for
zlib and Node (gzip(1) warns and goes on); `strFromU8` is `TextDecoder`, which strips a leading
U+FEFF by default; a gzip `mtime` outside the 32-bit range is written modulo 2^32 (the ZIP
writer rejects an out-of-range date, error 10).

## Bugs

Thirteen, fflate/1–13 in `bugs.toml`. The one-shot `gunzipSync` reads one member and sizes its
output from the last four bytes of the input, so zero padding gives empty output and a second
member truncates or throws (/1); no checksum or length trailer is ever verified, so corrupted
input decodes to silent garbage (/2); a gzip `filename` with a character outside Latin-1 or a
NUL yields a stream nobody can read (/3); `EncodeUTF8` encodes each push on its own, so a
surrogate pair split across pushes becomes two U+FFFD (/4); a ZIP entry comment over 65535
bytes is written without an error and corrupts the central directory (/5); the `Decompress`
stream builds the buffer joining a short first push with the next and never keeps it, so the
stream yields nothing, silently (/6); `Unzip`'s `start()` on an entry with an unregistered
method reports error 14 and then throws "ctr is not a constructor" (/7); a zlib stream cut to
under seven bytes, or an empty raw stream, decodes to empty output instead of an error (/8);
`flush(true)`, the sync flush added in 0.8.3, writes a malformed block and the stream is
undecodable from there, always at level 0 and in several other shapes (/9); a dictionary of up
to 32 bytes with incompressible input gives a stream zlib rejects and fflate misreads (/10); the
streaming `Gunzip` ends a truncated stream with partial output and no error where the one-shot
raises "unexpected EOF" (/11); the raw `Inflate` stream with a dictionary loses the dictionary
on an empty first push and decodes the rest to wrong bytes (/12); at level 0 an input of
exactly k × 65535 bytes gets a second final block and the zlib/gzip output is unreadable (/13).
/1, /2, /6, /8, /11, /12 came out of reading Node's streams, /3, /9, /10, /13 out of Node
reading fflate's, /4 out of the UTF-8 property, /5 and /7 out of the ZIP differential; /12 and
/13 were found by fresh-seed clean runs of the finished suite (shapes the collect runs had not
hit — the generator now lands on the 65535 boundary on purpose).

## History

- 2026-09-15: created at dcb3714a (0.8.3); 13 bugs.
