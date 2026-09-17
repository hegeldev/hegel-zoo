# zip

[zip-rs/zip2](https://github.com/zip-rs/zip2).

## What is tested

**`tests/end_to_end.rs`**
- `prop_write_read_roundtrip`: Crown roundtrip: an archive written with `ZipWriter` reads back with `ZipArchive` — the entry count is preserved, and every entry's name and bytes are preserved both when iterating by index and when looking up by name. Covers the empty archive (0 entries) and empty file entries (0 bytes) since both generators go down to zero.
- `prop_name_lookup_consistency`: `index_for_name`, `name_for_index`, and `file_names` agree with each other and with what was written, in write order.
- `prop_entry_metadata_consistency`: Entry metadata read back from the central directory is consistent with what was written: uncompressed size, CRC-32 (checked against the independent crc32fast oracle), compression method, and file/dir flags.
- `prop_empty_archive_with_comment_roundtrip`: An archive with zero entries and a drawn comment roundtrips: it opens, reports itself empty, and preserves the comment bytes exactly. One branch splices an EOCD magic into the comment, since the end-of-central-directory record is located by scanning backwards through the comment area.
- `prop_duplicate_name_rejected`: The writer rejects a duplicate file name (documented on `start_file`: "The file must not have the same name as a file already in the archive"), and the archive remains usable with the original entry intact.
- `prop_large_entry_roundtrip`: A few-hundred-KB entry (larger than any internal buffer) roundtrips byte-for-byte under every enabled compression method.

**`tests/invalid_path.rs`**
- `prop_sanitized_names_never_escape`: Security contract of `ZipFile::enclosed_name` ("It can't resolve to a path outside the current directory. It can't be an absolute path") and `ZipFile::mangled_name` ("Absolute paths are made relative, ParentDirs are ignored"): whatever hostile name is stored in the archive, the sanitized path is relative and contains no `..`, root, or prefix components, so joining it onto an extraction root can never escape that root.

**`tests/prepended_garbage.rs`**
- `prop_arbitrary_bytes_never_panic`: Opening and fully (but boundedly) reading ARBITRARY bytes never panics, hangs, or reads without bound — errors are the only acceptable failure mode.
- `prop_corrupted_archive_never_panics`: Build a small valid archive, then corrupt it with drawn byte overwrites or a truncation. Opening and boundedly reading the result may fail but must never panic. Overwrites are biased toward the tail of the file, where the EOCD and central directory (the fields that drive parsing) live.
- `prop_prepended_junk_preserves_contents`: Generalization of `test_prepended_garbage` above: the reader documents support for archives with prepended content (self-extracting archives), so ANY drawn junk prefix must leave the entry count, contents, and reported offset intact.

## Oracles

## Not tested

## History

- 2026-07-23: predecessor base commit `1058f8062102` (ci(deps): bump step-security/harden-runner from 2.19.4 to 2.20.0 (#...).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/zip.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped 1058f8062102 → 6fff6209289b (2026-09-11, "feat: add comment and test for ZipStreamReader and symlinks (#985)"; 9.0.0-pre3); 0 bug(s) still reproduce; add/add conflicts in tests/end_to_end.rs resolved by keeping both sides. 272 tests pass.
- 2026-09-14: base bumped 6fff6209289b → 5a4f79868cd6 (2026-09-14, "fix: copy extra fields in raw_copy_file (#955) (#982)"; 9.0.0-pre3); 0 bug(s) still reproduce. 273 tests pass.
- 2026-09-14: base bumped 5a4f79868cd6 → a543a1fc8f3f (2026-09-14, "fix: Symlink with very large declared size could lead to out-of-memory panic (#984)"; 9.0.0-pre3); 0 bug(s) still reproduce. 277 tests pass.
- 2026-09-14: base bumped a543a1fc8f3f → 75eec5b61f2e (2026-09-14, "ci(deps): bump release-plz/action from 0.5.132 to 0.5.133 (#987)"; 9.0.0-pre3); 0 bug(s) still reproduce. 277 tests pass.
- 2026-09-15: base bumped 75eec5b61f2e → d2d05e8eb513 (2026-09-15, "feat: read data descriptor from binary (#990)"; 9.0.0-pre3); 0 bug(s) still reproduce. 278 tests pass.
- 2026-09-15: base bumped d2d05e8eb513 → 80447c5e9071 (2026-09-15, "ci(deps): bump release-plz/action from 0.5.133 to 0.5.134 (#993)"; 9.0.0-pre3); 0 bug(s) still reproduce. 278 tests pass.
- 2026-09-16: base bumped 80447c5e9071 → 8b4991288b79 (2026-09-16, "fix: don't pre-allocate the declared size in the legacy decoders (#991)"; 9.0.0-pre3); 0 bug(s) still reproduce. 278 tests pass.
- 2026-09-16: base bumped 8b4991288b79 → 68b3e3b69804 (2026-09-16, "ci(deps): bump github/codeql-action/upload-sarif from 4.37.9 to 4.38.0 (#997)"; 9.0.0-pre3); 0 bug(s) still reproduce. 278 tests pass.
- 2026-09-17: base bumped 68b3e3b69804 → 8abd89514424 (2026-09-17, "ci(deps): bump release-plz/action from 0.5.135 to 0.5.136 (#999)"; 9.0.0-pre3); 0 bug(s) still reproduce. 278 tests pass.
- 2026-09-17: base bumped 8abd89514424 → 09c030eab56e (2026-09-17, "Merge commit from fork"; 9.0.0-pre3); 0 bug(s) still reproduce. 291 tests pass.
