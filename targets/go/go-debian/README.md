# go-debian

[paultag/go-debian](https://github.com/paultag/go-debian) (`pault.ag/go/debian`), the Debian
toolbelt for Go: package versions, dependency relationships, architectures, control-file
paragraphs and changelogs, against dpkg itself, which defines all of these formats.

## Build

The patch adds a `hegel/` package; `go test -count=1 -run TestHegel -v ./hegel/` needs dpkg
and dpkg's Perl modules (the `setup` commands of `target.toml` check them). A default run
takes a little over a minute, nearly all of it the shrinking of the twenty-six properties that
reach a bug, each shrink candidate drawn through the engine (the oracle's answers are memoised
and no longer the cost); under `HEGEL_NO_KNOWN=1` about thirty seconds at a thousand cases.

The properties are written to the repository's standard (STYLE.md rule 11): a `known` value
of nineteen switches, all off by default, one per recorded bug; each property's model
(`versionExpected`, `compareExpected`, `dependencyExpected`, `roundTripExpected`,
`archExpected`, `paragraphsExpected`, `writeExpected`, `changelogExpected`) states the
documented behaviour - dpkg's reading of the text, asked once per case and cached in the
record - with every switch off and, with a switch on, reproduces go-debian's rule for that bug
as a replica of its code (`parseInto`'s split at the last hyphen and its `ParseInt` epoch,
`String`'s zero epoch; `parseArchInto`'s padding with base/gnu and
`archToStringWithTupletable`; the parser's two-character operator, its `=` shortcut, the
untrimmed version number, the single-space list separators, the `[`/`<` fall-through into the
name; `Possibility.String`'s braceless substvar and its list written before the version;
`ParagraphReader.Next`'s newline per continuation line and its dot lines; `WriteTo`'s single
replacement of `"\n \n"` and its unescaped dot lines; `ParseOne`'s space-only indent, its
`RFC1123Z` date, its split at the first double space, its refusal of a comment line and its
exactly-`"\n"` blank line); the classifier runs the model per switch before the library is
called and names the shape of the bug a case is in, so the property fails naming it; under
`HEGEL_NO_KNOWN=1` the shapes are not drawn (the epochs beyond INT_MAX, the empty revision,
the colon after a zero epoch, the deprecated and the `=`-prefixed operators, the padding
before `)`, the tab and newline separators and `<>`, the glued lists, the substvars, a list
on a possibility that has a version, the dots-only and whitespace-only value lines, the
tab-indented and comment change lines, the rare dates and maintainers, the whitespace line
between entries) or are filtered out by the classifier (the wildcard pairs whose padding
changes a check, about three percent of the dependency cases whose whitespace composes
go-debian/7, the written values ending in an empty line), and the value checks of continued
fields - go-debian/11's shape, the format of nearly every control file - are dropped by the
judge (counted) while the keys, the order and the uncontinued values stay judged.

## Oracle

dpkg 1.22 (Ubuntu 24.04 / the GitHub runner's `dpkg-dev`): `dpkg --validate-version` and
`--compare-versions` per text, and dpkg's Perl library (`Dpkg::Deps`, `Dpkg::Arch`,
`Dpkg::Version`, `Dpkg::Control::HashCore`, and `Dpkg::Changelog::Debian` driven as
`dpkg-parsechangelog --all --format rfc822` drives it, checked identical to the process on 3000
changelogs) as one persistent `perl` child (`hegel/oracle.go`: hex-encoded arguments in, JSON
out; every answer memoised by its arguments). Both readings are put in one shape and compared as text. The
documented behaviour is dpkg's: `version.Parse` "verifies the version string as a whole, just
like dpkg(1)", Policy 7.1 for relationships, Dpkg::Arch for architectures. Not judged, because
the libraries differ by design or the input is outside the format: names dpkg refuses (go-debian
validates no package names) and version texts with spaces or closing characters inside a
relation; substvars in the parse property (dpkg's parser does not know them; their own round
trip is tested); texts padded with newlines (dpkg trims blanks only); a text dpkg only warns
about (Parse has no warnings, so its accept/reject is not judged); architecture names in lists
other than dpkg's canonical spellings (go-debian normalises them through the tuple table); a
whitespace-only line inside a paragraph and leading or trailing whitespace on a value line;
dpkg capitalising field names on output; duplicate or malformed field names; restriction lists
written without a space between them (`<a><b>`); changelog texts `dpkg-parsechangelog` warns
about.

## Properties

- `TestHegelVersionParseMatchesDpkg`: a version text (the epoch, the upstream pieces, a junk
  character, an inner hyphen, the revision pieces, the padding drawn as parts at the measured
  rates) parsed by `version.Parse` is accepted exactly when `dpkg --validate-version` reports
  no error, splits as `Dpkg::Version` splits it, and `String()` writes the canonical text (the
  zero epoch kept when the upstream part holds a colon), which parses back to the same version
  and compares equal to the text for dpkg. The shapes of go-debian/1 (twelve percent of the
  cases), 2 (four) and 8 (half a percent); over forty rounds at a hundred cases it shrinks to
  go-debian/1 every time (`0-`).
- `TestHegelCompareMatchesDpkg`: `version.Compare` on two to four clean versions built by
  construction (one often a mutation of the first: a `~`, a `+`, leading zeros, case, the
  epoch) has dpkg `--compare-versions`'s sign, is antisymmetric, and `sort.Sort(version.Slice)`
  leaves neighbours in dpkg's order; a text dpkg does not take cleanly or whose `String()` is
  not the text is assumed away (about one percent). No recorded bug lives here; it passes.
- `TestHegelDependencyParseMatchesDpkg`: a relationship field (package names, `:arch`
  qualifiers, version relations with every operator and spacing, architecture lists with and
  without negation, build-profile restriction lists, `,` and `|` with tabs, newlines and
  trailing commas, each part and the whitespace between parts drawn separately) parsed by
  `dependency.Parse` gives `Dpkg::Deps`'s reading when dpkg accepts the text, and every
  possibility of the reading written back with `Possibility.String()` is a text dpkg reads to
  that possibility; when dpkg refuses the text, Parse may refuse or read it, and its written
  possibilities must still read back the same. Two thirds of the cases are in the shape of a
  recorded bug (per 3000 cases: go-debian/3 782, 7 339, 4 278, 5 271, 6 238, 9 67, 19 58); over
  forty rounds at a hundred cases it fails every round, shrinking to go-debian/7
  (`libc6 < >`) and go-debian/9 (`libc6<!nocheck>`) by turns (26 to 14 in one run of forty,
  20 to 20 in another), so it is mapped to go-debian/7.
- `TestHegelDependencyStringRoundTrips`: for a text Parse reads (substvars included),
  `Parse(String(Parse(x)))` is `Parse(x)` (names, qualifiers, relations, architecture tuples,
  restriction lists) and `String` is stable; go-debian's own parser reads a list before or
  after the version, so go-debian/19 does not reach it. The shapes of go-debian/10 (four
  percent), 3 (six) and 7 (three); over forty rounds at a hundred cases it fails every round,
  shrinking to go-debian/10 (`${misc:Depends}`) about half the time (21 and 20 of forty in
  two runs), 7 and 3 the rest, so it is mapped to go-debian/10.
- `TestHegelArchMatchesDpkg`: `ParseArch` gives the tuple `Dpkg::Arch` gives
  (`debarch_to_debtuple`, or `debwildcard_to_debtuple` for wildcards), `String()` the
  canonical name, `Arch.Is` what `debarch_is` says and `ArchSet.Matches` what
  `debarch_is_concerned` says, over real architectures, wildcards and odd spellings; the
  padded wildcard of go-debian/3 in a fifth of the cases; over forty rounds it shrinks to
  go-debian/3 every time (`linux-any` against `amd64`).
- `TestHegelParagraphsMatchDpkg`: a control file (one to three paragraphs, fields with odd
  spacing around the colon and trailing whitespace, continuation lines with dots, empty and
  indented text, comment lines, blank lines, CRLF, no final newline, each part drawn
  separately) read by `control.ParagraphReader` gives `Dpkg::Control::HashCore`'s paragraphs:
  the same fields in order with the same values, or both refuse it; a text dpkg refuses for a
  key go-debian does not validate is not judged, a whitespace-only line inside a paragraph
  (a separator to dpkg, a continuation to go-debian, both allowed by Policy 5.1) is not drawn.
  Nine paragraphs in ten have a continuation line, go-debian/11's shape (the reader's dots
  line of 12 is named 11 first); over forty rounds at a hundred cases it shrinks to
  go-debian/11 every time (`Package: foo\n more\n`).
- `TestHegelParagraphWriteToMatchesDpkg`: a `Paragraph` with values of one to four lines
  (empty, dot-only, whitespace and indented lines, a leading or trailing newline) is written by
  `WriteTo` as HashCore writes the same fields (modulo trailing whitespace on a line) and
  reads back with `ParagraphReader` as dpkg reads HashCore's text back. The shapes of
  go-debian/12 (a dots-only line, 27 percent of the cases) and 16 (36) on the written text,
  go-debian/11 on the read-back of every multi-line value; over forty rounds at a hundred
  cases it shrinks to go-debian/16 every time (`Package: "a\n"`, written as a line of one
  space).
- `TestHegelChangelogMatchesDpkg`: a changelog of one to three entries (header lines with one
  or more distributions and the urgency and other options in the spellings dpkg meets; change
  lines with bullets, sections, blank lines, dashes and tabs; trailer lines with the date in
  the forms dpkg's grammar allows) parsed by `changelog.Parse` gives
  `Dpkg::Changelog::Debian`'s entries (source, version, distributions, urgency, maintainer,
  timestamp, change lines) whenever dpkg reads it without a warning; when dpkg warns or fails,
  or silently stops before the last entry, the case is noted, not judged - 87 percent of the
  population as the old test drew it (options dpkg warns about, invalid versions, a ` ;`
  header). The shapes of 13, 14, 15, 17 and 18 are the rare lines, dates, maintainers and
  the whitespace separator at their old rates (0.3 to 1.3 percent of the cases each); over
  forty rounds at a hundred cases it fails 28, shrinking to go-debian/14 (9 rounds), 15 (8),
  18 (8), 13 (2) and 17 (1), so it is mapped to go-debian/14 as intermittent.

One narrow property per bug, in the four shapes files, draws the bug's shape with random
surroundings and is judged by the same model, so it fails every run naming its bug by default
and passes under `HEGEL_NO_KNOWN=1`, where it draws the region past the shape:
`TestHegelEmptyRevisionsAreRefused` (go-debian/1), `TestHegelEpochsStopAtIntMax` (2),
`TestHegelWildcardsPadWithAny` (3), `TestHegelDeprecatedRelationsAreRead` (4),
`TestHegelUnknownRelationsAreRefused` (5), `TestHegelVersionPaddingIsTrimmed` (6),
`TestHegelListWhitespaceIsAnySpace` (7), `TestHegelZeroEpochsKeepTheirColon` (8),
`TestHegelGluedListsAreLists` (9), `TestHegelSubstvarsKeepTheirBraces` (10),
`TestHegelContinuationLinesJoinWithoutATrailingNewline` (11), `TestHegelDotLinesAreEscaped`
(12) and `TestHegelBlankValueLinesAreDotLines` (16, both judged on the written text alone so
that the read-back's go-debian/11 does not name the case first),
`TestHegelTabIndentedChangesAreRead` (13), `TestHegelDatesNeedNoWeekday` (14),
`TestHegelMaintainersMayHoldDoubleSpaces` (15), `TestHegelCommentLinesAreSkipped` (17),
`TestHegelWhitespaceLinesSeparateEntries` (18), `TestHegelVersionsAreWrittenBeforeLists` (19).

## Bugs

Nineteen, in `bugs.toml`: versions with an empty revision or upstream part (1), or an epoch
beyond INT_MAX (2), accepted; architecture wildcards padded with base/gnu instead of any, so
`Is` and `String` are wrong for `linux-any` (3); the deprecated `<`/`>` relations refused (4);
`==`-style relations accepted as `=` (5); whitespace before `)` kept in the version (6);
whitespace inside `[]` and `<>` lists and after an arch qualifier handled only as a single
space (7); a zero epoch dropped by `String()` when the upstream part has a colon (8); `[`/`<`
lists glued to the name taken into the name (9); substvars written without `${}` (10); a
newline appended per continuation line (11); dot lines neither escaped nor unescaped (12);
whitespace-only, doubled-empty and final empty value lines not written as ` .` (16); in
changelogs, tab-indented change lines (13), dates without a weekday or with a one-digit day
(14), double spaces in the maintainer part (15), comment lines (17) and whitespace-only lines
between entries (18) refused; and `Possibility.String()` writing the architecture list before
the version relation, an order dpkg refuses (19, found by the written-form check of the
dependency property). The replicas agree with the library on every shaped case in 3000.

## Not tested

The `deb` package (ar and tar reading, signature checks), OpenPGP clearsigned paragraphs,
`control`'s struct marshalling (`Unmarshal`/`Marshal`, `Changes`, `DSC`, `Index` files),
`hashio`, `Dependency` evaluation beyond parsing (no `implies`/`satisfies` API), `Paragraph.Update`.

## History

- 2026-09-20: written against cffc6a73b84de0ea4153fee14fa7084ed6a42d77 (2026-06-16, v0.21.0)
  with hegel.dev/go/hegel v0.6.33; 18 bugs.
- 2026-10-11: rewritten to the standard in two parts (the version and dependency properties,
  then the control and changelog ones); go-debian/19 found by the written-form check; 19 bugs.
