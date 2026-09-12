# strsim

[rapidfuzz/strsim-rs](https://github.com/rapidfuzz/strsim-rs).

## What is tested

**`tests/lib.rs`**
- `hegel_identity_all_metrics`: Identity axiom: every distance is 0 (and every similarity is exactly 1.0) when comparing a string with itself.
- `hegel_symmetry_all_metrics`: Symmetry axiom: d(a, b) == d(b, a) for every metric in the crate. (Exact float equality is intended: swapping the arguments only swaps commutative float additions.)
- `hegel_edit_distance_chain_and_bounds`: The edit distances form a chain: damerau <= osa <= levenshtein (each allows strictly more/cheaper operations than the next), all are bounded below by the length difference and above by max(len). For equal-length strings, levenshtein <= hamming (substituting every differing position is one way to edit one string into the other).
- `hegel_distance_zero_iff_equal`: Identity of indiscernibles: distance is zero if and only if the strings are equal (for the true edit distances).
- `hegel_triangle_inequality_true_metrics`: Triangle inequality for the two true metrics. levenshtein is a metric; damerau_levenshtein's docs explicitly state "the triangle inequality holds". (OSA is deliberately excluded — it does not satisfy it.)
- `hegel_single_edit_gives_distance_one`: A single insertion, deletion, or substitution (with a different char) yields distance exactly 1 for levenshtein, OSA, and Damerau-Levenshtein.
- `hegel_adjacent_transposition`: Swapping two adjacent distinct chars is one transposition: OSA and Damerau-Levenshtein give exactly 1, plain levenshtein gives exactly 2 (equal-length strings differing in exactly two positions can't be one edit apart), and hamming sees exactly the two swapped positions.
- `hegel_hamming_contract`: hamming's documented contract: Err(DifferentLengthArgs) iff the char counts differ, and otherwise Ok(number of positions whose chars differ) — never a panic.
- `hegel_jaro_winkler_bounds_and_prefix_bonus`: jaro and jaro_winkler stay in [0, 1]; the Winkler prefix bonus can only raise the score (jaro_winkler >= jaro), and it does not apply at all when jaro <= 0.7 or when there is no common first char.
- `hegel_normalized_scores_bounds`: The normalized scores stay in [0, 1] and hit exactly 1.0 iff the strings are equal ("1.0 means the strings are the same" per the docs).
- `hegel_damerau_implementations_agree`: The crate ships two independent Damerau-Levenshtein implementations: `damerau_levenshtein` (Zhao-Sahni linear-space algorithm) and `generic_damerau_levenshtein` (classic Lowrance-Wagner with a HashMap). They must agree on every input.
- `hegel_sorensen_dice_matches_reference`: sorensen_dice must match the documented bigram-based Dice coefficient. KNOWN FAILURE: sorensen_dice divides by *byte* lengths (`a.len() + b.len() - 2` on the whitespace-stripped `String`s) while the numerator counts *char* bigrams, so any non-ASCII character inflates the denominator and deflates the score. Minimal counterexample (found and shrunk by hegel): sorensen_dice("\u{80}aa", "aa") = 0.5, but the documented Dice coefficient is 2*1/(2+1) = 2/3. The `one_of!` branch below pins that counterexample so this test fails deterministically on every run until the bug is fixed.

## Oracles

## Not tested

## History

- 2025-11-27: predecessor base commit `dacc84c0dc61` (Fix clippy warnings).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/strsim.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
