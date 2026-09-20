# go-debian

[paultag/go-debian](https://github.com/paultag/go-debian) (`pault.ag/go/debian`), the Debian
toolbelt for Go: package versions, dependency relationships, architectures, control-file
paragraphs and changelogs, against dpkg itself, which defines all of these formats.

## What is tested

**`hegel/hegel_version_test.go`** (`version`)
- `TestHegelVersionParseMatchesDpkg`: a version text (epochs numeric, zero, huge, negative,
  signed, empty or not a number; upstream parts of digits, letters and `.+~:-`; revisions;
  junk characters; blank padding) parsed by `version.Parse` is accepted exactly when
  `dpkg --validate-version` reports no error (a text dpkg only warns about may go either way,
  since Parse has no warnings), splits as `Dpkg::Version` splits it, and `String()` parses back
  to the same version and compares equal to the text for dpkg.
- `TestHegelCompareMatchesDpkg`: `version.Compare` on pairs of clean versions (one often a
  mutation of the other: a `~`, a `+`, leading zeros, case, the epoch) has dpkg
  `--compare-versions`'s sign, is antisymmetric, and `sort.Sort(version.Slice)` leaves
  neighbours in dpkg's order.

**`hegel/hegel_dependency_test.go`** (`dependency`)
- `TestHegelDependencyParseMatchesDpkg`: a relationship field (package names, `:arch`
  qualifiers, version relations with every operator and spacing, architecture lists with and
  without negation, build-profile restriction lists, `,` and `|` with tabs, newlines and
  trailing commas) parsed by `dependency.Parse` gives `Dpkg::Deps`'s reading (package,
  qualifier, relation, version, architectures, restrictions, per relation and alternative) when
  dpkg accepts the text; when dpkg refuses it and Parse does not, Parse's reading written back
  with `String()` must be a relationship dpkg reads to the same structure.
- `TestHegelDependencyStringRoundTrips`: `Parse(String(Parse(x)))` is `Parse(x)` and `String`
  is stable, including substvars.
- `TestHegelArchMatchesDpkg`: `ParseArch` gives the tuple `Dpkg::Arch` gives
  (`debarch_to_debtuple`, or `debwildcard_to_debtuple` for wildcards), `String()` the
  canonical name, `Arch.Is` what `debarch_is` says and `ArchSet.Matches` what
  `debarch_is_concerned` says, over real architectures, wildcards and odd spellings.

**`hegel/hegel_control_test.go`** (`control`)
- `TestHegelParagraphsMatchDpkg`: a control file (one to three paragraphs, fields with odd
  spacing around the colon and trailing whitespace, continuation lines with dots, empty and
  indented text, comment lines, blank lines, CRLF, no final newline) read by
  `control.ParagraphReader` gives `Dpkg::Control::HashCore`'s paragraphs: the same fields in
  order with the same values, or both refuse it.
- `TestHegelParagraphWriteToMatchesDpkg`: a `Paragraph` with values of one to four lines
  (empty, dot-only, whitespace and indented lines, a leading or trailing newline) is written by
  `WriteTo` as HashCore writes the same fields (modulo trailing whitespace on a line) and reads
  back with `ParagraphReader` as the paragraph it was.

**`hegel/hegel_changelog_test.go`** (`changelog`)
- `TestHegelChangelogMatchesDpkg`: a changelog of one to three entries (header lines with one
  or more distributions and the urgency and other options in the spellings dpkg meets; change
  lines with bullets, sections, blank lines, dashes and tabs; trailer lines with the date in
  the forms dpkg's grammar allows) parsed by `changelog.Parse` gives `dpkg-parsechangelog
  --all --format rfc822`'s entries (source, version, distributions, urgency, maintainer,
  timestamp and the change lines) whenever dpkg reads it without a warning; when dpkg warns or
  fails, Parse may do as it likes (and when dpkg silently stops before the last entry, taking a
line for the old changelog format, the case is not judged). The urgency is compared lower-cased,
as dpkg reports it.

**`hegel/hegel_pins_test.go`**: one deterministic reproducer per recorded bug.

## Oracles and normalisations

dpkg 1.22 (Ubuntu 24.04 / the GitHub runner's `dpkg-dev`): `dpkg --validate-version` and
`--compare-versions` per case, `dpkg-parsechangelog` per generated changelog, and dpkg's Perl
library (`Dpkg::Deps`, `Dpkg::Arch`, `Dpkg::Version`, `Dpkg::Control::HashCore`) as one
persistent `perl` child (`hegel/oracle.go`: hex-encoded arguments in, JSON out). Both readings
are put in one shape and compared as text. Not judged, because the libraries differ by design
or the input is outside the format: names dpkg refuses (go-debian validates no package names)
and version texts with spaces or closing characters inside a relation; substvars (dpkg's parser
does not know them; their own round trip is tested); texts starting with `-` (dpkg's command
line) and texts padded with newlines (dpkg trims blanks only); architecture names in lists other
than dpkg's canonical spellings (go-debian normalises them through the tuple table); a
whitespace-only line inside a paragraph (a paragraph separator to dpkg, a continuation line to
go-debian - Policy 5.1 allows both) and leading or trailing whitespace on a value line (not
preserved by the format); dpkg capitalising field names on output; duplicate or malformed field
names (dpkg refuses, go-debian keeps the last value); restriction lists written without a space
between them (`<a><b>`, which dpkg reads as one profile `a><b`); changelog texts
`dpkg-parsechangelog` warns about.

## Known bugs (gated)

Eighteen bugs (`bugs.toml`): versions with an empty revision or upstream part, or an epoch
beyond INT_MAX, accepted; architecture wildcards padded with base/gnu instead of any (so `Is`
and `String` are wrong for `linux-any`); the deprecated `<`/`>` relations refused; `==`-style
relations accepted as `=`; whitespace before `)` kept in the version; whitespace inside `[]`
and `<>` lists and after an arch qualifier handled only as a single space; a zero epoch dropped
by `String()` when the upstream part has a colon; `[`/`<` lists glued to the name taken into
the name; substvars written without `${}`; a newline appended per continuation line (so
write/read cycles grow); dot lines neither escaped nor unescaped; whitespace-only, doubled-empty
and final empty value lines not written as ` .`; and, in changelogs, tab-indented change lines,
dates without a weekday or with a one-digit day, double spaces in the maintainer part,
comment lines and whitespace-only lines between entries refused. `hegel/known.go` gates them by generated shape; `HEGEL_NO_KNOWN=1` lifts
the gates.

## Not tested

The `deb` package (ar and tar reading, signature checks), OpenPGP clearsigned paragraphs,
`control`'s struct marshalling (`Unmarshal`/`Marshal`, `Changes`, `DSC`, `Index` files),
`hashio`, `Dependency` evaluation beyond parsing (no `implies`/`satisfies` API), `Paragraph.Update`.

## History

- 2026-09-20: written against cffc6a73b84de0ea4153fee14fa7084ed6a42d77 (2026-06-16, v0.21.0)
  with hegel.dev/go/hegel v0.6.33; 18 bugs.
