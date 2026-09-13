# regex-lite

[rust-lang/regex](https://github.com/rust-lang/regex), crate `regex-lite` (workspace member
`regex-lite/`): the small, fast-compiling regex engine that the crate docs describe as "intended to
be a drop-in replacement for the `regex` crate" apart from a short list of documented differences
(ASCII-only Perl classes, word boundaries and case folding; no `\p{..}`; no class set operations;
no octal; `&str` haystacks only; no `RegexSet`; opaque errors).

Written in the zoo (not imported from the predecessor).

## What is tested

**`regex-lite/tests/hegel.rs`**
- `find_agrees_with_regex`: `Regex::find_iter`, `find`, `find_at`, `is_match` and `is_match_at` report the same (byte-offset) matches as the `regex` crate.
- `captures_agree_with_regex`: Capture groups: names, counts and every group's span in every match agree with the `regex` crate; `Captures::name` agrees with indexing by number.
- `replacements_agree_with_regex`: `replace`, `replace_all` and `replacen` with a `&str` replacement (capture interpolation included) produce the same string as the `regex` crate.
- `split_agrees_with_regex`: `split` and `splitn` agree with the `regex` crate.
- `shortest_match_is_consistent`: `shortest_match` is documented to return *an* end offset of the leftmost match, possibly before `find`'s end; so it must exist exactly when `find` finds something, and lie within that match. Its existence must also agree with the `regex` crate.
- `random_pattern_acceptance_agrees_with_regex`: Random *strings* as patterns: both crates accept or reject the same pattern (the documented differences — `\p{..}`, class set operations, the `u` flag, octal — are kept out of the alphabet or assumed away), and when both accept it, they find the same matches. This covers syntax the structured generator never writes (odd escapes, `{,n}`, empty groups, nested repetitions, ...).
- `escape_is_literal`: `escape` agrees with the `regex` crate, and the escaped text compiles to a regex that finds exactly the leftmost non-overlapping literal occurrences.
- `known_bug_case_insensitive_range_spanning_cases`: KNOWN FAILURE (regex-lite/1). A bracket range spanning both letter cases is only half folded under `(?i)`: `ClassRange::ascii_case_fold` folds the `a-z` part of the range and returns, so the `A-Z` part of `[A-a]` is never lower-cased. `(?i)[A-a]` contains `B`..`Z`, so case-insensitively it must match every lowercase letter (`B` ∈ `[A-a]`, and the `regex` crate agrees); regex-lite matches none of `b`..`z`, and the negated class `(?i)[^A-a]` matches all of them.
- `known_bug_case_insensitive_negated_posix_class`: KNOWN FAILURE (regex-lite/2). A negated POSIX class is negated *before* case folding: `maybe_parse_posix_class` negates `[:^lower:]` to "anything but `a-z`" and only then does `(?i)` fold the class, which adds `a-z` back, so `(?i)[[:^lower:]]` matches every character. The crate documents `[[:^lower:]]` as `[^a-z]`, and its own `(?i)[^a-z]` folds before negating (the parser comments on why) and matches no letter at all — as does the `regex` crate for both spellings. Same for `[[:^upper:]]`.

The differential properties draw a small regex AST (literals, `.`, Perl and POSIX classes, bracket
classes with ranges, all ten empty assertions, concatenation, alternation, greedy and lazy
repetitions with bounds, capturing/non-capturing/named groups, inline flags `imsUR`) and print it
twice: verbatim for `regex-lite`, and for `regex` with each Perl class written out as the ASCII
bracket the `regex-lite` docs define it as and each word boundary wrapped in `(?-u:..)`. Builder
options (`case_insensitive`, `multi_line`, `dot_matches_new_line`, `swap_greed`, `crlf`) are drawn
and applied to both. Haystacks and literals come from an alphabet of ASCII letters, digits,
punctuation, `\n`, `\r`, `\t` and the caseless multi-byte scalars `☃` and `💩`, so that the
documented ASCII-vs-Unicode differences cannot show (only U+212A and U+017F fold to ASCII letters,
and neither can be drawn).

## Oracles

The `regex` crate itself (same workspace, so always the matching version), through the translation
above. `escape_is_literal` additionally checks against naive substring search.

## Not tested

Verbose mode (`x`), `size_limit`/`nest_limit` behaviour, Unicode-specific behaviour (`\p{..}`,
Unicode case folding — documented not to be supported), `RegexBuilder` error messages (documented
opaque), performance.

## History

- 2026-09-13: written in the zoo against `72d650cb0a88` (2026-08-10, "automata: replace uses of
  deprecated module integer constants"; regex-lite 0.1.9, regex 1.13.1) with hegeltest 0.44.1.
  Two bugs on the first run at `--test-cases 3000`: **regex-lite/1** (case-insensitive bracket
  ranges spanning both letter cases fold only their lowercase part: `(?i)[A-a]` does not match
  `b`..`z`) and **regex-lite/2** (a negated POSIX class is negated before case folding:
  `(?i)[[:^lower:]]` matches every letter). Each has a deterministic `known_bug_*` test; the six
  differential properties that can draw either pattern are pinned as intermittent. With both
  masked in a scratch run, 3 × 5000 cases found nothing else. 153 tests pass, 2 expected failures.
