# typescript/pathe — unjs/pathe (universal `node:path` replacement)

Hegel property tests for [`pathe`](https://github.com/unjs/pathe) 2.0.3, pinned at `bc7477a0`
(main, 2026-07-08): the drop-in `node:path` replacement that normalises Windows paths to forward
slashes (`normalize`, `join`, `resolve`, `relative`, `dirname`, `basename`, `extname`, `parse`,
`format`, `isAbsolute`, `toNamespacedPath`, `matchesGlob`) plus the `pathe/utils` helpers
(`filename`, `normalizeAliases`, `resolveAlias`, `reverseResolveAlias`). Used by Nuxt, Vite
plugins and most of the unjs ecosystem (tens of millions of weekly downloads). TypeScript, MIT, no runtime
dependencies apart from the bundled `zeptomatch` glob compiler. No AI-contribution policy is
published (README and `.github/workflows` checked 2026-09-16; there is no CONTRIBUTING); the zoo
only records bugs.

Tests are `test/hegel.test.mjs` (ESM, run by `node --test`) with the zoo's harness
`test/hegel-zoo.mjs`. Hegel is `@hegeldev/hegel` 0.4.5.

## How it is built

`dist/` is not committed and the package declares `packageManager: pnpm`, which makes npm refuse
to install into the package root ("Cannot read properties of null (reading 'edgesOut')"). The
setup therefore installs Hegel and TypeScript 5.9.3 together under `.hegel/` (one `npm install
--prefix .hegel` line; a second install into the same prefix would prune the first) and compiles
`src/*.ts` into `.hegel/dist` as **CommonJS** with `test/tsconfig.hegel.json`: the sources use
extensionless relative imports (`./_path`), which Node's ESM loader rejects but CommonJS resolves.
Because the package is `"type": "module"`, `test/hegel-dist-package.json` (`{"type":
"commonjs"}`) is copied into `.hegel/dist` so Node treats the build as CJS. The tests load it with
`createRequire`, and the harness imports Hegel from `.hegel/node_modules`.

## How it is tested

`node:path` is the oracle: `path.posix` for POSIX-looking inputs and `path.win32` for drive and
UNC paths, with win32 results compared after `\` → `/` (pathe's documented normalisation) and the
drive letter upper-cased. Inputs are random paths built from a small alphabet of segments (`a`,
`b`, `.`, `..`, `.c`, `a.b`, `a.b.c`, `..d`, `A`, …) with roots `/`, `//`, `///`, `./`, a drive
(`C:\`, `c:/`, bare `C:` in 5 % of cases) or a UNC prefix (`\\server\share`, `//server/share`),
single or doubled joiners and optional trailing slashes; globs come from a small grammar
(literals, `*`, `?`, `**`, bracket expressions with negation and ranges, braces with 2+
alternatives including empty ones and numeric ranges, `\`-escapes).

- **pathe agrees with `node:path.posix`** (`TestHegelAgreesWithNodePosix`): `normalize`, `join`,
  `resolve`, `relative`, `dirname`, `basename` (with and without `ext`), `extname`, `isAbsolute`,
  `parse` and `format(parse(p))` all equal node's on POSIX paths (inputs starting with `//` are
  skipped: pathe keeps the UNC prefix by design, node collapses it). Found bug 3.
- **pathe agrees with `node:path.win32` on drive paths** (`TestHegelAgreesWithNodeWin32OnDrivePaths`):
  the same functions on `C:\…`/`c:/…` inputs, compared in pathe's notation; `relative` is
  compared case-insensitively when the bodies contain upper-case letters (win32 is
  case-insensitive, pathe is not — a design difference, see below). Found bugs 1, 2, 5, 6 and 12.
- **UNC paths keep their prefix** (`TestHegelUncPathsKeepTheirPrefix`): normalising a UNC path
  keeps `//server/share`, `dirname` never climbs above the share, `isAbsolute` is true, `join`
  and `relative` round-trip within the share, and `parse` puts the share into `dir`. Found bugs 1
  and 4.
- **Path laws** (`TestHegelPathLaws`): `normalize` is idempotent and preserves `isAbsolute`;
  `join(dirname(p), basename(p))` normalises to `normalize(p)`; `resolve(a, relative(a, b))` is
  `resolve(b)`; `extname(p)` is a suffix of `basename(p)`; `format(parse(p))` normalises to
  `normalize(p)`; `parse(p).name + parse(p).ext === parse(p).base === basename(p)`. Found bugs
  12 and 15.
- **`format` agrees with `node:path.posix.format`** (`TestHegelFormatAgreesWithNodePosix`): on
  random `{root, dir, base, name, ext}` objects with fields dropped at random (skipping the shapes
  where node itself is inconsistent: `ext` without a dot, empty `base` with `name`, `..` that node
  leaves unnormalised, UNC-prefixed `dir`). Found bug 10.
- **`matchesGlob` matches its grammar** (`TestHegelGlobMatchesItsGrammar`): each generated glob is
  compiled by the test into a regular expression modelling zeptomatch's documented semantics
  (`*` = one segment without `/`, `?` = one character, `**` alone = anything, `**/` at the start =
  zero or more segments, `/**` at the end = the segment itself or anything below it, `[…]` = one
  character of the class, `{a,b}` = alternatives, `{1..3}` = the numbers, `\x` = literal `x`), and
  pathe's answer on random candidate paths (built from the glob's own literals plus decoys) must
  equal the model's; globs without `**`, escapes, ranges or empty alternatives are also checked
  against `node:path.posix.matchesGlob`. Found bugs 7, 8, 9, 13 and 14.
- **`pathe/utils` agrees with `parse`** (`TestHegelUtilsAgreeWithParse`): `filename(p)` equals
  `parse(p).name` (paths with a trailing slash skipped: `filename` returns `undefined` there);
  `normalizeAliases` orders `{"/root/a", "/root/a/sub", "/root/b"}`-style maps so that
  `resolveAlias` picks the longest prefix and `reverseResolveAlias` inverts it, including chained
  aliases (`{"@": "/r", "~": "@/h"}`). Found bug 11.

## Bugs

| id | title | kind | severity |
|---|---|---|---|
| pathe/1 | A `..` that climbs past a drive or UNC root drops the root (`C:\a\..\..` → `/`) | wrong-result | medium |
| pathe/2 | `dirname`/`basename`/`parse` of a drive root lose the drive (`dirname("C:\")` is `/`, `basename` is `C:`) | wrong-result | medium |
| pathe/3 | Three or more leading slashes become a UNC prefix (`///a` → `//a`) while `//` alone becomes `/` | wrong-result | low |
| pathe/4 | `parse()` of a UNC path has root `/`, so `dir` does not start with `root` | wrong-result | low |
| pathe/5 | `parse("c:/a")` mixes cases: root `c:/` but dir `C:/` | inconsistent | low |
| pathe/6 | `normalize("C:")` is the absolute `C:/` while `isAbsolute("C:")` is false; `resolve("C:", "a")` prepends the cwd; `normalize("c:")` is not idempotent | inconsistent | low |
| pathe/7 | An escaped letter or digit in a glob reaches the RegExp as an escape (`\d` matches `5`, not `d`) | wrong-result | medium |
| pathe/8 | A numeric brace range pads to the narrower endpoint (`{01..3}` misses `02`, matches `2`) | wrong-result | low |
| pathe/9 | A bracket expression starting with `]` is empty (`[]]` does not match `]`) | wrong-result | low |
| pathe/10 | `format()` does not ignore `root` when `dir` is given (`{root: "/", dir: "a", base: "b"}` → `/a/b`, node `a/b`) | contract | low |
| pathe/11 | `filename("..")` is `.` | wrong-result | low |
| pathe/12 | `resolve()` of a path that reduces to a drive root is `/C:` or `C:` | wrong-result | medium |
| pathe/13 | `matchesGlob("a", "[a-0]")` throws `SyntaxError` from the RegExp constructor (also `[!-.]`) | crash | low |
| pathe/14 | `*/**` at the end of a glob no longer matches the segment itself (`a/**` does) | inconsistent | low |
| pathe/15 | A UNC server starting with `.` is rewritten as the device namespace (`//.a/c` → `//./.a/c`) | wrong-result | low |

## Oracle limits and design differences (not counted)

- pathe keeps a doubled leading slash as a UNC prefix (`//a/b` stays `//a/b`) where
  `path.posix` collapses it to `/a/b`; this is documented behaviour and the POSIX property skips
  such inputs (bug 3 is only about *three* slashes, which neither platform treats as UNC).
- `path.win32` compares drive letters and path bodies case-insensitively in `relative`; pathe
  compares exactly. Only drive letters are upper-cased before comparison; `relative` is compared
  case-insensitively when the bodies contain upper-case letters.
- node quirks the tests skip rather than model: `parse("/..")` has `ext` `.`;
  `basename("/", ext)` returns `/`; `basename("a/", ".c")`-style trailing-slash cases;
  `basename("a/.c", ".c")` keeps the dotfile; `format` with an `ext` without a leading dot, an
  empty `base` beside a `name`, or a `..` that node leaves unnormalised; `matchesGlob` on dotfiles,
  negated globs, single-alternative braces `{b}`, `**` inside braces, negative numeric ranges
  `{-1..1}` and doubled slashes in the candidate.
- `filename("a/b/")` is `undefined` (documented: "returns undefined for paths ending in a slash").
- `resolve("//")` is `//` in pathe (the UNC design again) and `/` in node.
- `toNamespacedPath` is the identity in pathe (documented) and is not compared.

## History

- 2026-09-16: created against bc7477a0 (2.0.3); 7 properties, 15 bugs.
