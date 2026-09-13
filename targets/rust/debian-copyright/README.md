# debian-copyright

Hegel property tests for [debian-copyright](https://github.com/jelmer/debian-parsers)
(`debian-copyright/` member of the debian-parsers workspace, 0.1.55), the DEP-5
`debian/copyright` parser with a lossless (rowan) and a lossy (deb822-fast)
representation, DEP-5 glob patterns and license expressions.

Written for the zoo (no upstream property tests to import). The reference is
python-debian's `debian.copyright` (`Copyright`, `License.from_str`,
`globs_to_re`, `find_files_paragraph`), driven from a persistent `python3`
child, plus two small models: a DEP-5 glob matcher and the flattening of
license-expression trees.

## Properties

* `globs_match_like_python_debian`, `globs_match_newlines_like_python_debian`:
  `GlobPattern::try_new`/`is_match`/`is_match_path`, `literal_path`, `is_glob`
  against `globs_to_re` and the model, for patterns with escapes (valid and
  invalid) and paths derived from the pattern.
* `expressions_round_trip_through_display`, `expressions_round_trip_through_spdx`,
  `lenient_and_strict_parsers_agree_on_valid_input`: random `LicenseExpr`
  trees → `Display`/`to_spdx_string` → `parse`/`parse_strict`/`parse_spdx`
  give the same (flattened) tree; `license_names`, `leaves`, `name_ranges`,
  `map_leaves`; the two DEP-5 parsers agree wherever the strict one accepts,
  and the lenient one keeps every name of a well-placed expression.
* `license_values_are_read_like_python_debian`: `License::from_str`/`Display`
  against `License.from_str` (synopsis, text, `.` markers).
* `files_are_read_like_python_debian`, `find_files_agrees_with_python_debian`,
  `header_files_included_follows_the_model`, `header_fix_yields_the_current_format`,
  `incomplete_files_are_rejected_by_everyone`, `files_without_a_format_are_not_machine_readable`,
  `lossy_display_round_trips`: generated DEP-5 files (header fields, Files and
  stand-alone License paragraphs, multi-line values starting on the
  continuation line, comments between paragraphs, non-canonical Format URLs)
  are read the same by the lossless parser, the lossy parser and python-debian;
  `find_files`, `matcher()`, `find_license_for_file`, `find_license_by_name`,
  `FilesParagraph::matches`, `file_spans`, `is_file_included`, `Header::fix`;
  the lossy `Display` re-parses to the same file.
* `edits_are_read_back`, `edits_on_parsed_files_are_read_back`: sequences of
  `add_files`, `add_license`, `remove_*`, header/Files/License setters on a
  `lossless::Copyright`, read back by the live accessors, a re-parse, the lossy
  parser and python-debian.
* `wrap_and_sort_keeps_the_content`: `wrap_and_sort` keeps the paragraphs (as
  python-debian reads them), orders header/Files/License and the Files
  paragraphs by `pattern_sort_key`, and is idempotent.

## Bugs

All eight bugs in `bugs.toml` are zoo-original (found 2026-09-13 at 4dc04da):

1. `LicenseParagraph::name()` is None for a text-less License field, so
   `find_license_by_name`/`remove_license_by_name`/`find_license_for_file`
   miss stand-alone `License: MIT` paragraphs.
2. `wrap_and_sort(_, immediate_empty_line = true, _)` moves the License
   synopsis onto a continuation line (empty synopsis for every other reader).
3. Glob `*`/`?` do not match a newline in a path (python-debian: DOTALL).
4. The lossy parser strips the extra indentation of License text lines.
5. `wrap_and_sort` re-indents License text: `Spaces(n > 1)` adds n-1 spaces
   to every text line, and extra indentation is lost (two pinned tests).
6. `Display` of `And([A, Or([B, Or([C, D])])])` is "A, and B, or C or D",
   read back as (A and B) or C or D.
7. `parse` and `parse_strict` disagree on "A, or B, and C".
8. `wrap_and_sort` sorts paragraphs by the first pattern before sorting the
   patterns, so the result is not sorted and a second call changes it.

## Notes

* The general properties skip exactly the pinned shapes (text-less License
  paragraphs in name lookups, indented text for the lossy parser, multi-line
  License fields with `immediate_empty_line` or an indentation > 1, unsorted
  first patterns, nested same-operator trees, both comma operators in one
  expression).
* Inherited from deb822-lossless: after `Copyright::wrap_and_sort` the live
  tree labels continuation lines as KEY tokens, so `license()` on the live
  tree returns only the first line until the text is re-parsed
  (deb822-lossless/12); the pins therefore read the wrapped text through a
  re-parse. A `License:` value starting on the continuation line (empty
  synopsis, text only) is read by the crate with the first text line as the
  synopsis, through deb822-lossless/2; not generated here.
* python-debian has a bug of its own: `globs_to_re` with several patterns
  anchors only the last alternative (`\*|\*\Z`), so a Files paragraph with two
  patterns matches any path starting like the first one. `find_files` is
  compared with python only for single-pattern paragraphs; the model decides
  otherwise. python's `Files-Excluded` is line-based (a line with two patterns
  is one entry) where the crate and the spec split on whitespace; the test
  flattens python's tuple.
* Not bugs: `License::Display` (like python-debian's `License.to_str`) drops a
  trailing blank line of the text; the lossy `Header` only carries Format,
  Files-Excluded, Source and Upstream-Contact, so its `Display` drops the
  other header fields by design; header field order changes on lossy Display.
