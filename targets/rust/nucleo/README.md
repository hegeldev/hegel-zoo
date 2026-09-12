# nucleo

[helix-editor/nucleo](https://github.com/helix-editor/nucleo).

## What is tested

**`src/pattern/tests.rs`**
- `prop_pattern_parse_and_match_list_consistent`: `Pattern::parse` accepts arbitrary input without panicking, and `match_list` is consistent with `Pattern::score`: it returns exactly the items that score `Some`, with their scores, sorted in descending order.
- `prop_pattern_score_is_sum_of_atom_scores`: `Pattern::score` of a multi-atom pattern is the sum of its atoms' scores (and `None` as soon as one atom fails) -- this is how the docs describe multi-word matching.

**`src/tests.rs`**
- `prop_fuzzy_indices_form_matching_subsequence`: Fuzzy match indices are a strictly increasing, in-bounds subsequence of the haystack whose normalized characters spell out the needle (this is the check the existing `assert_matches` helper does for hand-picked cases, generalized to arbitrary inputs).
- `prop_contiguous_kind_indices_form_matching_window`: Substring/prefix/postfix/exact match indices are one contiguous in-bounds run mapping to the needle's characters.
- `prop_match_and_indices_variants_agree`: The `.._match` and `.._indices` variants of every algorithm agree: same Some/None decision, same score, and indices are produced exactly for matches of non-empty needles.
- `prop_fuzzy_match_iff_subsequence`: Fuzzy matching succeeds iff the needle is a subsequence of the normalized haystack (naive oracle). Holds for both the optimal and the greedy algorithm.
- `prop_substring_match_iff_contiguous_window`: Substring matching succeeds iff the needle matches a contiguous window of the normalized haystack (naive oracle).
- `prop_exact_match_oracle`: Exact matching succeeds iff the needle equals the normalized haystack after skipping whitespace on the sides where the needle itself is not whitespace.
- `prop_prefix_match_oracle`: Prefix matching succeeds iff the needle matches the normalized haystack right after its leading whitespace (which is only skipped when the needle does not itself start with whitespace).
- `prop_postfix_match_oracle`: Postfix matching succeeds iff the needle matches the normalized haystack right before its trailing whitespace (which is only skipped when the needle does not itself end with whitespace).
- `prop_match_kind_hierarchy`: The match kinds form a hierarchy: an exact match implies prefix and postfix matches, those imply a substring match, and a substring match implies both fuzzy matches.
- `prop_optimal_fuzzy_scores_at_least_greedy`: `fuzzy_match` is documented to find the match with the *highest* score, so it can never score below the greedy algorithm (which scores one particular match with the same scoring function). Both must agree on whether a match exists at all.
- `prop_ascii_and_unicode_representations_agree`: The same ASCII content must match the same way regardless of whether it is stored in the `Ascii` or the `Unicode` representation of `Utf32Str` (both are public and may be constructed directly).
- `prop_no_panic_on_arbitrary_input`: No algorithm panics on arbitrary unicode haystacks and (normalized) needles under arbitrary configurations.

**`src/utf32_str/tests.rs`**
- `prop_utf32_len_is_grapheme_count`: (no doc comment)
- `prop_utf32_ascii_variant_iff_ascii_graphemes`: Documented guarantees 1 and 2 of `Utf32Str`: a string of ASCII graphemes (ASCII without "\r\n") produces the `Ascii` variant holding exactly the original string; everything else produces the `Unicode` variant.

## Oracles

## Not tested

## History

- 2026-06-23: predecessor base commit `8c16d47cdfa9` (doc: Fix a typo).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/nucleo.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
