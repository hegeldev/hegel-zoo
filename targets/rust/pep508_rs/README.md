# pep508_rs

[pep508_rs](https://github.com/konstin/pep508_rs) parses Python dependency specifiers
(PEP 508: `requests[security] >= 2.8.1, == 2.8.* ; python_version > "3.8"`) and implements
environment markers as a canonical marker algebra (`MarkerTree`: `evaluate`, `negate`, `and`,
`or`, `is_true`/`is_false`/`is_disjoint`, DNF `Display`) — the engine uv resolves with (now
developed in astral-sh/uv as `uv-pep508`; this crate is its standalone release). Written in the
zoo at 0.9.2 (HEAD `b50980e`, 2026-02-02); tests in `tests/hegel.rs`.

## The oracle

**`packaging`** (PyPA's reference implementation, 26.3 here; `[run] setup` checks
`python3 -c 'import packaging.requirements, packaging.markers'`), driven as one persistent
`python3` child over a hex-encoded line protocol — the same arrangement as the zoo's
`pep440_rs` target:

- `packaging.requirements.Requirement` for the grammar and the parsed parts (canonical name,
  canonical extras, specifier set, URL, marker text);
- `packaging.markers.Marker.evaluate(env)` for marker semantics on random environments (the
  eleven marker variables, plus `extra`);
- PEP 508's text for the cases where `packaging` 26 knowingly deviates (see below).

## Properties

- **Markers** (`markers_evaluate_like_packaging`): random well-formed marker expressions —
  version keys against version literals (with wildcards, pre-releases, `~=`), inverted
  `'3.8' < python_version`, string keys with `==`/`!=`/`in`/`not in` against platform words and
  two-word lists, `'lin' in sys_platform`, `extra ==`/`!=` in mixed spellings, the deprecated
  key spellings — joined by `and`/`or` with parentheses, evaluated on a random environment
  with 0–1 extras: both implementations accept or reject alike and agree on the truth value;
  the crate's `Display` re-parses (by the crate, to an equivalent tree — structural equality is
  bug 9; by `packaging`, to the same truth value).
- **Marker algebra** (`marker_algebra_agrees_with_evaluation`): for two random markers,
  `negate`, `and`, `or` evaluate as ¬/∧/∨ on sampled environments; `is_true`, `is_false`,
  `is_disjoint` are never contradicted by an environment; `a ∧ a = a`, `¬¬a = a`, De Morgan on
  the canonical trees.
- **Requirements** (`requirements_parse_like_packaging`): texts from the PEP 508 grammar —
  names, extras with whitespace, 1–3 version specifiers (optionally parenthesised) or a URL, an
  optional marker — parse alike: same canonical name, extras, specifier set, URL; the marker
  evaluates alike; the crate's `Display` re-parses to an equivalent requirement for the crate and to
  the same parts for `packaging`.
- **Syntax near misses** (`requirement_syntax_agrees_with_packaging`): 1–2 random insertions,
  deletions or replacements in a valid requirement are accepted or rejected alike, for the
  plain name/extras/specifier shapes the grammar clearly decides (URLs, markers, trailing
  commas and names ending in `_` — `aa_`, which `packaging`'s `\b`-delimited IDENTIFIER token
  passes against the spec's name grammar — are where `packaging` is knowingly lenient; the
  last showed up as a rare CI failure on 2026-09-17).
- `python_version_compares_with_three_component_versions`: `python_version <op> '3.X.Y'`
  agrees with `packaging` for the six comparison operators.

The general generators stay away from the pinned shapes: no ordering operators on string
keys (bug 1 and `packaging`'s own deviation), `~=` on version keys only with two components
(bug 6), wildcards on `python_version` only with two components (bug 4), `===` only with a
version operand and alone in its specifier list (bug 3 and a `packaging` tokenizer quirk),
tree equality skipped for `false` trees and deprecated spellings (bugs 2, 5), extras never end
in a separator (bug 7), environments are final releases (bug 8) and marker literals carry no
pre-, post- or dev-release segment (the crate's documented deviation, below).

## Bugs (9, all zoo-original, found 2026-09-14)

- **pep508_rs/1** (medium) — string-keyed markers compare lexicographically even when both
  sides are valid versions: `platform_release < '6'` is true for release `22.6.0`; PEP 508 says
  PEP 440 rules apply then (`packaging` agrees).
- **pep508_rs/2** (low) — an unsatisfiable tree displays as `python_version < '0'`, which parses
  back to a satisfiable tree; `Requirement` `Display` → `from_str` does not round-trip a false
  marker.
- **pep508_rs/3** (medium) — `a===a` (arbitrary equality with a non-version string) is rejected
  with "expected version to start with a number" (root in `pep440_rs`).
- **pep508_rs/4** (medium) — `python_version == '3.5.0.*'` is deemed unsatisfiable; PEP 440
  zero-pads `3.5` and matches (`packaging` agrees).
- **pep508_rs/5** (low) — the deprecated spellings (`os.name`, …) make trees unequal to their
  current spellings, against the documented canonicality; their `Display` re-parses to a
  different tree.
- **pep508_rs/6** (medium) — `python_version ~= '3.5.0'` loses its last component (tree
  `python_full_version >= '3.5' and < '4'`, true for 3.6; PEP 440: `>= 3.5.0, == 3.5.*`).
- **pep508_rs/7** (medium) — `Requirement::from_str("a[b.]")` panics (`expect` in the extras
  parser) instead of returning an error.
- **pep508_rs/8** (high) — on a pre-release interpreter (`python_full_version = 3.13.0rc1`)
  `python_version == '3.13'` is false and `python_version < '3.13'` true: the expression is
  lowered to a release-only `python_full_version` range and tested against the environment's
  real `3.13.0rc1`.
- **pep508_rs/9** (medium) — `MarkerTree` is not canonical as documented: `X and ((X and A) or B)`
  with `A`, `B` on one string key and `X` a string or `extra` variable leaves adjacent equal-child
  edges unmerged, so two equivalent trees (same `evaluate`, same `Display`) are `!=` and hash
  differently. Found in uv's fork first (uv-pep508/6).

## Not bugs

- `packaging` 26's marker evaluation deviates from PEP 508 in two places the zoo leaves out:
  ordering operators on string keys whose sides are not both versions answer `false` (the spec
  and the crate use Python string comparison), and `in`/`not in` on version keys are substring
  tests (the crate documents version-aware matching as a deliberate deviation).
- `packaging` tokenises `===0,` as the arbitrary string, so `a===0, ==0.*` is an error for it
  and valid for the crate (the grammar agrees with the crate); `packaging` accepts a trailing
  comma (`a>=1.0,`) and any non-space run as a URL; the crate warns and ignores "bogus"
  marker comparisons (`'a' == 'a'`, `sys_platform ~= 'a'`, `extra > 'x'`) where `packaging`
  raises — documented leniency, generated only for the pins.
- The crate drops pre-, post- and dev-release segments from marker *literals*
  (`python_full_version == '3.13.0rc1'` is the tree `python_full_version == '3.13'`) so that its
  decision diagrams stay complementable — a deviation `src/marker/algebra.rs` documents; such
  literals are left out. (Testing the environment's un-stripped value against those ranges is
  bug 8.)
- The crate's `Display` is a DNF normal form with single quotes; compared by meaning.

## History

- 2026-09-14: created at b50980e (0.9.2); 8 bugs.
- 2026-09-14 (later): pep508_rs/9 (canonicity), re-found from uv-pep508/6; the round-trip properties compare markers by equivalence.
