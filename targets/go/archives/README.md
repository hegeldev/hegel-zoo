# go/archives

[mholt/archives](https://github.com/mholt/archives) (v0.1.5, 8 commits after): the archive and
compression library behind archiver, with tar and zip readers and writers, ten compression
formats, 7z and rar readers, format identification by name and content, and read-only file
systems over archives (`ArchiveFS`, `FileSystem`, `DeepFS`). Tested here: `FilesFromFS` and
`FilesFromDisk`, `Archive`/`Extract`/`Insert` of `Tar` and `Zip` with their options (alone and
under every compression format), the compression formats' writers and readers, `Identify`,
`ArchiveFS` and `DeepFS`, and the lexical path functions.

## Build

The patch adds `hegel.dev/go/hegel` to `go.mod` and a `hegel/` package of five
`hegel_zoo_*_test.go` files that drive the public API: `go test -count=1 -run TestHegel -v ./hegel`.
Two properties compare with tools when they are installed (`python3` for tarfile/zipfile;
`gzip`, `bzip2`, `xz`, `zstd`, `lz4`, `brotli`, `lzip` to decode streams) and skip the
comparison otherwise.

## Oracles

The generated tree itself: what goes into an archive must come out of Extract, entry for
entry (name, kind, content, link target, permissions, times, and the header fields the
options set), and the same archive read by Python's tarfile/zipfile must show the same
entries. The io/fs contract: `testing/fstest.TestFS` over `ArchiveFS`, and a model of the
archive's paths as a file system (WalkDir, Stat, Open, ReadDir, Sub, before and after the
index ArchiveFS builds on its first ReadDir). The package's own documentation of the
filenames map of `FilesFromDisk`/`FilesFromFS` (trailing separators, empty, "." and
slash-ended values, FollowSymlinks, ClearAttributes), of `DeepFS.SplitPath`, and of
`Identify` (a format from the name, the stream, or both; the stream returned unread; the
same answer for the same input). The compression formats' own readers and the reference
command-line decoders. The pin for the hang (archives/27) runs the call in a child process
of the test binary with a timeout.

## Generator

A tree of up to ten entries (files of 0 to 4096 bytes with block-aligned sizes frequent,
directories, symbolic links to siblings, tree paths, parents, their own directory or nowhere) with permissions and
times, written to a `fstest.MapFS` or to a directory on disk; names with spaces, dots,
upper case, non-ASCII, and archive-like extensions. Formats: `Tar` (USTAR/PAX/GNU, numeric
ids, owner overrides) and `Zip` (store, deflate, bzip2, zstd, xz; selective compression),
`Tar` under `Gz`, `Bz2`, `Xz`, `Zstd`, `Lz4`, `Brotli`, `Sz`, `Lzip`, `Zlib` and `MinLZ`
with their levels. Archives written by hand with archive/tar and archive/zip for the shapes
FilesFromFS never produces: implicit directories, entries out of order, `./` prefixes, a
`.` entry, directories with and without a trailing slash. For DeepFS, a disk tree holding
archives of every extension DeepFS recognises. For Identify, archives, compressed streams
(also truncated), random bytes and empty streams under right, wrong, neutral and missing
names.

## Properties

- `TestHegelArchiveRoundTrip`: FilesFromFS → Archive → Extract gives the tree back; Identify
  names the format from the bytes (named or not, seekable or not) and returns them unread;
  `fstest.TestFS` accepts the archive as an ArchiveFS; Python reads the same entries.
- `TestHegelArchiveFS`: a hand-written archive read through ArchiveFS is the file system of
  its paths (walk, stat, open, read, readdir, sub, missing names), before and after indexing.
- `TestHegelInsert`: files inserted into a Tar or Zip archive come out after its entries.
- `TestHegelFilesFrom`: FilesFromFS and FilesFromDisk on the same tree gather what the
  filenames map documents, with FollowSymlinks and ClearAttributes.
- `TestHegelIdentify`: Identify by name (the extension rules), by stream, both, repeatedly;
  no panic on arbitrary or truncated bytes.
- `TestHegelDeepFS`: a disk tree with archives walks through DeepFS as the tree with each
  archive replaced by its entries; SplitPath, PathIsArchive and PathContainsArchive agree.
- `TestHegelCompression`: every compression writer's stream is matched, identified, decoded
  by its reader and by the reference tool; gzip members with and without DisableMultistream.
- `TestHegelPin…`: one pin per recorded bug (expected failures).

## Bugs

Twenty-seven, recorded in `bugs.toml`. Unreadable output: zip archives written with
`ZipMethodXz` (archives/1, the xz header precedes each local header), `Tar.Insert` after a
block-aligned last entry (2), `Zip.Insert` dropping every file after a directory (3). ArchiveFS
before its index: Open of an implicit or late directory returns a descendant file (4), wrong
children (5), Stat of missing prefixes (6), wrong Name() of implicit directories (7),
ReadDir(-1) after ReadDir(n) (8). Identify: an empty zip unmatched (9), a different answer per
call when name and stream disagree (19), a panic on a truncated lzip stream (20), .tgz unknown
by name (26). Options: Lz4 levels 1-9 rejected (10); Zip.Insert storing (11), failing on the
custom methods (12), and copying a link's target content as the link (13). The filenames map:
"." gives leading slashes (14), trailing-slash keys fail on fs.FS (15) and misplace the value's
directory on disk (16); FollowSymlinks on fs.FS resolves from the root (17) and fails on
directory links (18), and on both sides recurses without end on a link to an ancestor directory
(27). DeepFS and paths: case in PathContainsArchive (21), SplitPath's first
character (22), directories named like archives (23). Streams: Lzip's empty output (24),
Brotli streams over 1 KiB unmatched (25).

## Modelled as recorded

Every bug has an `HZKnown` switch. While a switch is on the generator keeps away from the
shape or the checks skip it: no xz method in zips, lz4 level 0 only, empty zips not identified
by stream, the ReadDir-at-EOF lines of TestFS dropped, fresh Open/Stat checks skipped for
implicit or out-of-order directories and prefix names, Tar.Insert only after a non-aligned
regular file, Zip.Insert without directories, links or custom methods and its stored method
accepted, the "." value, trailing-slash keys and directory or relative links under
FollowSymlinks skipped on the affected side, followed links that lead back to an ancestor
skipped on both, Identify's determinism not required when the
name contradicts the stream, truncated lzip streams cut before the panic, mixed-case paths
for PathContainsArchive, extension-only first segments, archive-named directories renamed,
Lzip given a byte, brotli streams over 1 KiB not matched. The collector counts the
avoidances; `ZOO_KNOWN_OFF=name,name` turns switches off and the properties then fail.

## Not judged

An empty tar (1024 zero bytes) is not identified by stream, and under a compression format
Identify returns the compression only; Sz and MinLZ write no stream header for an empty
input, so their Match sees nothing; USTAR cannot encode non-ASCII names (archive/tar's
error); a PAX header without records reads back as USTAR; the order Open's directory file
lists entries in; files named like archives but holding other content, which DeepFS treats
as archives by its documentation.

## Not tested

The 7z and rar readers (no pure-Go writers; testdata only), `FileFS` and `DirFS` on their
own, `ArchiveAsync`, context cancellation, `TextEncoding` of zip names, hard links from disk
(`FilesFromDisk` hardlink detection), the `TopDir*` helpers, `Zip.TextEncoding`, Windows
paths.

## History

- 2026-09-22: new target, seven properties, 27 bugs.
