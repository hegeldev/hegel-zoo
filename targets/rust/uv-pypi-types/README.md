# uv-pypi-types

[uv-pypi-types](https://github.com/astral-sh/uv/tree/main/crates/uv-pypi-types) is the crate of
[uv](https://github.com/astral-sh/uv) holding its PyPI data types. This target covers its
**metadata module**: `Metadata23` (core metadata in the `METADATA`/`PKG-INFO` email format,
vendored from python-pkginfo-rs, plus the `core_metadata_format` writer), `ResolutionMetadata`
(`parse_metadata` for wheels, `parse_pkg_info` for sdists behind the Metadata-Version and
`Dynamic` gates of PEP 643, `parse_pyproject_toml` for PEP 621 projects), `Metadata10`,
`RequiresDist`, `PyProjectToml::requires_python`, and the `LenientRequirement` /
`LenientVersionSpecifiers` fix-ups for malformed PyPI metadata. Written in the zoo at 0.0.80 (uv
HEAD `c0df400`, 2026-09-12); tests in `crates/uv-pypi-types/tests/hegel.rs`, run in that
crate's directory (about one minute to build). The crate's other modules (`simple_json`,
`conflicts`, `parsed_url`, `identifier`, `module_name`) are open for later slices.

## The oracles

One persistent Python child (the first of `python3`, `/usr/bin/python3` that imports them;
`[run] setup` pip-installs/upgrades otherwise): PyPA's **`packaging.metadata.parse_email`**
(the specification's reference reader; raw dict + unparsed dict), **`packaging.requirements`**,
**`packaging.specifiers`**, **`packaging.version`**, **`packaging.utils.canonicalize_name`**,
and the PEP 621 reference **`pyproject_metadata.StandardMetadata.from_pyproject`**.

## Properties

- **Metadata23** (`metadata23_fields_match_packaging`): a generated `METADATA` — every core
  field in random header order, multi-use fields with several values, keywords, project URLs,
  the description as a header or as the body, non-ASCII values — parses to exactly
  `parse_email`'s raw dict with nothing unparsed; `FromStr` is `parse`; the value written by
  `core_metadata_format` parses back equal.
- **ResolutionMetadata** (`resolution_metadata_matches_packaging`): on the same files,
  `parse_metadata` gives the canonical name, `str(Version)`, `Requires-Dist` as packaging's
  requirements (name, specifiers, extras, marker), `Requires-Python` as its specifier set, the
  canonical extras and the dynamic-version flag; `parse_pkg_info` is the same read when
  Metadata-Version ≥ 2.2 and none of `Requires-Dist`/`Requires-Python`/`Provides-Extra` is
  `Dynamic`, the documented errors otherwise; `Metadata10` reads name and version.
- **Lenient parsing** (`lenient_parsing_is_transparent_on_valid_input`,
  `lenient_parsing_repairs_documented_breakages`): valid requirements and specifier sets pass
  through unchanged (and agree with packaging); each documented breakage — missing comma,
  `!=~X`, `>=X.*`, `!=N.N*`, trailing comma, `>dev`, `a1.0`, stray quotes, in `name spec`,
  `name (spec)` and marker forms — is repaired to the intended set, for single-digit
  components.
- **pyproject.toml** (`pyproject_metadata_matches_the_reference`): generated PEP 621 tables
  (name spellings, optional version/requires-python/dependencies, optional-dependencies with
  distinct extras, `dynamic` lists, a `[tool.poetry]` table) — `parse_pyproject_toml` (with and
  without an sdist version), `RequiresDist::from_pyproject_toml` and `requires_python()` agree
  with `pyproject_metadata` on the canonical name, version, requires-python, dependencies
  plus each extra's dependencies under `extra == '…'`, the canonical extras, and follow the
  crate's documented gates in `dynamic` order (dependencies/optional-dependencies/
  requires-python → error, version → error unless the sdist version is known, Poetry table
  without `dependencies` → error, no version → error).

## Bugs (2)

- **uv-pypi-types/1** (wrong-result, medium; `dynamic_field_names_are_case_insensitive`):
  `Dynamic` values are compared case-sensitively (`field == "Requires-Dist"`), where the
  format's field names are case-insensitive and `packaging` lowercases them — a `PKG-INFO`
  with `Dynamic: requires-dist` is trusted as static metadata, `Dynamic: version` is not seen.
- **uv-pypi-types/2** (contract, low; `lenient_fixups_handle_multi_digit_components`): the
  "missing dot" and "invalid tilde" fix-ups match single digits only — `!=3.10*` and
  `!=~5.10` are not repaired.

## Not bugs

- `UNKNOWN` values are dropped (distutils legacy); invalid `Provides-Extra` names are skipped
  with a warning in `ResolutionMetadata` (kept in `Metadata23`); a `Description` header plus a
  body gives the body (packaging: unparsed); duplicate `Project-URL` labels keep the last
  (packaging: unparsed); `Keywords` values are not trimmed (`a, b` → `" b"`; the
  specification only says "separated by commas", packaging strips); folded header values are
  unfolded with spaces (packaging keeps the fold) — the generators avoid these shapes.
- Extras are compared as sets (uv keeps a `[a,a]` list; packaging de-duplicates).
- A `Metadata-Version` like `02.2` or `2.10` is accepted by `parse_pkg_info`.
- 2026-09-14: base bumped c0df400a4cf4 → 83d556d712c7 (2026-09-14, "Scope required-environment checks to the current fork (#21672)"; 0.0.80); 2 bug(s) still reproduce. 53 tests pass.
- 2026-09-14: base bumped 83d556d712c7 → c40e652bc385 (2026-09-14, "Exclude backports-zstd from the Sentry PGO corpus (#21678)"; 0.0.80); 2 bug(s) still reproduce. 53 tests pass.
- 2026-09-14: base bumped c40e652bc385 → 85f73f491d4c (2026-09-14, "Use cargo nextest via astral-dev-toolchain (#21676)"; 0.0.80); 2 bug(s) still reproduce. 53 tests pass.
- 2026-09-14: base bumped 85f73f491d4c → 85fe61435fe5 (2026-09-14, "Use cargo bloat via astral-dev-toolchain (#21681)"; 0.0.80); 2 bug(s) still reproduce. 53 tests pass.
- 2026-09-15: base bumped 85fe61435fe5 → 941b557a69d7 (2026-09-14, "Remove unused Serde derives from index locations (#21685)"; 0.0.80); 2 bug(s) still reproduce. 53 tests pass.
- 2026-09-15: base bumped 941b557a69d7 → ffc98b158bad (2026-09-14, "Forbid install-action via zizmor (#21682)"; 0.0.80); 2 bug(s) still reproduce. 53 tests pass.
- 2026-09-15: base bumped ffc98b158bad → 643950ce49e4 (2026-09-14, "Update Rust crate async-trait to v0.1.92 (#21657)"; 0.0.80); 2 bug(s) still reproduce. 53 tests pass.
- 2026-09-15: base bumped 643950ce49e4 → b8aff80900e7 (2026-09-15, "Update dependency astral-sh/uv to v0.12.13 (#21655)"; 0.0.81); 2 bug(s) still reproduce. 53 tests pass.
- 2026-09-15: base bumped b8aff80900e7 → 000a665b745a (2026-09-15, "Batch HTTP cache writes in blocking tasks (#21675)"; 0.0.81); 2 bug(s) still reproduce. 53 tests pass.
- 2026-09-15: base bumped 000a665b745a → fd89f638d15f (2026-09-15, "Add regression test for symlinks inside install directory (#21693)"; 0.0.81); 2 bug(s) still reproduce. 53 tests pass.
- 2026-09-15: base bumped fd89f638d15f → a064ab2f6761 (2026-09-15, "Add regression test for `--target .` (#21695)"; 0.0.81); 2 bug(s) still reproduce. 53 tests pass.
- 2026-09-15: base bumped a064ab2f6761 → 2c35bb31de15 (2026-09-15, "Use Packse scenarios to speed up tool tests (#21634)"; 0.0.81); 2 bug(s) still reproduce. 53 tests pass.
- 2026-09-15: base bumped 2c35bb31de15 → ad552557b635 (2026-09-15, "Preserve local path intent when merging dependency metadata (#20631)"; 0.0.82); 2 bug(s) still reproduce. 53 tests pass.
- 2026-09-15: base bumped ad552557b635 → 694dfd8155ec (2026-09-15, "Verify distribution hashes (#21562)"; 0.0.82); 2 bug(s) still reproduce. 53 tests pass.
- 2026-09-15: base bumped 694dfd8155ec → ac9201b10433 (2026-09-15, "Allow manually specifying build dependency hashes in configuration (#21467)"; 0.0.82); 2 bug(s) still reproduce. 53 tests pass.
- 2026-09-15: base bumped ac9201b10433 → 1f245a625114 (2026-09-15, "Cover packaged editable self-dependency name mismatches (#21714)"; 0.0.82); 2 bug(s) still reproduce. 53 tests pass.
- 2026-09-15: base bumped 1f245a625114 → b44bd4561d97 (2026-09-15, "Use a small native extension in system Python tests (#21713)"; 0.0.82); 2 bug(s) still reproduce. 53 tests pass.
- 2026-09-15: base bumped b44bd4561d97 → bf12c8e61b2d (2026-09-15, "Enable Renovate updates for the release workflow (#21722)"; 0.0.82); 2 bug(s) still reproduce. 53 tests pass.
- 2026-09-15: base bumped bf12c8e61b2d → 7752bc92b53e (2026-09-15, "Update astral-sh/setup-uv action to v10.1.0 (#21666)"; 0.0.82); 2 bug(s) still reproduce. 53 tests pass.
- 2026-09-15: base bumped 7752bc92b53e → a265915acf9e (2026-09-15, "Expand Debian and official Python system-test images (#21726)"; 0.0.82); 2 bug(s) still reproduce. 53 tests pass.
- 2026-09-15: base bumped a265915acf9e → 27e80c1498d9 (2026-09-15, "renovate: update uv hashes correctly with setup-uv (#21724)"; 0.0.82); 2 bug(s) still reproduce. 53 tests pass.
- 2026-09-15: base bumped 27e80c1498d9 → b9df2d1d1ac7 (2026-09-15, "Move default-group selection onto project and workspace types (#21689)"; 0.0.82); 2 bug(s) still reproduce. 53 tests pass.
- 2026-09-15: base bumped b9df2d1d1ac7 → 9d8d76f4a13d (2026-09-15, "Use cargo-deny from toolchain (#21730)"; 0.0.82); 2 bug(s) still reproduce. 53 tests pass.
- 2026-09-16: base bumped 9d8d76f4a13d → c202b35405f1 (2026-09-15, "Encapsulate resolver metadata requests (#21735)"; 0.0.82); 2 bug(s) still reproduce. 53 tests pass.
- 2026-09-16: base bumped c202b35405f1 → 005d5cd9922b (2026-09-15, "Extract resolver requirement expansion (#21733)"; 0.0.82); 2 bug(s) still reproduce. 53 tests pass.
- 2026-09-16: base bumped 005d5cd9922b → f018faac8db2 (2026-09-16, "Update Python metadata for Pyodide 314.0.7, 0.29.5, 0.27.8 (#21741)"; 0.0.82); 2 bug(s) still reproduce. 53 tests pass.
- 2026-09-16: base bumped f018faac8db2 → f67344d87d2a (2026-09-16, "Skip `uv_build` fast path when pinned version differs (#21742)"; 0.0.82); 2 bug(s) still reproduce. 53 tests pass.
- 2026-09-16: base bumped f67344d87d2a → 3977dafee977 (2026-09-16, "Remove unused reqwest blocking feature from tests (#21749)"; 0.0.82); 2 bug(s) still reproduce. 53 tests pass.
- 2026-09-16: base bumped 3977dafee977 → bafbff9f631e (2026-09-16, "Respect artifact compatibility when initializing platform coverage (#21753)"; 0.0.82); 2 bug(s) still reproduce. 53 tests pass.
- 2026-09-16: base bumped bafbff9f631e → 108a3587b857 (2026-09-16, "Refactor HashDigest APIs (#21139)"; 0.0.82); 2 bug(s) still reproduce. 56 tests pass.
- 2026-09-16: base bumped 108a3587b857 → cc6880fd22c2 (2026-09-16, "Show captured publish test failures (#21757)"; 0.0.82); 2 bug(s) still reproduce. 56 tests pass.
- 2026-09-16: base bumped cc6880fd22c2 → 6b40d9e51d24 (2026-09-16, "Enforce non-staleness of cargo deny's `bans.build` list (#21756)"; 0.0.82); 2 bug(s) still reproduce. 56 tests pass.
- 2026-09-17: base bumped 6b40d9e51d24 → ec2783923893 (2026-09-17, "Add regression test for uv#21773 (#21775)"; 0.0.82); 2 bug(s) still reproduce. 56 tests pass.
- 2026-09-17: base bumped ec2783923893 → aa324fd49753 (2026-09-17, "Fix `uv check` without a workspace (#21777)"; 0.0.82); 2 bug(s) still reproduce. 56 tests pass.
- 2026-09-17: base bumped aa324fd49753 → 5e2ad786d5ae (2026-09-17, "Use astral-dev-toolchain for cargo-xwin (#21316)"; 0.0.82); 2 bug(s) still reproduce. 56 tests pass.
- 2026-09-17: base bumped 5e2ad786d5ae → 6dbe16aa4c1c (2026-09-17, "Reject unsupported Git URL schemes in lockfiles (#21779)"; 0.0.82); 2 bug(s) still reproduce. 56 tests pass.
- 2026-09-17: base bumped 6dbe16aa4c1c → 7cfd935f89de (2026-09-17, "Reject proxy URLs without a host (#21781)"; 0.0.82); 2 bug(s) still reproduce. 56 tests pass.
- 2026-09-17: base bumped 7cfd935f89de → 9ddc43085513 (2026-09-17, "Move shared thread initialization into uv-threads (#21746)"; 0.0.82); 2 bug(s) still reproduce. 56 tests pass.
- 2026-09-17: base bumped 9ddc43085513 → 5d64ede21e9e (2026-09-17, "Remove Hash API (#21786)"; 0.0.82); 2 bug(s) still reproduce. 56 tests pass.
- 2026-09-17: base bumped 5d64ede21e9e → 7bc36767ae3e (2026-09-17, "Avoid warning when both `native-tls` and `system-certs` are configured (#21806)"; 0.0.82); 2 bug(s) still reproduce. 56 tests pass.
- 2026-09-17: base bumped 7bc36767ae3e → 6dffe7e03898 (2026-09-17, "Ignore `UV_NATIVE_TLS` when `UV_SYSTEM_CERTS` is set (#21805)"; 0.0.82); 2 bug(s) still reproduce. 56 tests pass.
- 2026-09-17: base bumped 6dffe7e03898 → a2f820ad0ceb (2026-09-17, "Assign release pull requests to the workflow initiator (#21808)"; 0.0.82); 2 bug(s) still reproduce. 56 tests pass.
- 2026-09-17: base bumped a2f820ad0ceb → 761ff1379b3b (2026-09-17, "Bump version to 0.12.16 (#21809)"; 0.0.83); 2 bug(s) still reproduce. 56 tests pass.
- 2026-09-18: base bumped 761ff1379b3b → 6e093a90d45a (2026-09-17, "Avoid allocations for duplicate OnceMap registrations (#21810)"; 0.0.83); 2 bug(s) still reproduce. 56 tests pass.
- 2026-09-18: base bumped 6e093a90d45a → 46184d04b02e (2026-09-17, "Represent resolver package node kinds with an enum (#21802)"; 0.0.83); 2 bug(s) still reproduce. 56 tests pass.
- 2026-09-18: base bumped 46184d04b02e → d88bb84e7bd4 (2026-09-17, "Skip CI on `uv-security/main` (#21815)"; 0.0.83); 2 bug(s) still reproduce. 56 tests pass.
