# otoml

otoml's parser and printer, against Python's `tomllib` (3.11+) and the TOML 1.0 spec.

## What is tested

- `reads_like_tomllib`: a reference writer spells a generated document every valid way — bare,
  quoted and dotted keys, all four string forms with every escape, integers in four bases with
  underscores, float forms, all four date-time kinds, inline tables, `[[arrays of tables]]`,
  comments, CRLF — and otoml reads it as tomllib does.
- `printer_output_reads_back`, `printer_output_is_toml`: the printer's output, with its options,
  reads back as the value in otoml and in tomllib.
- `big_integers_are_rejected`: integers no OCaml int holds are an error, not a wrapped value.
- `header_definitions_like_tomllib`, `dotted_definitions_like_tomllib`,
  `inline_table_definitions_like_tomllib`: documents that define a table more than once are
  accepted or rejected as tomllib does.

## Not tested

Integers in [2^62, 2^63) (otoml uses OCaml's 63-bit int, as its README says), the calendar
validity of dates (documented as superficial), year 0 (Python's `datetime` cannot hold it),
leap seconds, sub-microsecond fractions, the accessor and update API, the functor.

## History

- 2026-10-09: created at 04e6370e (1.0.5), hegel-ocaml 0.26.1; otoml/1-12.
