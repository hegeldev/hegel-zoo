# go/archives

[mholt/archives](https://github.com/mholt/archives) (v0.1.5, 8 commits after): the archive and
compression library behind archiver, with tar and zip readers and writers, ten compression
formats, 7z and rar readers, format identification by name and content, and read-only file
systems over archives (`ArchiveFS`, `FileSystem`, `DeepFS`). Tested here: `FilesFromFS` and
`FilesFromDisk`, `Archive`/`Extract`/`Insert` of `Tar` and `Zip` with their options (alone and
under every compression format), the compression formats' writers and readers, `Identify`,
`ArchiveFS` and `DeepFS`, and the lexical path functions.

## Build

The patch adds `hegel.dev/go/hegel` to `go.mod` and a `hegel/` package of `hegel_zoo_*_test.go`
files that drive the public API: `go test -count=1 -run TestHegel -v ./hegel`. `HEGEL_TEST_CASES`,
`HEGEL_SEED` and `HEGEL_VERBOSE` pass through to the engine; `HEGEL_COLLECT=1` records the
mismatches of the rewritten properties and prints their counts; `HEGEL_NO_KNOWN=1` switches
their known shapes off (below).
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

The two rewritten properties (part 1 of the rewrite to the standard, below) draw records from
package-level generators. `filesCase`: a tree of up to eight entries (a name from the pool of
twenty-six under the root or, at 60 %, under a directory already drawn; a directory at 25 %,
a file at 60 - a size from the block-aligned table at 60 % else 0..3000; compressible text,
one byte or random bytes at a third each -, else a link to a sibling name, an earlier entry's
path, `../name`, `.` in a subdirectory or `/nowhere/name`; a link to itself or to another
link is redirected to `/nowhere` by a pure settling pass), the mapping (the root `.` at 25 %
or when the tree has no file or directory, else a path of the tree; a trailing slash on a
directory key at 30 - `dieCoin(27)` realises 30 -; the value from `""` (twice), `.`, `x`,
`x/`, `x/y`, `x/y/`, a file key's `.` and a trailing key's slash-ended value replaced by the
builder: the two combinations the documentation leaves open), FollowSymlinks and
ClearAttributes at 30 % each. `deepCase`: a tree of up to six entries with the files and links
named like archives renamed on disk (DeepFS treats them as archives by its documentation),
zero to three archives of every extension DeepFS recognises in the root or a directory,
their names upper-cased at 20 %, each holding an inner tree of up to five entries that the
library's own Archive writes, and the lexical paths: every model path with its `/`-prefixed,
`/`-suffixed and upper-cased forms, and one of nine made-up paths. Every weight is drawn
through the fair-bit dice of the idioms and the realised rate over 3000 cases stands beside
it (the kinds 25/60/15 realise 24/60/14, the parent 60 realises 62, the size table 60
realises 60, follow and clear 30 realise 31 and 30, an archive in a directory 50 realises
48); a case costs about 270 draws (690 at most) for FilesFrom and 480 (1440) for DeepFS.

`identifyCase`: the content one of five kinds (random bytes of 0..64, an empty stream, an
archive of a tree of up to four entries written by Tar or Zip - the zip methods without xz,
part 3's bug - and a tar under a compression format at 50 %, a compressed stream of a
payload, a truncated compressed stream cut to 0..12 bytes; realising 18/15/32/17/18) and the
name one of six (none, the content's own extension, a neutral or misleading name, a
compression extension, an archive extension, an odd spelling; 15 to 18 each); the archive
and the stream are built in the property under the judge, the construction a check of its
own. `compressionCase`: a format from the ten at a tenth each (the levels 0..9, Lz4's too,
Brotli's quality 0..11, Gz multithreaded at 30 %), a payload of `hzData`'s population, and the
write cut into pieces by a drawn list of lengths. A case costs about a hundred draws for
either.

`roundTripCase`: a tree of up to ten entries as `filesCase`'s, gathered by FilesFromFS with
ClearAttributes at 30 %; the archival a Tar (the format none/USTAR/PAX/GNU at a quarter
each, numeric ids and owner overrides at 20 %) or a Zip (Store, Deflate twice, Bzip2, Zstd,
Xz at a sixth each; selective compression at 30 %) at 50/50, a tar under a compression
format of `compressionCase`'s population at 50 % (Lz4's levels included); the bytes written in
the property under the judge, the construction a check of its own. `archiveFSCase`: an
archive written by hand with archive/tar or archive/zip (zip at 40 %) for the shapes
FilesFromFS never produces: up to eight entries at depth one to three (directories,
files, links in tars at 30/60/10), directory names with a trailing slash at 60 % (always in
zips), a `./` prefix at 15 %, the parents explicit all, none or each at a coin (40/30/30),
the order as placed, parents first or shuffled by drawn keys (35/30/35), a `.` entry in
tars at 20 %, a directory for Sub, and whether the missing-name and ReadDir-rest checks run
(40 and 50 %). A case costs about 340 draws (850 at most) for the round trip and 310 (800)
for ArchiveFS.

`insertCase`: a base tree of up to six entries and an extra tree of up to four, both of
`filesCase`'s population, gathered by FilesFromFS; the archival a Tar with its options or a
Zip (Store, Deflate twice, Bzip2, Zstd at 4/8/4/4; no Xz, which is the round trip's shape;
selective compression at 30 %) at 50/50; the base archive built in the property under the
judge and the extras inserted into a copy of its bytes in memory. A case costs about 350
draws (890 at most).

## Properties

- `TestHegelArchiveRoundTrip`: FilesFromFS → Archive → Extract gives the tree back; Identify
  names the format from the bytes (named or not, seekable or not) and returns them unread;
  `fstest.TestFS` accepts the archive as an ArchiveFS; Python reads the same entries.
- `TestHegelArchiveFS`: a hand-written archive read through ArchiveFS is the file system of
  its paths (walk, stat, open, read, readdir, the rest after ReadDir(1), sub, missing names),
  before and after indexing, and `fstest.TestFS` accepts it.
- `TestHegelInsert`: files inserted into a Tar or Zip archive come out after its entries (a
  zip's same-named entries replaced), with their contents, link targets and methods.
- `TestHegelFilesFrom`: FilesFromFS and FilesFromDisk on the same tree gather what the
  filenames map documents, with FollowSymlinks and ClearAttributes; a call whose expansion
  the model never finishes still returns (judged in a child process).
- `TestHegelIdentify`: Identify by name (the extension rules), by stream, both, six times
  over seekable and buffered streams: the documented answer, the stream returned unread, the
  same answer every time, no panic on arbitrary or truncated bytes.
- `TestHegelDeepFS`: a disk tree with archives walks through DeepFS as the tree with each
  archive replaced by its entries; SplitPath, PathIsArchive and PathContainsArchive agree.
- `TestHegelCompression`: every compression writer opens, its stream is matched by content
  and by name and by no other format, identified, decoded by its reader and by the reference
  tool; gzip members with and without DisableMultistream.
- `TestHegelPin…`: one pin per recorded bug (expected failures).
- Twenty-eight narrow properties, one per recorded bug (below):
  `TestHegelDotValuesGiveRelativeNames` (14), `TestHegelTrailingSlashKeysEnumerateOnFS` (15),
  `TestHegelTrailingSlashKeysKeepTheValue` (16),
  `TestHegelRelativeLinksResolveFromTheirDirectory` (17),
  `TestHegelDirectoryLinksAreFollowedOnFS` (18), `TestHegelAncestorLinksReturn` (27),
  `TestHegelPathContainsArchiveIgnoresCase` (21), `TestHegelSplitPathSplitsTheFirstSegment`
  (22), `TestHegelDirectoriesNamedLikeArchivesAreWalked` (23),
  `TestHegelEmptyZipsAreMatchedByStream` (9), `TestHegelLz4LevelsOpenWriters` (10),
  `TestHegelMisnamedStreamsIdentifyAlike` (19), `TestHegelTruncatedLzipStreamsDoNotPanic`
  (20), `TestHegelEmptyLzipStreamsRead` (24), `TestHegelLongBrotliStreamsAreMatched` (25),
  `TestHegelTgzNamesIdentify` (26), `TestHegelTruncatedLzipHeadersErrAlike` (28),
  `TestHegelXzZipsExtract` (1), `TestHegelFreshOpenOfLateDirectoriesIsADirectory` (4),
  `TestHegelFreshOpenListsOnlyChildren` (5), `TestHegelFreshStatOfPrefixesIsNotExist` (6),
  `TestHegelImplicitDirectoriesHaveBaseNames` (7), `TestHegelDirectoryFilesReadTheRest` (8),
  `TestHegelTarInsertAfterAlignedEntries` (2), `TestHegelZipInsertContinuesAfterDirectories`
  (3), `TestHegelZipInsertCompresses` (11), `TestHegelZipInsertKnowsTheRegisteredMethods`
  (12), `TestHegelZipInsertStoresLinkTargets` (13).

## Bugs

Twenty-eight, recorded in `bugs.toml`. Unreadable output: zip archives written with
`ZipMethodXz` (archives/1, the xz header precedes each local header), `Tar.Insert` after a
block-aligned last entry (2), `Zip.Insert` dropping every file after a directory (3). ArchiveFS
before its index: Open of an implicit or late directory returns a descendant file (4), wrong
children (5), Stat of missing prefixes (6), wrong Name() of implicit directories (7),
ReadDir(-1) after ReadDir(n) (8). Identify: an empty zip unmatched (9), a different answer per
call when name and stream disagree (19), a panic on a truncated lzip stream (20), .tgz unknown
by name (26), a cut inside the lzip header erring differently by seekability (28).
Options: Lz4 levels 1-9 rejected (10); Zip.Insert storing (11), failing on the
custom methods (12), and copying a link's target content as the link (13). The filenames map:
"." gives leading slashes (14), trailing-slash keys fail on fs.FS (15) and misplace the value's
directory on disk (16); FollowSymlinks on fs.FS resolves from the root (17) and fails on
directory links (18), and on both sides recurses without end on a link to an ancestor directory
(27). DeepFS and paths: case in PathContainsArchive (21), SplitPath's first
character (22), directories named like archives (23). Streams: Lzip's empty output (24),
Brotli streams over 1 KiB unmatched (25).

## Properties and the recorded bugs

The model states the documented behaviour; the `known` switch
set (`type known [27]bool`, one index per bug id, all off by default) turns a replica of the
library's rule on in its place, each transcribed from the lines of `archives.go` and `fs.go`
it follows: `nameOnDiskToNameInArchive` keeping the separator after the root for the value
`.` (14) and trimming the value's first element for a trailing key, the directory itself
added (16); `fs.WalkDir` of a slash-ended name (15); `followSymlinkFS` looking a relative
target up from the walked root (17) and a directory target up inside `fs.Sub` of itself (18);
an expansion deeper than the tree never returning (27); `PathContainsArchive` on the path as
written (21); `SplitPath`'s scan from the second character (22); `DirFS.ReadDir` listing the
archives under an archive-named directory as files (23). The classifier runs the model per
switch on the case before the library is called and names the first bug in id order whose
switch alone changes the expected checks (sufficiency), else the first whose switch is needed
(necessity), else a hole; every mismatch by default is a named shape and no named shape
passes. The checks: per side (fs, then disk) whether the call returns, the error's kind, the
sorted names, and per entry the kind, link target, content, permissions and times; the names
of a call whose documented expansion never finishes are left open (`unspecified`, not
compared), only its returning is checked.

Over 3000 default cases the FilesFrom property names 259 to 284 shapes (9 %), every one by
sufficiency with the library agreeing with the replica in all of them: archives/14 in 113 to
140, 15 in about 135, 17 in 7, 18 in 4; 16 lies behind 15 (every trailing key fails on the fs
side first; 50 to 72 cases) and 27 behind 17 or 18 (a link that leads back is a link to a
directory; 4 to 5 cases), so the wide property names neither. The DeepFS property names
about 2560 (85 %): 21 in 2500 (the upper-cased form of every path is drawn, and an archive's
name is among the paths), 22 in about 50 (sufficient in 300, behind 21), 23 sufficient in
about 160, never named. Over nine rounds at the default count the FilesFrom property shrank
to 15 six times (`{"a/": ""}` on a directory `a`) and to 14 three times (`{".": "."}`); the
DeepFS property to 21 seven times (`a.ZIP/x`) and to 22 twice (`.zip`); over forty rounds at a
hundred cases both fail every round, the FilesFrom property to 15 in 22 (14 in 17, 17 once), the
DeepFS property to 21 in 25 (22 in 15): both are mapped plain to those. A default run takes
about a minute and a half on this machine (the FilesFrom shrink and the child processes), a
thousand cases under `HEGEL_NO_KNOWN=1` under three minutes.
The hang (27): a case whose expansion the model marks as endless - 4 to 5 per 3000 per side -
runs both library calls in a child process (the test binary re-executed with
`HZ_ARCHIVES_CHILD=files`, the case as JSON on its stdin, the child's stack capped at a
mebibyte so that the recursion dies within milliseconds; the parent waits up to four seconds)
and the other cases call the library in process under a one-second context, which the
library's walk checks. The narrow properties force the shape with the rest of the case drawn
as in the wide property: 14 (a key without a trailing slash and the value `.`; 18 % rejected
for follow errors), 15 (a trailing key, the fs side), 16 (a trailing key with a value, judged
past 15 on the disk side), 17 (a relative link in a subdirectory, no other link), 18 (a link
to a directory, no other link), 27 (a link to `.`, judged past 17 and 18 - the fs side's
resolution is their shape -, every case in two child processes, so twenty cases by default
and a shrink budget of forty), 21 (an upper-cased extension), 22 (an extension-only first
segment, no upper case, no trailing slash: `.zip/` splits alike either way), 23 (an
archive-named directory holding an archive).

The Identify and Compression properties thread the same switch set: `Zip.Match` reading four
new bytes per candidate header, so that an empty zip's end record is never compared (9);
`Lz4.OpenWriter` handing the level to pierrec/lz4 as a bit flag (10); `Identify` ranging over
the formats map, so that the archival name in an error, or the answer when name and stream
disagree, varies by map order (19); lzip-go's header read panicking on a cut of six to
twenty-one bytes (20); Lzip's writer leaving an empty input headerless (24);
`isValidBrotliStream` decoding the first kibibyte with the decoder the library uses (25, the
replica runs that decoder on the bytes); the name rules of `Tar.Match` and `Gz.Match`, which
know no `.tgz` (26); the rewindReader returning the replayed bytes of a buffered stream with
io.EOF, so that a cut inside the lzip header errs differently by seekability (28). The
documented Identify answer is a set, by the doc comment's "and/or": the name's answer, the
stream's, and the name's archive under the stream's compression; errors are compared by
kind, and the error of a truncated stream is the decoder's own (the model runs the
third-party decoders the library wraps). The consistency of six calls (seekable and buffered,
three times each) is one check with four values: the same, varying by the archival name
only (19, with "same" allowed since six draws may agree), differing by seekability (28), or
varying (19 where the answer itself depends on map order, left open).

Over 3000 default cases the Identify property names about 1035 shapes (35 %): 19 in 1020 to
1052 (an error's archival name varies for every stream a decoder rejects), 10 in 122 to 159,
9 in 51 to 79, 25 in 0 to 8, 20 in 1 to 10, 24 in 0 to 2, 26 in 0 to 1; the 28-shaped cases
(5 to 12) are all named 19 first, since their archival name varies too; the library agrees
with the replica in every shaped case, and 44 to 48 shaped cases pass (19's six calls happen
to agree, about one in twenty). The Compression property names 10 in 299 to 322, 24 in 15 to
17, 25 in 30 to 36. Over nine rounds at the default count the Identify property shrank to 19
every time (`x.gz` or `x.tar.gz` over an empty stream), the Compression property to 24 eight
times (`Lzip{}` over no bytes) and to 25 once; over forty rounds at a hundred cases both fail
every round, the Identify property to 19 in all forty, the Compression property to 24 in 35
(25 in 5): both are mapped plain to those.
The narrow properties: 9 (an empty zip of every method, plain names), 10 (Lz4 at a level
1..9), 19 (a misnamed stream over twelve calls, level 0, no truncation, no `.br` name), 20
(an lzip cut of 6..12 bytes, past 0..3), 24 (Lzip over an empty input), 25 (brotli over
random bytes of 1025..4096 made incompressible by a fixed keystream, since the engine's bytes
compress a little; 100 % of the cases shaped), 26 (`x.tgz` and its spellings over a tar.gz
stream, where 19 cannot arise), 28 (a cut of 4 or 5 bytes, judged past 19).

The round-trip and ArchiveFS properties thread the same switch set: the xz compressor
writing its stream header before archive/zip writes the local file header, so that Extract
fails at the first non-directory entry, Python's zipfile refuses the archive, TestFS cannot
open the files and Identify reads the bytes as a corrupt xz stream (1); the un-indexed Open
handler opening the first entry under the requested directory as the directory when the
directory's own entry is missing or late (4), and listing the files of implicit or late
subdirectories, and of `./`-spelt names, as children, since `fileIsIncluded` compares raw
names with the skip list (5); the un-indexed Stat's fallback on a string prefix (6); the
implicit directory's Name() the full path before the index and, after it, the name the index
loop stored under the parent's path - the root's included (7); `dirFile.ReadDir(n <= 0)`
returning every entry (8); the empty zip (9) and the Lz4 levels (10) by the Identify and
Compression rules. The model of ArchiveFS is a file system built from the entries, read
fresh and indexed under the switches, and `fstest.TestFS` is transcribed over it so that the
check is the set of line classes TestFS reports (empty when it passes).

Over 3000 default cases the ArchiveFS property names about 2710 shapes (90 %), every one
by sufficiency with the library agreeing with the replica in all of them: 4 in 2175 to 2195,
8 in 146 to 165, 6 in 149 to 200, 7 in 139 to 147, 5 in 41 to 69; 8 alone would name every
non-empty archive (TestFS's ReadDir at EOF) and 7 about 2480, but 4 is first in id order.
The round-trip property names about 2790 (93 %): 8 in 2423 to 2533 (every non-empty
archive), 1 in 144 to 256, 9 in about 110, 10 in 1 to 5 (an Lz4 level is named 8 first
unless the tree is empty). Over nine rounds at the default count the round-trip property
shrank to 9 every time (an empty zip); the ArchiveFS property to 6 four times, 8 three
times and 4 twice; over forty rounds at a hundred cases both fail every round, the round-trip
property to 9 in all forty and the ArchiveFS property to 8 in 27 (4 in 10, 6 in 2, 7 once):
both are mapped plain to those.
The narrow properties: 1 (a zip with the Xz method over a non-empty tree, a hundred cases
with a shrink budget of sixty since every case runs Python), 4 (a directory whose entry is
missing or late, Open fresh; judged past 7 and 8), 5 (an implicit or late subdirectory or a
`./`-spelt file under an explicit directory), 6 (a missing name that is a string prefix of an
entry), 7 (an implicit directory, judged past the earlier shapes), 8 (ReadDir(1) then
ReadDir(-1) on a directory file of any archive).

The Insert property threads the switches of its five bugs: `Tar.Insert` rounding an offset
already on a block boundary up by a whole block, so that the archive reads back its old
entries and then an invalid header (2); `Zip.Insert` returning at a directory entry (3),
leaving the inserted files' method Store without SelectiveCompression (11), handing a
Bzip2, Zstd or Xz method to the updater's own registry with SelectiveCompression (12, the
same-named base entry removed before the lookup fails) and copying a link's target content
as the link's text, the first len(target) bytes of it, a missing or directory target failing
the insertion (13). Over 3000 default cases it names about 1640 shapes (55 %), every one by
sufficiency with the library agreeing with the replica in all of them: 2 in 616 to 631, 3
in 445 to 458, 11 in 349 to 423, 12 in 83 to 107, 13 in 85 to 91; the overlaps go to the
lowest id. Over forty rounds at a hundred cases it shrank to 2 twenty-seven times and to
11 thirteen (nine rounds at the default count: 2 six times, 11 three), so it is mapped to 2.
The narrow properties: 2 (a tar whose base's last entry is a directory, a link, an
empty or 512-multiple file, or no entry at all; 4 % rejected for USTAR surroundings), 3 (a
zip, the extras a directory followed by a file, no link, no custom method), 11 (a zip with a
method other than Store and no selective compression, an inserted file), 12 (Bzip2 or Zstd
with selective compression and a compressible extra file), 13 (a link among the extras,
its target existing at 3/7).

Under `HEGEL_NO_KNOWN=1` the shapes are off: the fs side's checks of a trailing key are
dropped (15, counted), the cases the classifier names as 14, 16, 17, 18 or 27 are filtered out
(10 % of the FilesFrom property's), the upper-cased paths and `.zip` are at weight zero and
the archive-named directories are renamed (21, 22, 23: nothing filtered). The narrow
properties draw the region past their shape and pass. The pins alone fail there.
Under `HEGEL_NO_KNOWN=1` the Identify property drops the consistency check of the cases the
classifier names 19 (3 %) and draws no Lz4 level above 0, no lzip cut but the empty one, no
empty Lzip input, no `.tgz` name and no empty zip; the Compression property draws no Lz4
level above 0, no empty Lzip input and no long undecodable brotli stream (nothing filtered,
nothing dropped).
The round-trip property draws no Xz zip, no Lz4 level above 0 and no empty zip, and drops
8's TestFS class (93 % of its cases); the ArchiveFS property draws no prefix names and drops
the fresh-mode checks the shapes of 4, 5 and 7 cover and the ReadDir-rest and TestFS checks
of 8 (92 % of its cases have a check dropped, counted).
The Insert property draws, under `HEGEL_NO_KNOWN=1`, a base tree whose last entry in
archive order is a file of an unaligned size (the aligned shape is half of the tars, too
many to filter), extras without directories or links, no custom method with selective
compression, and drops the inserted entries' method check without it (11, 24 % of its
cases, counted).

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
- 2026-10-14 (part 1 of four): the harness of the standard beside the old one;
  `TestHegelFilesFrom` and `TestHegelDeepFS` rewritten with their nine gates turned into
  switches off by default and nine narrow properties; the hang judged in a child process;
  the notes of archives/14 (the directory itself is skipped, not named `/`) and 27 (a root-level
  link to `.` hangs too) corrected.
- 2026-10-14 (part 2 of four): `TestHegelIdentify` and `TestHegelCompression` rewritten with
  their six gates turned into switches, eight narrow properties; archives/28 found by the
  consistency check (a truncated lzip header errs differently by seekability) and recorded;
  the notes of 10 (the bit-flag values are accepted), 19 (never Tar for `x.gz` over a tar) and
  26 (`x.tar.tgz`) corrected.
- 2026-10-14 (part 3 of four): `TestHegelArchiveRoundTrip` and `TestHegelArchiveFS` rewritten
  with their eight gates turned into switches, `fstest.TestFS` transcribed over the model,
  six narrow properties; the pin of 19 hardened (four hundred calls); the notes of 1 (Identify
  reads the bytes as corrupt xz) and 7 (the root's name after indexing) widened.
- 2026-10-14 (part 4 of four): `TestHegelInsert` rewritten with its five gates turned into
  switches, five narrow properties; the old harness removed: one harness, twenty-eight
  switches, seven wide and twenty-eight narrow properties; the notes of 12 (a link meets the
  same error; the same-named entry is removed first) and 13 (shorter targets, directory
  targets) widened. The series complete.
