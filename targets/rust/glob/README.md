# glob

[rust-lang/glob](https://github.com/rust-lang/glob).

## What is tested

**`src/lib.rs`**
- `prop_pattern_new_never_panics`: Property: `Pattern::new` returns `Ok` or `PatternError` for arbitrary input; it never panics (parse robustness).
- `prop_escape_roundtrip_matches_original`: Property (from `Pattern::escape`'s docs): "The resulting string will, when compiled into a `Pattern`, match the input string".
- `prop_escape_matches_nothing_else`: Property (from `Pattern::escape`'s docs): the escaped pattern matches the input string "and nothing else" — in particular not a string one edit (insert/remove/replace a char) away from the original.
- `prop_literal_pattern_matches_exactly_itself`: Property: a pattern containing no metacharacters consists solely of `Char` tokens (see the debug_assert in `fill_todo`), and literal matching under default options on unix is exact character equality, so such a pattern matches a string iff it equals the pattern.
- `prop_matches_agrees_with_matches_with_default_options`: Property (from `Pattern::matches`'s docs): `matches` uses the default match options, i.e. it agrees with `matches_with(_, MatchOptions::new())`.
- `prop_matcher_agrees_with_naive_reference`: Property: `?`, `*`, `[...]`, `[!...]` and literal semantics (from the `Pattern` docs), including `require_literal_separator` and `require_literal_leading_dot` (from the `MatchOptions` docs), agree with a naive backtracking reference matcher over a small alphabet. Case sensitivity is exercised by separate properties.
- `prop_case_insensitive_literal_matches_any_casing`: Property (from `MatchOptions::case_sensitive`'s docs: upper/lower case relationships between ASCII characters are ignored when false): an escaped ASCII literal matches any per-character re-casing of itself under case-insensitive options.
- `prop_case_sensitive_match_implies_case_insensitive_match`: Property: for patterns without negated classes, turning off `case_sensitive` only widens per-character acceptance (`chars_eq` and `in_char_specifiers` add ASCII-case matches, never remove any), so a case-sensitive match implies a case-insensitive match. Negated classes are excluded because they invert acceptance: `[!a]` matches "A" case-sensitively but not case-insensitively (see test_pattern_matches_case_insensitive_range).
- `prop_recursive_wildcard_matches_any_directory_prefix`: Property (from the `Pattern` docs: `**` "matches the current directory and arbitrary subdirectories", and test_recursive_wildcards: `**/test` matches "test", "one/test", "one/two/test"): a pattern `**/<name>` matches `<name>` prefixed by any sequence of directory components.

**`tests/glob-std.rs`**
- `prop_glob_returns_exactly_the_matching_directory_entries`: Property (from `glob()`'s docs: returns "all the `Path`s that match the given pattern", "Paths are yielded in alphabetical order"): for a fresh directory with a known set of entries, `glob(<dir>/<component>)` yields exactly the entries whose file name satisfies `Pattern::new(<component>).matches(name)`, sorted.

## Oracles

## Not tested

## History

- 2026-07-21: predecessor base commit `cfa2a58f2e44` (chore: release v0.3.4).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/glob.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
