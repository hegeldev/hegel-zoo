# crop

[noib3/crop](https://github.com/noib3/crop).

## What is tested

**`tests/graphemes.rs`**
- `graphemes_concat_matches_original`: (no doc comment)

**`tests/iterators.rs`**
- `iter_chunks_concat_matches_original`: Concatenating the chunks of a `Rope` reproduces the exact text it was built from (this is how the crate-level docs suggest writing a `Rope` to disk).
- `iter_lines_match_str_lines`: The `Lines` iterator agrees with `str::lines()` in both directions (the crate's fuzz target asserts the forward direction after every edit).
- `iter_raw_lines_concat_matches_original`: Concatenating the lines returned by `RawLines` (terminators included) reproduces the original text, per the `raw_lines()` docs.
- `iter_chars_match_str_chars`: The `Chars` iterator agrees with `str::chars()` in both directions.

**`tests/rope_builder.rs`**
- `builder_matches_appended_text`: A `Rope` built by appending arbitrary fragments equals both the concatenated `String` and the `Rope` created directly from it.
- `rope_from_str_to_string_roundtrip`: `String` -> `Rope` -> `String` is the identity, for the full Unicode domain.

**`tests/rope_indexing.rs`**
- `byte_of_line_then_line_of_byte_roundtrip`: `byte_of_line()` returns the offset of the *start* of a line, so feeding it back to `line_of_byte()` must return the original line index (for every existing line, i.e. `line_index < line_len()`).
- `line_of_byte_documented_panics`: `line_of_byte()`'s "# Panics" section only lists out-of-bounds offsets (greater than `byte_len()`), and its example even queries an offset in the middle of a `"\r\n"` pair, so per the docs any `offset <= byte_len()` is valid and returns the line the byte belongs to. KNOWN FAILURE: `line_of_byte()` panics with "byte offset 1 is not a char boundary" on `Rope::from("\u{80}").line_of_byte(1)`. The char-boundary requirement is enforced (via `GapBuffer::assert_char_boundary` in `RawLineMetric::measure_up_to`, src/rope/metrics.rs) but is not documented, unlike e.g. `insert()`/`byte_slice()` whose docs spell out their code-point-boundary panics. Either the docs or the behavior is wrong; this test pins the documented contract.

**`tests/rope_replace.rs`**
- `rope_edits_match_string_model`: (no doc comment)

**`tests/slicing.rs`**
- `byte_slices_match_str_slices`: Property-based version of `byte_slice_random`: repeatedly byte-slicing a `Rope`/`RopeSlice` of arbitrary Unicode text always matches the equivalent `str` slice.
- `line_slices_match_str_slices`: `line_slice(start..end)` returns exactly the text between the start of line `start` and the start of line `end` (line terminators included), per the `line_slice()` docs.

**`tests/utf16_conversion.rs`**
- `utf16_len_matches_char_sum`: `utf16_len()` equals the sum of `char::len_utf16()` over the text, which is the definition given in the `utf16-metric` feature docs.
- `utf16_code_unit_of_byte_matches_model`: `utf16_code_unit_of_byte()` matches the UTF-16 length of the text preceding the byte offset.
- `byte_of_utf16_code_unit_matches_model`: `byte_of_utf16_code_unit()` is the inverse of `utf16_code_unit_of_byte()` at every char boundary.

## Oracles

## Not tested

## History

- 2026-03-02: predecessor base commit `d0234ce772eb` (Fix `offset` in `UnitsBackward::remainder()`).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/crop.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-12: base bumped d0234ce772eb → 291ebca637a1 (2026-08-23, "Fix data race in concurrent `Rope` mutation"; 0.4.3); 1 bug(s) still reproduce. 174 tests pass.
