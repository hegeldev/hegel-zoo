# ssh_config

[kevinburke/ssh_config](https://github.com/kevinburke/ssh_config), a Go parser for `ssh_config`
files, against the OpenSSH client's own reading of the same file: for a generated config and a
queried host, `Config.Get`/`GetAll` must give what `ssh -G` prints.

## What is tested

**`hegel/hegel_ssh_test.go`** (needs `ssh`)
- `TestHegelMatchesSSH`: a generated config (directives before any block for the implicit `Host *`;
  up to four `Host` or `Match` blocks with one to three patterns from a small alphabet using `*`,
  `?` and `!`, `Match all`, `Match host` with comma lists; keywords in canonical, lower and upper
  case, separated from their values by spaces, tabs or `=`; values sometimes quoted; blank and
  comment lines, end-of-line comments, indentation, CRLF) is written to a file and `ssh -G -F`
  asked about one alias; the package's `Get` (first value wins) or `GetAll` (for the accumulating
  keywords) must agree, for 21 keywords: Port, User, HostName, Compression, ForwardAgent,
  IdentitiesOnly, BatchMode, ConnectTimeout, ServerAliveInterval, ServerAliveCountMax, LogLevel,
  StrictHostKeyChecking, RequestTTY, AddressFamily, HostKeyAlias, ProxyCommand, LocalCommand,
  IdentityFile, CertificateFile, SendEnv, SetEnv. When the package has no value, ssh's default
  (learnt once from an empty config) is expected.

- One narrow property per recorded bug, drawing its shape region with random contents (names,
  positions, masks, the directives around it) and judged by the same `ssh -G` comparison:
  `TestHegelTabSeparatedHostPatternsMatch` (a tab inside a `Host` pattern list),
  `TestHegelQuestionMarkMatchesOneCharacter` (a `?` pattern against an alias one character
  shorter or longer), `TestHegelMatchHostCommaListMatchesEachPattern` (a `Match host` comma
  list), `TestHegelMatchHostSeesTheHostName` (a `HostName` directive before a `Match host` naming
  it) and `TestHegelMatchHostIgnoresCase` (pattern and alias in different case). Each fails every
  run.

**`hegel/hegel_pins_test.go`**: one deterministic reproducer per recorded bug, with the value
`ssh -G` gives.

## Oracles

`ssh -G` (OpenSSH 9.6 here; the runner image's). The package returns the configured text, ssh the
effective value, so the comparison spells the package's answer as ssh does: HostName and
HostKeyAlias lowercased (HostName defaults to the lowercased alias), `yes`/`no` of RequestTTY and
StrictHostKeyChecking as `true`/`false`, `DEBUG1` as `DEBUG`, `QUIET` as `SILENT`, `ProxyCommand
none` as unset, ServerAliveInterval defaulting to 300 under `BatchMode yes`, a file named twice in
IdentityFile/CertificateFile once, SendEnv's words split, and SetEnv taken from the first directive
that applies with the first assignment of each variable (ssh treats the option as one list). Not
generated, because the semantics differ by design or ssh rejects them: fully quoted ProxyCommand or
LocalCommand values (ssh keeps the quotes for these), end-of-line comments on those two keywords
(part of the command for ssh), `Match` criteria other than `host`/`all` and the `host=list`
spelling (the package rejects them), `Include`, `%` tokens in anything but commands. A config ssh
rejects is counted, not judged.

## Known bugs

Five bugs (`bugs.toml`): tab-separated Host patterns read as one pattern; `?` matching zero
characters; `Match host` not splitting its comma list, matched against the alias instead of the
hostname, and case-sensitively. The generators draw their shapes by default (tabs between Host
patterns, `?` patterns, Match host comma lists, a HostName directive beside a Match host block,
upper case in Match patterns and aliases): `TestHegelMatchesSSH` reaches them at their natural
rates (/1 in about 9% of cases, /2 and /3 in about 4%, /4 and /5 rarely) and is an expected
failure mapped to /1, the shape it shrinks to in most runs (`Host foo<TAB>foo`; sometimes a `?`
pattern), and the five narrow properties are the expected failures of their bugs. A mismatch that
a recorded bug explains says so in the failure (`hegel/known.go` names the shape); the pins are
regression examples beside the properties. `HEGEL_NO_KNOWN=1` switches the known shapes off for a
run that looks past the bugs: the wide generator avoids the coarse shapes and skips the precise
`?` disagreements (about 3% of its cases), and the narrow properties draw the neighbouring
non-bug shape (spaces for tabs, the `?` given one character, one-pattern lists, HostName equal to
the alias, one spelling); every property then passes.

## Not tested

`Include` (files), `Match` criteria other than `host` and `all`, `UserSettings` (the user's and
system files), the typed defaults of `validators.go` beyond what ssh prints, `Config.String`
round-trips, comment preservation.

## History

- 2026-09-20: written against bd15f5d44042e84fa6a04fcb0f1d176fc804397f (2026-05-04, "dependabot:
  add 7-day cooldown to all updates") with hegel.dev/go/hegel v0.6.33; 5 bugs.
- 2026-09-24: unsteered (STYLE.md rule 11): the known shapes are drawn by default, the wide
  property and five narrow properties are the expected failures, `HEGEL_NO_KNOWN=1` switches
  the shapes off.
