# deb822-lossless

[deb822-lossless](https://github.com/jelmer/debian-parsers/tree/main/deb822-lossless) is a lossless
(rowan CST) parser and editor for deb822 files — Debian `control`, `Packages`, `Sources`, `.changes`,
`.dsc` and friends: `Deb822` → `Paragraph` → `Entry`, with lookups, setters, paragraph operations,
incremental reparsing and `wrap_and_sort`. Written in the zoo at 0.5.18 (debian-parsers commit
`4dc04da`, 2026-09-05). The crate is a workspace member: `subdir = "deb822-lossless"`.

## The oracles

- **dpkg's `Dpkg::Control::HashCore`** (dpkg 1.22; Perl, driven as a persistent child through
  `JSON::PP`): `parse` called until it returns no fields gives the paragraphs with their fields in
  order. It strips trailing whitespace and one indent character, unescapes a lone `.` continuation
  line to an empty line, drops `#` comment lines in column 0 and capitalises field names.
- **python-debian's `Deb822.iter_paragraphs`** (2.0), a second persistent child: paragraphs with
  fields in order; trailing whitespace stripped on the first line, continuation lines kept verbatim.

Values are compared line by line with the surrounding whitespace of each line removed — the common
ground of the crate (which drops continuation indents), dpkg and python-debian — and keys
case-insensitively. `[run] setup` checks that both oracles load.

## Properties

- **Parsing**: generated documents of 0–3 paragraphs with 1–4 fields (mixed-case keys with `-_.+~`,
  values of punctuation-heavy words and non-ASCII, empty values, 0–3 continuation lines with space or
  tab indents and `.` lines, comment lines between fields and inside values, leading blank lines and
  comments, 1–2 blank separator lines, optional final newline; flags for trailing whitespace, CRLF,
  empty first lines and whitespace-only separators) must be read by the strict parser with dpkg's
  and python-debian's paragraphs, keys and values; whatever the strict parser accepts, dpkg accepts.
- **The CST**: any text (documents with random `:`/`#`/newline/CR/space mutations) prints back
  verbatim from the relaxed parse, strict and relaxed agree on the errors, error ranges lie inside
  the text, every accessor and position query runs without panicking; `paragraph_at_position`,
  `paragraph_at_line`, `entry_at_line_col`, `entry_at_position`, `line_col` and the key/colon/value
  ranges agree with the text ranges of the nodes.
- **Incremental reparse**: `reparse` is lossless for any edit of any text; for edits inside a value
  line, or replacing a field or continuation line by another, it equals a full parse (tree, structure
  and errors); for arbitrary edits it should too.
- **Lookups**: `get`, `get_entry`, `get_all`, `contains_key`, `keys` are case-insensitive
  first-match views of `items`; `Paragraph::from_str` is the first paragraph.
- **Editing**: 1–4 random edits (`set`, `insert`, `remove`, `rename`, `set_multiline`,
  `change_field_indent`, `normalize_field_spacing`, `insert_comment_before`, `wrap_and_sort` per
  paragraph and per document, `insert_paragraph`, `add_paragraph`, `remove_paragraph`,
  `move_paragraph`, `swap_paragraphs`) on paragraphs inside a document; after each, the live tree, a
  strict re-parse of its text, dpkg and python-debian all read the model.
- **Builders and canonicalisers**: `Paragraph::from(Vec<(k, v)>)` / `FromIterator` documents are
  read back by everyone; `Entry::try_with_formatting` / `new` / `with_indentation` produce entries
  that parse to their key and value; `wrap_and_sort` (any indent, `immediate_empty_line`, line
  limit, sorted entries) keeps the fields, parses, is idempotent and keeps comments;
  `normalize_field_spacing` keeps the values, leaves exactly `Key: value`, and is idempotent.

## Bugs (10, all zoo-original, all medium)

- **deb822-lossless/1** — trailing whitespace on a value line is part of `value()` (`Section: net   `
  → `net   `); both oracles strip it.
- **deb822-lossless/2** — an empty first line is dropped from the value: `Description:\n long` reads
  as `long`, not `\nlong`; the setters write the inverse shape.
- **deb822-lossless/3** — CRLF files fall apart: `\r` is a newline of its own, so `A: 1\r\nB: 2\r\n`
  is two paragraphs and continuation lines are orphaned.
- **deb822-lossless/4** — a continuation line whose text starts with `#` is lexed as a comment and
  the field is rejected; `wrap_and_sort(immediate_empty_line)` produces that shape itself.
- **deb822-lossless/5** — `Parse::reparse` is not a full parse: an edit that joins paragraphs keeps
  them apart, and errors outside the reparsed region are dropped.
- **deb822-lossless/6** — `wrap_and_sort` turns a comment line inside a paragraph into value text
  (`A: x\n#c` → `A: x\n #c`, `A:\n#c` → `A: #c`).
- **deb822-lossless/7** — `convert_index(0)` is root child 0 whatever it is: `remove_paragraph(0)`
  deletes a leading blank line instead of the paragraph; `move_paragraph` goes wrong around comments
  and double blank lines.
- **deb822-lossless/8** — rewriting a field with an empty first line breaks the lines: `set` puts the
  new value on an unindented line, `change_field_indent` splits the paragraph.
- **deb822-lossless/9** — edits after a last line without a trailing newline glue lines together:
  `A: 1` + `insert("B", "2")` = `A: 1B: 2`; swapping the last paragraph merges it with its neighbour.
- **deb822-lossless/10** — `Deb822::wrap_and_sort` is not idempotent on its own tree: it flattens the
  comment lines before a paragraph into bare root tokens, and a second pass drops their newlines
  (`# c\nA: 1\n` → `# cA: 1\n`).
- **deb822-lossless/11** — `move_paragraph` merges paragraphs: moving one forward in a
  three-paragraph file removes the blank line the next paragraph needs.

The general properties skip exactly the inputs each bug covers (`hits_*` helpers on the generated
document or on the live tree before an edit); each bug has its own pinned test asserting the
oracles' behaviour.

## Not bugs

- Whitespace-only lines separate paragraphs for dpkg and python-debian but are an error for the
  strict parser; Policy 5.1 lets parsers choose, so those documents are only checked in relaxed mode.
- dpkg rejects duplicate field names and fields whose name ends in `-`, and unescapes ` ..` to `.`;
  the crate reads them like python-debian does. The generator avoids these shapes.
- A lone `\r` is not a Debian line ending; texts containing one are not sent to dpkg.
- An empty paragraph (its last field removed) has no text; the edit property drops it from the model.
- 2026-09-17: base bumped 4dc04da82229 → b1568f26a9e5 (2026-09-17, "Merge pull request #475 from jelmer/drop-minimal-versions"; 0.5.18); 11 bug(s) still reproduce; fixed upstream: deb822-lossless/3. 186 tests pass.
