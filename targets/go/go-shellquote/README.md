# go-shellquote

[kballard/go-shellquote](https://github.com/kballard/go-shellquote) joins and splits strings
by sh's word-splitting rules: `Join(args...)` quotes each argument so that `/bin/sh` splits the
result back into the arguments; `Split(input)` splits on blanks, tabs and newlines honouring
backslash escapes, single and double quotes (no `$'…'`, no expansions), returning one of three
`Unterminated…Error` values for unbalanced input. 260 lines, last changed in 2018 (a
line-continuation fix), no `go.mod` — the patch adds one; a dependency of many Go tools. MIT.
No CONTRIBUTING or AI policy; not archived. Checked 2026-09-15. Upstream already has a
`testing/quick` property (`Split(Join(x)) == x`); the zoo adds the shells themselves.

## Oracle

Three shells and a model. bash 5.2 reads the line as the body of an array assignment
(`set -f; set +B; a=( <line> )`), so unquoted newlines are allowed; dash and busybox ash read it
as the operands of `set --` (`set -f; set -- <line>`), on lines without unquoted newlines. The
words come back NUL-separated after a count. Split is compared with them on lines made of bare
text, escapes, line continuations, single- and double-quoted pieces, without the shells'
expansions (`$`, backtick, `~` or `#` at the start of a word), operators or globbing. Join is
compared with all three shells on arbitrary words. `modelSplit` is the documented rule set for
Split on arbitrary text, including the three error cases.

## Properties

- `TestHegelSplitAgreesWithBash` — 0–5 words, separators including newlines: `Split` and bash
  agree on success/failure and on the words. Clean.
- `TestHegelSplitAgreesWithSh` — the same without unquoted newlines, against dash or busybox
  ash. Clean.
- `TestHegelJoinRoundTripsThroughTheShells` — 0–5 arbitrary words (quotes, backslashes, `$`,
  backticks, operators, blanks, newlines, CR, `~`, invalid UTF-8, empty): each shell splits
  `Join(words...)` back into `words`. Words beginning with `#` are prefixed (go-shellquote/1).
- `TestHegelSplitInvertsJoin` — `Split(Join(words...)) == words` for the same words, and a
  single word without blanks or quotes is backslash-escaped rather than quoted. Clean.
- `TestHegelSplitFollowsTheDocumentedRules` — arbitrary text (and shell lines with random
  tails): `Split` returns the model's words or the model's error value. Clean.

## Bugs

| id | severity | title |
|----|----------|-------|
| go-shellquote/1 | medium | `Join` leaves a leading `#` unquoted, so the word and everything after it become a comment |

## Not bugs

- `Split("echo a # b")` is `["echo", "a", "#", "b"]` while sh drops the comment: Split
  documents itself as quoting-only ("does not attempt to perform any other sort of expansion";
  no `$'…'`), and treating `#` literally is the useful behaviour for splitting an option string
  — a scope choice, not recorded. Join's `#` (above) is different: its contract names `/bin/sh`.
- `Split` treats `;`, `|`, `&`, `<`, `>`, `(` and `)` as ordinary characters where sh sees
  operators — the same scope choice.
- A backslash before an ordinary character inside double quotes is kept (`"\d"` is `\d`), as in
  sh.
