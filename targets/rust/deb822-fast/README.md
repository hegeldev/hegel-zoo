# deb822-fast

Hegel property tests for [deb822-fast](https://github.com/jelmer/debian-parsers)
(`deb822-fast/` member of the debian-parsers workspace, 0.2.3), the lossy
deb822 parser with an owned API (`Deb822`, `Paragraph`, `Field`), a borrowed
low-allocation API (`BorrowedParser`) and a streaming `ParagraphReader`, plus
the `convert` helpers used by `deb822-derive`.

Written for the zoo (no upstream property tests to import). The references are
the two implementations on the machine — dpkg's `Dpkg::Control::HashCore`
(a persistent Perl child) and python-debian's `Deb822` (a persistent Python
child) — and the crate's own three parsers, which must agree with each other.

## Properties

* `paragraphs_are_read_like_python_debian`, `paragraphs_are_read_like_dpkg`:
  generated documents (comments, trailing whitespace, empty first lines,
  ` .` lines, tab indents, missing final newline) are read as the same
  paragraphs, keys compared case-insensitively and values line by line with
  the surrounding whitespace removed (the common ground of the three readers).
* `the_model_is_what_the_parser_reads`: the exact value the crate documents
  (leading whitespace of every line dropped, trailing whitespace kept) for LF
  documents; `get` case-insensitively; `from_reader`; `Paragraph: FromStr`
  errors (`UnexpectedEof`, `ExpectedEof`).
* `the_borrowed_parser_agrees_with_the_owned_parser`,
  `the_paragraph_reader_agrees_with_from_str`: on arbitrary text (generated
  documents with random mutations) the three parsers return the same
  paragraphs or the same error; `BorrowedField::lines/join/as_single_line`,
  `BorrowedParagraph::get/get_single/get_field`, `iter_paragraphs_borrowed`.
* `display_of_a_parsed_document_round_trips`,
  `display_of_a_built_paragraph_round_trips`,
  `display_output_is_read_by_the_references`: `Display` of a parsed document
  or a built paragraph re-parses to the same thing and is read by dpkg and
  python-debian as the same paragraphs.
* `edits_follow_the_list_model`, `set_with_field_order_keeps_unknown_fields_sorted`:
  `insert`, `set`, `remove`, `set_with_field_order` (both canonical orders),
  the `Deb822LikeParagraph` trait, `iter_mut`, `into_iter`/`collect` against a
  list model with case-insensitive names; a new known field keeps the known
  fields in canonical order and never moves the others.
* `format_multi_line_is_read_back`, `format_folded_keeps_the_words`,
  `format_single_line_accepts_exactly_single_lines`: the `convert` helpers.

## Bugs

All seven bugs in `bugs.toml` are zoo-original (found 2026-09-13 at 4dc04da):

1. A whitespace-only line inside a paragraph is a continuation line for the
   owned and borrowed parsers (a paragraph separator for dpkg, python-debian
   and `ParagraphReader`): two stanzas are merged.
2. The owned parser rejects a whitespace-only line between paragraphs that
   the two other parsers and the references skip.
3. CRLF: a `\r\n` blank line is `UnexpectedToken("\r")`, values keep `\r`,
   `Display` drops it again.
4. Whitespace before the colon is part of the field name (`K : v` →
   `get("K")` is None); names with inner whitespace are accepted.
5. `Display` writes an empty continuation line as ` `, which dpkg and
   python-debian read as the end of the paragraph (`format_multi_line`
   writes ` .`).
6. `Display` of a value ending in `\n` writes a blank line after the field.
7. `ParagraphReader` skips an indented comment line before a paragraph that
   `from_str` and the borrowed parser reject.

## Notes

* The general properties skip exactly the pinned shapes: whitespace-only
  lines, CRLF documents with a blank line (all of CRLF for the Display round
  trip), indented comments between paragraphs, empty continuation lines and
  values ending in a newline in built paragraphs.
* By design and not recorded: the crate drops all leading whitespace of a
  continuation line (dpkg drops one character, python-debian none) and keeps
  trailing whitespace; a line without a colon is an error (python-debian
  ignores it, dpkg reads an empty field); duplicate field names are kept as
  duplicates (`get` returns the first; python-debian keeps the last, dpkg
  rejects them) and are not generated. `Paragraph::set`'s documentation
  promises insertion "at the appropriate position based on canonical field
  ordering" but it appends; only `set_with_field_order` orders.
* dpkg unescapes a continuation line of two or more dots (` ..` → `.`), so
  generated values contain no dot runs; dpkg's ` .` → empty line is undone
  before comparing.
- 2026-09-17: base bumped 4dc04da82229 → b1568f26a9e5 (2026-09-17, "Merge pull request #475 from jelmer/drop-minimal-versions"; 0.2.3); 7 bug(s) still reproduce. 72 tests pass.
