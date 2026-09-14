# pyproject-toml

[pyproject-toml](https://github.com/PyO3/pyproject-toml-rs) (PyO3's `pyproject.toml` parser,
used by maturin) deserialises `[build-system]` (PEP 517/518), `[project]` (PEP 621, the
pyproject.toml specification) and `[dependency-groups]` (PEP 735) into typed structs over
`pep440_rs`/`pep508_rs`, resolves dependency groups and self-referencing extras
(`PyProjectToml::resolve`), and — behind the `pep639-glob` feature — validates PEP 639
`license-files` globs (`check_pep639_glob`, `parse_pep639_glob`). Written in the zoo at 0.13.7
(HEAD `072336b`, 2026-02-25); tests in `tests/hegel.rs`, run with `--features pep639-glob`.

## The oracles

One persistent Python child (the first of `python3`, `/usr/bin/python3` that imports the
modules; `[run] setup` pip-installs them if neither does):

- **`dependency_groups`** — the PEP 735 reference implementation (`DependencyGroupResolver`):
  normalisation, include resolution, cycle and missing-group errors;
- **`tomllib`** — the raw document, compared field by field with the crate's structs
  (`serde_json::to_value`);
- **`pyproject_metadata`** — its `license-files` rejection of patterns escaping the project
  directory (`_get_files_from_globs`).

Alongside: a model of PEP 639's restricted glob grammar written from the PEP's text, a model
of the crate's documented self-reference expansion, and the serde round trip through `toml`.

## Properties

- **Dependency groups** (`dependency_groups_resolve_like_the_reference`): random
  `[dependency-groups]` tables — 1–5 groups in mixed spellings (distinct after normalisation),
  PEP 508 items, `include-group` tables naming existing groups by their declared spelling or a
  missing one, cycles included — resolve to the same requirement lists as the reference (order
  and duplicates kept), and fail exactly when the reference fails (cycle / missing group).
- **Self references** (`self_referencing_extras_expand_like_the_model`): `spam[test]` inside
  `[project.optional-dependencies]` and `[dependency-groups]` expands to the resolved
  requirements of extra `test`; missing extras and cycles are errors — against a model of the
  documented behaviour.
- **PEP 639 globs** (`license_globs_validate_like_pep_639`): 1–4 path components built from
  literals, `*`, `?`, character ranges, `**`, and the PEP's forbidden pieces (`[!a]`, `[a?]`,
  `\`, `!`, `@`, space, `**x`, `***`, `..x`): `parse_pep639_glob` accepts exactly the patterns
  the PEP allows, and every accepted pattern stays inside the project for `pyproject_metadata`.
- **The document** (`documents_deserialize_field_by_field_and_round_trip`): full documents from
  the `[build-system]`/`[project]`/`[dependency-groups]` grammars (readme string or table,
  license string or table, authors/maintainers, urls, scripts, gui-scripts, entry-points,
  optional-dependencies, license-files, dynamic, …) deserialise to exactly what `tomllib` reads,
  and `toml::to_string` → `PyProjectToml::new` is the identity.

The general generators stay away from the pinned shapes: includes and self references use the
declared spelling (bugs 1, 6), group names are distinct after normalisation (bug 2), include
tables carry one key (bug 3), globs have no leading slash (bug 4), the project name is
normalised (bug 5), license tables carry one key (bug 8).

## Bugs (8, all zoo-original, found 2026-09-14)

- **pyproject-toml/1** (medium) — `include-group` names are matched by exact text:
  `{include-group = "test-group"}` does not find `Test_Group` (PEP 735: normalise before
  comparing; the reference resolves it).
- **pyproject-toml/2** (low) — `a_b` and `a-b` are accepted as two groups (PEP 735: SHOULD be an
  error; the reference raises).
- **pyproject-toml/3** (low) — an include table with extra keys is accepted and the keys ignored
  (PEP 735: "a table with exactly one key").
- **pyproject-toml/4** (medium) — `/LICENSE` passes the PEP 639 glob check (the PEP: "the
  leading slash character MUST NOT be used"; `pyproject_metadata` rejects it).
- **pyproject-toml/5** (medium) — self references compare the requirement's normalised name
  with the project's raw name: with `name = "Spam_Egg"` no self reference is ever recognised.
- **pyproject-toml/6** (low) — an extra referred to in another spelling appears twice in
  `ResolvedDependencies::optional_dependencies` (`Test_X` and `test-x`).
- **pyproject-toml/7** (low) — `check_pep639_glob` accepts `LICENSE**`, `LICEN[CE`, `[`, which
  `parse_pep639_glob` then rejects.
- **pyproject-toml/8** (low) — `license = {text = …, file = …}` parses as `License::Text`,
  dropping the file (specification: MUST be an error).

## Not bugs

- The crate is a structural parser and says so: it does not validate SPDX expressions, the
  PEP 639 rule against combining `license-files` with a `license` table, `dynamic`, the
  validity of the project name or extra names (`String` fields with TODOs), or readme tables
  (`readme = {}` parses). None of these are counted; bug 8 is counted because the parse loses
  data it was given.
- `pep508_rs` renders requirements normalised (`Lobster_Thermidor` → `lobster-thermidor`,
  `python_version < '3.8'` → `python_full_version < '3.8'`); the document property uses
  normalised names and markers on string keys so that the field-by-field comparison is exact.
- The PEP 639 text leaves several shapes open (`""`, a trailing `/`, `//`, `.` components,
  `a..b` inside a component, `[z-a]`, non-ASCII letters, `x**`); the model follows the crate's
  reading where the PEP is silent and the generator avoids the rest.
- Resolution of self references is a crate feature beyond PEP 735 (the reference leaves
  `spam[test]` as a requirement); it is checked against a model of the crate's own doc.

## History

- 2026-09-14: created at 072336b (0.13.7); 8 bugs.
