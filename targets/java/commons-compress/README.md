# commons-compress

[Apache Commons Compress](https://github.com/apache/commons-compress) (`org.apache.commons:commons-compress`,
1.29.0-SNAPSHOT, pinned at the master commit of 2026-09-07): archivers (tar, zip, cpio, ar, 7z, ...), compressors
(gzip, bzip2, xz, lzma, lz4, snappy, zstd, deflate, .Z, ...), the `ArchiveStreamFactory`/`CompressorStreamFactory`
detectors and the byte-level utilities.

The tests are a Maven module `hegel/` added by the patch; `[run] setup` installs the library from the pinned tree into the
local Maven repository (everything but compilation skipped; about a minute). The pull request template links the ASF
Generative Tooling Guidance and asks for AI assistance to be disclosed.

## The oracles

- **The formats' reference tools**, as child processes with the archive or stream on stdin: GNU tar 1.35 (`tar -tf -`),
  GNU cpio 2.15 (`cpio -t`, `cpio -i --to-stdout name`), binutils ar 2.42 (`ar t`, `ar p`), Info-ZIP unzip 6.00
  (`unzip -t`), gzip 1.12, bzip2 1.0.8, xz 5.4.5 (also `--format=lzma`) and zstd 1.5.5 as decoders and encoders
  (several compression levels, checks, concatenated members).
- **Python 3.12**: `tarfile` and `zipfile` list every member as JSON (name, size, mode, ids, times, type, link, data
  hash, `testzip`) and write archives in every format they know (ustar/gnu/pax; stored/deflated/bzip2/lzma zips) for
  the library to read; `gzip`, `bz2`, `lzma` and `zlib` encode and decode streams.
- **In-process codecs**: airlift aircompressor 2.0.3 for LZ4 blocks, raw and framed Snappy and zstd frames in both
  directions; the JDK's `ZipInputStream`, `CRC32` and `java.util.zip` for zips and deflate.
- **Byte-level models**: the RFC 1952 gzip header (flags, MTIME, XFL, OS, extra subfields, name, comment, CRC16,
  trailer CRC32/ISIZE) built from the parameters and compared byte for byte; reference implementations of the bit
  reader, little-endian coding, fixed-length block padding and an in-memory channel.
- **The library against itself**: every tar option (four long-name modes × three big-number modes × pax for non-ASCII
  names) and zip option (encodings, language-encoding flag, unicode extra fields, zip64 modes, stored/deflated,
  seekable or streamed output, comments, unix modes) writes archives that `TarArchiveInputStream`/`TarFile` and
  `ZipFile`/`ZipArchiveInputStream` read back with the modelled metadata; cpio in its four formats; ar in both
  long-name modes; every compressor round-trips through the factory with `write(int)`/`write(byte[])`/
  `write(byte[], off, len)` mixed, is detected, reports its statistics and survives `finish()`.

Tools missing on the machine are skipped (`Tools.available`). Known limits of the oracles are avoided rather than
recorded: GNU tar refuses ids beyond `uid_t`, Debian's unzip trips its zip-bomb check on data descriptors, binutils reads
only 15 characters of an unterminated 16-character ar name, Python's tarfile passes a float mtime through a double (the
tests write the pax record themselves), the factory's `decompressConcatenated` is documented for gzip, bzip2 and xz only.

## What the properties found

The recorded bugs (`bugs.toml`, pinned in `CommonsCompressPinsTest`) fall into a few families: readers narrowing
values to `int` (tar base-256 ids, the Snappy varint, the gzip MTIME); writers accepting what the format cannot hold and
producing corrupt or misleading archives instead of refusing (cpio field overflow, the cpio `TRAILER!!!` name, ar
reserved and non-ASCII names, ar excess data, a sized tar directory, a 70000-byte zip comment, a 7z name with NUL);
metadata lost between writer and reader (a GNU long name next to a pax header, long owner names in pax mode, the zip
NTFS extra inventing 1601-01-01 access times, 7z directory flags); `finish()`/`close()` contracts (gzip appends a bogus
member, xz throws, zstd writes nothing, an empty LZ4 block throws); and small input-validation gaps in the compressors
and utilities.
