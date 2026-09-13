# debian-control

[debian-control](https://github.com/jelmer/debian-parsers/tree/main/debian-control) parses Debian
control files; the zoo tests its relationship-field parsers (`Depends:`, `Build-Depends:` and
friends): the lossless rowan CST in `lossless::relations` (`Relations` → `Entry` → `Relation` with
setters, `ensure_*` helpers, `wrap_and_sort`, implication and satisfaction checks, substvars) and
the plain-struct parser in `lossy::relations`. Written in the zoo at 0.3.14 (debian-parsers commit
`4dc04da`, 2026-09-05). The crate is a workspace member: `subdir = "debian-control"`.

## The oracles

- **dpkg's `Dpkg::Deps`** (dpkg 1.22; Perl, driven as a persistent child through `JSON::PP`):
  `deps_parse($text, build_dep => 1)` gives the structure (package, qualifier, relation, version,
  architecture list, restriction lists per simple dependency) and the canonical `output`;
  `$outer->implies($inner)` (`deps_eval_implication`, `_arch_is_superset`, `_restrictions_imply`)
  is the reference for `is_implied_by`; `get_evaluation` against a `Dpkg::Deps::KnownFacts` of
  installed packages is the reference for `satisfied_by`.
- **python-debian's `PkgRelation`** (2.0; the regexes dak and most Debian tooling use), a second
  persistent child: names, qualifiers, versions, architecture and profile flags of the same texts.

`[run] setup` checks that `Dpkg::Deps` loads and warns when python-debian is missing (that property
then returns early).

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

## Bugs (18, all zoo-original)

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
