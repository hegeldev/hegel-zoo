# yojson

`Yojson.Safe`'s reader and writers, and `Util.member`/`Util.index`.

## What is tested

- `roundtrip`, `pretty_roundtrip`: written values read back unchanged.
- `writer_is_standard`: a strict RFC 8259 reader reads the output as the same value.
- `writer_refuses_non_finite`: writing raises exactly on NaN and the infinities (3.0.0).
- `reader_reads_standard_spellings`: every standard spelling of a value reads back as it.
- `int_literal_boundary`: `` `Int `` within the int range, `` `Intlit `` beyond it.
- `member_is_first_binding`, `index_counts_from_both_ends`: against list models.

## Not tested

`Basic`, `Raw`, the streaming readers, `prettify`/`compact`, yojson-five, the rest of `Util`,
and what the reader accepts beyond standard JSON.

## History

- 2026-10-08: created at df9e87cd (3.0.0+), hegel-ocaml 0.26.1; no bugs at 1000 test cases.
