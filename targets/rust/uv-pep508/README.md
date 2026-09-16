# uv-pep508

[uv-pep508](https://github.com/astral-sh/uv/tree/main/crates/uv-pep508) is uv's fork of
[pep508_rs](../pep508_rs): Python dependency specifiers (PEP 508: `requests[security] >= 2.8.1,
== 2.8.* ; python_version > "3.8"`) and environment markers as a canonical marker algebra
(`MarkerTree`: `evaluate`, `negate`, `and`, `or`, `is_true`/`is_false`/`is_disjoint`, DNF
`Display`) — the engine uv resolves with. Written in the zoo at 0.0.80 (uv HEAD `c0df400`,
2026-09-12); tests in `crates/uv-pep508/tests/hegel.rs`, run in that crate's directory.

The test file is the zoo's `pep508_rs` file ported: `use uv_pep508`, `ExtraName` from
`uv-normalize`, `MarkerTree` is `Copy` and `and`/`or` return the combined tree. The fork also
reasons about the platform variables jointly — `platform_system == 'Linux'` *is* the node
`sys_platform == 'linux'` (likewise Windows/`win32`, Darwin/`darwin`, AIX, Android, Emscripten) and
known-impossible pairs such as `os_name == 'nt' and sys_platform == 'linux'` are `false` — so the
environment generator draws consistent (`os_name`, `sys_platform`, `platform_system`) triples, as
real interpreters report them.

## The oracle

**`packaging`** (PyPA's reference implementation, 26.3 here; `[run] setup` checks
`import packaging.requirements, packaging.markers` under `python3` and `/usr/bin/python3`),
driven as one persistent Python child over a hex-encoded line protocol:
`packaging.requirements.Requirement` for the grammar and the parsed parts (canonical name,
canonical extras, specifier set, URL, marker text); `packaging.markers.Marker.evaluate(env)` for
marker semantics on random environments (the eleven marker variables, plus `extra`); PEP 508's
text for the cases where `packaging` 26 knowingly deviates (below).

## Properties

- **Markers** (`markers_evaluate_like_packaging`): random well-formed marker expressions —
  version keys against version literals (2–3 components, wildcards, `~=`), inverted
  `'3.8' < python_version`, string keys with `==`/`!=`/`in`/`not in` against platform words and
  two-word lists, `extra ==`/`!=` in mixed spellings, the deprecated key spellings — joined by
  `and`/`or` with parentheses, evaluated on a random consistent environment with 0–1 extras: both
  implementations accept or reject alike and agree on the truth value; the crate's `Display`
  re-parses (by the crate, to an equivalent tree — structural equality is bug 6; by
  `packaging`, to the same truth value).
- **Marker algebra** (`marker_algebra_agrees_with_evaluation`): for two random markers,
  `negate`, `and`, `or` evaluate as ¬/∧/∨ on sampled environments; `is_true`, `is_false`,
  `is_disjoint` are never contradicted by an environment; `a ∧ a = a`, `¬¬a = a`, De Morgan on
  the canonical trees.
- **Requirements** (`requirements_parse_like_packaging`): texts from the PEP 508 grammar parse
  alike (canonical name, extras, specifier set, URL; the marker evaluates alike) and the crate's
  `Display` re-parses to an equivalent requirement for the crate and to the same parts for
  `packaging`.
- **Syntax near misses** (`requirement_syntax_agrees_with_packaging`): 1–2 random insertions,
  deletions or replacements in a valid requirement are accepted or rejected alike, for the plain
  name/extras/specifier shapes the grammar clearly decides; a panic is a failure.
- `python_version_compares_with_three_component_versions`, and four `pep508_rs` pins that **hold
  here because the fork fixed them**: `python_version == '3.5.0.*'` matches Python 3.5
  (pep508_rs/4), the deprecated key spellings make equal trees (pep508_rs/5), `python_version ~=
  '3.5.0'` keeps its last component (pep508_rs/6), an extra ending in a separator is an error, not
  a panic (pep508_rs/7).

The general generators stay away from the pinned shapes: no ordering operators on string keys
(bug 1 and `packaging`'s own deviation), `===` only with a version operand (bug 3), re-parsed trees compared by equivalence (bug 6), not at all for `false` trees (bug 2), environments are final releases (bug 4), `python_version !=
'X.Y.Z.*'` only with `Z = 0` (bug 5), and marker literals carry no pre-, post- or dev-release
segment (the crate's documented deviation, below).

## Bugs (6, found 2026-09-14; four inherited from `pep508_rs`, two new)

- **uv-pep508/1** (medium) — string-keyed markers compare lexicographically even when both sides
  are valid versions: `platform_release < '6'` is true for release `22.6.0`; PEP 508 says PEP 440
  rules apply then (`packaging` agrees) (pep508_rs/1).
- **uv-pep508/2** (low) — an unsatisfiable tree displays as `python_version < '0'`, which parses
  back to a satisfiable tree (`python_full_version < '0'`); `Requirement` `Display` → `from_str`
  does not round-trip a false marker (pep508_rs/2).
- **uv-pep508/3** (medium) — `a===a` (arbitrary equality with a non-version string) is rejected
  with "expected version to start with a number" (pep508_rs/3; root uv-pep440/5).
- **uv-pep508/4** (high) — on a pre-release interpreter (`python_full_version = 3.13.0rc1`)
  `python_version == '3.13'` is false and `python_version < '3.13'` true: the expression is lowered
  to a release-only `python_full_version` range and tested against the environment's real
  `3.13.0rc1` (pep508_rs/8).
- **uv-pep508/5** (medium, new) — `python_version != '3.5.1.*'` is the tree `false`, like its `==`
  twin; the complement of an unsatisfiable `==` must be `true` (as `python_version != '3.5.1'` is,
  and as `packaging` says). The fork's fix of pep508_rs/4 covers `X.Y.0.*` only.
- **uv-pep508/6** (medium, new) — `MarkerTree` is not canonical as documented: `X and ((X and A)
  or B)` with `A`, `B` on one string key leaves adjacent equal-child edges unmerged (five `os_name`
  ranges where the re-parse of its own `Display` has three), so two equivalent trees are `!=` and
  hash differently. `pep508_rs` has it too (pep508_rs/9).

## Not bugs

- `packaging` 26's marker evaluation deviates from PEP 508 in two places the zoo leaves out:
  ordering operators on string keys whose sides are not both versions answer `false` (the spec
  and the crate use Python string comparison), and `in`/`not in` on version keys are substring
  tests (the crate documents version-aware matching as a deliberate deviation).
- `packaging`'s tokenizer ends identifiers on `\b`, and `_` is a word character, so it accepts a
  name or extra ending in `_` (`a_`, `a[b_]`) that PEP 508's `identifier_end` forbids; the crate
  follows the grammar ("must end with an alphanumeric character"). It also tokenises `===0,` as
  the arbitrary string, accepts a trailing comma (`a>=1.0,`) and any non-space run as a URL; the
  crate warns and ignores "bogus" marker comparisons (`'a' == 'a'`, `extra > 'x'`) where
  `packaging` raises — documented leniency.
- The crate drops pre-, post- and dev-release segments from marker *literals*
  (`python_full_version == '3.13.0rc1'` is the tree `python_full_version == '3.13'`) so that its
  decision diagrams stay complementable — a deviation `src/marker/algebra.rs` documents; such
  literals are left out. (Testing the environment's un-stripped value against those ranges is
  bug 4.)
- `platform_system == 'Linux'` is false on an environment whose `sys_platform` is `darwin`: the
  fork treats the two variables as one for the well-known systems (see above), and no interpreter
  reports that combination.
- `python_version == '3.5.1.*'` and `python_version ~= '3.5.1'` are unsatisfiable: `python_version`
  is `X.Y`, so PEP 440 zero-pads it and neither can match (`packaging` agrees); only the `!=`
  (bug 5) is wrong.
- The crate's `Display` is a DNF normal form with single quotes; compared by meaning.

## History

- 2026-09-14: created at c0df400 (0.0.80); 6 bugs (4 inherited from pep508_rs, 2 new; uv-pep508/6 re-found in pep508_rs as pep508_rs/9).
- 2026-09-14: base bumped c0df400a4cf4 → 83d556d712c7 (2026-09-14, "Scope required-environment checks to the current fork (#21672)"; 0.0.80); 6 bug(s) still reproduce. 126 tests pass.
- 2026-09-14: base bumped 83d556d712c7 → c40e652bc385 (2026-09-14, "Exclude backports-zstd from the Sentry PGO corpus (#21678)"; 0.0.80); 6 bug(s) still reproduce. 126 tests pass.
- 2026-09-14: base bumped c40e652bc385 → 595c8e2c6812 (2026-09-14, "Use cargo codspeed via astral-dev-toolchain (#21674)"; 0.0.80); 6 bug(s) still reproduce. 126 tests pass.
- 2026-09-14: base bumped 595c8e2c6812 → 85fe61435fe5 (2026-09-14, "Use cargo bloat via astral-dev-toolchain (#21681)"; 0.0.80); 6 bug(s) still reproduce. 126 tests pass.
- 2026-09-15: base bumped 85fe61435fe5 → 941b557a69d7 (2026-09-14, "Remove unused Serde derives from index locations (#21685)"; 0.0.80); 6 bug(s) still reproduce. 126 tests pass.
- 2026-09-15: base bumped 941b557a69d7 → ffc98b158bad (2026-09-14, "Forbid install-action via zizmor (#21682)"; 0.0.80); 6 bug(s) still reproduce. 126 tests pass.
- 2026-09-15: base bumped ffc98b158bad → 2cc6abcd20dc (2026-09-14, "Update Rust crate futures to v0.3.34 (#21659)"; 0.0.80); 6 bug(s) still reproduce. 126 tests pass.
- 2026-09-15: base bumped 2cc6abcd20dc → b8aff80900e7 (2026-09-15, "Update dependency astral-sh/uv to v0.12.13 (#21655)"; 0.0.81); 6 bug(s) still reproduce. 126 tests pass.
- 2026-09-15: base bumped b8aff80900e7 → 000a665b745a (2026-09-15, "Batch HTTP cache writes in blocking tasks (#21675)"; 0.0.81); 6 bug(s) still reproduce. 126 tests pass.
- 2026-09-15: base bumped 000a665b745a → fd89f638d15f (2026-09-15, "Add regression test for symlinks inside install directory (#21693)"; 0.0.81); 6 bug(s) still reproduce. 126 tests pass.
- 2026-09-15: base bumped fd89f638d15f → a064ab2f6761 (2026-09-15, "Add regression test for `--target .` (#21695)"; 0.0.81); 6 bug(s) still reproduce. 126 tests pass.
- 2026-09-15: base bumped a064ab2f6761 → 2c35bb31de15 (2026-09-15, "Use Packse scenarios to speed up tool tests (#21634)"; 0.0.81); 6 bug(s) still reproduce. 126 tests pass.
- 2026-09-15: base bumped 2c35bb31de15 → ad552557b635 (2026-09-15, "Preserve local path intent when merging dependency metadata (#20631)"; 0.0.82); 6 bug(s) still reproduce. 127 tests pass.
- 2026-09-15: base bumped ad552557b635 → 694dfd8155ec (2026-09-15, "Verify distribution hashes (#21562)"; 0.0.82); 6 bug(s) still reproduce. 126 tests pass.
- 2026-09-15: base bumped 694dfd8155ec → ac9201b10433 (2026-09-15, "Allow manually specifying build dependency hashes in configuration (#21467)"; 0.0.82); 6 bug(s) still reproduce. 127 tests pass.
- 2026-09-15: base bumped ac9201b10433 → 1f245a625114 (2026-09-15, "Cover packaged editable self-dependency name mismatches (#21714)"; 0.0.82); 6 bug(s) still reproduce. 126 tests pass.
- 2026-09-15: base bumped 1f245a625114 → b44bd4561d97 (2026-09-15, "Use a small native extension in system Python tests (#21713)"; 0.0.82); 6 bug(s) still reproduce. 127 tests pass.
- 2026-09-15: base bumped b44bd4561d97 → bf12c8e61b2d (2026-09-15, "Enable Renovate updates for the release workflow (#21722)"; 0.0.82); 6 bug(s) still reproduce. 127 tests pass.
- 2026-09-15: base bumped bf12c8e61b2d → 7752bc92b53e (2026-09-15, "Update astral-sh/setup-uv action to v10.1.0 (#21666)"; 0.0.82); 6 bug(s) still reproduce. 127 tests pass.
- 2026-09-15: base bumped 7752bc92b53e → a265915acf9e (2026-09-15, "Expand Debian and official Python system-test images (#21726)"; 0.0.82); 6 bug(s) still reproduce. 127 tests pass.
- 2026-09-15: base bumped a265915acf9e → 27e80c1498d9 (2026-09-15, "renovate: update uv hashes correctly with setup-uv (#21724)"; 0.0.82); 6 bug(s) still reproduce. 127 tests pass.
- 2026-09-15: base bumped 27e80c1498d9 → 9d8d76f4a13d (2026-09-15, "Use cargo-deny from toolchain (#21730)"; 0.0.82); 6 bug(s) still reproduce. 127 tests pass.
- 2026-09-16: base bumped 9d8d76f4a13d → c202b35405f1 (2026-09-15, "Encapsulate resolver metadata requests (#21735)"; 0.0.82); 6 bug(s) still reproduce. 127 tests pass.
