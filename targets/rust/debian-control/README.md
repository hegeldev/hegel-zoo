# debian-control

[debian-control](https://github.com/jelmer/debian-parsers/tree/main/debian-control) parses Debian
control files; the zoo tests its relationship-field parsers (`Depends:`, `Build-Depends:` and
friends) in `tests/hegel.rs`: the lossless rowan CST in `lossless::relations` (`Relations` →
`Entry` → `Relation` with setters, `ensure_*` helpers, `wrap_and_sort`, implication and
satisfaction checks, substvars) and the plain-struct parser in `lossy::relations`; and, in
`tests/hegel_control.rs`, the `debian/control` layer: `lossless::control` (`Control`, `Source`,
`Binary` getters/setters, `add_*`/`remove_binary`, `sort_binaries`, `wrap_and_sort`, range
queries, identities), `lossy::control`, the typed values in `fields` (`Priority`, `MultiArch`,
`Urgency`, `StandardsVersion`, `PackageListEntry`, `format_description`) and `vcs` (`ParsedVcs`,
`Vcs`); and, in `tests/hegel_files.rs`, the upload-side files: `lossless::changes::Changes`
(`.changes`), `lossless::buildinfo::Buildinfo` (`.buildinfo`, getters and setters), the checksum
entry types (`Md5Checksum`, `Sha1Checksum`, `Sha256Checksum`, `Sha512Checksum`, `changes::File`)
and `pgp::strip_pgp_signature`; and, in `tests/hegel_apt.rs`, the apt index stanzas:
`lossless::apt::{Package, Source, Release}` (Packages, Sources, Release/InRelease) and their
`lossy::apt` derive twins; and, in `tests/hegel_ftpmaster.rs`, `lossy::ftpmaster::Removal` (dak's
`removals.822` stanzas). That is every module of the crate. Written in the zoo at 0.3.14
(debian-parsers commit `4dc04da`, 2026-09-05). The crate is a workspace member:
`subdir = "debian-control"`.

## The oracles

- **dpkg's `Dpkg::Deps`** (dpkg 1.22; Perl, driven as a persistent child through `JSON::PP`):
  `deps_parse($text, build_dep => 1)` gives the structure (package, qualifier, relation, version,
  architecture list, restriction lists per simple dependency) and the canonical `output`;
  `$outer->implies($inner)` (`deps_eval_implication`, `_arch_is_superset`, `_restrictions_imply`)
  is the reference for `is_implied_by`; `get_evaluation` against a `Dpkg::Deps::KnownFacts` of
  installed packages is the reference for `satisfied_by`.
- **python-debian's `PkgRelation`** (2.0; the regexes dak and most Debian tooling use), a second
  persistent child: names, qualifiers, versions, architecture and profile flags of the same texts.

- **dpkg's `Dpkg::Control::Info`** (the parser `dpkg-source` reads `debian/control` with; a third
  persistent Perl child, `hegel_control.rs`): the source and per-package field sets of every
  generated, built, sorted or wrapped control file, and its structural errors.
- **lintian's `Vcs-*` regexes** (`Lintian::Check::Fields::Vcs`, same child) for the
  `<url> [-b <branch>] [[<path>]]` grammar of `Vcs-Git`/`Vcs-Hg`/`Vcs-Cvs`; **Debian Policy §5.6**
  is the generated model (field sets of the two paragraph kinds, `Rules-Requires-Root`,
  `Multi-Arch`, `Essential`, description paragraphs with `.` blank lines and verbatim lines).

- **dpkg's `Dpkg::Control` with a file type** (`CTRL_FILE_CHANGES`, `CTRL_FILE_BUILDINFO`; a Perl
  child in `hegel_files.rs`): the fields dpkg reads from a `.changes`/`.buildinfo`, whether it saw
  an OpenPGP signature (`is_pgp_signed`), and `field_is_allowed_in` for the model's field sets.
- **python-debian's `Changes`** (`Files`/`Checksums-*` entries, `get_pool_path`) and
  `Deb822.split_gpg_and_payload` (a Python child), **gpg** (`--clearsign` with an ephemeral key
  generated once per test process, on a fixed pool of payloads), and the layout `dpkg-genchanges`
  and `dpkg-genbuildinfo` write (probed on a real build) as the generated model.

- **dpkg's `Dpkg::Control` with an index type** (`CTRL_INDEX_PKG`, `CTRL_INDEX_SRC`,
  `CTRL_REPO_RELEASE`; a Perl child in `hegel_apt.rs`): the fields dpkg reads from a Packages,
  Sources or Release stanza (dpkg canonicalises the case of names it knows — `MD5sum`,
  `Description-Md5` — so names are compared case-insensitively).
- **python-debian's `Packages`/`Sources`/`Release`** (raw values; the typed `Files`/`Checksums-*`,
  `MD5Sum`/`SHA1`/`SHA256`/`SHA512` entry lists) and **apt's date parser** (`apt_pkg.str_to_time`,
  what apt accepts in `Date:`/`Valid-Until:`), one Python child; the layout `dpkg-scanpackages`,
  `dpkg-scansources` and apt-ftparchive write as the generated model; and, when the machine has
  them, the **real Packages and InRelease files under `/var/lib/apt/lists`** (Packages decompressed
  with `/usr/lib/apt/apt-helper cat-file`, up to 4000 stanzas; InRelease through
  `strip_pgp_signature`) as a corpus — the two corpus properties return early where there are none.
- **python-debian's `Deb822`** (raw fields, a Python child in `hegel_ftpmaster.rs`) and **dak's
  `removals.822`** itself: the 2026 file (3295 stanzas, fields `Date`/`Ftpmaster`/`Suite`/
  `Sources`/`Binaries`/`Reason`/`Bug`/`Also-Bugs`/`Also-WNPP`, list fields with the first entry
  on a continuation line, `Also-WNPP:` mostly empty) was surveyed for the model and seven of its
  stanzas are embedded as a corpus.

`[run] setup` checks that `Dpkg::Deps`, `Dpkg::Control::Info`, `Dpkg::Control`,
`Dpkg::Control::Types` and `Dpkg::Control::FieldsCore` load, that `gpg` is present, and warns when
python-debian/python-apt are missing (the relations property then returns early; `hegel_files.rs`
and `hegel_apt.rs` need them).

## Properties

- **Parsing**: generated fields of 0–4 entries with 1–3 alternatives, names with `.+-`, epochs,
  `~`, every operator, `:any`/`:native`/`:amd64`, architecture lists (wildcards, negated),
  restriction formulas of 1–2 lists, dpkg's whitespace freedoms (tabs, newlines anywhere `\s*` is
  allowed, `a,,b`, a trailing comma). The strict lossless parser and the lossy parser must read
  every field dpkg reads with dpkg's structure; each relation's canonical rendering
  (`wrap_and_sort`) and the lossy `Display` must be dpkg's `output`; python-debian must split the
  same way; the deprecated `<`/`>` must read as `<=`/`>=`.
- **The CST**: any text (mutated fields, junk, substvars) prints back verbatim from the relaxed
  parse, strict and relaxed agree on errors, the accessors do not panic on error-free trees;
  `Entry`/`Relation` `FromStr` are the single-entry/relation views.
- **Implication**: for pairs on the same package, `is_implied_by` claims exactly what dpkg's
  `implies` proves (version cells; qualifiers; alternative groups).
- **Satisfaction**: `satisfied_by` (lossless, lossy, per entry) against random installed sets
  equals dpkg's evaluation.
- **Editing**: 1–3 random edits (`set_version`, `drop_constraint`, `set_archqual`,
  `set_architectures`, `add_profile`, `Entry::push`, `remove_relation`, `remove_entry`, `push`,
  `insert`, `drop_dependency`, `add_dependency`, `ensure_minimum_version`, `ensure_exact_version`,
  `ensure_some_version`, `filter_entries`); after each, the accessors on the edited tree, a strict
  re-parse of its text and dpkg agree, and the edit's own promise holds. `wrap_and_sort` keeps the
  relations, sorts, is canonical and idempotent; `Ord` is total and consistent with `Eq`; substvars
  are listed, ensured once and dropped; the lossless and lossy builders and the conversions between
  them print what dpkg reads.

`debian/control` layer (`tests/hegel_control.rs`; generated files have a source paragraph with any
subset of the Policy source fields in random order and 0–3 binary paragraphs with `Package`,
`Architecture`, `Description` and optional others, any subset of the two-line descriptions with
`.` markers and verbatim lines, with or without a final newline):

- **Reading** (`control_files_are_read_like_dpkg`): `Control::to_string()` is the identity; every
  `Source`/`Binary` getter (name, maintainer, uploaders, identities and their email ranges, section,
  priority, standards version, relations, `vcs_git`, `vcs_browser`, homepage, rules-requires-root,
  testsuite, `is_qa_package`, architecture, multi-arch, essential, `description`) follows the model;
  `items()` gives the fields in order; dpkg reads the same source and package field sets; the
  range queries (`source_in_range`, `binaries_in_range`, `fields_in_range`, `overlaps_range`) find
  exactly the paragraph that owns the range.
- **Lossy** (`lossy_control_files_are_read_like_the_model`): the derive structs follow the model
  (no verbatim lines), `Display` re-parses to an equal value and is read by dpkg, and the two layers
  agree on the typed fields.
- **Vcs** (`vcs_git_values_parse_like_lintian`): lintian's regex, `ParsedVcs`, `Vcs::from_field` /
  `to_field` / `subpath` agree on url, branch and path in either order (single spaces); Hg and Cvs
  values likewise.
- **Typed fields** (`typed_fields_round_trip`): `Priority`, `MultiArch`, `Urgency`,
  `StandardsVersion` (components, `Ord`, `Display`→`FromStr`) and `PackageListEntry` (≤3 extras)
  survive a round trip; `format_description` indents and encodes blank lines.
- **Building** (`built_control_files_are_read_back`): a file built with `add_source`/`add_binary`
  and every setter is read back by the getters, by a re-parse (equal tree without verbatim lines),
  by dpkg, with the fields in `SOURCE_FIELD_ORDER`/`BINARY_FIELD_ORDER`; `remove_binary` removes
  exactly one paragraph.
- **Sorting and wrapping** (`sort_binaries_orders_the_paragraphs`,
  `wrap_and_sort_keeps_the_values_and_is_idempotent`): binaries end up in name order (`keep_first`
  honoured), every field is untouched / every value preserved, the source stays first, dpkg still
  reads the file, and `wrap_and_sort` is idempotent on the re-parsed text (no verbatim lines).

Upload-side files (`tests/hegel_files.rs`):

- **`.changes`** (`changes_files_are_read_like_dpkg_and_python_debian`): files laid out as
  dpkg-genchanges writes them (all standard fields, list fields one entry per continuation line,
  `Changes` with `.` blank lines, optional `Changed-By`/`Closes`) print back verbatim, every getter
  follows the model, `parse` has no errors, dpkg reads the same values and allows every field,
  python-debian's `Files`/`Checksums-*` entries and `get_pool_path` agree.
- **Signatures** (`clearsigned_files_are_split_like_python_debian_and_dpkg`): gpg-clearsigned
  payloads, also with CRLF, without a final newline or with an extra armor header, are split by
  `strip_pgp_signature` into python-debian's payload lines and the glued armor block; dpkg reads
  the same fields signed and unsigned; unsigned text passes through.
- **`.buildinfo`** (`buildinfo_files_are_read_like_dpkg`, `built_buildinfo_files_are_read_back`):
  the getters follow the model and dpkg on files laid out like dpkg-genbuildinfo's (single-line
  `Build-Tainted-By`, unquoted `Environment` — the real layouts are pinned), and a file built with
  `Buildinfo::new()` and every setter is read back by the getters, a re-parse and dpkg.
- **Checksum entries** (`checksum_entries_round_trip`): the four checksum types and
  `changes::File` survive `Display` → `FromStr`, accept extra whitespace and reject missing parts.

apt index files (`tests/hegel_apt.rs`; stanzas laid out as dpkg-scanpackages / dpkg-scansources /
apt-ftparchive write them, list fields one entry per continuation line, checksum lines with or
without apt's size padding, `.` blank lines in descriptions):

- **Packages** (`packages_stanzas_are_read_like_python_debian_and_dpkg`): the lossless text is
  the identity and every `Package` getter (name, version, sizes, maintainer, architecture, the nine
  relation fields, section, priority, description, homepage, source, checksums, `Description-md5`,
  `Tag`/`Task`, `Multi-Arch`) follows the model; the lossy struct follows the model and its
  `Display` re-parses to an equal value (with `Source:` without a version — pinned); python-debian
  reads the same raw fields; dpkg reads the same fields as a `CTRL_INDEX_PKG` stanza.
- **Sources** (`sources_stanzas_are_read_like_python_debian_and_dpkg`): likewise for `Source`
  (`binary()` entries, uploaders, `Vcs-*`, build relations, `Package-List`, `Directory`, `Files`
  and the three `Checksums-*` lists), the lossy struct (round trip with one binary and ≤1 trigger —
  pinned), python-debian's entry lists and dpkg's `CTRL_INDEX_SRC`.
- **Release** (`release_files_are_read_like_python_debian_apt_and_dpkg`): likewise for `Release`
  (`Date`/`Valid-Until` as the epoch seconds apt reads, with `+0000` dates — `UTC` is pinned;
  `NotAutomatic`/`ButAutomaticUpgrades`/`Acquire-By-Hash`, architectures, components, changelogs,
  the four checksum lists), the lossy struct and its round trip, python-debian's lists and dpkg's
  `CTRL_REPO_RELEASE`.
- **Corpus** (`real_packages_stanzas_are_read_by_both_layers`,
  `real_release_files_are_read_by_both_layers`): a random real stanza / InRelease payload prints
  back verbatim, the lossless getters agree with python-debian and the lossy struct with the
  lossless getters, the lossy `Display` round-trips (Packages without a source version), dpkg sees
  as many fields as python-debian, apt reads the `Date`.

Removals (`tests/hegel_ftpmaster.rs`): `removals_are_read_like_python_debian` — generated dak-style
stanzas (optional `Suite`, `Sources`, `Binaries` with `[arch, …]`, `Bug`, `Also-Bugs`, empty or
numbered `Also-WNPP`; list fields with the first entry on the key line — dak's layout is pinned)
are read field for field, python-debian sees the same values, and the struct's `to_paragraph()`
reads back equal and is read the same by python-debian; `real_removals_are_read_like_python_debian`
does the same on the embedded real stanzas (list entries compared without the pinned empty one).

## Bugs (40, all zoo-original)

Removals (found 2026-09-14):

- **debian-control/40** (medium) — `Removal::sources`/`binaries` start with an empty entry for
  every real dak stanza (`Sources:\n foo` — `lines()` keeps the empty key line).

apt index files (found 2026-09-14):

- **debian-control/35** (high) — `Release::date()`/`valid_until()` panic on every real Release
  file: chrono's RFC 2822 parser rejects the `UTC` zone name (and apt's space-padded hour).
- **debian-control/36** (medium) — `no_support_for_architecture_all()` reads
  `No-Support-For-Architecture-All: yes`; the field is `No-Support-for-Architecture-all: Packages`.
- **debian-control/37** (medium) — lossy `Package` `Display` writes `Source: name (= version)`,
  which the re-parse drops.
- **debian-control/38** (medium) — lossy `Source` `Display` joins `Binary`/`Testsuite-Triggers`
  with spaces; they read back as one entry.
- **debian-control/39** (medium) — the lossless `apt` getters panic on malformed values (`Version:
  1_2`, `Size: big`, `Homepage: not a url`, `Multi-Arch: maybe`, two-part checksum lines).

Upload-side files (found 2026-09-14):

- **debian-control/28** (medium) — `Changes::read`/`from_file` cannot read a clearsigned
  `.changes`; the crate's own `strip_pgp_signature` is never applied.
- **debian-control/29** (low) — `strip_pgp_signature` calls a blank line after the signature
  block junk.
- **debian-control/30** (medium) — `get_pool_path` puts `lib*` sources under `lib/` instead of
  `libX/` (python-debian's `source[:4]`).
- **debian-control/31** (medium) — `version()`, `urgency()`, `checksums_*()`, `files()` and
  `get_pool_path()` panic on malformed fields.
- **debian-control/32** (medium) — `Buildinfo::build_tainted_by`/`binaries` split on a single
  space; dpkg-genbuildinfo's one-tag-per-line field reads as one entry.
- **debian-control/33** (medium) — `Buildinfo::environment` keeps dpkg-genbuildinfo's `"…"`
  quoting and panics on a line without `=`.
- **debian-control/34** (low) — `set_environment` writes unquoted values in `HashMap` order.

`debian/control` layer (found 2026-09-14):

- **debian-control/19** (medium) — `Source::vcs()` is always `None`: it passes `Vcs-Git` to
  `Vcs::from_field`, which matches `Git`.
- **debian-control/20** (medium) — `rules_requires_root()` panics on Policy's `binary-targets` and
  `<namespace>/<case>` values; the lossy layer refuses such files.
- **debian-control/21** (low) — `multi_arch()` panics on an unknown value where `priority()`
  returns `None`.
- **debian-control/22** (low) — `Vcs::to_branch_url()` panics for a Git repository without a branch.
- **debian-control/23** (low) — `ParsedVcs` wants single spaces around `-b`/`[path]`; doubled
  spaces leak into the URL and branch, a tab hides them (lintian splits on `\s+`).
- **debian-control/24** (medium) — `Control::wrap_and_sort` turns verbatim description lines into
  ordinary ones.
- **debian-control/25** (low) — the lossy `description` drops the verbatim indentation the lossless
  `description()` keeps.
- **debian-control/26** (low) — `format_description` output fed to `set_description` is indented
  twice, mis-encoding the blank-line markers.
- **debian-control/27** (low) — `PackageListEntry` `Display` is `HashMap`-ordered and `FromStr`
  truncates `k=v=w`.

Relations (found 2026-09-13):

Medium:

- **debian-control/1** — negated architectures lose their `!`: `architectures()` returns
  `["amd64"]` for `[!amd64]`, `wrap_and_sort` writes the opposite restriction; the lossy parser
  rejects them.
- **debian-control/2** — the lossy parser's `<...>` loop mishandles whitespace: `<a b>` splits or
  fails, `< a>` opens an empty group, `<a >` is rejected; its `Display` writes `, ` inside a list.
- **debian-control/4** — `Relation::is_implied_by` ignores qualifiers, architecture lists and
  profiles (`pkg:any` "implied by" `pkg`).
- **debian-control/5** — `Entry::is_implied_by` says `a` is implied by `a | b`; the doc example
  encodes it, `ensure_relation` adds nothing.
- **debian-control/6** — `set_version` on `pkg:any` writes `pkg (>= 1):any`, unparsable for dpkg.
- **debian-control/7** — `Entry::from(Vec<Relation>)` writes `|` as a COMMA token; removing an
  alternative afterwards leaves `| b`.
- **debian-control/8** — `add_profile` replaces the existing restriction list instead of adding one.
- **debian-control/9** — `ensure_minimum_version` / `ensure_exact_version` drop the qualifier,
  architectures and profiles of the relation they update.
- **debian-control/11** — removing the last alternative of an entry leaves an empty entry that
  `len()` counts.
- **debian-control/12** — `version()` panics on any operator text outside the five spellings,
  including the deprecated `<` / `>` dpkg accepts and `a(a)`.
- **debian-control/15** — `pkg (>> V)` is not seen to imply `pkg (>= V)` (one `>` that should be `>=`).
- **debian-control/16** — `wrap_and_sort` writes the qualifier as bare tokens: `archqual()` is None
  on the result and a second pass drops `:any`.
- **debian-control/17** — `set_architectures` / `add_profile` on a relation without such a list
  splice in an immutable rowan node; the next edit (and the builder with two restriction lists)
  panics.
- **debian-control/18** — `Entry::push` on an entry inside a field nests the whole field into the
  entry: `a, b` becomes `a | c, b, b`, `len()` shrinks.

Low:

- **debian-control/3** — the lossy parser rejects a newline inside a relation.
- **debian-control/10** — `Ord` compares name and version only while `Eq` compares the qualifiers.
- **debian-control/13** — the lossy parser rejects the deprecated `<` / `>`.
- **debian-control/14** — `pkg (>= 1 )` (whitespace before `)`) is rejected by both parsers.

The general properties skip exactly the inputs each bug covers (`hits_*` helpers); each bug has
its own pinned test asserting dpkg's behaviour.

## Not bugs

- dpkg is lenient about `(=>1)` (relation `=`, version `>1`) and `a,,b`; the crate's strict parser
  rejecting the former is fine, the pin only demands no panic.
- python-debian's `<.+>` does not span lines (it never sees dpkg's line folding), so the
  python-debian property skips fields with newlines.
- dpkg's `implies` answers undef for `a | a` implying `a`; the implication generator keeps
  alternative names distinct.
- `deps_parse` dies on illegal architecture names, so the generator uses real ones and wildcards.
- `debian/control` layer, inherited from the deb822 crates and not recorded again: `items()`/`get()`
  drop the continuation indent entirely (documented in deb822-lossless; the raw-field comparison
  strips it, `description()` uses `get_multiline`), edits after a last line without a final
  newline glue lines (deb822-lossless/9; the sorting property forces the newline), and after
  `wrap_and_sort` the live tree is not the parse of its text (deb822-lossless/12; the property reads
  the re-parsed text). `set_description` with a verbatim line builds a tree whose tokens differ
  from the parse (values agree; `tree_eq` is skipped for it). `Homepage` is not in
  `BINARY_FIELD_ORDER`, so a set `Homepage` goes last — the model allows unknown fields after the
  ordered ones. `essential()` is `== "yes"` only (Policy spells it `yes`); `StandardsVersion`
  `Display` drops trailing zero components (`4.6.0` → `4.6`), which lintian does not object to;
  neither is recorded. The general generators avoid the pinned shapes: `Rules-Requires-Root: no`
  only, valid `Multi-Arch`, single-spaced Vcs values, no verbatim lines for the lossy and
  `wrap_and_sort` properties, `set_description` with the value convention, ≤3 `PackageListEntry`
  extras without `=` in the values.
- Upload-side files: `Changes` and `Buildinfo` implement neither `Display` nor (for `Changes`)
  `FromStr` — the tests read the text through `rowan::ast::AstNode::syntax()` and `Changes::read`;
  noted, not recorded. The leading empty line of a list field (`Files:\n …`) is dropped by
  `description()` (deb822-lossless/2, inherited). gpg's dash-escaping (`- ` before lines starting
  with `-` or `From `) is left in place by `strip_pgp_signature`, but dpkg's `Dpkg::Control::HashCore`
  and python-debian do the same, and no deb822 line starts that way; not recorded. The general
  generators avoid the pinned shapes: no `lib*` source names, well-formed fields, single-line
  `Build-Tainted-By`, unquoted `Environment` values, signed texts without a trailing blank line.
  gpg signs a fixed pool of six payloads once per process (an ephemeral ed25519 key in a temporary
  `GNUPGHOME`) so the property costs no signing per case.
- apt index files: the lossless `apt` types have no `Display` either (read through `syntax()`);
  `Package::tags(&self, field)` takes the field name (`tags("Tag")`) and `Source::binary()` returns
  the comma list as `Relations` — odd APIs, not bugs. chrono rejects a date whose weekday is wrong
  (`ParseError(Impossible)`) where apt ignores the weekday; RFC 5322 requires it to match, so the
  model uses correct weekdays and this is not recorded. `url::Url` normalises `Homepage`
  (`http://www.libreoffice.org` gains a `/`); the corpus property compares normalised forms. A
  paragraph ends at the first blank line, so an InRelease payload with two blank lines before the
  signature (Tailscale's) is compared with trailing newlines trimmed. The lossy `Release`/`Source`
  `Display` puts the first checksum entry on the key line after two spaces and double-indents the
  rest; it parses back, cosmetic. The general generators avoid the pinned shapes: `+0000` dates,
  `Source:` without a version, the lossy `Source` round trip only with one binary and ≤1 trigger,
  well-formed values.
- Removals: `Removal` has no `Display` and `to_paragraph()` is generic over the paragraph type
  (`let p: deb822_fast::Paragraph = r.to_paragraph()`); `Also-Bugs`/`Also-WNPP` are not modelled,
  so a round trip through the struct drops them (a lossy struct — noted, not recorded). The general
  generator writes list fields with the first entry on the key line; dak's layout is the pin.
- 2026-09-17: base bumped 4dc04da82229 → b1568f26a9e5 (2026-09-17, "Merge pull request #475 from jelmer/drop-minimal-versions"; 0.3.14); 40 bug(s) still reproduce. 401 tests pass.
