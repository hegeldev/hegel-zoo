# typescript/minimatch — isaacs/minimatch (glob matching)

Hegel property tests for [`minimatch`](https://github.com/isaacs/minimatch) 10.2.6, pinned at
`ded1bbd0` (main, 2026-07-27), the glob matcher used by npm, glob, ESLint, Mocha and much else
(~300M weekly downloads). TypeScript sources, one runtime dependency (`brace-expansion`),
BlueOak-1.0.0. No AI-contribution policy is published (README and `.github/` checked 2026-09-16);
the zoo only records bugs.

Tests are `test/hegel.test.mjs` (ESM, run by `node --test`) with the zoo's harness
`test/hegel-zoo.mjs` and the generators and oracle bridge `test/hegel-glob.mjs` (shared with the
picomatch target, adapted). Hegel is `@hegeldev/hegel` 0.4.5.

## How it is built

`dist/` is not committed (tshy builds it on `prepare`), so the setup installs Hegel, TypeScript
5.9.3 and `brace-expansion@5.0.12` (the version the lockfile resolves) and compiles `src/` into
`.hegel/dist` as CommonJS with `test/tsconfig.hegel.json`; the tests `require()` that build. The
differentials need `bash` ≥ 4.4 on PATH.

## How it is tested

- **bash as the oracle** (`TestHegelMatchesLikeBashGlobbing`): random patterns of 1–4 segments
  (literals, `*`, `?`, bracket expressions incl. POSIX classes and awkward forms, extglobs `@( )
  *( ) +( ) ?( )`, brace lists, escaped specials, `**` segments) with candidate paths built from
  the atoms' solutions, their mutations and random names; the paths are materialised in a scratch
  tree and bash lists what the pattern expands to (`dotglob`/`nocaseglob` mirror `dot`/`nocase`).
  minimatch is given a directory path with a trailing slash, as bash lists it (`a/**` matches `a/`,
  not `a`). This property found bugs 3 and 8.
- **Brace expansion against bash** (`TestHegelBraceExpansionAgreesWithBash`): random brace
  expressions — comma lists (nested, single-item, with empty items), numeric sequences (negative,
  zero-padded, stepped, descending), letter sequences — must expand to bash's list in bash's order
  (`set -f; printf '%s\0' <expr>`); `nobrace` returns the expression; the `Minimatch.set` has at
  most one row per distinct expansion; every expansion is matched by the expression. Found bug 7.
- **The API agrees with itself** (`TestHegelApiIsConsistent`): `minimatch`, `Minimatch#match`,
  `filter`, `match(list)` and `makeRe().test` give one answer; `!pattern` is the complement,
  `flipNegate` undoes it, `nonegate` makes `!` literal; `#pattern` is a comment, literal under
  `nocomment` or as `\#`; `optimizationLevel` 0/1/2 agree on plain paths; a trailing slash and
  doubled slashes are ignored; backslashes are separators under `platform: "win32"`; every prefix
  of a match is a `partial` match; `nocase` equals lower-casing both sides (no brackets);
  `matchBase` matches the basename; `noglobstar` turns `**` into `*`; `hasMagic()` is true iff a
  part is not a literal (braces only with `magicalBraces`); `noext`/`nobrace` make the feature
  literal; a pattern without magic matches exactly its literal. Found bugs 2, 4, 5, 6 and 9.
- **`escape` makes a literal pattern** (`TestHegelEscapeMakesALiteralPattern`): for a random
  string of letters and every special character, `escape(s, {magicalBraces: true})` matches `s`
  and none of its one-edit mutations, `hasMagic()` is false, and `unescape` undoes `escape` in both
  brace modes. Found bug 1.

Under `ZOO_COLLECT=1` the counts show which bug shapes and oracle limits the generator reached and
how many mismatches had no known shape; the recorded bugs are skipped by shape (`Known` in the test
file) so the properties stay strict on everything else, and each has a pin.

## What was found (9 bugs, `bugs.toml`)

| id | severity | title |
|---|---|---|
| minimatch/1 | medium | `escape()` leaves a leading `!` or `#` alone: the escaped pattern negates or is a comment |
| minimatch/2 | medium | a POSIX class plus a literal `-`, `#`, comma or space throws a `SyntaxError` (`\-`/`\#` are invalid escapes under the `u` flag); `makeRe()` returns false |
| minimatch/3 | medium | an escaped character after a leading `*`/`?` never matches: `*1\}` rejects `01}` (the fast-path test keeps the backslash) |
| minimatch/4 | medium | `makeRe()` drops a trailing `/**` when an earlier segment is `**`: `a/**/b/**` rejects `a/x/b/y` |
| minimatch/5 | medium | `makeRe()`'s `**` admits a dotfile directly below its parent: `a/**` matches `a/.b`, `a/**/c` matches `a/.b/c` |
| minimatch/6 | low | `makeRe()` of `a/**` matches the bare `a` while `match()` does not |
| minimatch/7 | medium | a comma-less brace pair stops brace expansion: `{ac}{1..3}` and `{{1..3}}` stay unexpanded (in `brace-expansion` 5.0.12) |
| minimatch/8 | medium | a star after a leading extglob that can match nothing matches dotfiles: `*(b)*`, `?(b)*`, `@(b|)*` match `.a` |
| minimatch/9 | low | a trailing slash satisfies a final `?(…)`/`*(…)` part: `a/b/` matches `a/b/?(x)` and `**/?(x)` though not `a/b/*` |

Bugs 4–6 are all disagreements between `makeRe()` (the README's "single regular expression
expressing the entire pattern") and `match()`; 3 is in the fast-path test of `parse()`; 8 is in the
AST's dot guard (the same shape as picomatch/3); 7 is in the dependency `brace-expansion`, reached
through `minimatch.braceExpand` and the `Minimatch.set`.

## Oracle limits and documented behaviour (not recorded)

- bash's `nocaseglob` applies only to path components with glob characters and folds case inside
  bracket expressions differently from a regex `i` flag, so `nocase` is only generated for
  all-glob, bracket-free patterns.
- A pattern's first segment `**` changes meaning when prefixed (`!**` is `!*`), so the `nonegate`
  and `nocomment` checks skip such patterns.
- Documented deviations respected by the generator: negated extglobs (`!(…)`) differ from bash in
  the greedy case; extglob nesting beyond `maxExtglobRecursion` (2) is not parsed; `{a}` without a
  comma is literal; `optimizationLevel: 2` may reject through `makeRe()` what `match()` accepts
  when the path has `.`/`..` segments (none are generated).
- `escape()` does not escape braces unless `magicalBraces` is set (documented in `escape.ts`); the
  strict round trip is checked with `magicalBraces: true` and the default mode only for strings
  without braces.
- POSIX classes match the full Unicode range in minimatch (`[[:alpha:]]` matches `é`, documented);
  the generator's solutions stay ASCII.
