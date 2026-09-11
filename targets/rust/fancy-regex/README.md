# fancy-regex

[fancy-regex/fancy-regex](https://github.com/fancy-regex/fancy-regex).

## What is tested

**`src/vm.rs`**
- `state_save_hegel`: (no doc comment)

**`tests/captures.rs`**
- `prop_plain_subset_captures_agree_with_regex_crate`: On the plain-regex subset, fancy-regex's `captures` must agree with the `regex` crate on the presence of a match, the number of groups, and the exact span of every group — including with the backtracking VM forced via a no-op lookahead prefix (which adds no groups).
- `prop_capture_names_never_panics_known_failure`: KNOWN FAILURE — pins a real bug in fancy-regex; deliberately left failing. `Regex::capture_names()` panics with an index-out-of-bounds for any *delegated* pattern in which a named group is repeated `{0}` times. Root cause: the delegated `regex` program elides `(?<n>a){0}` entirely, so `captures_len()` is 1, but fancy-regex's own parse recorded `named_groups["n"] == 1`, and `capture_names()` writes `names[1]` into a `Vec` of length 1 (src/lib.rs:1643). Minimal reproducer:     fancy_regex::Regex::new("(?<n>a){0}").unwrap().capture_names(); The generator below constructs the failing shape directly so the test fails deterministically on every run.
- `prop_captures_group0_equals_find`: For arbitrary fancy patterns, group 0 of `captures` must have exactly the span reported by `find`.

**`tests/finding.rs`**
- `prop_plain_subset_find_agrees_with_regex_crate`: On the plain-regex subset, fancy-regex's `find` must return exactly the same span as the `regex` crate — on the delegation fast path and with the backtracking VM forced via a no-op lookahead prefix.
- `prop_find_iter_spans_wellformed`: `find_iter` (with full fancy features in play) must yield spans that are in bounds, on char boundaries, non-overlapping and in increasing order, and its first item must equal `find`.
- `prop_matched_text_rematches_anchored`: For plain patterns with no anchors or word boundaries, matching is context-free: the matched substring, taken alone, must re-match the pattern anchored at both ends.

**`tests/matching.rs`**
- `prop_plain_subset_is_match_agrees_with_regex_crate`: On the plain-regex subset (no lookaround, no backreferences), fancy-regex must agree with the `regex` crate about whether a haystack matches — both on the delegation fast path and when the backtracking VM is forced by prefixing a no-op lookahead.
- `prop_compile_never_panics`: Compiling an arbitrary pattern string must never panic — it either succeeds or returns an error. Supplements fuzz/fuzz_targets/fuzz_parser.rs with near-valid patterns (a valid generated pattern with random edits), which reach much deeper than uniformly random text.
- `prop_match_never_panics`: Matching with a successfully compiled pattern must never panic on any haystack: every entry point returns Ok or a runtime error.
- `prop_backtrack_limit_errors_instead_of_hanging`: Catastrophic backtracking must hit the documented backtrack limit and return `RuntimeError::BacktrackLimitExceeded` instead of hanging.
- `prop_escape_then_match_roundtrip`: `escape` round-trip: escaping arbitrary text yields a pattern that compiles and matches exactly that text, in full, at position 0.

## Oracles

## Not tested

## History

- 2026-07-05: predecessor base commit `d00f0f7a2382` (Merge pull request #263 from fancy-regex/anchored_search).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/fancy-regex.patch`).
- 2026-09-11: imported into the zoo; ported to hegeltest 0.44.1.
