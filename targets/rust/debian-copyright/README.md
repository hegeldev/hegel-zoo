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
* `wildcards_match_a_newline_in_the_path`: a `*` or `?` that must cover a
  newline, between random literal prefix and suffix, judged like the wide
  property (debian-copyright/3, fails every run).
* `expressions_round_trip_through_display`, `expressions_round_trip_through_spdx`,
  `lenient_and_strict_parsers_agree_on_valid_input`: random `LicenseExpr`
  trees → `Display`/`to_spdx_string` → `parse`/`parse_strict`/`parse_spdx`
  give the same (flattened) tree; `license_names`, `leaves`, `name_ranges`,
  `map_leaves`; the two DEP-5 parsers agree wherever the strict one accepts,
  and the lenient one keeps every name of a well-placed expression.
* `strict_parser_flattens_a_chain_after_a_comma`: `A, and B and C` and
  `A, or B or C` with random names; `parse_strict` must give the lenient
  parser's flat tree (debian-copyright/9, fails every run).
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

All nine bugs in `bugs.toml` are zoo-original (1-8 found 2026-09-13 at 4dc04da,
9 on 2026-10-06 at b1568f26):

1. `LicenseParagraph::name()` is None for a text-less License field, so
   `find_license_by_name`/`remove_license_by_name`/`find_license_for_file`
   miss stand-alone `License: MIT` paragraphs.
2. `wrap_and_sort(_, immediate_empty_line = true, _)` moves the License
   synopsis onto a continuation line (empty synopsis for every other reader).
3. Glob `*`/`?` do not match a newline in a path (python-debian: DOTALL);
   wrongly recorded as fixed at the 2026-09-17 bump, reopened 2026-10-06.
4. The lossy parser strips the extra indentation of License text lines.
5. `wrap_and_sort` re-indents License text: `Spaces(n > 1)` adds n-1 spaces
   to every text line, and extra indentation is lost (two pinned tests).
6. `Display` of `And([A, Or([B, Or([C, D])])])` is "A, and B, or C or D",
   read back as (A and B) or C or D.
7. `parse` and `parse_strict` disagree on "A, or B, and C".
8. `wrap_and_sort` sorts paragraphs by the first pattern before sorting the
   patterns, so the result is not sorted and a second call changes it.
9. `parse_strict` keeps a same-operator chain after `, and`/`, or` nested
   (`A, and B and C` is And([A, And([B, C])])) where `parse` flattens it, and
   its own Display re-parses to the flat tree.
Drawn by default (STYLE.md rule 11): `globs_match_newlines_like_python_debian`
and `lenient_and_strict_parsers_agree_on_valid_input` keep drawing the shapes
of debian-copyright/3 and /9 and fail at their natural rates (about one case
in 200 and far fewer than one in 1000), so they are expected failures marked
intermittent; the narrow properties `wildcards_match_a_newline_in_the_path`
(a wildcard that must cover a newline, judged by python-debian and the model)
and `strict_parser_flattens_a_chain_after_a_comma` (`A, op B op C`) fail
every run. `HEGEL_NO_KNOWN=1` (read once) switches the /9 shape off in the
wide property; /3's own property has no gate, like a pin.

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
- 2026-09-17: base bumped 4dc04da82229 → b1568f26a9e5 (2026-09-17, "Merge pull request #475 from jelmer/drop-minimal-versions"; 0.1.55); 7 bug(s) still reproduce; fixed upstream: debian-copyright/3. 209 tests pass.
- 2026-10-06: weekly 1000-case run 37296133806 failed `globs_match_newlines_like_python_debian` on `*` vs "\n": debian-copyright/3 reopened (never fixed; the bump's 100-case run passed by chance); local long runs found debian-copyright/9 (strict parser nests a chain after a comma operator); narrow properties for both, wide ones mapped intermittent; the /7 shape detector made token-based (the soup's double spaces and `OR` slipped past it).
