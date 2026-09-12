# aho-corasick

[BurntSushi/aho-corasick](https://github.com/BurntSushi/aho-corasick).

## What is tested

**`src/tests.rs`**
- `hegel_standard_find_iter_agrees_with_naive`: (no doc comment)
- `hegel_leftmost_first_find_iter_agrees_with_naive`: (no doc comment)
- `hegel_leftmost_longest_find_iter_agrees_with_naive`: (no doc comment)
- `hegel_anchored_find_iter_agrees_with_naive`: Anchored searches must agree with the naive scanner restricted to matches that begin exactly where each search starts.
- `hegel_overlapping_iter_reports_every_occurrence`: An overlapping search must report *every* occurrence of *every* pattern, in order of (end, start, pattern ID). Empty patterns are excluded because of a known bug pinned by `hegel_known_bug_overlapping_duplicates_empty_matches` below: with an empty pattern, overlapping searches report duplicate empty matches.
- `hegel_is_match_iff_find_iff_find_iter`: `is_match`, `find` and `find_iter` must be consistent with each other and with the naive occurrence scan, for both anchored and unanchored searches and a drawn start-of-search position.
- `hegel_replace_all_bytes_agrees_with_naive_splice`: `replace_all_bytes` must equal a naive left-to-right splice of the naive scanner's non-overlapping matches.
- `hegel_all_backends_report_identical_matches`: Every automaton backend (auto-selected, noncontiguous NFA, contiguous NFA, DFA) crossed with prefilter and byte-class settings must report exactly the same matches.
- `hegel_ascii_case_insensitive_agrees_with_naive_folded`: An ASCII-case-insensitive searcher must behave exactly like a naive scan over the ASCII-lowercased patterns and haystack. The alphabet includes `@`/`` ` `` and `[`/`{`, which differ by 0x20 like ASCII letter pairs do but must NOT be folded.
- `hegel_stream_find_iter_agrees_with_naive`: `stream_find_iter` (standard semantics only, no empty patterns) must agree with the naive scanner, including across the stream buffer's 64KB roll boundary and for arbitrary read-chunk schedules.
- `hegel_packed_searcher_agrees_with_naive_leftmost`: The packed searcher (Teddy/Rabin-Karp SIMD fast paths, a completely separate implementation from the AC automatons and not covered by the fuzz target) must agree with the naive leftmost scanners.
- `hegel_known_bug_leftmost_ignores_leftmost_empty_match`: KNOWN FAILURE: leftmost searches do not report the leftmost match when the leftmost match is an empty match and a non-empty pattern matches later. `MatchKind::LeftmostFirst`/`LeftmostLongest` document that "the leftmost match kind always prefers the leftmost match among all possible matches". With patterns `["ab", ""]` and haystack `"aab"`, the leftmost match is the empty match at offset 0 (pattern 1) — the regex `ab|` reports exactly that — but `find_iter` reports only `(0, 1, 3)`, a match starting at offset 1. The behavior is also internally inconsistent: with patterns `["b", ""]` and haystack `"ab"` (where the automaton dies at offset 0 instead of walking into a later full match), the leftmost empty match IS reported. The cause is in `try_find_fwd_imp` in `src/automaton.rs`: the pending empty match recorded for the start state is unconditionally overwritten by any later match, even though that match starts further right. All backends (noncontiguous NFA, contiguous NFA, DFA) share the bug.
- `hegel_known_bug_overlapping_duplicates_empty_matches`: KNOWN FAILURE: overlapping searches report duplicate empty matches. With patterns `["", "ab"]` and haystack `"ab"`, `find_overlapping_iter` reports `(0, 2, 2)` twice: `[(0,0,0), (0,1,1), (1,0,2), (0,2,2), (0,2,2)]`. The cause is in `NFA` construction (`src/nfa/noncontiguous.rs::fill_failure_transitions`): when the start state is a match state (an empty pattern exists), a state whose failure transition points at the start state receives the start state's matches twice — once via `copy_matches(fail, next)` when its parent is processed, and once via the unconditional `copy_matches(start_unanchored_id, id)` when it is processed itself. This needs a state of depth >= 2 whose failure state is the start state, which is why the hand-written `OVERLAPPING` tests above (all depth-1 patterns alongside the empty pattern) do not catch it. All backends share the bug.

## Oracles

## Not tested

## History

- 2026-04-21: predecessor base commit `c82178696b9d` (build(deps): bump actions/checkout in the actions group (#171)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/aho-corasick.patch`).
- 2026-09-11: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-12: base bumped c82178696b9d → 6c0abf5681bf (2026-08-10, "lint: remove uses of deprecated module integer constants"; 1.1.5); 2 bug(s) still reproduce. 276 tests pass.
