# regexp2

[dlclark/regexp2](https://github.com/dlclark/regexp2) (`github.com/dlclark/regexp2/v2`) is a
backtracking regular-expression engine ported from .NET's `System.Text.RegularExpressions`:
lookarounds, backreferences, atomic groups, possessive quantifiers, conditionals, `\X`, a
`RE2` compatibility option, an `ECMAScript` option, right-to-left matching, `Replace`/`Split`
with .NET semantics, and a `compat` package with `regexp.Regexp`'s method signatures. Pinned at
9d0d2ffe88a8 = v2.8.0 (2026-09-07). MIT. No CONTRIBUTING.md or AI policy ("bug reports and
pull requests with tests are welcome"); not archived. Checked 2026-09-15. Upstream carries the
.NET, PCRE, RE2 and rust-regex corpora as table tests plus a fuzz test.

## Oracles

- **Perl 5.38**, held open as a child over JSON lines, for the default (.NET/Perl) syntax: the
  first match from a start position (`pos` + `//g`) and the `//g` sequence, each group's last
  capture as (index, length) in characters. The grammar renders every pattern for .NET, Perl
  and RE2 at once: literals (ASCII, `é`, `日`, `😀`, `\n`), `.`, `\d\w\s` and negations,
  bracket classes, `^ $ \A \z \Z \b \B`, capturing/named/non-capturing/atomic groups,
  lookahead and fixed-length lookbehind, numbered and named backreferences, greedy/lazy/
  possessive quantifiers, `i`/`m`/`s` flags; texts over `a b A 0 1 space \n - é É 日 😀`.
- **Go's `regexp`** for the RE2-expressible subset through the `compat` adapter and the `RE2`
  option, every method (`Match*`, `Find*`, `FindAll*` with n ∈ {-1, 0, 1, 2}, string/byte/
  reader variants) compared exactly.
- **Models**: `Replace`/`ReplaceFunc` and `Split` against the documented rules applied over
  the engine's own `FindStringMatch`/`FindNextMatch` sequence; `GetGroupNames`/`GetGroupNumbers`/
  `GroupNameFromNumber`/`GroupNumberFromName` against the .NET numbering rule (and textual
  order under `OptionMaintainCaptureOrder`); `RightToLeft` existence of a match equals
  left-to-right for patterns without backreferences, atomic groups, possessive quantifiers or
  lookarounds; `Escape`/`Unescape`.

Where the engines legitimately differ the properties do not judge: the restart after an empty
match (.NET moves one position, Perl retries non-empty), `^` under `m` after a final newline
(.NET matches there, Perl does not), an empty iteration of a loop whose body can match empty
(.NET takes one and keeps its captures, Perl and RE2 do not: `(a*|)*` on "a" captures "" in
.NET and "a" in RE2; `(?:a*?|b*?)*b+?` on "abb" is [0 3] for RE2 and [0 2] for .NET and Perl),
and captures inside a negative lookahead (Perl keeps those of the failed body, .NET discards
them). Perl 5.38's own optimiser answers wrongly for three shapes, which are not judged against
it either: a possessive quantifier in an alternation (`a*?日+?^|a*+|` on "a" gives 0+0, though
`a*+` matches "a"), a lazy quantifier directly before a literal above U+00FF (`a*?日|A+` on
"AA" gives two one-character matches; `A+` must take "AA"), and under `/i` a lookahead over a
quantified literal (`(?i)(?=b*)a` on "a" finds nothing).

## Properties

- `TestHegelFirstMatchAgreesWithPerl` — `FindRunesMatchStartingAt` from every start and
  `FindStringMatch` from 0: group 0 and every participating group equal Perl's. Clean, once the
  start positions the search filter drops (regexp2/1, detected by re-matching anchored with
  `\G`) and `\B` after a loop of non-word characters (regexp2/8) are set aside.
- `TestHegelMatchSequenceAgreesWithPerl` — the `FindNextMatch` chain equals Perl's `//g`
  sequence when no match is empty. Clean, same provisos.
- `TestHegelCompatAdapterMatchesGoRegexp` — 30 method/limit combinations equal `regexp`'s
  on the RE2 subset. Clean, with regexp2/1, /2 (nil vs empty), /6 (`\b` with non-ASCII letters),
  /7 (mixed named/unnamed groups, judged with `OptionMaintainCaptureOrder`) and /8 set aside.
- `TestHegelReplaceAndSplitFollowTheMatchSequence` — `Replace`, `ReplaceFunc` (templates with
  `$$ $& $\` $' $_ $n ${n} ${name}`) and `Split` follow the match sequence and the count
  limits (Replace count 0 and Split counts above 1 pinned; Split with non-participating groups
  pinned). Clean.
- `TestHegelGroupNumberingFollowsTheDotNetRule` — clean.
- `TestHegelRightToLeftFindsTheSameTexts` — clean (regexp2/1 and /8 set aside).
- `TestHegelEscapeRoundTrips` — clean.

## Bugs

| id | severity | title |
|----|----------|-------|
| regexp2/1 | high | A branch beginning with a literal or positive class before a branch beginning with `.` or a negated class is never matched: the first-character filter merges the two sets into a negation (`a\|.` does not match "a") |
| regexp2/2 | low | compat's `FindAll`, `FindAllIndex` and `FindAllStringIndex` return an empty non-nil slice, not nil, when n is positive and nothing matches |
| regexp2/3 | medium | `Replace` and `ReplaceFunc` with count 0 return the empty string instead of the input |
| regexp2/4 | medium | `Split`'s count is the number of matches used, not the number of pieces: count 2 makes two splits and exactly one split is unreachable |
| regexp2/5 | low | `Split` adds an empty string for every capturing group that did not take part in the match |
| regexp2/6 | medium | In RE2 mode `\b` and `\B` use Unicode word characters while `\w` is ASCII, so the compat adapter disagrees with `regexp` around accented and CJK letters |
| regexp2/7 | low | compat returns submatches in .NET group order (unnamed first) when named and unnamed groups are mixed, permuting them against `regexp` |
| regexp2/8 | medium | A greedy loop of non-word characters followed by `\B` is made atomic, so `\D+\B`, `\W+\B` and `-+\B` never give back a character: `\D+\B` finds nothing in "ba" |

## Not bugs

- Group numbering puts unnamed groups first (`(?<y>\d{4})-(\d{2})` → names `0, 1, y`): .NET's
  rule, documented, with `OptionMaintainCaptureOrder()` to opt out.
- After an empty match the next search starts one position on (`x*` over "ab" gives four
  matches); `Replace` and `Split` act at each: .NET semantics.
- `Multiline` `^` matches after a trailing newline: .NET semantics (Perl differs).
- `GetGroupNames` returns numbers as strings for unnamed groups; `GroupNumberFromName` is -1
  for an unknown name and `GroupNameFromNumber` "" for an unknown number.
