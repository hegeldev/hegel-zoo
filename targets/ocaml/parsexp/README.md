# parsexp

Parsexp's `Single`, `Many`, `Many_and_positions` and `Eager` parsers, at v0.17.0 (HEAD needs
unreleased OxCaml packages).

## What is tested

- `many_reads_spellings`, `single_reads_spellings`: every documented spelling of a value
  (whitespace, line/block/sexp comments, bare or quoted atoms, every escape, line
  continuations) reads back as it.
- `writers_round_trip`: sexplib0's `to_string`, `to_string_hum` and `to_string_mach` read back.
- `accepts_exactly_the_grammar`, `single_needs_exactly_one`: on spellings with an edit, accepted
  exactly when a reference reader of the README grammar accepts, with the same values.
- `escapes_agree_with_reference`: decimal and hex escapes in range and out, truncated and
  unknown escapes, in atoms and inside block comments.
- `positions_match_reference`: every node's range.
- `chunked_feeding_agrees`, `eager_agrees_with_many`: feeding in chunks as small as 0 bytes.

Where the README is loose, the reference follows parsexp's deliberate choices: `#|` or `|#`
inside an unquoted atom is an error, a `#` before `;` stays in the atom, a lone CR is an error.

## Not tested

The CST parsers, `Conv_*`, the `Positions` iterator, and the `Lexing.lexbuf` readers.

## History

- 2026-10-09: created at 332967db (v0.17.0), hegel-ocaml 0.26.1; no bugs at 1000 test cases.
