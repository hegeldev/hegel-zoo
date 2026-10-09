# sexplib

Sexplib's own readers, writers to files, annotated parser, `With_layout`, `Path` and `Conv`,
at the tip of the `oxcaml` branch (master needs unreleased versions of Jane Street's other
libraries).

## What is tested

- `of_string_reads_spellings`, `of_string_many_reads_spellings`: every spelling of a value
  (whitespace, line/block/sexp comments, bare or quoted atoms, every escape) reads back as it.
- `of_string_needs_exactly_one`: on spellings with an edit, `of_string`, `of_bigstring` and
  their `Annotated` versions accept exactly when a reference reader of the README grammar reads
  one value.
- `writers_round_trip`, `save_load_round_trip`: `to_string*` and `save_*` read back.
- `load_sexps_reads_spellings`, `load_sexp_reads_one`: the file and channel readers, with
  buffers of 1 to 9 bytes.
- `input_sexp_leaves_the_rest`: two `input_sexp` calls read two values.
- `annotated_ranges_match_reference`, `annotated_parse_in_chunks_agrees`,
  `parse_in_chunks_agrees`: annotated ranges against the reference, `parse` fed in chunks
  from a starting `Parse_pos`, `find_sexp`.
- `conv_error_points_at_culprit`: `of_string_conv(_exn)` and `load_sexp_conv(_exn)` blame
  the right node and location.
- `scan_reads_spellings`, `scan_accepts_exactly_the_grammar`, `layout_reads_spellings`,
  `layout_accepts_exactly_the_grammar`: the ocamllex reader behind `scan_*` and
  `With_layout`, against the reference with the README's OCaml string conventions.
- `layout_render_round_trip`, `layout_render_after_edits`: `With_layout.Render` of parsed
  and of edited layouts reads back.
- `path_get_matches_model`, `path_replace_laws`: `Path.parse` with escapes, `get`, `replace`,
  `subst_path` against a model.
- `search_physical_finds_subterm`: `search_physical` and `subst_found`.
- `conv_round_trips`, `mat_of_sexp_checks_dimensions`: `Conv` for floats, integers, chars,
  strings, options, lists, arrays, hash tables, bigstrings, vectors and matrices.

## Not tested

sexplib0 (`Sexp_conv`, the printers), `Sexp_grammar`, `Exn_magic`, `num`, `unix` and the
error messages' wording.

## History

- 2026-10-09: created at f7dd083f (v0.18~preview.130.106+341), hegel-ocaml 0.26.1; 6 bugs.
