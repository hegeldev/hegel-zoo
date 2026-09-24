# fancy-regex

[fancy-regex/fancy-regex](https://github.com/fancy-regex/fancy-regex).

## What is tested

**`src/vm.rs`**
- `state_save_hegel`: (no doc comment)

**`tests/captures.rs`**
- `prop_plain_subset_captures_agree_with_regex_crate`: On the plain-regex subset, fancy-regex's `captures` must agree with the `regex` crate on the presence of a match, the number of groups, and the exact span of every group — including with the backtracking VM forced via a no-op lookahead prefix (which adds no groups).
- `prop_capture_names_never_panics_known_failure`: KNOWN FAILURE — pins a real bug in fancy-regex; deliberately left failing. `Regex::capture_names()` panics with an index-out-of-bounds for any *delegated* pattern in which a named group is repeated `{0}` times. Root cause: the delegated `regex` program elides `(?<n>a){0}` entirely, so `captures_len()` is 1, but fancy-regex's own parse recorded `named_groups["n"] == 1`, and `capture_names()` writes `names[1]` into a `Vec` of length 1 (src/lib.rs:1643). Minimal reproducer:     fancy_regex::Regex::new("(?<n>a){0}").unwrap().capture_names(); The generator below constructs the failing shape directly so the test fails deterministically on every run.
- `prop_captures_group0_equals_find`: For arbitrary fancy patterns, group 0 of `captures` must have exactly the span reported by `find`.
- `starred_group_of_a_lazy_repeat_captures_like_regex`: pin of fancy-regex/2 (expected failure).

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

The `regex` crate on the plain subset (no lookaround, no backreferences), on the delegation path and with the backtracking VM forced by a no-op lookahead prefix.

## Bugs (see `bugs.toml`)

| id | severity | title |
|---|---|---|
| fancy-regex/1 | medium | `capture_names()` panics for a delegated pattern with a `{0}`-repeated named group (fixed upstream in 0.19.2, 857c92c2f9f7) |
| fancy-regex/2 | low | a capturing group whose body is one lazy unbounded repeat, repeated with `*`, is rewritten `(X*?)*` -> `(X*?)?` before delegation, so the group's span differs from the regex crate's |

## Not bugs (tolerated)

- Engines do not agree on the capture of a final empty iteration of a repeated group. `\b` and `\B` are always hard, so a plain pattern holding one runs on fancy-regex's VM, which keeps that capture as Perl and Python do: `(a|\b)*` on `a` gives group 1 = (1, 1) where the `regex` crate gives (0, 1) (and (1, 1) itself for `(a|\b){0,3}`); `(a|)*`, whose group is delegated whole, gives the regex crate's (0, 1). For a repeated group holding a word boundary the captures property compares presence, group count and group 0 only (3% of plain patterns).
- regex-syntax elides a capturing group repeated `{0}` (`(a){0}` has one group for the regex crate, two for fancy-regex's parser and for Python); for such a pattern fancy-regex may report more groups than the oracle (the VM path always, the delegation path when a `\b`/`\B` sends the pattern to the VM), and the extra groups must be unset.
- fancy-regex refuses a quantifier on a non-capturing or flag group around an empty expression (`(?:)*` is TargetNotRepeatable) which the regex crate accepts; the generator never quantifies one. A variable-width lookbehind whose body holds a group that a backreference names is a documented `FeatureNotYetSupported` (0.08% of fancy patterns, skipped).

## Not tested

## History

- 2026-07-05: predecessor base commit `d00f0f7a2382` (Merge pull request #263 from fancy-regex/anchored_search).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/fancy-regex.patch`).
- 2026-09-11: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped d00f0f7a2382 → 6d43a32c8de1 (2026-09-06, "CHANGELOG: Add Unreleased section"; 0.19.1); 1 bug(s) still reproduce; add/add conflicts in tests/matching.rs resolved by keeping both sides. 640 tests pass.
- 2026-09-13: base bumped 6d43a32c8de1 → e2684857abcf (2026-09-13, "Version 0.19.2"; 0.19.2); 1 bug(s) still reproduce; add/add conflicts in tests/common/mod.rs, tests/matching.rs resolved by keeping both sides. 657 tests pass.
- 2026-09-16: base bumped e2684857abcf → b4ba488d23da (2026-09-16, "Merge pull request #282 from Keats/giallo-changes"; 0.19.2); 1 bug(s) still reproduce. 662 tests pass.
- 2026-09-18: base bumped b4ba488d23da → 857c92c2f9f7 (2026-09-18, "Merge pull request #279 from chiliec/fix-capture-names-zero-repeat"; 0.19.2); 0 bug(s) still reproduce; fixed upstream: fancy-regex/1. 663 tests pass.
- 2026-09-24: generators rewritten in combinator style (patterns as syntax trees rendered by pure functions: `Alt`/`Piece`/`Atom` for the plain subset through `recursive`, `Fancy` items with numbered groups for the fancy features, a `Hit` that splices a witness of the pattern into the haystack); three latent model gaps closed (`(?:(?:))*`-style empty groups quantified, a backreference into a lookbehind, the `{0}` elision on the VM path) and the empty-iteration tolerance above added; fancy-regex/2 found by the rewrite's 2000-case runs. 664 tests pass, 1 expected failure.
