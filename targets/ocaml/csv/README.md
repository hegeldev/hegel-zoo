# csv

ocaml-csv's reader and writer, its header rows, and the functions on `Csv.t` in memory.

## What is tested

- `write_read_roundtrip`: tables read back unchanged for every writer option and separator.
- `reader_agrees_with_python`: RFC 4180 text in varied spellings reads as Python's `csv` (strict) reads it.
- `chunked_reader_agrees_with_of_string`: an input object returning arbitrary short reads gives what `of_string` gives.
- `unterminated_quoted_field_fails`: a quoted field left open at end of input raises `Csv.Failure`.
- `rows_header_matches_model`, `row_find_matches_model`, `row_get_is_nth_or_empty`: `has_header`/`header` against the documented merge rules.
- `square`, `is_square`, `trim`, `set_columns`, `set_rows`, `sub`, `compare`, `concat`, `transpose`, `associate`: against list models.

## Not tested

`csv-lwt`, `csv-eio`, `csvtool`, `fix`, files and channels, `print_readable`.

## History

- 2026-10-09: created at 72ef9e4e (2.4+), hegel-ocaml 0.26.1; csv/1-4.
