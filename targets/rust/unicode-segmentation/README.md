# unicode-segmentation

[unicode-rs/unicode-segmentation](https://github.com/unicode-rs/unicode-segmentation).

## What is tested

**`src/word.rs`**
- `hegel_ascii_matches_unicode_word_indices`: Fast path must equal general path for any ASCII input. (Port of `proptest_ascii_matches_unicode_word_indices`.)
- `hegel_ascii_matches_unicode_word_indices_rev`: Fast path must equal general path for any ASCII input, backwards. (Port of `proptest_ascii_matches_unicode_word_indices_rev`.)

**`tests/test.rs`**
- `hegel_graphemes_concat_is_identity`: Property: concatenating the graphemes (extended or legacy) of a string reproduces the string exactly. (Port of `quickcheck_join_graphemes`.)
- `hegel_word_bounds_concat_is_identity`: Property (documented on `split_word_bounds`): "The concatenation of the substrings returned by this function is just the original string." (Port of `quickcheck_join_words`.)
- `hegel_sentence_bounds_concat_is_identity`: Property (documented on `split_sentence_bounds`): "The concatenation of the substrings returned by this function is just the original string."
- `hegel_graphemes_forward_reverse_agree`: Property: reverse (double-ended) iteration agrees with forward iteration for `graphemes` and `grapheme_indices`, in both extended and legacy mode. (Port of `quickcheck_forward_reverse_graphemes_{extended,legacy}`.)
- `hegel_word_bounds_forward_reverse_agree`: Property: reverse (double-ended) iteration agrees with forward iteration for `split_word_bounds` and `split_word_bound_indices`. (Port of `quickcheck_forward_reverse_words`.)
- `hegel_grapheme_indices_are_consistent`: Property: `grapheme_indices` yields consecutive offsets whose segments are the slices of the input, and agrees with `graphemes`.
- `hegel_word_bound_indices_are_consistent`: Property: `split_word_bound_indices` yields consecutive offsets whose segments are the slices of the input, and agrees with `split_word_bounds`.
- `hegel_sentence_bound_indices_are_consistent`: Property: `split_sentence_bound_indices` yields consecutive offsets whose segments are the slices of the input, and agrees with `split_sentence_bounds`.
- `hegel_unicode_words_match_filtered_word_bounds`: Property (documented on `unicode_words`): the words are exactly the `split_word_bounds` substrings containing at least one char with the Alphabetic property or General_Category=Number — i.e. exactly `char::is_alphanumeric`. The crate moved to Unicode 18.0.0 at 346f36a while the standard library (rustc 1.98) is on 17.0.0, and the crate then uses its own tables, so strings containing a code point Unicode 18 added to Alphabetic or Number (32 ranges, the set difference of the crate's tables) are assumed away until std catches up (`std_knows` in the patch; it lets everything through once `char::UNICODE_VERSION` reaches 18). Also exercises the ASCII fast path taken by `unicode_words` on all-ASCII input, and checks `unicode_word_indices` agrees.
- `hegel_unicode_sentences_match_filtered_sentence_bounds`: Property (documented on `unicode_sentences`): the sentences are exactly the `split_sentence_bounds` substrings containing at least one alphanumeric char (see `hegel_unicode_words_match_filtered_word_bounds`).
- `hegel_cursor_is_boundary_agrees_with_iterator`: Property: `GraphemeCursor::is_boundary`, queried with the whole string as one chunk at every char boundary (reusing one cursor via `set_cursor`), agrees with the boundary set implied by `grapheme_indices`.
- `hegel_cursor_next_boundary_chunked_agrees_with_iterator`: Property: driving `GraphemeCursor::next_boundary` forward over arbitrary chunk splits (answering `NextChunk`/`PreContext` requests) visits exactly the boundaries reported by `grapheme_indices`. Chunked cursor use across rule-relevant boundaries (e.g. GB11 across a chunk split) is the risky code path. KNOWN FAILURE (suspected library bug, GB12/GB13 analogue of the GB11 chunk-boundary bug fixed in 9a42b9d): for s = "0\u{1f1e6}\u{1f1e6}" with chunks [(0, "0\u{1f1e6}"), (5, "\u{1f1e6}")], `next_boundary` reports a boundary at 5, splitting the flag grapheme "\u{1f1e6}\u{1f1e6}". `next_boundary`'s forward pass counts the first RI (`ris_count = Some(1)`), then `is_boundary` at offset == chunk_start requests pre-context anyway, and `handle_regional` seeds its backward scan with the existing count, counting the same RI twice; the even parity wrongly yields a break. A fresh cursor's `is_boundary` at offset 5 correctly returns false.
- `hegel_cursor_state_machine_agrees_with_iterator`: Property (stateful model test): interleaved `next_boundary`, `prev_boundary`, `set_cursor` and `is_boundary` calls on one cursor always agree with the boundary set from `grapheme_indices`. Mixed-direction use exercises the cursor's cached-state resumption paths.
- `hegel_cursor_prev_boundary_chunked_agrees_with_iterator`: Property: driving `GraphemeCursor::prev_boundary` backward over arbitrary chunk splits (answering `PrevChunk`/`PreContext` requests) visits exactly the boundaries reported by `grapheme_indices`, in reverse.
- `known_failure_gb12_chunk_split_double_counts_regional_indicators`: deterministic pin of unicode-segmentation/1 (the report's minimal counterexample: a chunk split between two regional indicators makes `next_boundary` break inside a flag grapheme); added by the zoo.

## Oracles

## Not tested

## History

- 2026-06-01: predecessor base commit `66a032fd8d66` (Publish 1.13.3).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/unicode-segmentation.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1. The predecessor's KNOWN FAILURE was the
  property `hegel_cursor_next_boundary_chunked_agrees_with_iterator`, which passed at the default case
  count under 0.44.1 (the bug needs the chunk split between the two RIs); the zoo added the deterministic
  pin `known_failure_gb12_chunk_split_double_counts_regional_indicators` from the report's counterexample.
- 2026-09-13: base bumped 66a032fd8d66 → 048d51fe1d9b (2026-09-02, "Apply GB5 before GB9b in GraphemeCursor::provide_context (#180)"; 1.13.3); 0 bug(s) still reproduce; fixed upstream: unicode-segmentation/1. 59 tests pass. PR #180 changed provide_context so an RI already counted by the forward pass is not re-counted by the backward scan; its regression test `test_grapheme_cursor_ris_count_across_chunks` is exactly the zoo's counterexample.
- 2026-09-17: base bumped 048d51fe1d9b → 346f36a42592 (2026-09-17, "feat: Upgrade to Unicode 18.0.0 (#184)"; 1.13.3); 0 bug(s) still reproduce. 65 tests pass.
