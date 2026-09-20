# typescript/node-csv — adaltas/node-csv (csv-parse and csv-stringify, against Python's csv)

node-csv is the `csv-parse` / `csv-stringify` family (~14M weekly downloads): a streaming CSV
parser with a large option surface (quotes, escapes, multi-character delimiters, comments,
trimming, slicing by line and record, columns, casting, delimiter discovery) and its writer. The
patch checks both against Python's `csv` module and against a model of the parser's options on
generated documents, and pins 10 bugs.

## How it is built

No build: `packages/csv-parse/lib` and `packages/csv-stringify/lib` are plain ES modules with no
runtime dependencies; Hegel goes under `.hegel/`. The oracle needs `python3` on PATH (stdlib
only: `csv`, `json`).

## How it is tested

`hegel/hegel.test.mjs` runs under `node --test`; `hegel/hegel-zoo.mjs` is the zoo's shared
harness. `hegel/oracle.py` is held open for the whole run and answers over two FIFOs (one JSON
line per request, see `hegel/csv.mjs`): `csv.reader` on a text with a dialect (strict, newline
handling as `io.StringIO(newline="")`), or `csv.writer` on records with a dialect.

| Property | What it checks |
|---|---|
| `TestHegelStringifyParseRoundTrip` | `stringify` then `parse` with matching separators gives the records back, across delimiters (single, multi-character, non-ASCII), quotes, escapes (the quote or another character), record delimiters (the named ones and custom strings), `quoted`/`quoted_empty`/`quoted_string`/`quoted_match`, `eof`, `bom`, `escape_formulas` (modelled as the `'` prefix) and `header`+`columns` (objects back) |
| `TestHegelStringifyOutputReadByPython` | Python's strict `csv.reader` with the matching dialect reads `stringify`'s output as the records (everything quoted when the escape is not the quote, since Python's escape acts outside quotes too) |
| `TestHegelPythonOutputParsed` | `parse` reads what Python's `csv.writer` writes (QUOTE_MINIMAL/ALL/NONNUMERIC with doubling, or an escape character with QUOTE_ALL), record delimiter given or discovered |
| `TestHegelParseMatchesTheModel` | on a generated RFC 4180-style document (quoted and bare fields, embedded line breaks, comment lines, padding around fields when trimmed, empty lines, ragged rows, a BOM) `parse` gives what the model says under `skip_empty_lines`, `relax_column_count[_less/_more]`, `from`/`to`, `from_line`/`to_line`, `columns: true`, `info: true` (`lines`, `records`), an explicit or discovered record delimiter, or throws the error the model expects; on the plain subset Python's strict reader checks the generator's expectation too |
| `TestHegelStreamMatchesOneShot` | the same document (30% mutated), fed to the `Parser` stream in random chunks (often one byte, cutting UTF-8 sequences and multi-character separators), gives the records or the error code of the one-shot parse; `raw` and `info` compared when set |
| `TestHegelDelimiterDiscovery` | on alphanumeric records where the delimiter dominates every other character, `delimiter_discover` finds it and `parse` with `delimiter_auto` gives the records |
| `TestHegelHostileInputNeverCrashes` | mutated documents, junk and well-formed documents under random option sets: `parse` returns or throws a `CsvError`; the stream ends or errors with a `CsvError` within 5 s; `stringify` on arrays of strings returns a string |

The generator (`hegel/csv.mjs`) draws fields from words, punctuation (delimiters, quotes,
escapes, comment and formula characters), line breaks and odd characters (NBSP, ideographic
space, U+2028, NUL, BOM, astral); `ZOO_COLLECT=1` turns mismatches into `# COLLECT` counts and
`HEGEL_TEST_CASES` (default 100) widens the sweep. Known bugs are gated in `hegel/known.mjs` by
the shape of the case (a bare field with a line break, a lone empty field, a comment line before
`from_line`, a CRLF in a quoted field, a non-ASCII sample for discovery); `ZOO_NO_KNOWN=1` lifts
the gates.

## Bugs

10 open, all pinned (see `bugs.toml`). In 1000-case sweeps, every property agrees with its oracle
or model on every case not touched by them:

- `stringify` leaves a field holding a CR or LF bare unless it is the configured record
  delimiter, so Python (and csv-parse's own record-delimiter discovery) split the record (1);
  writes a record of one empty field as an empty line, which vanishes at the end of the output
  (2); and applies the `escape_formulas` prefix after the quoting decision, so with `quote: "'"`
  the output cannot be parsed (3).
- `parse` drops the record at `from_line` when a comment line precedes it (4); counts a CRLF
  inside a quoted field as two lines, so `info.lines`, `from_line` and `to_line` are off (5);
  `delimiter_auto` throws on any character beyond U+007E (6) and on a stream that ends without
  data (9); `raw` keeps one byte of a CRLF record delimiter or of a multi-character delimiter (7);
  `cast` turns `0x10`, `0b11`, `0o7` into 0 (8).
- The `Parser` stream, with a quote of several bytes, throws `CSV_INVALID_CLOSING_QUOTE` (or
  drops the record under `skip_records_with_error`) when a chunk ends inside a delimiter of
  several bytes right after a closing quote; the one-shot parse is fine (10).

## Accepted differences and notes (not counted as bugs)

- csv-parse's `escape` acts only inside quoted fields and csv-stringify doubles the escape only
  when it quotes; Python's `escapechar` acts everywhere and its writer always escapes it. The
  interop properties therefore quote everything (`quoted: true`, `QUOTE_ALL`) when the escape is
  not the quote. Python's reader also gives no fields for an empty line where csv-parse gives
  `[""]`: canonicalised in the comparisons.
- The line count advances on the CR/LF bytes csv-parse meets: a custom record delimiter that
  does not start with a CR or LF (`;\n`, `||`, U+001E) never advances it, so `from_line`,
  `to_line` and `info.lines` refer to line 1 throughout; a `\n\n` delimiter counts as one line.
  The model follows this.
- A bare field of only whitespace on a line of its own is an empty line for `skip_empty_lines`
  with `ltrim`, a record `[""]` with `rtrim` alone; a last line without a record delimiter that
  reads as empty is nothing. The model follows the code here.
- Comments start anywhere in a line by default (`comment_no_infix: false`), so the generator
  keeps the comment string out of bare fields; a space or tab delimiter is a delimiter before it
  is trimmable whitespace, so the padding written under `ltrim`/`rtrim` never uses it.
- `to` counts the records handled, including those skipped by `from` (so `to < from` yields
  nothing); `columns: true` takes the first record at or after `from_line` as the header, and the
  generator skips headers with duplicate or empty names.
- Delimiter discovery is a heuristic (a character frequency score with preferred characters): the
  property only judges samples where the delimiter's count exceeds every other character's.

## Not tested

`encoding` other than UTF-8 (UTF-16 BOM switching was probed by hand and works), `cast` beyond the
pinned case (`cast_date`, cast functions), `columns` given as an array or function,
`group_columns_by_name`, `objname`, `on_record`/`on_skip`, `skip_records_with_error` beyond the
stream comparison, `max_record_size`, `ignore_last_delimiters`, the callback and `stream/`
`sync` API variants, the CJS builds (`dist/`), csv-stringify on object records with nested
`columns` keys, `header_as_comment`, `cast` on non-string values, and the `csv`, `csv-generate`
and `stream-transform` packages.

## History

- 2026-09-20: created at 745f045 (csv-parse 6.8.3, csv-stringify 7.0.2), 7 properties, 10 bugs.
