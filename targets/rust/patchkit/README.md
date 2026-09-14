# patchkit

[patchkit](https://github.com/breezy-team/patchkit) parses, prints and applies patch files
(Breezy's patch library, ported from bzr); the zoo tests `unified` (`UnifiedPatch`, `Hunk`,
`HunkLine`, `parse_patch`, `parse_patches`, `reverse`, `as_bytes`, `apply_exact`), `apply`
(`apply_fuzzy`, `dry_run`, `ApplyOptions`), `ed` (`EdPatch`, GNU diff's normal format), `quilt`
(`Series`) and `timestamp` (`format_patch_date`, `parse_patch_date`) in `tests/hegel.rs`.
Written in the zoo at 0.3.8 (commit `341ce8c`, 2026-09-01). The lossless `edit` module
(rowan CST of unified/context/normal/ed diffs and series files) is not covered yet.

## The oracles

- **GNU diff 3.10** writes the inputs: `diff -u` (with `--label`s, or with its default
  nanosecond timestamps), `diff -ruN` over two generated trees (added, removed, changed and
  unchanged files, subdirectories), and normal-format `diff a b` for the `ed` module.
- **GNU patch 2.7.6** is the reference for application: `patch -f -F<fuzz> -o out -r rej in`
  on a perturbed copy of the original, reading its exit status, the output file (what it leaves
  on disk even when some hunks fail) and its per-hunk report (`Hunk #2 succeeded at 5 with
  fuzz 1 (offset 2 lines).` / `Hunk #1 FAILED at 1.`).
- **patchutils' `lsdiff`** for the file list of a multi-file patch; **quilt** (`quilt --quiltrc
  - series` in a scratch tree) for the patch list of a series file; **coreutils `date`**
  (`date -u -d @secs`) for the wall-clock part of patch timestamps. `[run] setup` needs `diff`
  and `patch`; `lsdiff` and `quilt` are optional (their comparisons are skipped when absent).

## Properties

- **Unified diffs** (`diff_u_output_parses_prints_and_applies`): for random files of 0–10
  lines (odd contents: empty lines, tabs, lines that look like headers or hunk lines, a missing
  final newline) and 1–3 line edits, `diff -u` output parses, `as_bytes` is byte-identical to
  diff's text and re-parses equal, hunk ranges match their bodies, `apply_exact` gives the
  modified file and `reverse().apply_exact` the original, `apply_fuzzy`/`dry_run` on the
  original report every hunk at offset 0 and fuzz 0, and `parse_patches`/`parse_patch` find
  exactly that patch. `diff_u_timestamps_are_split_off_and_parse`: with diff's default headers
  the names and the `\t`-separated timestamps are split as diff wrote them.
- **Fuzzy application** (`fuzzy_application_agrees_with_gnu_patch`): the patch is applied to a
  perturbed original (lines prepended, appended, inserted, changed) with fuzz 0–2; success, the
  per-hunk (offset, fuzz) outcome, the patched content and the partial content after failures
  all equal GNU patch's; `dry_run` reports the same outcomes.
- **Multi-file patches** (`recursive_diffs_are_split_per_file_and_apply`): `diff -ruN` output
  splits into one `UnifiedPatch` per changed file with `a/`/`b/` names (the `diff -ruN` lines are
  junk and dropped), each applies to its file (empty for added/removed), `strip_prefix` strips
  the prefix, and the list equals `lsdiff`'s.
- **Normal diffs** (`normal_diff_output_parses_and_applies`): `diff a b` (normal format, which
  `patch` reads back to `b`) parses as an `EdPatch` and applies to `a` giving `b` — pinned, see
  the bugs.
- **Series files** (`series_files_are_read_like_quilt_and_round_trip`): 0–6 lines of patch names
  with 0–2 options, indentation, comments and blank lines: `Series::read` gives the model's
  entries, `patches()`/`len`/`contains`/`remove` behave, `quilt series` lists the same names, and
  `write` → `read` is the identity (without comments — pinned).
- **Timestamps** (`patch_dates_format_like_date`, `patch_dates_parse_like_date`): for `secs` up to
  2100 and offsets of whole minutes within ±14 h, `format_patch_date` is `date`'s wall clock at
  the offset plus `+HHMM` (the epoch always in UTC, pre-epoch an error) and `parse_patch_date`
  inverts it; `date`'s rendering parses to `(secs, offset)`; a missing or out-of-range zone gives
  the specific error.

## Bugs (6, all zoo-original, found 2026-09-14)

- **patchkit/1** (medium) — `format_patch_date` shows the UTC wall clock with a non-UTC zone
  suffix (the offset is printed, not applied); `parse(format(s, off))` is off by the zone.
- **patchkit/2** (medium) — `EdPatch::parse_patch` rejects normal-diff ranges (`2a3,4`).
- **patchkit/3** (high) — `EdPatch::apply` `assert_eq!(start, end)` panics on every hunk whose
  old and new line numbers differ (`0a1`, `1a2`, `2d1`, …), i.e. on `diff`'s output for a
  one-line insertion or deletion; `a` also inserts before the line instead of after.
- **patchkit/4** (medium) — `parse_patch_date` rejects GNU diff's nanosecond timestamps.
- **patchkit/5** (low) — `Series::write` writes comments as `# # comment`; read/write is not
  the identity.
- **patchkit/6** (medium) — `parse_patch_date` adds the minutes of a negative offset instead of
  subtracting them: `-0330` reads as -02:30, `-0030` as +00:30.

## Not bugs

- `patch -f` is used so that GNU patch never treats a failing hunk as a reversed patch; the
  crate has no reversed-patch detection either. The fuzzy property keeps final newlines on both
  files (patch's `\ No newline` handling is exercised by the exact property).
- `diff -ruN` writes an empty added/removed file as no change; the model treats absent as empty.
  `lsdiff` prints whichever name it considers best (`a/…` for a removed file); the comparison
  strips both prefixes.
- The general generators avoid the pinned shapes: negative offsets with minutes in the parse
  property, the
  series round trip only without comments; the timestamp *format* and *normal diff* properties are
  themselves expected failures (every non-UTC offset / every real normal diff hits the bug).

## History

- 2026-09-14: created at 341ce8c (0.3.8); 6 bugs.
