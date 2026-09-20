# doublestar

[bmatcuk/doublestar](https://github.com/bmatcuk/doublestar) (v4) is the Go glob library with
`**`: `Match`/`PathMatch` (documented drop-in replacements for `path.Match`/`filepath.Match`
that add `/**/`, `{a,b}` alternatives and `[!…]` classes), `Glob`/`GlobWalk` over an `io/fs.FS`
(a drop-in for `io/fs.Glob`), `FilepathGlob` (for `filepath.Glob`), `SplitPattern`,
`ValidatePattern`, and the options `WithFilesOnly`, `WithNoHidden`, `WithCaseInsensitive`,
`WithFailOnIOErrors`, `WithFailOnPatternNotExist`, `WithNoFollow`. About 1 900 lines without
tests; the upstream table has 177 pattern/name rows. The pinned commit is the January 2026 head,
one commit past v4.9.2. MIT. No CONTRIBUTING or AI policy; not archived; 715 stars. Checked
2026-09-14.

## Oracle

Three, layered. (1) The standard library on the shared syntax — patterns without alternatives,
without a `**` segment (a mid-segment `**` is documented to act like `*`, as in `path.Match`),
and with classes `path.Match` accepts (no `!`, no `-` as a range endpoint or at a class edge):
`Match` must agree with `path.Match`, `PathMatch` with `filepath.Match`, `Glob` with
`io/fs.Glob`, result and error alike. (2) A reference matcher written from the documented
grammar, in the test file: alternatives (nested, possibly empty) are expanded to a set of
patterns; pattern and name are split on `/`; a `**` segment matches zero or more name
segments, and a pattern ending in `/**` or `/**/` also matches the directory itself (for
`Glob`, only when it is a directory); every other segment is matched by a `path.Match`-style
single-segment matcher with doublestar's class rules (`!` or `^` negation, a `-` at either end
is literal, `\c` is c); on a mismatch the rest of the pattern is validated, as `Match` does;
`ValidatePattern` is "every alternative well formed". (3) bash 5.2 with `globstar` and
`nullglob` (`dotglob` unless `WithNoHidden`) on a fixed tree of 19 files and 12 directories,
comparing `Glob`'s result set with bash's expansion (bash's trailing slashes stripped, its
unexpanded brace words filtered by existence, doublestar's `.` for the root dropped).

## Properties

- `TestHegelMatchAgreesWithPathMatch` — standard-syntax patterns of one to four segments
  (literals, `*`, `?`, classes, escapes, mid-segment `**`, leading/trailing slash, 10 % damaged)
  against names that are tree paths, decorated tree paths or random segments: `Match` vs
  `path.Match`, `PathMatch` vs `filepath.Match`, `MatchUnvalidated` vs `Match`,
  `ValidatePattern` vs `path.Match`'s error.
- `TestHegelMatchFollowsTheGrammar` — the full syntax (alternatives up to two deep, `**`
  segments, `!` classes) against the reference matcher: result and error, `MatchUnvalidated`,
  `PathMatch`, `PathMatchUnvalidated`, `ValidatePattern` vs the model's validity.
- `TestHegelGlobListsWhatMatchAccepts` — `Glob` on the tree as a set equals the model's list
  (with `WithFilesOnly` a quarter of the time), has no duplicates, `GlobWalk` visits the same
  names, `FilepathGlob(dir/pattern)` is `Glob` joined with the base, `Match(pattern, p)` agrees
  with membership for every tree path, `io/fs.Glob` agrees on the shared syntax, and
  `WithCaseInsensitive` only adds matches.
- `TestHegelGlobAgreesWithBash` — `Glob` (30 % `WithNoHidden`) vs bash on the tree.
- `TestHegelSplitPatternRoundTrips` — a literal base (some segments with an escaped `*`)
  joined to a pattern whose first segment has a meta character splits back into the unescaped
  base and the pattern.

Twenty thousand cases per property before saving, plus two plain runs. What the generators
avoid, by redrawing or skipping, is the pinned shapes: two `**` segments in a row and a final
`**` after a segment containing `*` (doublestar/1, /2), an unmatched `}` (/3), an alternative
malformed on its own (/4), a trailing slash on a wildcard-free pattern (/5), a backslash before
a non-meta character in `Glob` patterns (/6), an empty alternative in `Glob` patterns (/7),
`FilepathGlob` with a trailing slash (/8), a class at the start of a segment under
`WithNoHidden` (/9), an alternative beginning with `**` (/10), a class that can match `/`
(negated, or a range spanning 0x2F) against a name containing `/` (/11), a group inside a
group in `Glob` patterns (/12); the two `Match`
checks also skip `**` patterns against an empty or slash-terminated name, or with a trailing
slash (the /1 family). Also excluded as design: `//` in `Glob` patterns (an
io/fs path with an empty segment matches nothing, as `fs.Glob`), `.`/`..` segments and leading
slashes in `Glob` patterns (documented to match nothing), and `-` as a range endpoint (`[--b]`,
read differently by every implementation; `path.Match` refuses it).

## Bugs (12; details in bugs.toml)

| id | severity | shape |
|----|----------|-------|
| doublestar/1 | low | the tail after the name ends is recognised by string equality: `a/**/**` and `a*/**` don't match `a`, `**/**` doesn't match `""`, `-**/` matches `-` |
| doublestar/2 | medium | `Glob` returns duplicates: `a/**/**`, `**/?/**`, overlapping alternatives `{?,*}` |
| doublestar/3 | low | unmatched `}`: literal for `Match("a}", "a}")`, `ErrBadPattern` for `Match("a}", "b")`, refused by `ValidatePattern` and `Glob` |
| doublestar/4 | low | `Match("{a,[}", "a")` succeeds, `Match("{a,[}", "b")` is `ErrBadPattern` — malformed alternatives are validated lazily |
| doublestar/5 | low | `Glob("f/")` returns the regular file as `"f/"`; `Glob("a/")` returns `"a/"` where `Glob("*/")` returns `"a"` |
| doublestar/6 | medium | `Glob("\\f")`, `Glob("a/\\e")`, `Glob("\\.i")` find nothing — only `*?[]{}` are unescaped, `Match` accepts them |
| doublestar/7 | medium | `Glob("some{thing,}")` lists `something` but not `some` — the README's own example; empty alternatives are dropped |
| doublestar/8 | low | `FilepathGlob(dir/*/)` returns regular files: `Clean` removes the trailing slash (`filepath.Glob`: nothing; `Glob`: directories) |
| doublestar/9 | low | `WithNoHidden`: `[.a]i` and `[!b]i` list `.i` (bash: never) |
| doublestar/10 | medium | `b{**}` matches `b/-` (`b**` does not): the alternative's `**` is taken as segment-start |
| doublestar/11 | medium | `a[!1]b` matches `a/b`, `a[.-c]a` matches `a/a`: a class matches the separator — negated always, ranges spanning 0x2F too (`path.Match`: false) |
| doublestar/12 | medium | `Glob("*/{{*}}/*")` lists `1/2/3/4`: a nested group makes `Glob` descend one level too far (`*/{*}/*` and `Match` do not) |

## Not bugs (documented or design)

- `{a}` (one alternative) matches `a`; bash needs a comma for brace expansion. The doc's grammar
  allows a single term.
- Classes are more permissive than `path.Match`'s: `[a-]`, `[-a]` (a `-` at either end is
  literal, as in bash) and `[!a]` parse where `path.Match` returns `ErrBadPattern`.
- `Glob("**")` and `Glob("**/")` include `"."`, the root itself, by the "`a/**` matches `a`"
  rule; bash lists no `.`; `io/fs.Glob("**")` is `*`.
- `Glob` returns nothing for `//`, `./`, `../` segments and leading slashes, like `io/fs.Glob`
  (documented; `SplitPattern` exists for that).
- `ErrBadPattern` equal to `path.ErrBadPattern` — documented as not to be relied on.
- Zone of `Match` vs `Glob` for files under `a/**`: `Match("f/**", "f")` is true ("might be a
  directory") while `Glob("f/**")` is empty for a regular file — the documented rule concerns
  names, and `Glob` knows the file type.
- 2026-09-20: base bumped a9ad9e0ef4d6 → 314a6092ed05 (2026-09-19, "Merge branch 'sidsri14-master'"; v4.10.1); 12 bug(s) still reproduce. 5 tests pass.
