# shellescape

[alessio/shellescape](https://github.com/alessio/shellescape) (`al.essio.dev/pkg/shellescape`)
escapes strings for safe use as POSIX shell arguments: `Quote`, `QuoteCommand`, `StripUnsafe`,
`StripSpaces`, the `bufio` split function `ScanTokens`, and the `escargs` command
(`cmd/escargs`, a NUL/newline-aware xargs-style escaper). Pinned at 693bd3506cec (2026-09-02,
past v1.6.1). MIT. Its `AGENTS.md` is guidance for coding agents, not a restriction; no
CONTRIBUTING.md; not archived. Checked 2026-09-15. Upstream has table tests, examples and a
fuzz test that round-trips `Quote` through `google/shlex`.

## Oracles

- bash 5.2, dash and busybox ash, each reading `Quote(s)` / `QuoteCommand(args)` as a shell
  word list (`a=( … )` in bash, `set -- …` in the POSIX shells, globbing and brace expansion
  off) and printing the words back NUL-separated — the contract "can safely be used as one
  token in a shell command line".
- Python's `shlex.quote`, the algorithm the package says it derives from, held open as a child
  over JSON lines; invalid UTF-8 travels as surrogate escapes, so the comparison is byte for byte.
- The documented safe set `[\w@%+=:,./-]` (ASCII `\w`) as a model; Go's `unicode.IsPrint` and
  `unicode.IsSpace` for the Strip functions; `strings.Split` on NUL / `bufio.ScanLines`'s rules
  for `ScanTokens` and `escargs`.

## Properties

- `TestHegelQuoteRoundTripsThroughTheShells` — strings of 0–24 pieces from safe characters,
  shell metacharacters, quotes, controls (newline, CR, ESC, DEL…), non-ASCII letters and spaces,
  zero-width/format characters and invalid bytes; 0–5 of them as a command. Each of the three
  shells reads the quoted text back as exactly the original words. Clean.
- `TestHegelQuoteMatchesShlexQuoteAndTheDocumentedRule` — `Quote` equals `shlex.quote` byte for
  byte (NUL included) and the documented rule; `QuoteCommand` is the space-joined `Quote`s. Clean.
- `TestHegelStripFunctionsFollowTheUnicodeTables` — on valid UTF-8, `StripUnsafe` keeps exactly
  the `IsPrint` runes, `StripSpaces` drops exactly the `IsSpace` runes; both idempotent and
  commuting; on invalid UTF-8 only idempotence is judged (shellescape/1). Clean.
- `TestHegelScanTokensSplitsOnNUL` — a `bufio.Scanner` with `ScanTokens` over random data
  through buffers of 1–64 bytes yields the words between NULs, an unterminated last word
  included, no empty word after a final NUL. Clean.
- `TestHegelEscargsQuotesEveryInputLine` — the built `escargs` on generated input (lines with
  LF or CRLF, or NUL-terminated items with `-0`, blank items, `-D`, `-a file`) prints `Quote` of
  each item joined by single spaces, exit 0, nothing on stderr. Clean (items under 64 KiB;
  shellescape/2 pinned separately).

## Bugs

| id | severity | title |
|----|----------|-------|
| shellescape/1 | low | `StripUnsafe` and `StripSpaces` turn every invalid UTF-8 byte into U+FFFD instead of removing or keeping it |
| shellescape/2 | medium | `escargs` drops the rest of its input silently, with exit status 0, once a line exceeds `bufio.Scanner`'s 64 KiB limit |

## Not bugs

- `Quote("\x00")` is `'<NUL>'`: no shell can carry a NUL in an argument, and `shlex.quote` does
  the same; the shell round trip skips NUL, the shlex differential includes it.
- `escargs` strips one trailing CR from each line (`bufio.ScanLines`'s documented behaviour) and
  `QuoteCommand(nil)` is `""` (an empty command line).
- `StripUnsafe` removes NBSP, U+2028/2029 and every non-ASCII space: `unicode.IsPrint` accepts
  only the ASCII space, as documented.
- `~`, `#`, `*`, `!` are always quoted although not every shell treats them specially in every
  position: the safe set is deliberately conservative, as in `shlex.quote`.
