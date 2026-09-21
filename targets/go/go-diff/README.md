# go/go-diff

[sourcegraph/go-diff](https://github.com/sourcegraph/go-diff) parses and prints unified diffs
(single and multi-file, GNU diff and git flavours, extended git headers, `Only in` messages)
into `diff.FileDiff`/`diff.Hunk` structs, computes `Stat`s and reverses diffs. It computes no
diffs itself. Pinned at `cf64c62` (v0.9.0, 2026-09-10, MIT; no AI policy in README or
`.github`, no CONTRIBUTING).

## Build

The tests live in a new package directory `hegel/` of the upstream module; `go.mod` gains
`hegel.dev/go/hegel`. The run command is `go test -count=1 -run TestHegel -v ./hegel`. The
tests run `diff` (GNU diffutils), `patch` and `git` from `PATH`; CI's Ubuntu image has all
three.

## Oracle

The producers and consumers of unified diffs. GNU `diff -U<n>` (n 0..3, sometimes `-p`) of
two generated texts (short lines from a small alphabet that includes lines looking like diff
syntax, optional final newline, optional CRLF) and `git diff --cached` of a random change to
a small repository (edits, additions, deletions, renames, mode changes, binary files, `-M`
or `--no-renames`, `--binary`) produce the diffs. A model of what a hunk means (ranges must
match the body, the old side must match the old text, the new side is the new text; the
no-newline conventions of `Body`/`OrigNoNewlineAt`) checks the parse; GNU `patch --fuzz=0`
and `git apply` check the printed and reversed diffs against the texts and trees. Printing
is compared byte for byte after normalizing the two spellings the format allows (`N` vs
`N,1` ranges, git's trailing tab after names with spaces).

## Properties

- `TestHegelParseUnified`: GNU diff's output parses; the hunks apply to the old text and
  give the new one; `StartPosition`, `Stat` and the reprinted diff agree with the input;
  with and without `KeepCR` on CRLF texts.
- `TestHegelReverse`: `ReverseFileDiff` swaps names and times, its hunks turn the new text
  back into the old one (model and `patch`), and reversing twice reprints the original.
- `TestHegelStructRoundTrip`: a generated `FileDiff` (times, sections, git extended headers,
  no-newline markers) printed and parsed is the same `FileDiff`; the same for `PrintHunks`
  and `ParseHunks`.
- `TestHegelMultiFile`: git's diff of a random change parses into one `FileDiff` per path
  with the names `--name-status` reports, reprints identically, and the printed diff and its
  `ReverseMultiFileDiff` are accepted by `git apply` and produce the new and the old tree.

## Bugs

Three, see `bugs.toml`: a reversed GIT binary patch keeps its sections in forward order (1);
a `---`/`+++` pair of body lines before the next hunk header is taken for a file header even
though the hunk header's counts say otherwise (2); a file name ending in a space loses it (3,
pin only).

## Modelled as recorded, not counted

- `PrintFileDiff` writes names unquoted (a `TODO` in the source): names with tabs, quotes,
  backslashes or non-ASCII parsed from git's quoted headers print as different diffs. The
  generators use names without such characters.
- A header timestamp without a zone (Apple diff) parses as UTC and prints with `+0000`;
  hunk ranges print as `N,1` where diff writes `N`.
- Hunk headers whose counts disagree with the body are accepted as written; trailing content
  after the last file of a multi-file diff is dropped silently (documented for
  `ReadFileWithTrailingContent`).
- `Stat` counts a `-` line directly followed by a `+` line as one changed line; the
  property checks only that added + changed and deleted + changed match the body.
- CRLF diffs parsed without `KeepCR` lose their carriage returns, as documented, and
  `patch` then rejects the reprinted diff on CRLF files.
