# decompress

[decompress](https://github.com/mirage/decompress)'s DEFLATE, zlib, gzip and LZO codecs, against
Python's `zlib`.

## What is tested

Inputs mix random bytes, short runs repeated hundreds of times, and repeats about 32 KiB apart.
Streams go through the streaming APIs with input and output buffers down to a byte.

- `inflate_raw_from_python`, `inflate_zlib_from_python`, `inflate_gzip_from_python`: decompress
  reads what Python writes at every level, strategy, memory level and window size; for gzip, every
  header field (FTEXT, FHCRC, MTIME, OS, FEXTRA subfields, FNAME, FCOMMENT).
- `python_inflates_de`, `python_inflates_zl`, `python_inflates_gz`: Python reads what decompress
  writes, gzip header fields included.
- `ns_inflate_from_python`, `python_inflates_ns`: the same for the whole-buffer `Ns` functions.
- `gzip_member_leaves_rest`: decoding stops after the first member and leaves the rest unread.
- `corrupt_raw_agrees_with_zlib`, `corrupt_zlib_agrees_with_zlib`, `corrupt_gzip_agrees_with_zlib`:
  on truncated or bit-flipped streams decompress accepts what zlib accepts, with the same output,
  and otherwise reports the error without raising.
- `lzo_roundtrip`: `Lzo.uncompress_with_buffer` inverts `Lzo.compress`.

## Not tested

Preset dictionaries, `Lz77` and `Queue` directly, the `Channel` sources, `rfc1951`.

## History

- 2026-10-09: created at d0e44781 (v1.6.1+), hegel-ocaml 0.26.1; twelve bugs (decompress/1-12).
