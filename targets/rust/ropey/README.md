# ropey

[cessen/ropey](https://github.com/cessen/ropey): the `ropey` crate (1.6, master), a utf8 text
rope indexed by chars with line-break tracking (`Rope`, `RopeSlice`, the `Bytes`/`Chars`/`Lines`/
`Chunks` iterators, `RopeBuilder`, `str_utils`); the text buffer of the Helix editor.

Written in the zoo (not imported from the predecessor). Run with `--features small_chunks` — the
crate's internal feature (used by its own fuzzers) that caps leaf chunks at 9 bytes, so a few
dozen characters make a tree several levels deep with chunk boundaries everywhere; with the
default ~1 KiB chunks short texts never leave a single leaf. Only the crate's unit tests
(`--lib`) and `tests/hegel.rs` are run: upstream's `tests/proptest_tests.rs` takes 70 s and, under
`small_chunks`, `pt_chunk_at_byte_slice`/`pt_chunk_at_char_slice` failed once in six runs
(proptest could not persist the input; not reproduced — see the notes).

## What is tested

**`tests/hegel.rs`**
- `edits_match_the_string_model`: a rope edited by an arbitrary script (`insert`, `insert_char`,
  `remove` in every range form, `split_off` + `append`, `shrink_to_fit`; positions drawn as
  fractions of the current length) holds the same text as the `String` edited alike; after every
  step the crate's own `assert_integrity`/`assert_invariants` hold, `len_chars` and `capacity`
  agree; the result passes every query check below, equals a rope built from the text directly,
  and a clone (`is_instance`) edits independently.
- `queries_match_the_model`: on a rope of arbitrary chunk structure, every query agrees with the
  model on its text (see below) and the `get_*`/`try_*` variants give `None`/the documented
  `Error` variant with the documented payload exactly out of bounds.
- `slices_behave_like_ropes_of_their_text`: a slice by char range in any range form, or by byte
  range on char boundaries, behaves in every respect like a rope of exactly its text — including
  line counts when the slice splits a CRLF pair — and so does a slice of the slice; `Rope::from`
  and `String::from` a slice; byte ranges off a char boundary are refused. KNOWN FAILURE ropey/1,
  intermittent (needs the byte-range form and an end between CR and LF).
- `byte_slices_count_lines_like_char_slices`: a slice by byte range equals the slice by the same
  char range in every respect, with the range end aimed at CRs followed by LF. KNOWN FAILURE
  ropey/1, intermittent (a CI run passed it); the deterministic pin is
  `pin_byte_slice_ending_in_a_split_crlf_counts_the_cr` (a 3 KB text sliced by byte range up to
  a CR).
- `comparisons_and_hash_match_strings`: `==`, `Ord` (byte-wise like `str`) and `Hash` on ropes
  and slices agree with the strings whatever the chunk structure (the same text built two ways),
  including comparisons with `&str`/`String`/`Cow` in both directions, rope vs slice, prefix
  ordering, `Display`.
- `builders_and_conversions_round_trip`: `RopeBuilder` fed arbitrary pieces, `From`/`FromIterator`
  from `&str`/`String`/`Cow`, `From<Rope>` for `String`/`Cow`, `from_reader` over a reader with
  arbitrary short reads (multi-byte chars split across reads) then `write_to`; invalid UTF-8 from
  the reader is an `InvalidData` error; an empty rope has one line.
- `str_utils_agree_with_the_model`: `byte_to_char_idx`, `char_to_byte_idx`, `byte_to_line_idx`,
  `char_to_line_idx`, `line_to_byte_idx`, `line_to_char_idx` on plain strings, including their
  documented clamping of past-the-end indices.

The per-slice check (`check_slice`) covers `len_bytes/chars/lines/utf16_cu`; `byte_to_char`,
`char_to_byte`, `byte_to_line`, `char_to_line`, `char_to_utf16_cu`, `utf16_cu_to_char` at every
position (mid-char bytes and mid-surrogate code units rounding down as documented); `byte`,
`char`, `line`, `line_to_byte`, `line_to_char` for every index; `bytes`/`chars`/`lines`/`chunks`
forwards, from the middle (`*_at`), backwards (`reversed()` from an end iterator, `prev()`, a
forward walk `reverse()`d) and their `ExactSizeIterator::len`; `as_str`; `chunk_at_byte` for
every byte (mid-char too), `chunk_at_char`, `chunk_at_line_break` (the chunk contains the index,
starts on a char boundary, offsets right) and `chunks_at_byte`.

Text is drawn from an alphabet of ASCII, 2-, 3- and 4-byte chars and every recognised line break
(LF, CR, VT, FF, NEL, LS, PS — so CRLF pairs, lone CRs and pairs split by edits or slices are
common).

## Oracles

A `String` mirror of every edit and a model of the documented line-break rules (LF, CRLF as one
break, CR, VT, FF, NEL, LS, PS with the default `unicode_lines`; the start of the text and every
position after a break start a line; a break belongs to the line it ends), from which every index
conversion, line and iterator result is derived. `RopeSlice`s are compared with the model on the
slice's own text. The crate's `assert_integrity`/`assert_invariants` check the tree itself.

## Not tested

The `cr_lines`-only and LF-only feature configurations, `simd` off, the default chunk size
(the same code with bigger leaves; ropey/1 was confirmed there by hand on a 3 KiB text),
`Rope::from_reader` with reader errors, `RopeBuilder::_append_chunk`/`_finish_no_fix` (hidden),
upstream's own `tests/` suite.

## History

- 2026-09-13: written in the zoo against `199266599096` (2026-09-09, "Fix bug in std::cmp::Ord
  implementation."; 1.6.1 + master) with hegeltest 0.44.1. Three test defects fixed on the way
  (`Debug` lists chunks; `reversed()` flips direction in place, it is not `rev()`; mid-char
  bytes round down). Clean at 3 × 6 000 cases; at 10 000 cases per property: **ropey/1** — a
  `byte_slice` ending between the CR and LF of a CRLF pair undercounts `len_lines()` when it
  spans more than one leaf (`new_with_byte_range` lacks the `is_crlf_split` adjustment that
  `slice()` got in 1.5.1); confirmed with default features on a 3 KiB text. Not reported
  upstream.
