# bstr

[BurntSushi/bstr](https://github.com/BurntSushi/bstr).

## What is tested

**`src/escape_bytes.rs`**
- `prop_escape_unescape_roundtrip`: `unescape_bytes` is documented as the dual of `escape_bytes`: unescaping an escaped byte string reproduces the original bytes, for arbitrary (including invalid UTF-8) input.

**`src/ext_slice.rs`**
- `prop_to_str_lossy_agrees_with_std`: `to_str_lossy` (and `to_str_lossy_into`) agree with `String::from_utf8_lossy`, which documents the same "substitution of maximal subparts" strategy.
- `prop_char_decoding_apis_agree`: `char_indices` tiles the input exactly, agrees with `chars`, and their concatenation is the lossy decoding of the input.
- `prop_char_iteration_reverses`: Reverse iteration (which uses the separate `decode_last` code path) yields exactly the reverse of forward iteration.
- `prop_lines_with_terminator_concat_is_identity`: Documented guarantee: concatenating everything yielded by `lines_with_terminator` reproduces the original byte string.
- `prop_lines_agree_with_std`: On valid UTF-8, `lines` agrees with `str::lines` from std.
- `prop_fields_agrees_with_std_split_whitespace`: (no doc comment)
- `prop_trim_agrees_with_char_predicate`: (no doc comment)
- `prop_split_join_roundtrip`: `join` is the inverse of both `split_str` and `rsplit_str`, and no yielded element contains the (non-empty) splitter. Note that `rsplit_str` is *not* asserted to be the exact reverse of `split_str`: for self-overlapping separators the two directions legitimately pick different non-overlapping match sets (e.g. `b"\xC2\x80\xC2\x80\xC2\x80".split_str(b"\xC2\x80\xC2")`), just like `str::split` vs `str::rsplit` in std.
- `prop_splitn_consistent_with_split`: `splitn_str`/`rsplitn_str` are consistent with `split_str`/ `rsplit_str`: the first `n - 1` pieces match and the last piece is the joined remainder.
- `prop_find_rfind_agree_with_naive_scan`: `find`/`rfind` (and the `Finder`/`FinderReverse` types) agree with a naive scan.
- `prop_find_iter_matches_naive_scan`: `find_iter`/`rfind_iter` yield exactly the greedy non-overlapping matches computed by a naive scan.
- `prop_replace_agrees_with_std`: On valid UTF-8 with a non-empty needle, `replace`/`replacen` agree with `str::replace`/`str::replacen`. (Empty needles are excluded: bstr documents byte-oriented empty-needle splitting, while std is char-oriented.)
- `prop_ascii_case_conversion_agrees_with_std`: (no doc comment)
- `prop_case_conversion_idempotent`: (no doc comment)

**`src/unicode/grapheme.rs`**
- `prop_grapheme_indices_tile_input`: `grapheme_indices` tiles the input exactly, each grapheme not containing a replacement codepoint is the exact decoding of the bytes it spans, and the concatenation of all graphemes is the lossy decoding of the input.
- `prop_grapheme_iteration_reverses`: Documented guarantee: reverse iteration yields exactly the same grapheme clusters, in reverse order.

**`src/unicode/sentence.rs`**
- `prop_sentences_tile_input`: Documented guarantee: concatenating everything yielded by `sentences` results in the original string. The ranges yielded by `sentence_indices` must tile the input. Restricted to valid UTF-8 because invalid UTF-8 trips the bug pinned by `known_failure_sentences_drop_input_after_invalid_utf8` above.

**`src/unicode/word.rs`**
- `prop_words_with_breaks_tile_input`: Documented guarantee: concatenating everything yielded by `words_with_break_indices` results in the original string, modulo replacement codepoint substitutions (i.e. the lossy decoding of the input). The yielded ranges must tile the input.

## Oracles

## Not tested

## History

- 2026-07-15: predecessor base commit `08a77375dfa8` (doc: add AI Policy (#232)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/bstr.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
