# configparser

[configparser](https://github.com/QEDK/configparser-rs) (QEDK) is an ini-style configuration
parser "inspired by Python's `configparser`": sections, `=`/`:` delimiters, `;`/`#` comments and
inline comments, case-insensitive names, valueless keys, indented continuation lines
(`set_multiline`), typed getters, a `[DEFAULT]` cascade, and `writes`/`pretty_writes`; 27M
downloads, 3.3.0 released 2026-09. Written in the zoo at 3.3.0 (upstream HEAD `7ceae18`);
tests in `tests/hegel.rs`.

## The oracle

Python's own `configparser`, one child process, configured to the crate's defaults
(`inline_comment_prefixes=(';', '#')`, `allow_no_value=True`, `strict=False`, no interpolation,
`empty_lines_in_values=True`), with `[DEFAULT]` prepended so the crate's sectionless keys are
Python's defaults. The generated text keeps to the intersection of the two grammars: headers
are never indented (an indented header after a key is a continuation line in Python, a header in
the crate — documented), never padded inside the brackets (Python keeps the padding), never
`default` in any case but Python's `DEFAULT`; inline comments are preceded by whitespace (Python
requires it); no continuation line starts with `[`; no key starts with `[` (a header attempt for
the crate, a key for Python). Python 3.12 itself crashes (`AttributeError`) on a continuation
line after a valueless key — 3.13 raises `MultilineContinuationError` — and those cases are
skipped. Section names are lowercased on the Python side, as the crate documents.

- `parsing_agrees_with_python`: 0–8 lines of headers, keys with or without delimiter/value/inline
  comment, indented continuation text, comment lines and blank lines; sections, keys and values
  (or the error) agree.
- `entry_points_agree_and_append_merges`: `read`, `load_from_stream`, `get_map`,
  `get_map_ref`, `sections`; `read_and_append` is a section-wise merge.
- `parsed_config_writes_and_reads_back`: a parsed configuration written with any
  `WriteOptions` (indentation ≥ 1, multiline on or off) reads back to the same map (an empty
  default section has no representation and is excused).
- `map_edits_follow_a_model`: `set`/`setstr`/`get`/`remove_key`/`remove_section`/`clear` and
  their return values against a `HashMap` with the documented casefolding, `new` and `new_cs`.
- `typed_getters_follow_the_docs`: `getint`/`getuint`/`getfloat`/`getbool`/`getboolcoerce`
  with and without `cascade_defaults`.
- `doc_examples`.

## Bugs (4)

- **configparser/1** (wrong-result, medium; `default_section_name_is_casefolded_like_headers`):
  the default section name is never casefolded while headers are — with
  `set_default_section("Top")`, sectionless keys go under `Top`, a `[Top]` header under `top`,
  and `get("Top", k)` finds neither.
- **configparser/2** (wrong-result, low; `inline_comment_only_line_is_a_comment`): with inline
  comment symbols distinct from the line-comment symbols, a line that is only an inline comment
  becomes a key `""`.
- **configparser/3** (contract, low; `set_values_write_and_read_back`): `writes()` ("always
  safe") does not read back for values put in with `set`: a value line starting with `[` or a
  comment symbol, padding, a trailing newline, a key containing a delimiter.
- **configparser/4** (contract, low; `zero_indentation_output_reads_back`):
  `multiline_line_indentation = 0` writes continuation lines flush left, which read back as keys.

## Not bugs

- Divergences from Python that the crate documents or that follow from its own rules: section
  names lowercased and trimmed; sectionless keys allowed (Python: `MissingSectionHeaderError`);
  an indented `[header]` ends a multiline value; inline comments need no preceding whitespace; a
  line starting with `[` and lacking `]` is an error (Python: a key); `[]` is a section named
  `""`; a continuation after a valueless key gives `"\ncont"` (Python 3.12 crashes, 3.13 errors).
- `getboolcoerce` accepts `t`/`y`/`f`/`n` beyond Python's `getboolean`; `getint` is
  `str::parse::<i64>` (no `5_0`, no whitespace).
- An empty default section is not written (it has no header) and so does not round-trip.
