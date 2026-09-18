# re2j

[google/re2j](https://github.com/google/re2j) (BSD-3-Clause): RE2/J, the Java port of Go's
`regexp` — linear-time matching with the `java.util.regex` API shape (`Pattern`, `Matcher`,
`PatternSyntaxException`, RE2 syntax with `(?P<name>…)` and `(?<name>…)` groups, `Pattern.quote`,
`split`, `namedGroups()`, `LONGEST_MATCH`, and a `byte[]` UTF-8 input API). Pinned at
`951a6159` (build.gradle version 1.8, ten commits after `re2j-1.7`, 2026-05-22). Upstream builds
with Gradle, so the patch's Maven module `hegel/` compiles the library's own sources
(`java/com/google/re2j`, minus `module-info.java` and the GWT `super/` sources) as its main
sources via `<sourceDirectory>` and `[run] setup = []`; the harness `Zoo.java`, the judge's
`ZooListener` and the tests live in `hegel/src/test/java/zoo/`.

## What is tested

`Rx.java` generates patterns as a small AST over the syntax the two engines share — literals from
a 19-character alphabet (ASCII letters and digits, space, newline, escaped metacharacters, `é`,
`K`/`k`/`s`/`ſ` for case folding, the supplementary character `𝒳`), `.`, bracket classes, the
`\d \w \s \p{L} \p{Lu} \p{N} \x41 \x{e9} \Qa.b\E` escapes, the anchors `^ $ \b \B \A \z`,
sequences, alternations (sometimes with an empty branch), capturing, non-capturing, named and
flag groups `(?i: (?s: (?m: (?-i: …)`, and the repetitions `* + ? {2} {1,} {0,2} {1,3} {0} {0,0}
{2,2}`, greedy or lazy — and renders each pattern once for RE2/J and once for `java.util.regex`
(only the named-group spelling and the `u` after `i` differ). Inputs are short strings over the
same alphabet; flags `CASE_INSENSITIVE` (with `UNICODE_CASE` on the Java side), `DOTALL` and
`MULTILINE` are drawn at random.

`Re2jTest`:

- **findAndGroupsAgreeWithJavaUtilRegex** — both engines accept or both reject; `groupCount`,
  `namedGroups()`, `pattern()`/`flags()`; the whole `find()` loop with every group span, group
  strings by number and name, `matches`, `Pattern.matches`, `lookingAt`, `find(int)` from every
  position; after the loop has failed, `group()` throws.
- **splitAgreesWithJavaUtilRegex** — `split(input, limit)` for limits -1, 0, 1, 2, 3 and
  `split(input)`.
- **replacementAgreesWithJavaUtilRegex** — random replacement templates (`$0`, `$n`, `${name}`,
  `\$`, `\\`, literals) through `replaceAll`, `replaceFirst`, an `appendReplacement`/`appendTail`
  loop, and `quoteReplacement`.
- **quoteIsLiteralAndByteInputAgreesWithChars** — `Pattern.quote` against Java's; the `byte[]`
  UTF-8 API against the `String` API on the same input (match spans converted to characters,
  group strings, `matches()`); `equals`/`hashCode`.
- **flagsAndLongestMatchAreConsistent** — inline flags against `compile` flags; `LONGEST_MATCH`
  starts where the first-match pattern does, ends no earlier, and finds a match iff the other
  does; `matches ⇒ lookingAt`, a first match spanning the input ⇒ `matches`.
- **caseInsensitiveLiteralAndClassAgree** — `(?i)X` and `(?i)[X]` accept the same code points over
  random `X` from all planes, and both agree with `java.util.regex`'s `(?iu)X`.
- **junkPatternsAreRejectedOrWork** — random edits of a generated pattern either throw
  `PatternSyntaxException` or compile and match without any other exception or error.

`Re2jPinsTest` — one plain JUnit test per recorded bug.

## Oracles

`java.util.regex` is the oracle on the shared syntax; the documented differences between RE2 and
Perl-style engines are gated, and each gate applies only when the two results differ:

| gate | RE2 (and RE2/J) | java.util.regex |
| --- | --- | --- |
| `empty-iteration-capture` | no extra empty iteration of a repeated nullable group: `(a*)+` on "aa" leaves group 1 = 0-2, `(^){0,2}` sets group 1 = 0-0 | one more empty iteration: 2-2, and -1 for the second |
| `unicode-case-folding` | `(?i)` applies simple case folding to every class, so `(?i)\w` and `(?i)[a-z]` match `ſ` (U+017F) | `\w` and the class stay ASCII |
| `dollar-before-final-newline` | `$` without `(?m)` only at the very end | also before a final "\n" |
| `multiline-caret-at-end-of-text` | `(?m)^` also at the end of the text (after a trailing "\n", or on "") | never at the end of the input |
| `java-unicode-word-boundary` | `\b`/`\B` are ASCII (like `\w`): `é` and `ſ` are not word characters | `\b` uses `Character.isLetterOrDigit`, so `é` is a word character (while `\w` stays ASCII), and an empty `\B` match falls between the two surrogates of `𝒳` |

Go's `regexp` (the code RE2/J is a port of) adjudicated the disputed cases by hand — a small Go
program run locally, not part of the committed tests — and decides what "correct" means for the
RE2-specific bugs (split, repeat limits, `[[:]`, invalid UTF-8, `(?i)[X]`).

## Bugs

See `bugs.toml`. `split` of an input made only of delimiters returns `[""]` (1). The `byte[]`
API: a signed-byte comparison makes every non-ASCII character look like the start of the text to
`^ \A \b` (2), `find()` after an empty match advances one byte and matches inside a character (3),
reading a group re-runs the match over a truncated window in which `$` matches and changes
`group()`/`end()` (7), and invalid UTF-8 bytes swallow the following byte or end the input (10).
Captures: a group inside `{0}` is reported as 0-0 (4), `${name}` of a non-participating group
inserts "null" (5), a repetition at the root of the pattern that simplification rewrites loses
`namedGroups()` and `group(name)` (6). `Matcher` contract: a failed `find()` leaves the previous match readable (8),
malformed replacement templates are accepted silently (9). Limits: `matches()` overflows the stack
on `(?:(?:a?){1000}){10}` (11), nested repeat counts have no product limit so `((a{100}){100}){100}`
is a million instructions (12), 20 000 nested parentheses overflow the stack in `compile` (13).
Syntax: `[[:]` and `[[:]]` are rejected (14), `(?i)[X]` stops folding above U+1044F while `(?i)X`
does not (15), an unbalanced `)` is reported as an internal error (16).

## Not tested

Performance (linear-time guarantee, `programSize()` bounds), the GWT super-sources, the
`(?U)`-style Perl flags RE2 does not support, `java.util.regex` features RE2/J lists as unsupported
(regions, `hitEnd`, `MatchResult`, `CANON_EQ`, `COMMENTS`, `LITERAL`).

## Notes

- RE2/J accepts `\é` (a backslash before a non-ASCII letter), which Go rejects as an invalid
  escape and `java.util.regex` accepts; not recorded, since nothing observable depends on it.
- `(?m)^` on an empty input matches in RE2 and RE2/J and does not in `java.util.regex`; gated as
  `multiline-caret-at-end-of-text` with the trailing-newline case.
- `PatternSyntaxException.getPattern()` shows the pattern with the flag prefix `compile` prepends
  (`(?i)a(` for `compile("a(", CASE_INSENSITIVE)`); not recorded.

## History

- 2026-09-18: created at 951a6159 (1.8) with 7 properties and 16 bugs.
