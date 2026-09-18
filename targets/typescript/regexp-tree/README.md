# typescript/regexp-tree — DmitrySoshnikov/regexp-tree (against V8)

regexp-tree is the regular-expression processor behind ESLint's `no-useless-escape`-style
rules, `eslint-plugin-regexp` and webpack's `regexp-minifier`: a parser for ECMAScript regexes
(flags `gimsuyd` plus the non-standard `x`), an AST traverser and transformer, an optimizer
(some thirty rewrite passes), a compatibility transpiler that rewrites named groups, the `s`
flag and the `x` flag for older engines (with a `RegExpTree` runtime wrapper that restores the
`groups` object), and a finite-automaton interpreter (regex → NFA → DFA → `test`) for the
classical subset. The patch checks all of these against the JavaScript engine itself — V8 in
Node 22, through `new RegExp` and `exec` — and pins 34 bugs.

## How it is built

`src/` is plain CommonJS and the library has no runtime dependencies; the published `dist/` is
only babel output of it. Nothing is built: the tests `createRequire` `src/regexp-tree.js`. The
setup installs Hegel under `.hegel/` with `npm install --prefix .hegel`; the upstream tree and
its lock file stay untouched.

## How it is tested

`hegel/hegel.test.mjs` runs under `node --test`; `hegel/hegel-zoo.mjs` is the zoo's shared
harness and `hegel/gen.mjs` the generators: a grammar-driven regex generator (alternatives,
groups of every kind including named groups and lookbehind, classes with ranges and escapes,
`\p{..}` properties, all quantifier forms, greedy and lazy, backreferences numbered and named,
the assertions) with an alphabet that includes case-folding traps (`ſ`, `K`, `ß`, `é`), a
literal `ε`, an astral emoji and the parser's own special characters; a flag generator; a
mutation step that deletes, duplicates or inserts a piece at a random position (so invalid
regexes are tried too); and a smaller generator for the automaton subset (`a b c x`, `|`,
groups, `* + ?`).

The oracle is V8: whether `new RegExp(source, flags)` accepts a pattern, what `exec` returns on
generated inputs (index, captures and `groups`), how many groups a pattern has (`(?:src)|`
against the empty string) and what they are named.

| Property | What it checks |
|---|---|
| `TestHegelParserAcceptsWhatV8Accepts` | `parse` accepts exactly the patterns `new RegExp` accepts, 40% of them mutated into near-misses |
| `TestHegelGenerateReproducesTheSource` | `generate(parse(re))` is the source text (up to `{n,n}` → `{n}`) or at least a regex V8 treats identically |
| `TestHegelAstDescribesTheRegexV8Runs` | groups (count, numbers, names) and backreferences match V8's; every `Char` node's `codePoint`/`symbol` is the character V8 matches; with `captureLocations` each node's `loc` covers exactly its generated text |
| `TestHegelOptimizePreservesTheMatches` | `optimize` yields a valid regex with the same `exec` results on generated inputs; `toString`, `getSource`/`getFlags` and `toRegExp` agree; a second `optimize` is a fixed point |
| `TestHegelCompatTranspilePreservesTheMatches` | `compatTranspile` and `exec` give V8's results, named groups included; with the `x` flag, a whitespace-and-comment version of the pattern transpiles to the same regex as the plain one |
| `TestHegelTransformAndToRegExpAgree` | `transform` with a no-op handler set keeps the regex; `toRegExp(re)` is `new RegExp` on every accepted pattern |
| `TestHegelFiniteAutomatonAgreesWithV8` | `fa.toNFA(re).matches(s)`, `fa.toDFA(re).matches(s)` and `fa.test(re, s)` equal `^(?:re)$` in V8 |

`TestHegelPin…` are plain tests, one per bug in `bugs.toml`. The properties gate (and count)
the shapes of the known bugs by the text of the pattern — a legacy octal escape without the u
flag, an astral literal under u, a `\k` to a name not yet defined, an empty alternative given
to the automaton builder, and so on — so that every mismatch they report is new. The
generator never produces a `\k<name>` with a non-ASCII name that no earlier group defines,
because the parser then never returns (regexp-tree/32); that pin runs `parse` in a worker
thread with a three-second limit.

## Bugs (34)

See `bugs.toml`. By component: the parser accepts what V8 rejects or the reverse in nine
places (u-mode lone brackets and legacy escapes, `[\d-z]` as a range, `\k` to an undefined
name, quantified lookaheads, `[\B]`, `\u{..}` in group names, Unicode 12.1 property tables,
control escapes without a code point); it decodes escapes wrongly in seven (legacy octal as
decimal so that `\40` means `(`, `\8`/`\9` as control characters, `\08` as one character,
forward references numbered and named as literal text, `\c1` as `c1`, astral literals as two
surrogates) and gets two locations wrong; the optimizer changes the language of a regex in
eight ways (`[b^]` → `[^b]`, `a{0}` → `a*`, characters moved into a class without re-escaping,
İ → i, `(?=a)(?=a)` → `(?=a){2}`, unescaping `}` and `]` under u, `toString` naming a different
regex from `getSource`, the `x` flag kept for `toRegExp`); `generate` throws on trees holding
an array node and the x-mode lexer cannot end on a comment; `exec` adds `groups: {}`; and the
automaton interpreter starts in the wrong DFA state (`/a*b/` rejects "b"), takes the literal
`ε` for its epsilon symbol and crashes on empty alternatives. The parser hanging forever on
`\k<π>` (regexp-tree/32) is the one that matters for anyone parsing untrusted patterns.

## Not tested

The `v` flag (not among the documented flags; not attempted), the `dist/` build (babel output
of the same source), the ESLint-oriented helpers that are not in the public API, and the
optimizer's individual transforms as units (they are exercised only through `optimize`).

## Notes

- Everything is measured against Node 22's V8 with ECMAScript 2024 Annex B semantics (the
  `RegExp` constructor without the u flag is the Annex B grammar). Where the spec and Annex B
  differ, V8's behaviour is the reference.
- Not bugs: `generate` sorts flags; `{n,n}` is spelled `{n}`; in x-mode a literal space atom
  is dropped by design (the property spells one as `[ ]`).

## History

- 2026-09-18: created against 0.1.27 (06e849a3); 34 bugs found.
