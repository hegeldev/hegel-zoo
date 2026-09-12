# tar

[composefs/tar-rs](https://github.com/composefs/tar-rs).

## What is tested

**`tests/all.rs`**
- `prop_archive_write_read_roundtrip`: The crown round-trip: any set of entries written with `Builder` (paths with `/`, Unicode, and >100-byte names forcing the GNU long-name extension; arbitrary contents and metadata) reads back byte-for-byte identical through `Archive::entries()`.
- `prop_link_name_roundtrip`: Hard links and symlinks round-trip their path and link target, including >100-byte targets that force the GNU long-link extension.
- `prop_pax_extensions_roundtrip`: PAX extended headers written with `append_pax_extensions` come back unchanged (keys and values, in order) via `Entry::pax_extensions`.
- `prop_hostile_archive_bytes_never_panic`: Decoder robustness (key untrusted-input property): iterating and reading entries from arbitrary bytes, corrupted valid archives, or checksum-valid headers with hostile size/sparse fields never panics, never reads more data than exists, and always terminates.
- `prop_truncated_archive_never_panics`: Truncating a valid archive at any byte offset is handled gracefully: entries before the cut still decode, and the decoder returns `Err` or stops (never panics) at the damage.
- `prop_corrupted_header_rejected`: Corrupting any single checksummed byte of the leading header block makes the decoder reject the entry with an error (checksum property).
- `prop_concat_ignore_zeros`: Concatenated archives: by default reading stops at the first end-of-archive marker; with `set_ignore_zeros(true)` both archives' entries appear, in order.
- `prop_unpack_in_never_escapes`: Path-traversal safety: unpacking an entry whose raw header name contains ".." components (bypassing the writer's validation) never creates anything outside the destination directory.

**`tests/header/mod.rs`**
- `prop_header_size_mtime_roundtrip`: size and mtime (12-byte numeric fields) round-trip over the full u64 range, across the octal/base-256 representation boundary.
- `prop_header_uid_gid_roundtrip`: uid and gid (8-byte numeric fields) round-trip for all values that fit in 63 bits. Values with bit 63 set are excluded: the base-256 marker bit collides with the data (see the pinned known failure below).
- `prop_header_uid_roundtrip_full_range`: KNOWN FAILURE: `set_uid` silently corrupts values >= 2^63. An 8-byte base-256 numeric field stores the extension marker in bit 63 of the field, which is also bit 63 of the value: `numeric_extended_into` does `dst[0] |= 0x80`, so `set_uid(u64::MAX ^ (1 << 63))` and `set_uid(u64::MAX)` produce identical bytes and `uid()` returns the bit-63-set reading for both. There is no error; the value is silently changed. `set_gid` shares the code path. The generator pins the failing region deterministically.
- `prop_header_mode_roundtrip`: mode round-trips for values up to 7 octal digits (the field is 8 bytes of octal text; larger values are a pinned known failure below).
- `prop_header_mode_roundtrip_full_range`: KNOWN FAILURE: `set_mode` silently truncates values >= 2^21 (0o10000000). The mode field is 8 bytes of octal text (7 digits + NUL). `octal_into` zips the digits against the field and silently drops the most significant digits that do not fit, so e.g. `set_mode(0o10000000)` stores 0 and `mode()` returns 0 with no error. Unlike uid/gid/size/mtime, `set_mode` never falls back to the base-256 extension. `set_device_major` and `set_device_minor` (also 8-byte octal, u32-valued) share this defect. The generator pins the failing region deterministically.
- `prop_header_set_path_roundtrip`: If `set_path` accepts a path, `path_bytes` returns exactly the same bytes — for all three header flavors, including the ustar prefix/name split for paths over 100 bytes.
- `prop_header_set_path_rejects_traversal`: `set_path` rejects absolute paths and any path containing a `..` component, for every header flavor.
- `prop_header_set_cksum_matches_spec`: `set_cksum` writes the checksum the tar spec defines: the unsigned sum of all 512 header bytes with the checksum field counted as eight spaces.

## Oracles

## Not tested

## History

- 2026-07-08: predecessor base commit `2c19ee2fbd01` (Sync common files from infra repository).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/tar.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
