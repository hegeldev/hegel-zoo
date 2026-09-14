# uv-normalize

[uv-normalize](https://github.com/astral-sh/uv/tree/main/crates/uv-normalize) is the crate of
[uv](https://github.com/astral-sh/uv) that holds its validated, normalised names: `PackageName`,
`ExtraName` and `GroupName` (the [name normalization
specification](https://packaging.python.org/en/latest/specifications/name-normalization/), PEP
685, PEP 735), the pip-compatible `PipGroupName` (`--group [path:]name`), the lenient
`DistInfoName` for `.dist-info` directory names, and the `DefaultExtras`/`DefaultGroups`
serde shapes (`"all"` or a list). Written in the zoo at 0.0.80 (uv HEAD `c0df400`,
2026-09-12); tests in `crates/uv-normalize/tests/hegel.rs`, run in that crate's directory.

## The oracle

One persistent Python child (the first of `python3`, `/usr/bin/python3` that imports it; `[run]
setup` pip-installs/upgrades it if neither has `packaging` ≥ 26) running PyPA's
**`packaging.utils`** (26.3): `canonicalize_name(name, validate=True)` is the specification's
reference validator and normaliser, `canonicalize_name(name)` the lenient form `DistInfoName`
documents itself as, `is_normalized_name` the normal-form check. `PipGroupName` is checked
against **pip's `--group` callback** (`_handle_dependency_group`, pip ≥ 25.1 — the machine's pip
24.0 predates it, so its three lines are reproduced verbatim in the oracle script over
`pathlib.PurePath`) followed by `canonicalize_name` of the group name, as `dependency_groups`
does for pip.

## Properties

- **Names** (`names_normalize_like_packaging`): over strings from the name alphabet salted with
  other ASCII and non-ASCII characters, `PackageName`, `ExtraName`, `GroupName` (`from_str` and
  `from_owned`) accept exactly what `canonicalize_name(validate=True)` accepts and give the same
  text; the result is `is_normalized_name`, stable under re-parsing, and its own `Display`.
- **Equality** (`equality_is_equality_of_normal_forms`): two spellings (re-spellings by case
  flips and separator swaps, or independent names) are equal names iff packaging normalises
  them alike, and `Ord` follows the normalised text.
- **Serde** (`names_round_trip_through_serde`): names deserialise from any spelling
  (normalising, via `visit_str` and `visit_string`), serialise as the normalised text, round
  trip, and reject invalid spellings as errors.
- **Dist-info spelling** (`dist_info_spelling_escapes_dashes`): `as_dist_info_name` is the
  normalised name with `-` as `_`; `DistInfoName::new` of it is the package name again.
- **Lenient names** (`dist_info_names_normalize_like_packaging`): over ASCII text of any
  shape, `DistInfoName::new` is `canonicalize_name` without validation.
- **pip groups** (`pip_group_names_parse_like_pip`): `[path:]name` over a pool of paths
  (relative, absolute, `a:b/pyproject.toml`, non-`pyproject.toml` files, empty, `C:`) and
  names of every kind parses exactly when pip's callback accepts it, with pip's path and the
  normalised name; `Display` and serde round-trip.
- **Default lists** (`default_lists_round_trip_through_serde`): `DefaultExtras`/`DefaultGroups`
  serialise as `"all"` or the list of normalised names, deserialise from either shape
  (normalising raw spellings), reject any other string, and default to the empty list.

## Bugs (2)

- **uv-normalize/1** (wrong-result, low; `dist_info_names_handle_non_ascii_like_packaging`):
  `DistInfoName` works on bytes — when a non-ASCII name needs any normalisation each UTF-8 byte
  is pushed as a Latin-1 character (`Ä_x` → `Ã\u{84}-x`), and non-ASCII uppercase is never
  lowercased (`Ä` stays `Ä`; `canonicalize_name` gives `ä`).
- **uv-normalize/2** (contract, low; `pip_group_paths_are_checked_by_file_name`): the path of
  a `PipGroupName` is checked with `ends_with("pyproject.toml")`, so `notpyproject.toml:dev`
  or `dir/x-pyproject.toml:dev` are accepted where pip requires the *file name* to be
  `pyproject.toml`.

## Not bugs

- packaging's validation regex uses `re.IGNORECASE | re.ASCII` since 26.x; older releases
  case-folded `[A-Z]` in Unicode and accepted the Kelvin sign `K` and `ſ`. The crate rejects
  them, as the specification's regex does; `[run] setup` requires packaging ≥ 26.
- pip's `PurePath(path).name` strips a trailing slash, so pip accepts `x/pyproject.toml/:dev`
  and the crate does not; pip cannot open that path afterwards, so this is not counted.
- `DefaultExtras`/`DefaultGroups` accept only the exact string `"all"` (not `"ALL"`), as uv's
  documentation spells it.
