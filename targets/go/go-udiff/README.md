# go-udiff

[aymanbagabas/go-udiff](https://github.com/aymanbagabas/go-udiff), a copy of the Go tools'
internal diff package (Myers/LCS line and character diffs, edits, unified output), against GNU
patch and git apply: the unified diffs it writes must apply to the old text and give the new one,
its edits must apply with `Apply`, and `ApplyUnified` and `Merge` must agree with them.

## What is tested

**`hegel/hegel_udiff_test.go`** (needs `patch` and `git`)
- `TestHegelUnifiedApplies`: for an old text of up to twenty lines from a small alphabet (letters,
  blank and whitespace-only lines, lines that look like diff syntax, non-ASCII, CR-terminated lines;
  with or without a final newline) and a new text (a few line replacements, deletions, insertions
  and moves, or an independent text), `ToUnified` of `Lines` or of `Strings` edits with 0, 1, 2, 3
  or 5 context lines is applied to a file holding the old text by `patch --binary --fuzz=0 -p1` and
  by `git apply` (`--unidiff-zero` for context 0); both must accept it and leave the new text.
  Equal texts give an empty diff; `Unified` is `ToUnified(Lines, 3)`.
- `TestHegelArbitraryEdits`: one to four disjoint edits at arbitrary rune boundaries (deletions,
  insertions, replacements with newlines inside; given sorted or shuffled) apply with `Apply` to the
  replacement, and their `ToUnified` applies with patch and git apply to the same text.
- `TestHegelEditsApply`: `Lines`, `Strings` and `Bytes` edits are sorted, disjoint, in bounds, at
  line or rune boundaries, never no-ops, and `Apply`/`ApplyBytes` gives the new text.
- `TestHegelApplyUnified`: `ApplyUnified(Unified(old, new), old)` is `new`.
- `TestHegelMerge`: two edit lists changing disjoint lines of a text of distinct lines merge and
  apply to the combined text; both sides replacing one line differently is reported as a conflict;
  `Merge(x, x)` and `Merge(x, nil)` are `x`.

**`hegel/hegel_pins_test.go`**: one deterministic reproducer per recorded bug.

## Oracles

GNU patch (2.7.6 here) and git apply (2.43), both strict (`--fuzz=0`; git apply checks hunk
counts), on a scratch file; `--binary` keeps patch from its CRLF heuristics, so CR-terminated
lines are content like any other. Equality of texts and the manual replacement for arbitrary
edits. Pins use GNU diff's `-U0` headers for the range syntax.

## Known bugs (gated)

Four bugs (`bugs.toml`): zero-context hunks writing a one-line range for an empty side; `ApplyUnified`
rejecting context lines, and the no-newline marker; `Bytes` reading non-UTF-8 bytes as U+FFFD.
`hegel/known.go` gates the first three exactly (a hunk header without a count on a side that has
no lines; a context line; the marker in the diff), so `HEGEL_NO_KNOWN=1` only lifts them. The
fourth is not generated: the properties use UTF-8 texts, and the pin holds the damaged ones.

## Not tested

The `lcs` and `myers` packages directly (they are reached through `Lines`/`Strings`/`Bytes`);
minimality of the diffs (the LCS is compared with nothing); `Merge` of overlapping but compatible
edits beyond the identical case; the difftest data.

## History

- 2026-09-20: written against a8de762fc44b09108c21d20ac1bbb0619a17b6e6 (2026-07-16, "feat:
  import upstream package (#39)", after v0.4.1) with hegel.dev/go/hegel v0.6.33; 4 bugs.
