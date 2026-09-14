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
`Vcs`). Written in the zoo at 0.3.14 (debian-parsers commit `4dc04da`, 2026-09-05). The crate is a
workspace member: `subdir = "debian-control"`.

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

`[run] setup` checks that `Dpkg::Deps` and `Dpkg::Control::Info` load and warns when python-debian
is missing (that property then returns early).

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

## Bugs (27, all zoo-original)

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
