# go-git

[go-git/go-git](https://github.com/go-git/go-git), the pure Go Git implementation, against the git
binary: its `.gitignore` handling (`plumbing/format/gitignore`, the package `Worktree.Status` uses
to decide which files are untracked) on generated worktrees, compared entry by entry with
`git check-ignore`.

## What is tested

**`hegel/hegel_gitignore_test.go`** (needs `git`)
- `TestHegelIgnoreMatchesGit`: a generated worktree (up to three levels of directories and files
  named from a small alphabet with the characters the pattern syntax cares about: `a.b`, `[a]`,
  `!a`, `#a`, `a*`, `a?`, `a `, `-`, `a b`; a `.gitignore` at the root and in some directories, with
  generated lines: negations, leading and trailing slashes, `*`, `?`, bracket expressions with
  ranges, negation and POSIX classes, `**` segments, escapes, trailing spaces and `\ `, comments,
  blank lines, CRLF) is written into a scratch repository. go-git walks it the way `Worktree.Status`
  does (`gitignore.RootPatterns`, `Scope.Descend` with `DirPatterns` for each directory that has a
  `.gitignore`, `Scope.Match` for each entry) and `git check-ignore -v -z --non-matching --stdin`
  answers for every entry; the two must agree on which entries are ignored. Lands on bug 1, 2, 5, 6
  or 7 depending on the run, and passes a default run now and then (intermittent).

**`hegel/hegel_shapes_test.go`**: one narrow property per recorded bug, drawing the bug's region
with random contents (a trailing `/**` over a directory, an escaped space before trailing spaces,
a doubled slash, a path slice with spare capacity, a negation matching a directory, a slash inside
brackets, a `**` followed by two segments over a false-start path), judged by the same git oracle
(or, for `DirPatterns`, by the slice left behind): the deterministic expected failure for each bug.

**`hegel/hegel_pins_test.go`**: one deterministic reproducer per recorded bug, through the same
Scope walk; the first also through `Worktree.Status`.

## Oracles

git (2.43 here; the runner's) on the same tree. The paths are asked about without a trailing
slash, as a walk sees them. Not generated, because the git version would decide the answer: a `**`
next to a non-slash character (`foo**/bar`, `**bar`), mishandled by git before 2.52.0
(`match_pathname` gave fnmatch no prefix context; go-git's conformance suite notes the same). Not
generated either: tabs, non-ASCII names, case folding (`core.ignorecase` is false on Linux),
`.git/info/exclude` and `core.excludesFile`.

## Known bugs

Seven bugs (`bugs.toml`), all in the pattern parser and matcher, five of them changing what
`Worktree.Status` reports: a trailing `/**` excludes the directory itself (so its `.gitignore` is
never read), a negation matching a directory re-includes its contents, a doubled slash is
collapsed, a slash inside brackets is split, trailing spaces after an escaped space are
over-trimmed, `DirPatterns` writes into the caller's slice, and a `**` segment never backtracks:
`globMatch` lets it consume path components only up to the first one the next segment matches, so
`**/*/b` misses a/c/b, `**/a/b` misses a/a/b and `x/**/a/b` misses x/a/a/b, all of which git
ignores (go-git/7, found on 2026-09-25 once the generators drew `**` before a wildcard segment).
The generators draw all seven shapes; `hegel/known.go` names the shape of a case (the first four
by the patterns in the tree, the negation bug and the `**` bug on git's deciding pattern) and a
mismatch reports it. A drawn tree holds a false-start path for a drawn `**` pattern only once in
many thousand cases, so the wide grammar seeds one into about one tree in a hundred. Not drawn:
`**` next to a non-slash character (git itself disagreed before 2.52). `HEGEL_NO_KNOWN=1` (read
once) looks past the recorded bugs: the grammar is built without the shapes (`**` only right
before the last segment, no doubled slashes, no slash inside brackets, ...), the narrow
properties draw the neighbouring region, a residual negation case (about 0.3%) is skipped by
name, and every property passes.

## Not tested

Everything else in go-git: objects, packfiles, index, config, refs, transports, merges. The
`Matcher` built from the deprecated `ReadPatterns` (which cannot express an excluded parent, as its
documentation says).

## History

- 2026-09-20: written against 0f3a0a2c25513f2666ac9b88a6745f7b2382f572 (2026-09-17, v6 development,
  "Merge pull request #2395 from go-git/fix/config-quadratic-lookup") with hegel.dev/go/hegel
  v0.6.33; 6 bugs.
- 2026-09-25: generators rewritten as combinators, the properties draw the known shapes;
  go-git/7 (a `**` followed by two segments never backtracks) found by the freed differential;
  7 bugs.
