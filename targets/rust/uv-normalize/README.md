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
- 2026-09-14: base bumped c0df400a4cf4 → 83d556d712c7 (2026-09-14, "Scope required-environment checks to the current fork (#21672)"; 0.0.80); 2 bug(s) still reproduce. 12 tests pass.
- 2026-09-14: base bumped 83d556d712c7 → c40e652bc385 (2026-09-14, "Exclude backports-zstd from the Sentry PGO corpus (#21678)"; 0.0.80); 2 bug(s) still reproduce. 12 tests pass.
- 2026-09-14: base bumped c40e652bc385 → 595c8e2c6812 (2026-09-14, "Use cargo codspeed via astral-dev-toolchain (#21674)"; 0.0.80); 2 bug(s) still reproduce. 12 tests pass.
- 2026-09-14: base bumped 595c8e2c6812 → 85fe61435fe5 (2026-09-14, "Use cargo bloat via astral-dev-toolchain (#21681)"; 0.0.80); 2 bug(s) still reproduce. 12 tests pass.
- 2026-09-15: base bumped 85fe61435fe5 → 941b557a69d7 (2026-09-14, "Remove unused Serde derives from index locations (#21685)"; 0.0.80); 2 bug(s) still reproduce. 12 tests pass.
- 2026-09-15: base bumped 941b557a69d7 → ffc98b158bad (2026-09-14, "Forbid install-action via zizmor (#21682)"; 0.0.80); 2 bug(s) still reproduce. 12 tests pass.
- 2026-09-15: base bumped ffc98b158bad → 6f7795bb4f6e (2026-09-14, "Update Rust crate axoupdater to v0.10.2 (#21658)"; 0.0.80); 2 bug(s) still reproduce. 12 tests pass.
- 2026-09-15: base bumped 6f7795bb4f6e → b8aff80900e7 (2026-09-15, "Update dependency astral-sh/uv to v0.12.13 (#21655)"; 0.0.81); 2 bug(s) still reproduce. 12 tests pass.
- 2026-09-15: base bumped b8aff80900e7 → 000a665b745a (2026-09-15, "Batch HTTP cache writes in blocking tasks (#21675)"; 0.0.81); 2 bug(s) still reproduce. 12 tests pass.
- 2026-09-15: base bumped 000a665b745a → fd89f638d15f (2026-09-15, "Add regression test for symlinks inside install directory (#21693)"; 0.0.81); 2 bug(s) still reproduce. 12 tests pass.
- 2026-09-15: base bumped fd89f638d15f → cdabfcedb50b (2026-09-15, "Revert "Reject symlinked wheel installation destinations" (#21699)"; 0.0.81); 2 bug(s) still reproduce. 12 tests pass.
- 2026-09-15: base bumped cdabfcedb50b → 2c35bb31de15 (2026-09-15, "Use Packse scenarios to speed up tool tests (#21634)"; 0.0.81); 2 bug(s) still reproduce. 12 tests pass.
- 2026-09-15: base bumped 2c35bb31de15 → ad552557b635 (2026-09-15, "Preserve local path intent when merging dependency metadata (#20631)"; 0.0.82); 2 bug(s) still reproduce. 12 tests pass.
- 2026-09-15: base bumped ad552557b635 → 694dfd8155ec (2026-09-15, "Verify distribution hashes (#21562)"; 0.0.82); 2 bug(s) still reproduce. 12 tests pass.
- 2026-09-15: base bumped 694dfd8155ec → ac9201b10433 (2026-09-15, "Allow manually specifying build dependency hashes in configuration (#21467)"; 0.0.82); 2 bug(s) still reproduce. 12 tests pass.
- 2026-09-15: base bumped ac9201b10433 → 1f245a625114 (2026-09-15, "Cover packaged editable self-dependency name mismatches (#21714)"; 0.0.82); 2 bug(s) still reproduce. 12 tests pass.
- 2026-09-15: base bumped 1f245a625114 → b44bd4561d97 (2026-09-15, "Use a small native extension in system Python tests (#21713)"; 0.0.82); 2 bug(s) still reproduce. 12 tests pass.
- 2026-09-15: base bumped b44bd4561d97 → bf12c8e61b2d (2026-09-15, "Enable Renovate updates for the release workflow (#21722)"; 0.0.82); 2 bug(s) still reproduce. 12 tests pass.
- 2026-09-15: base bumped bf12c8e61b2d → 7752bc92b53e (2026-09-15, "Update astral-sh/setup-uv action to v10.1.0 (#21666)"; 0.0.82); 2 bug(s) still reproduce. 12 tests pass.
- 2026-09-15: base bumped 7752bc92b53e → a265915acf9e (2026-09-15, "Expand Debian and official Python system-test images (#21726)"; 0.0.82); 2 bug(s) still reproduce. 12 tests pass.
- 2026-09-15: base bumped a265915acf9e → 27e80c1498d9 (2026-09-15, "renovate: update uv hashes correctly with setup-uv (#21724)"; 0.0.82); 2 bug(s) still reproduce. 12 tests pass.
- 2026-09-15: base bumped 27e80c1498d9 → b9df2d1d1ac7 (2026-09-15, "Move default-group selection onto project and workspace types (#21689)"; 0.0.82); 2 bug(s) still reproduce. 12 tests pass.
- 2026-09-15: base bumped b9df2d1d1ac7 → 9d8d76f4a13d (2026-09-15, "Use cargo-deny from toolchain (#21730)"; 0.0.82); 2 bug(s) still reproduce. 12 tests pass.
- 2026-09-16: base bumped 9d8d76f4a13d → c202b35405f1 (2026-09-15, "Encapsulate resolver metadata requests (#21735)"; 0.0.82); 2 bug(s) still reproduce. 12 tests pass.
- 2026-09-16: base bumped c202b35405f1 → 005d5cd9922b (2026-09-15, "Extract resolver requirement expansion (#21733)"; 0.0.82); 2 bug(s) still reproduce. 12 tests pass.
- 2026-09-16: base bumped 005d5cd9922b → f018faac8db2 (2026-09-16, "Update Python metadata for Pyodide 314.0.7, 0.29.5, 0.27.8 (#21741)"; 0.0.82); 2 bug(s) still reproduce. 12 tests pass.
- 2026-09-16: base bumped f018faac8db2 → f67344d87d2a (2026-09-16, "Skip `uv_build` fast path when pinned version differs (#21742)"; 0.0.82); 2 bug(s) still reproduce. 12 tests pass.
- 2026-09-16: base bumped f67344d87d2a → 3977dafee977 (2026-09-16, "Remove unused reqwest blocking feature from tests (#21749)"; 0.0.82); 2 bug(s) still reproduce. 12 tests pass.
- 2026-09-16: base bumped 3977dafee977 → bafbff9f631e (2026-09-16, "Respect artifact compatibility when initializing platform coverage (#21753)"; 0.0.82); 2 bug(s) still reproduce. 12 tests pass.
- 2026-09-16: base bumped bafbff9f631e → 108a3587b857 (2026-09-16, "Refactor HashDigest APIs (#21139)"; 0.0.82); 2 bug(s) still reproduce. 12 tests pass.
- 2026-09-16: base bumped 108a3587b857 → cc6880fd22c2 (2026-09-16, "Show captured publish test failures (#21757)"; 0.0.82); 2 bug(s) still reproduce. 12 tests pass.
- 2026-09-16: base bumped cc6880fd22c2 → 6b40d9e51d24 (2026-09-16, "Enforce non-staleness of cargo deny's `bans.build` list (#21756)"; 0.0.82); 2 bug(s) still reproduce. 12 tests pass.
- 2026-09-17: base bumped 6b40d9e51d24 → ec2783923893 (2026-09-17, "Add regression test for uv#21773 (#21775)"; 0.0.82); 2 bug(s) still reproduce. 12 tests pass.
- 2026-09-17: base bumped ec2783923893 → aa324fd49753 (2026-09-17, "Fix `uv check` without a workspace (#21777)"; 0.0.82); 2 bug(s) still reproduce. 12 tests pass.
- 2026-09-17: base bumped aa324fd49753 → 5e2ad786d5ae (2026-09-17, "Use astral-dev-toolchain for cargo-xwin (#21316)"; 0.0.82); 2 bug(s) still reproduce. 12 tests pass.
- 2026-09-17: base bumped 5e2ad786d5ae → 6dbe16aa4c1c (2026-09-17, "Reject unsupported Git URL schemes in lockfiles (#21779)"; 0.0.82); 2 bug(s) still reproduce. 12 tests pass.
- 2026-09-17: base bumped 6dbe16aa4c1c → 7cfd935f89de (2026-09-17, "Reject proxy URLs without a host (#21781)"; 0.0.82); 2 bug(s) still reproduce. 12 tests pass.
- 2026-09-17: base bumped 7cfd935f89de → ef1e0689b461 (2026-09-17, "Make Git stamping opt-in for development builds (#21750)"; 0.0.82); 2 bug(s) still reproduce. 12 tests pass.
- 2026-09-17: base bumped ef1e0689b461 → 5d64ede21e9e (2026-09-17, "Remove Hash API (#21786)"; 0.0.82); 2 bug(s) still reproduce. 12 tests pass.
- 2026-09-17: base bumped 5d64ede21e9e → 7bc36767ae3e (2026-09-17, "Avoid warning when both `native-tls` and `system-certs` are configured (#21806)"; 0.0.82); 2 bug(s) still reproduce. 12 tests pass.
- 2026-09-17: base bumped 7bc36767ae3e → 6dffe7e03898 (2026-09-17, "Ignore `UV_NATIVE_TLS` when `UV_SYSTEM_CERTS` is set (#21805)"; 0.0.82); 2 bug(s) still reproduce. 12 tests pass.
- 2026-09-17: base bumped 6dffe7e03898 → a2f820ad0ceb (2026-09-17, "Assign release pull requests to the workflow initiator (#21808)"; 0.0.82); 2 bug(s) still reproduce. 12 tests pass.
- 2026-09-17: base bumped a2f820ad0ceb → 761ff1379b3b (2026-09-17, "Bump version to 0.12.16 (#21809)"; 0.0.83); 2 bug(s) still reproduce. 12 tests pass.
- 2026-09-18: base bumped 761ff1379b3b → 6e093a90d45a (2026-09-17, "Avoid allocations for duplicate OnceMap registrations (#21810)"; 0.0.83); 2 bug(s) still reproduce. 12 tests pass.
