# debian-changelog

[debian-changelog](https://github.com/jelmer/debian-parsers/tree/main/debian-changelog) is a
lossless (rowan CST) parser and editor for `debian/changelog` files: entries with their header
(`package (version) distributions; urgency=...`), change lines, `[ Author ]` sections and
trailer (` -- Name <email>  date`), plus helpers for `Closes:`/`LP:` bug references, building
and releasing entries, and wrapping change text. Written in the zoo at 0.2.24 (debian-parsers
commit `4dc04da`, 2026-09-05). The crate is a workspace member: `subdir = "debian-changelog"`.

## The oracles

- **`dpkg-parsechangelog`** (dpkg 1.22, `Dpkg::Changelog::Debian`), run per generated changelog
  with `--all --format rfc822`: its stanzas (`Source`, `Version`, `Distribution`, `Urgency`,
  `Maintainer`, `Date`, `Timestamp`, `Closes`, `Launchpad-Bugs-Fixed`, `Changes`) are the
  reference for the fields, its warnings say what is a policy "should" and its exit status what
  is not a changelog at all.
- **python-debian's `debian.changelog`** (a line-for-line port of dpkg's regexes), driven as a
  persistent `/usr/bin/python3` child (hex-encoded fields, one request per line) for the
  high-volume properties: the `closes:` / `lp:` bug-list regexes and the header/trailer splits.

`[run] setup` checks that `dpkg-parsechangelog` is present and warns when python-debian is not
(those properties then return early).

## Properties

- **Parsing** (`changelogs_parse_like_dpkg`): generated changelogs — 1–3 entries, package names
  with `.+-`, versions from the archive's shapes, 1–3 distributions, `urgency` in any case,
  `binary-only`, `X[BCS]-*` keys, bodies with bullets, continuation lines, `[ Author ]` sections,
  blank lines and bug references in many spellings, trailers with unicode names, empty names,
  weekday present/absent/wrong, one- and two-digit days, comments between entries, deliberate
  malformations (no distribution, no `;`, no version, one space before the date, no trailer).
  What dpkg reads cleanly the strict parser must read; what dpkg refuses the strict parser must
  refuse; every field, `datetime()`, `change_lines()` and the closed bug lists must agree.
  `header_and_trailer_lines_split_like_dpkg` does the same per line against python-debian.
- **The CST** (`the_tree_is_lossless_for_any_text`): strict and relaxed parses print the input
  back verbatim for any text (mutated changelogs, fragments, junk), the accessors never panic,
  `Parse::ok()` agrees with `from_str`; `entry_at_offset` / `entries_in_range` find the entry
  containing every offset; `from_iter` and `pop_first` keep the entries' text.
- **Bug references** (`bug_references_agree_with_the_reference_regexes`): `iter_bug_refs`,
  `bug_at_offset` and `bug_ref_spans` agree with each other and with dpkg's regexes.
- **Editing**: the builder's output is read back by dpkg and by the crate with the given fields
  (including `urgency()`); `new_entry()` goes on top as UNRELEASED with the incremented version;
  1–3 random setters (`set_package`, `set_version`, `set_distributions`, `set_urgency`,
  `set_metadata`, `set_maintainer`, `set_timestamp`, `set_datetime`, `append_change_line`,
  `prepend_change_line`, `add_bullet`) are visible in memory, in the re-parsed text and to dpkg;
  `add_bullet` keeps every word, indents continuation lines and keeps `Closes: #N` together;
  `try_add_changes_for_author` and `try_add_change_for_author` agree and open sections;
  `Urgency` round-trips in any case.

## Bugs (13, all zoo-original)

- **debian-changelog/2** (medium) — package and distribution names with `+` (`g++`,
  `libsigc++-2.0`) do not parse: the lexer's identifier characters lack `+`.
- **debian-changelog/6** (medium) — an entry built without an urgency has no `;` in its header;
  `dpkg-parsechangelog` fails on the file.
- **debian-changelog/9** (medium) — `prepend_change_line` inserts after the first blank line of
  the entry, so with no (or two) blank lines after the header the line lands after the existing
  changes (also through `ensure_first_line`, `take_uploadership`, `try_add_change_for_author`).
- **debian-changelog/11** (medium) — after `set_maintainer` / `set_timestamp` / `set_datetime`
  the accessors return `None` (a token is spliced where a node is expected) until re-parsed.
- **debian-changelog/12** (medium) — `set_metadata` adding a second key writes `; a=b c=d`
  without a comma; dpkg reads one option and loses the new key (or the urgency).
- **debian-changelog/1** (low) — the strict parser accepts headers without a distribution or
  without `;`, which dpkg does not recognise as headers.
- **debian-changelog/3** (low) — `datetime()` is `None` for dates dpkg reads: no weekday,
  one-digit day, trailing whitespace on the trailer line.
- **debian-changelog/4** (low) — bug lists are read more greedily than dpkg/dak/Launchpad:
  `Closes: #1 #2`, `#1,, #2`, `#1 , #2`, `#  5`, `lp:#12`, `LP: 12`, `LP: #1, 2`.
- **debian-changelog/5** (low) — `CLOSES:` (any case but `Closes:`/`closes:`) and `bug#NNN` /
  `bug NNN` items are not read; dpkg reads them.
- **debian-changelog/7** (low) — `Entry::try_add_change_for_author` on an entry without changes
  opens an empty `[ Maintainer ]` section; the `changes::` sibling does not.
- **debian-changelog/8** (low) — the `bugs` module does not read `Closes: # 123`, which dpkg and
  `find_closed_debian_bugs` do.
- **debian-changelog/10** (low) — `add_bullet` / `textwrap::textwrap` can exceed the documented
  78 columns (textwrap's optimal fit trades a small overflow for a ragged break).
- **debian-changelog/13** (low) — `bug_at_offset` returns the first number of the comma-delimited
  fragment, so a cursor on `456` in `Closes: #123 and LP: #456` yields `Debian(123)`.

The general properties skip exactly the inputs each bug covers (`hits_*` helpers); each bug has
its own pinned test asserting dpkg's behaviour.

## Not bugs

- `urgency=low (HIGH for security)`: dpkg accepts the annotation silently; the strict parser
  reports one error by design (upstream issue #466, the relaxed parse keeps the entry) — skipped.
- dpkg's `closes:` regex has no word boundary, so `Encloses: #7` closes #7 for dpkg; the `bugs`
  module deliberately requires one — not counted.
- A whitespace-only line at the end of the changes is a blank line for dpkg and a change line
  for the crate; the comparison trims such lines.
- Perl truthiness: `dpkg-parsechangelog` prints `Source: unknown` for a package named `0`
  (the generator does not produce it) and `Urgency: unknown` for a missing urgency.
- Tab-indented change lines (`\t* x`) are change data for dpkg (`\s{2,}`) but not for the crate;
  policy says spaces, so they are not generated.
