# glob

[gobwas/glob](https://github.com/gobwas/glob) is a Go glob matcher over plain strings:
`Compile(pattern, separators...)` builds a backtracking matcher tree for the syntax `*`
(non-separator run), `**` (anything), `?`, `[abc]`/`[a-c]`/`[!…]` classes, `{a,b}`
alternatives and `\c` escapes; `Pattern.Match(s)` matches the whole string. About 2 100 lines
without tests; the pinned commit is the September 2026 head, v1.0.0 plus two cosmetic commits.
MIT. No CONTRIBUTING or AI policy; not archived; 1 000 stars; 4 open issues. Checked
2026-09-15. Upstream already fuzzes `Match` against a regexp translation of the pattern
(`FuzzMatchRegexp`), so the matching engine is well covered; the zoo adds an independent
model, `path.Match`, bash and the API's edges.

## Oracle

Three, layered. (1) `path.Match` and `filepath.Match` with `/` as the only separator, on the
syntax they share: no groups, no `**`, classes without negation and without a `-` or leading
`^` in a set. (2) A reference matcher written from the grammar in `Compile`'s documentation
with the lexer's tie-breaks: a class is either one range `lo-hi` (the first character taken
verbatim, even a backslash) or a non-empty set with `\c` escapes, `!` negates only as the
first class character, `}` and `,` are literal outside a group; groups are expanded to a set
of flat patterns, each matched by a memoised backtracking walk over runes (literals compare
bytes, wildcards and classes decode one rune, an invalid byte being one U+FFFD). (3) bash 5.2
with `extglob` (`[[ $s == $p ]]`, `LC_ALL=C`) on printable-ASCII patterns without separators:
`*` and `**` become `*`, `{a,b}` becomes `@(a|b)`.

## Properties

- `TestHegelMatchAgreesWithPathMatch` — shared-syntax patterns with separator `/`: `Compile`
  fails exactly when `path.Match` does, `Match` equals `path.Match` and `filepath.Match`.
- `TestHegelMatchFollowsTheGrammar` — the full syntax with 0–3 separators drawn from
  `/ . : ö space a * NUL`, 8 % damaged patterns (raw meta characters, deletions, `[a-`, an
  invalid byte): `Compile` accepts exactly the grammar's patterns, otherwise a `*SyntaxError`
  with an offset inside the pattern; `Match` equals the model; `String()` and `Separators()`
  return what was compiled.
- `TestHegelSeparatorsOnlyRestrict` — adding a separator never adds a match, widening every
  `*` to `**` never removes one, and the pattern re-rendered from its parse matches the same.
- `TestHegelQuoteMetaRoundTrips` — `QuoteMeta(s)` compiles with any separators, matches `s`
  and not a different string, escapes exactly the meta characters and unescapes to `s`.
- `TestHegelMatchAgreesWithBash` — ASCII patterns without separators vs bash's extglob. The
  generator runs in a bash mode here: printable ASCII only, no `]`, `\`, `^` or `-` in a set
  and no leading `!`, no empty or stars-only alternative and no `*` right before a group
  (bash 5.2 reads `[!]` as a class, refuses `@(a|)` and does not match `x*@(a|*)` against
  `x`, unlike the grammar).
- `TestHegelMatchIsConcurrencySafe` — a backtracking pattern (pooled match state) answers
  the same from six goroutines as sequentially.

Twenty thousand cases per property before saving, 200 000 for the grammar, separator and
bash properties; strings are built as witnesses of the pattern and then mutated, 4 % get an
invalid byte. The path.Match property likewise generates its shared-syntax patterns directly
(a standard mode) and the concurrency property prepends `*a` to a stateless pattern, so no
property skips more than a few per cent of its cases — hegel's filter-too-much health check
otherwise fails the run, and `hegel.Test` reports that with a bare `--- FAIL` and no text. The generators never draw an invalid rune value as a separator (glob/1) and the
QuoteMeta property does not embed the quoted string in a group or class (glob/2); the
grammar property checks a syntax error's offset, not its reason (glob/3).

## Bugs (3; details in bugs.toml)

| id | severity | shape |
|----|----------|-------|
| glob/1 | low | `Compile("*", -1)` stops at U+FFFD and invalid bytes, `Compile("?", -1)` does not: an invalid separator rune is U+FFFD for the star's `IndexAny` only |
| glob/2 | low | `{` + `QuoteMeta("a,b")` + `,zz}` is three alternatives: `,` is not escaped though `\,` is accepted everywhere (same for `!`/`-` in a class) |
| glob/3 | low | `Compile("[\xff]")` says "unexpected end of input", `Compile("\\\xff")` "trailing backslash" — the UTF-8 error is overwritten |

## Not bugs (documented or design)

- `test/**/*` does not match `test/file` with separator `/` (open issue #46): `**` is any
  sequence and the two slashes are literal, exactly as documented; the model agrees.
- `{a}` is a group of one, `{}` matches the empty string, `{,a}` has an empty alternative —
  all by the grammar (bash's extglob disagrees on empty alternatives).
- A class is one range or one set: `[a-cx]` and `[a-c-e]` are syntax errors, `[ab-c]` is the
  set `{a, b, -, c}`, `[!-a]` the negated set `{-, a}`; a range starting with `!` cannot be
  written (documented: `!` negates as the first character).
- `Separators()` returns the slice given, so `Compile("a", []rune{}...)` returns an empty
  non-nil slice where the doc says "nil when there are none".
- `Match("*??", "€")` is false where `path.Match` says true: the standard library retries a
  star at byte offsets and lets `?` take the split bytes of a rune; gobwas matches runes, as
  documented. The path.Match property skips non-ASCII strings when the pattern has a `*`.
- Invalid UTF-8 in the pattern is a syntax error; in the string an invalid byte is one
  character for `?`, `*` and classes (matching `[!a]` and `[�]`) and never equals a literal.
