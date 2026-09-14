# shell-words

[shell-words](https://github.com/tmiasko/shell-words) processes command lines "according to
parsing rules of Unix shell as specified in Shell Command Language in POSIX.1-2008": `split`
(documented as "exactly the same" as a Unix shell when the input has no operators, assignments
or expansions, and as compatible with GLib's `g_shell_parse_argv` and "very close" to Python's
`shlex.split`), `quote` and `join` ("a single command line suitable for execution in Unix
shell"); 145M downloads, 1.1.1 released 2025-12. Written in the zoo at 1.1.1 (upstream HEAD
`8d2868b`); tests in `tests/hegel.rs` (edition 2015: `extern crate`).

## The oracles

The same harness as the `shlex` target: **bash 5.2** held open as one child, its array
assignment `x=( <text> )` the word splitter (it accepts newlines between words like the crate;
a syntax error is a distinct reply); **dash** and **busybox ash** per case via `set --`;
**python3**'s `shlex.split`/`quote`/`join` as one child. Strings travel as hex.

- `split_agrees_with_bash`: arbitrary command-line text over letters, whitespace (newlines
  included), quotes, backslashes, `#`, `!`, `^`, `\r`, punctuation, control characters and
  non-ASCII — nothing bash expands and nothing an array assignment reads (`=`, `[`, `(`, `)`).
  `split` == bash's words, `Err(ParseError)` == bash's syntax error. Text ending in a backslash
  is left to `doc_examples` (the array oracle cannot see it; the shells keep `a\` literally, as
  the crate does).
- `quoting_round_trips_through_every_shell`: `join` of 0–4 words over every ASCII punctuation
  character, control characters, `\r`/`\n`/`\t` and non-ASCII splits back to the words under
  bash, dash, busybox ash, the crate's own `split` and — when no word carries a `\r`, which
  Python treats as a delimiter — Python `shlex.split`; `join` is the quoted words separated by
  single spaces. The generator avoids the pinned shape (a word with `{` and `}`).
- `python_quoting_is_understood`: Python's `shlex.quote`/`shlex.join` output splits back under
  the crate.
- `doc_examples`.

## Bugs (1)

- **shell-words/1** (wrong-result, high; `brace_expansion_is_quoted`): `quote` leaves `{` and
  `}` bare, so bash and zsh brace-expand the "quoted" word — `join(["rm", "{a,b}"])` is
  `rm {a,b}`, which bash runs with two arguments; `{1..3}` becomes three. The shape of
  RUSTSEC-2024-0006 in the sibling crate `shlex`, fixed there in 2024.

## Not bugs

- `quote` leaves `!` and `^` bare; both are expanded by bash's history mechanism, but only in
  interactive shells, which no oracle here can drive (history expansion stays off under `set -H`
  when bash reads a pipe). The doc's "copied and pasted into an actual shell" use is exactly the
  interactive one, so this is worth a look upstream, but it is recorded here as an observation,
  not a bug.
- `quote` leaves control characters other than newline and tab bare; harmless in
  non-interactive shells, unsafe on a terminal (the `shlex` crate's `quoting_warning` covers
  the same ground).
- `\r` is a word character (documented; Python's `shlex` splits on it); `\`‑newline outside
  quotes is removed; `w1#w2` is one word (Python's `shlex` starts a comment there — a fourth
  divergence the doc's list of three does not mention).
- Bash 5.2.21 itself mangles the bytes `\x01` and `\x7f` (its internal CTLESC/CTLNUL markers)
  after a quote or a backslash in a word — a bash bug; the two bytes are left out of the
  alphabets.
