# patchkit

[patchkit](https://github.com/breezy-team/patchkit) parses, prints and applies patch files
(Breezy's patch library, ported from bzr); the zoo tests `unified` (`UnifiedPatch`, `Hunk`,
`HunkLine`, `parse_patch`, `parse_patches`, `reverse`, `as_bytes`, `apply_exact`), `apply`
(`apply_fuzzy`, `dry_run`, `ApplyOptions`), `ed` (`EdPatch`, GNU diff's normal format), `quilt`
(`Series`) and `timestamp` (`format_patch_date`, `parse_patch_date`) in `tests/hegel.rs`, and
the lossless `edit` module — the rowan CST of unified, context, normal and ed diffs
(`edit::parse`, `Patch`, `PatchFile`, `Hunk`, `HunkHeader`, `check_counts`, `fix_counts`,
`detect_format`), its incremental `Parse::reparse`, and the `edit::series` parser and editor
(`SeriesFile::{push, prepend, insert, remove, set_options, add_comment, rename, move_to,
insert_comment, clear, update_all, reorder}`, `PatchEntry::set_name`) — in `tests/hegel_edit.rs`.
Written in the zoo at 0.3.8 (commit `341ce8c`, 2026-09-01).

## The oracles

- **GNU diff 3.10** writes the inputs: `diff -u` (with `--label`s, or with its default
  nanosecond timestamps), `diff -ruN` over two generated trees (added, removed, changed and
  unchanged files, subdirectories), normal-format `diff a b` for the `ed` module, and for the
  CST also `diff -c` and `diff -e`.
- For the `edit` CST, **the crate's own `unified` parser** (byte-exact against diff, see
  above) is the oracle for the paths, ranges and lines of a unified diff; the other formats are
  read back with a small line classifier (command lines, `<`/`>`/`!`/`+`/`-`/`  ` bodies,
  `.` terminators); the contract for `reparse` is the crate's own (`reparse_tests`: the same
  green tree as a full parse); the series editor is checked against a list model, a re-parse
  of its text, the lossy `Series::read` and `quilt series`.
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

### The `edit` CST (`tests/hegel_edit.rs`)

- **Unified** (`unified_cst_agrees_with_the_unified_parser`): `diff -u` output (labels or
  timestamps, lines with tabs, empty lines, `-x`/`+plus`/`@@ …`/`\ …`/`1a`/`*** x` contents,
  missing final newlines) parses without errors, `syntax().to_string()` is the input, there is
  one `PatchFile` whose paths, hunk ranges (an implicit count reads as 1), line kinds, line
  texts and `\ No newline` markers equal the `unified` parser's, `check_counts` is empty and
  `stats` match. `fix_counts_leaves_diff_output_alone`: `fix_counts` is false and the text
  unchanged on diff output (pinned).
- **Context** (`context_diff_output_parses_structurally`): `diff -c` output — text identity, one
  `ContextDiffFile` with both paths, one hunk per `***************`, each with header, old and
  new sections whose ranges and line kinds (context/change/add/delete/marker) match the text.
- **Normal** (`normal_diff_output_parses_structurally`): `diff a b` — text identity, one
  `NormalHunk` per command line with the command text and the `<`/`>` lines (files with final
  newlines; the marker case is pinned).
- **Ed** (`ed_script_output_parses_structurally`): `diff -e` — one `EdCommand` per command,
  the right kind, line numbers and content lines up to the `.` terminator.
- **Incremental reparse** (`patch_reparse_matches_a_full_parse`, `series_reparse_matches_a_full_parse`):
  a random byte-range replacement in a patch text (1–3 diffs of random formats with git/`diff
  -ruN`/`Only in` junk lines) or a series file, `reparse` vs `parse` — text identity and equal
  green trees (pinned: fixed counterexamples first).
- **Series files** (`series_cst_reads_like_quilt`): indentation, tabs, options, trailing `#
  comments`, blank lines, a missing final newline — no errors, text identity, patches/options
  and comment texts equal the model, the lossy `Series::read` and `quilt series` list the same
  names. `series_editor_matches_a_list_model`: 1–6 random editor operations against a list
  model, checked on the live tree, on a re-parse of its text and (at the end) with `quilt
  series`.

## Bugs (16, all zoo-original, found 2026-09-14)

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

The `edit` module (second slice):

- **patchkit/7** (high) — the unified CST ends a hunk at any `---`/`+++` line without looking at
  the header counts: a deleted `-- sql comment` line starts a bogus second `PatchFile`.
- **patchkit/8** (low) — `fix_counts` rewrites a correct `@@ -1 +1 @@` to `-1,1 +1,1` and
  returns true; `check_counts` reads the implicit count as 1.
- **patchkit/9** (medium) — a quoted file name with spaces (`--- "sp ace"\t…`, as diff writes
  it) is cut at the first space; the `unified` parser keeps it.
- **patchkit/10** (medium) — normal diff: a `\ No newline` marker on the old side of a `c` hunk
  ends the hunk and the `---` separator becomes a unified file header.
- **patchkit/11** (medium) — `Parse::reparse` differs from a full parse when its slice ends
  inside a line (junk-line tokens under the root, whitespace-only series lines).
- **patchkit/12** (high) — `SeriesFile::reorder` panics on any series of two or more patches.
- **patchkit/13** (medium) — `push`/`insert`/`add_comment` on a series without a final newline
  glue the new entry onto the last line (`a.patchb.patch`).
- **patchkit/14** (low) — `-p1` on a plain patch name warns "Invalid strip level" (the level
  is compared with the depth of the series entry).
- **patchkit/15** (low) — a whitespace-only last line without a newline is a parse error.
- **patchkit/16** (low) — the lossy `Series::read` keeps trailing `# comment` words as options.

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
- In `tests/hegel_edit.rs` the general generators likewise avoid the pinned shapes: no line
  contents starting with `--`/`++` (patchkit/7), final newlines for the normal-format property
  (patchkit/10), no `reorder` in the editor model (patchkit/12), always a final newline for the
  editor and never a whitespace-only unterminated last line for the reader (patchkit/13, /15).
  The two `reparse` properties are pins themselves (fixed counterexamples first, then random).
- `edit::HunkLine::text()` returns `None` for an empty added/removed/context line (`+` alone);
  the model reads that as `""`. `diff -e` encodes a line consisting of `.` with an `s/.//`
  command, which a syntax tree cannot represent; the ed generator never produces such a line.
  Context-diff ranges (`*** 1,5 ****`) are first,last pairs, read through the shared
  `HunkRange` node as start/count without any accessor claiming otherwise. quilt lists an
  indented `  # comment` as a patch named `#` (`cat_series` deletes only `^#` lines); the
  generator never indents comments.

## History

- 2026-09-14: created at 341ce8c (0.3.8); 6 bugs.
- 2026-09-14: second slice, the lossless `edit` module and `edit::series` editor
  (`tests/hegel_edit.rs`); 10 more bugs (patchkit/7–16).
