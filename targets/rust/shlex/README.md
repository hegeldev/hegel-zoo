# shlex

[shlex](https://github.com/comex/rust-shlex) splits strings into shell words "using the same
syntax as the POSIX shell" and quotes words for "any POSIX-compatible shell" (tested upstream
against bash, zsh, dash, busybox ash, mksh and fish), aiming at Python `shlex` and C `wordexp`
compatibility too; 819M downloads, 2.0.1 released 2026-05. Written in the zoo at 2.0.1
(upstream HEAD `653936e`); tests in `tests/hegel.rs`.

## The oracles

The shells and Python themselves:

- **bash 5.2** held open as one child for the whole run. A compound array assignment
  `x=( <text> )` is bash's own word splitter and, unlike a command line, accepts newlines between
  words the way the crate does; the text arrives via `printf -v` hex escapes and `eval`, the words
  come back NUL-separated, a syntax error (unterminated quote) is a distinct reply.
- **dash** and **busybox ash**, one process per case: `set -- <quoted line>`.
- **python3**'s `shlex.split`, `shlex.quote`, `shlex.join`, one child, byte strings as hex with
  `surrogateescape` so invalid UTF-8 round-trips.

Properties:

- `split_agrees_with_bash`: arbitrary command-line text over letters, whitespace (newlines
  included), quotes, backslashes, `#`, `!`, `^`, `\r`, punctuation, a control character and
  non-ASCII bytes (valid UTF-8 or not) — nothing bash expands and nothing an array assignment
  reads (`=`, `[`, `(`, `)`). `bytes::split` == bash's words, `None` == bash's syntax error. A
  text ending in an unescaped backslash is documented as an error for the crate and skipped.
- `iterator_and_str_api_agree_with_bytes_split`: `Shlex`, `had_error`, `line_no` (= newlines
  read + 1) and the `str` front end against `bytes::split`.
- `quoting_round_trips_through_every_shell`: `try_join` of 0–4 words over every ASCII
  punctuation character, control characters, `\r`/`\n`/`\t`, non-ASCII, `\xa0` and invalid
  UTF-8 splits back to the words under bash, dash, busybox ash, Python `shlex.split` and the
  crate's own parser; `join` is the quoted words separated by single spaces.
- `python_quoting_is_understood`: Python's `shlex.quote`/`shlex.join` output splits back under
  the crate.
- `quoting_contracts`: nul bytes give `QuoteError::Nul` unless `allow_nul(true)`; `str` and
  `bytes` front ends agree; valid UTF-8 in, valid UTF-8 out; `Quoter::new()` is the default.
- `doc_examples`.
- The general split generator avoids the pinned shape: a `\`‑newline at the start of a word.

## Bugs (1)

- **shlex/1** (wrong-result, medium; `line_continuation_at_word_start_yields_no_word`): a line
  continuation at the start of a word yields an empty word — `a \<newline> b` splits into
  `["a", "", "b"]`, `\<newline>` alone into `[""]`; bash, dash and ash give `["a", "b"]` and
  `[]`.

## Not bugs

- Bash 5.2.21 itself mangles the bytes `\x01` and `\x7f` (its internal CTLESC/CTLNUL markers)
  after a quote or a backslash in a word — `x=( "'\x7f" )` yields `'\x01\x7f`, `\a\x01` yields
  `a\x01\x01`; dash and busybox ash are fine. That is a bash bug in the zone the crate's warning
  covers ("does not quote control characters because they cannot be quoted portably"); the two
  bytes are left out of the alphabets, other control characters are in.
- Splitting follows the shells, not Python's `shlex`, where they differ: `\r` is a word
  character (documented in the README), `\`‑newline outside quotes is removed (Python keeps a
  newline), `foo#bar` is one word (Python starts a comment), `"\$"` drops the backslash (Python
  keeps it — the crate never emits `$` or backquote inside double quotes for this reason).
- A string ending right after an unescaped backslash is an error (`None`), as in Python; bash
  drops the backslash.
- Non-ASCII words are always quoted (documented as the `\xa0` mitigation); `try_quote` returns
  `Borrowed` only for a word that needs no quoting.
