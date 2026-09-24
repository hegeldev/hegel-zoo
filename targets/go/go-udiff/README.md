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
- `TestHegelApplyUnified`: `ApplyUnified(Unified(old, new), old)` is `new`, for texts that share
  lines (so the diff has context lines) as well as independent ones, with or without final newlines.
- One narrow property per recorded bug, drawing its shape region with random contents and checked
  the same way: `TestHegelZeroContextDiffsApply` (only-delete or only-insert edit lists with context
  0 through patch and git apply), `TestHegelApplyUnifiedCopiesContextLines` (a text of two or more
  lines with one edit, so the diff has a context line), `TestHegelApplyUnifiedReadsTheNoNewlineMarker`
  (independent texts with a final newline missing on at least one side) and
  `TestHegelBytesEditsApplyToAnyBytes` (`Bytes` edits on texts with non-UTF-8 bytes applied with
  `ApplyBytes`). Each fails every run.
- `TestHegelMerge`: two edit lists changing disjoint lines of a text of distinct lines merge and
  apply to the combined text; both sides replacing one line differently is reported as a conflict;
  `Merge(x, x)` and `Merge(x, nil)` are `x`.

**`hegel/hegel_pins_test.go`**: one deterministic reproducer per recorded bug.

## Oracles

GNU patch (2.7.6 here) and git apply (2.43), both strict (`--fuzz=0`; git apply checks hunk
counts), on a scratch file; `--binary` keeps patch from its CRLF heuristics, so CR-terminated
lines are content like any other. Equality of texts and the manual replacement for arbitrary
edits. Pins use GNU diff's `-U0` headers for the range syntax.

## Known bugs

Four bugs (`bugs.toml`): zero-context hunks writing a one-line range for an empty side; `ApplyUnified`
rejecting context lines, and the no-newline marker; `Bytes` reading non-UTF-8 bytes as U+FFFD. The
generators draw their shapes by default: context 0 one time in six (`TestHegelUnifiedApplies` and
`TestHegelArbitraryEdits` reach /1 in 3-6% of their cases and are intermittent expected failures at
100 cases), texts sharing lines and missing final newlines (`TestHegelApplyUnified` fails every run,
shrinking to the marker of /3 in most runs and to a context line of /2 in some), and non-UTF-8
bytes in the narrow `Bytes` property; the four narrow properties are the expected failures of their
bugs and the pins are regression examples beside them. `hegel/known.go` keeps the shape tests and
names the shape in a failure; `HEGEL_NO_KNOWN=1` switches the known shapes off for a run that
looks past the bugs (context 0 one time in twenty, independent texts for `ApplyUnified`,
distinct-line replacements, UTF-8 words only, the rest skipped by the shape tests: 2-3% of the
wide properties' cases), and every property then passes. `TestHegelEditsApply` keeps UTF-8 texts:
`Strings` on invalid UTF-8 has the same offset flaw as `Bytes` but is not recorded.

## Not tested

The `lcs` and `myers` packages directly (they are reached through `Lines`/`Strings`/`Bytes`);
minimality of the diffs (the LCS is compared with nothing); `Merge` of overlapping but compatible
edits beyond the identical case; the difftest data.

## History

- 2026-09-20: written against a8de762fc44b09108c21d20ac1bbb0619a17b6e6 (2026-07-16, "feat:
  import upstream package (#39)", after v0.4.1) with hegel.dev/go/hegel v0.6.33; 4 bugs.
- 2026-09-24: unsteered (STYLE.md rule 11): the known shapes are drawn by default, the wide
  properties and four narrow ones are the expected failures, `HEGEL_NO_KNOWN=1` switches the
  shapes off (it used to lift the gates).
