# typescript/picomatch — micromatch/picomatch (glob matching)

Hegel property tests for [`picomatch`](https://github.com/micromatch/picomatch) 4.0.7, pinned at
`9fab7bf6` (master, 2026-08-27), the glob matcher under micromatch, fast-glob, chokidar, Vite,
ESLint and much else (~200M weekly downloads). Plain CommonJS, no dependencies, MIT. No
AI-contribution policy is published (README and `.github/contributing.md` checked 2026-09-16); the
zoo only records bugs.

Tests are `test/hegel.test.mjs` (ESM, run by `node --test`) with the zoo's harness
`test/hegel-zoo.mjs` and the generators and oracle bridge `test/hegel-glob.mjs`. Hegel is
`@hegeldev/hegel` 0.4.5, installed by the backend's default `npm install --no-save`. The
differential needs `bash` ≥ 4.4 on PATH (`globstar`, `extglob`, `nullglob`, `dotglob`, `nocaseglob`).

## How it is tested

- **bash as the oracle** (`TestHegelMatchesLikeBashGlobbing`): a random pattern of 1–4 segments —
  literals, `*`, `?`, bracket expressions (lists, ranges, negations, POSIX classes with `posix`,
  awkward forms such as `[]a]` and `[a\-b]`), extglobs `@( ) *( ) +( ) ?( )`, brace lists, escaped
  specials and `**` segments — is generated together with candidate paths built from the atoms'
  solutions, their mutations (segments added, dropped, extended, truncated, dotted, re-cased) and
  random names. The paths are materialised as files and directories in a scratch tree and bash lists
  what the pattern expands to (`dotglob`/`nocaseglob` mirror `dot`/`nocase`); `picomatch.isMatch`
  must agree on every path. The README's documented deviations from bash are respected by
  construction (no negated extglobs, `(?` never generated, `{a}` without a comma is literal) and its
  remaining limits are listed below. This property found bugs 2, 3, 5, 6 and 7, and after the
  2026-09-23 rewrite of the generators in combinator style its 1000-3000-case runs found 8 and 9.
- **The API agrees with itself** (`TestHegelApiIsConsistent`): `isMatch`, the matcher function,
  `makeRe(...).test`, `picomatch.test(...)`, the state-returning matcher and `contains`/`capture`
  give one answer; `!pattern` is the complement (and literal under `nonegate`); an array of patterns
  is the union; `ignore` subtracts; `nocase` equals lower-casing both sides; `basename` matches the
  last segment; `onResult`/`onMatch`/`onIgnore` fire once per input/match/ignored input;
  `maxLength` rejects long patterns with a `SyntaxError`.
- **Disabled features are literal, and `scan` describes the pattern**
  (`TestHegelDisabledFeaturesAreLiteral`): under `noextglob`/`nobrace`/`nobracket` a pattern made of
  that feature matches its own text; a pattern without glob atoms matches exactly its literal (also
  under `nocase`); `scan()` reports `isGlob` iff the pattern has a glob atom, `prefix + base + "/" +
  glob` rebuilds the input, `isGlob` agrees with `parts: true`, everything the pattern matches is
  the base or lies below it, `negated` is set for `!pattern`, and `parts` rebuild the pattern. This
  property found bugs 1 and 4.
- **`picomatch/posix` and `windows`** (`TestHegelPosixEntryPointAgrees`): the dependency-free
  entry point answers as the main one, and a path with backslashes matches under `windows: true`
  exactly when its slash form matches. This property found bug 10 in the 2026-09-23 long runs.

Under `ZOO_COLLECT=1` the counts show which bug shapes and oracle limits the generator reached and
how many mismatches had no known shape; the recorded bugs are skipped by shape (`Known` in the test
file) so the properties stay strict on everything else, and each has a pin. Rounds of 300–1000
cases per property were run until a round added nothing.

## What was found (10 bugs, `bugs.toml`)

| id | severity | title |
|---|---|---|
| picomatch/1 | medium | `scan()` stops at a brace group without a comma: `a{b}/*.js` is reported as not a glob, with no base/glob split |
| picomatch/2 | medium | a trailing `/**` does not match the parent segment when it ends in a star: `c*/**` rejects `cx` (while `cx/**`, `c?/**`, `[c]x/**` accept it) |
| picomatch/3 | medium | a star after a leading extglob or brace group that can match the empty string matches dotfiles: `*(b)*`, `?(b)*`, `@(b|)*`, `{b,}*` match `.a` |
| picomatch/4 | medium | `scan()` takes an escaped `\{` for a brace group: `isBrace` true, and without a closing brace the rest of the pattern is swallowed |
| picomatch/5 | medium | a `?` right after `)` is a regex quantifier, not a one-character wildcard: `@(a)?` matches `a` and rejects `ab` |
| picomatch/6 | medium | `**` next to a brace group or `@(…)` in one segment crosses path separators: `**{b,c}x` and `**@(b)x` match `a/bx`, `@(a)**` matches `ax/c` |
| picomatch/7 | low | `a/**/?(b)` matches the bare `a`: the optional `/**/` lets the pattern end before a group that can match nothing |
| picomatch/8 | medium | a negated bracket expression holding a POSIX class matches the separator: `a[![:upper:]]b` matches `a/b` |
| picomatch/9 | medium | a POSIX class after a leading `**/` blocks an explicit dotfile segment: `**/.a/[[:digit:]]` rejects `.a/0` |
| picomatch/10 | low | under `windows: true` a negated bracket matches a backslash kept before a glob-special character: `a[!a]*` matches `a\*` |

Bugs 2, 3, 5, 6, 7, 8 and 9 are in the parser/regex generation (`lib/parse.js`), 1 and 4 in the fast
scanner (`lib/scan.js`) that fast-glob-style consumers use to split a pattern into a static base and
a glob, and 10 in the windows path normalisation (`lib/utils.js` with `lib/constants.js`).

## Oracle limits and documented behaviour (not recorded)

- Bash's pathname expansion needs a directory for a trailing `/**`, while picomatch documents that
  `foo/**` matches `foo`; the oracle also lists the matches of the pattern with its trailing `/**`
  segments removed.
- `nocaseglob` applies only to path components that contain glob characters (literal components
  are looked up as written), so `nocase` is only generated for patterns whose every segment has a
  glob atom; and bash folds case differently from a regex `i` flag inside bracket expressions
  (`[[:lower:]]` and `[a-d]` do not match `Z`/`D` under `nocaseglob`, `[^[:lower:]]` does), so not
  with brackets either.
- A bracket expression at the start of a segment may match a leading dot in picomatch (its own
  tests assert `[[:punct:]]` matches `.`); bash requires a literal dot. Skipped when it occurs.
- `?()` (an extglob with no alternatives) matches nothing in bash and behaves like `?(…)` with an
  empty alternative in picomatch; not generated.
- Documented deviations respected by the generator: negated extglobs (`!(…)`) are not greedy in
  picomatch; `(?` opens a regex group ("regex features"); `{a}` without a comma is literal;
  `+(a||b)`, `+(a|aa)` and other "risky" repeated extglobs are turned literal by the
  `maxExtglobRecursion` safeguard (the differential skips a pattern when `maxExtglobRecursion:
  false` changes its regex).
- `maxLength` limits the *pattern* (parse.js throws `Input length: N, exceeds maximum allowed
  length: M` for the glob); the README's option table says "the input string", which elsewhere in
  the README is the string being tested. Doc-only inconsistency, so not recorded.
- A leading `./` in a pattern is stripped (documented); `.` and `..` segments are not generated.
