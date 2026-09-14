# r-description

[r-description-rs](https://github.com/jelmer/r-description-rs) parses and edits R package
`DESCRIPTION` files: a lossy `RDescription` struct (derived over `deb822-fast`), a lossless
`RDescription` over `deb822-lossless`, a rowan CST for the `Depends`/`Imports`/… relation
fields (`lossless::Relations`/`Relation`, with editing methods) and a lossy twin, plus
`Version` (R version numbers) and `VersionConstraint`. Written in the zoo at 0.4.1 (commit
`57dcf01`, 2026-07-25); tests in `tests/hegel.rs`.

## The oracle

**R itself** (`r-base-core`, R 4.3.3 here; `[run] setup` requires `Rscript`, CI installs it).
A persistent `Rscript` child answers with base R's own machinery, which is what defines the
format:

- `read.dcf` for the file format — field values, continuation lines (leading whitespace
  stripped, joined with `\n`, a lone `.` is an empty line), trimming;
- `tools:::.split_dependencies` / `.split_op_version` for the relations grammar (name, operator,
  version; whitespace after the operator is mandatory, anything after `)` is ignored,
  duplicate entries are dropped);
- `package_version` / `numeric_version` for version syntax and ordering — the ordering
  `loadNamespace` and `R CMD INSTALL` use to check requirements (`do.call(op, list(actual,
  required))`), under which trailing zero components do not count;
- `tools:::config_val_to_logical` (what `str_parse_logic` in `R CMD INSTALL` accepts) for
  logical fields such as `LazyData`;
- Writing R Extensions for what the code cannot show (the `URL` field is "a list of URLs
  separated by commas or whitespace").

## Properties

- **Versions**: random 2–5-component versions (with `-` separators and leading zeros) parse,
  normalise and order like `numeric_version`; random digit/dot/dash strings are accepted by
  `Version::from_str` exactly when `package_version` accepts them.
- **Relations**: an R-valid relations field (distinct names, optional `(<op><ws>version)`,
  arbitrary whitespace and continuation lines) reads the same through the lossy parser, the
  lossless parser and `.split_dependencies`; the lossless text is kept; every relation's own
  text re-parses; `wrap_and_sort` yields the sorted canonical model. A constrained relation is
  satisfied by an installed version exactly when R's `do.call(op, …)` says so (both parsers,
  `Relations` too).
- **Editing**: 1–6 random `push`/`insert`/`remove_relation`/`replace`/`set_version`/
  `drop_constraint` calls on a parsed lossless field keep the tree, its text (re-parsed by the
  crate and read by `.split_dependencies`) and a `Vec` model in step.
- **DESCRIPTION files**: the five fields the lossy struct requires plus a random subset of
  nineteen optional ones, in random order, with field-shaped values (multi-line descriptions,
  relation fields, URL lists with labels, dates, logicals): every field reads through the
  lossless getters and the lossy struct as `read.dcf` reads it, relation fields as
  `.split_dependencies` reads them; the lossless text is identical; the lossy struct round-trips
  through its own `Display` and R reads the same values from the rendering.
- **`UrlEntry`** round-trips through `Display` with and without a label.

The general generators stay away from the pinned shapes: versions end in a non-zero component
(bug 1), `insert(0, _)` is not applied to a one-relation list (bug 4), `LazyData` is
`true`/`false` (bug 5), no `.` continuation lines (bug 6), URL paths without parentheses and
URL lists separated by commas (bugs 8, 9).

## Bugs (9, all zoo-original, found 2026-09-14)

- **r-description/1** (medium) — `Version` orders `1.2` below `1.2.0`; `numeric_version` (the
  comparison R checks requirements with) treats them as equal, so `R (>= 3.5.0)` is unsatisfied
  by R 3.5 and `(== 1.2)` by 1.2.0.
- **r-description/2** (low) — `1.+2` parses as a version (`u32::from_str` takes a sign).
- **r-description/3** (medium) — `lossless::Relation::satisfied_by` is `true` for an
  unconstrained relation whose package is not installed; the lossy twin and R say no.
- **r-description/4** (medium) — `Relations::insert(0, R)` into `cli (>= 1.0)` writes
  `Rcli (>= 1.0)`: the one-relation list is taken for empty (no comma) and no separator is added.
- **r-description/5** (medium) — `lazy_data()` is `Some(false)` for `LazyData: TRUE` / `yes`,
  spellings `R CMD INSTALL` accepts.
- **r-description/6** (low) — a ` .` continuation line (an empty line to `read.dcf`) is kept as
  a literal `.`.
- **r-description/7** (low) — the lossless accessors `unwrap()`: `imports()` panics on
  `foo (>= 1.0) bar` (R reads `foo (>= 1.0)`), `bug_reports()` on any non-URL text.
- **r-description/8** (low) — `UrlEntry` splits a URL at its first `(`
  (`…/R_(programming_language)` → URL `…/R_`, label `programming_language`).
- **r-description/9** (medium) — a whitespace-separated `URL` list, allowed by Writing R
  Extensions, is read as the single URL `https://a.org/%20https://b.org/`.

## Not bugs

- R's `.split_dependencies` drops duplicate entries (`unique`) and keeps empty ones (`a,,b`); the
  crate does the reverse. R is stricter about whitespace (`cli(>=3.4.0)` and `( >= 1.0 )` are
  errors in R, the crate accepts them) and ignores text after `)`; a name with `_` is an R
  package-name error and a crate parse error. The properties generate the grammar both accept.
- R has two orderings: `utils::compareVersion` says `1.2 < 1.2.0`, `numeric_version` says
  equal; the dependency machinery uses the latter, so that is the oracle (bug 1).
- `package_version` turns a component above `.Machine$integer.max` into `NA`; not generated.
- The lossy struct reorders fields, normalises `Version` (`1.2-3` → `1.2.3`), re-renders
  relation and URL fields and drops fields it has no member for (`Enhances`, `RoxygenNote`,
  `Roxygen`); the property compares its rendering with R at the level of values, not text.
- The `url` crate normalises `/.` and `/..` path segments; generated URL paths have no dots.

## History

- 2026-09-14: created at 57dcf01 (0.4.1); 9 bugs.
