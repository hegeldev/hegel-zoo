# uv-pep440

[uv-pep440](https://github.com/astral-sh/uv/tree/main/crates/uv-pep440) is uv's fork of
[pep440_rs](../pep440_rs): PEP 440 `Version` parsing, normalisation and ordering,
`VersionSpecifier`/`VersionSpecifiers` parsing and containment, and — with the `version-ranges`
feature — conversions to `Ranges<Version>` used by uv's resolver. Written in the zoo at 0.0.80 (uv
HEAD `c0df400`, 2026-09-12); tests in `crates/uv-pep440/tests/hegel.rs`, run in that crate's
directory with `--features version-ranges`.

The test file is the zoo's `pep440_rs` file ported: `use uv_pep440`, the fork's private builders
(`with_epoch`, `with_dev`, `with_local`) replaced by rebuilding a version through its text,
`release_specifier_to_range(spec, trim)`, and the two pins about `u64::MAX` dropped (below).

## The oracle

One persistent Python child (the first of `python3`, `/usr/bin/python3` that imports it; `[run]
setup` pip-installs it if neither does) running PyPA's **`packaging`** — `packaging.version` and
`packaging.specifiers`: parsing and normalisation (`str(Version)`), ordering, `Specifier`/
`SpecifierSet.contains(prereleases=True)` (the crate implements the operator semantics and leaves
the pre-release policy to the caller), the `===` operand. Alongside: `Display` round trips,
`Ord`/`Eq`/`Hash` consistency, the builders against the parser, and `VersionSpecifier::contains`
against the `Ranges<Version>` conversion.

## Properties

Versions parse and normalise like `packaging` (every spelling of pre/post/dev/local, `v`,
whitespace, leading zeros, junk), order like it, and rebuild from their parts; wildcard patterns
parse like `packaging` specifiers; specifiers and specifier sets parse and contain like
`packaging` on candidates around the specified version; the builders (`from_version`,
`from_pattern`, the `*_version` constructors) accept exactly what the parser accepts; the
`Ranges` conversions agree with `contains` (and the release-only conversion with release-only
candidates). Four `pep440_rs` pins hold here as regular properties, since the fork fixed them:
`<V` admits the pre-releases of other versions (pep440_rs/1), `<X.postN` as a range keeps `X`
(pep440_rs/2), `==X.Y.*` pads a shorter candidate (pep440_rs/8), `>X.postN` as a range keeps
`X.postN+1.devM` (pep440_rs/10).

## Bugs (5, found 2026-09-14; all inherited from `pep440_rs`, where the zoo found them first)

- **uv-pep440/1** (low) — blank items in a specifier set are errors (`">=1.0,"`, `" "`);
  `packaging` skips them (pep440_rs/4).
- **uv-pep440/2** (low) — an all-digit local segment beyond `u64` is kept as a string and sorts
  below every number (pep440_rs/5).
- **uv-pep440/3** (medium) — `>V` excludes the post-releases of other versions of the same release:
  `>1.0a1` does not contain `1.0.post1`, `>0a1` not `0.post0` (PEP 440 excludes only post-releases
  *of V*; `packaging` and the crate's own range conversion agree) (pep440_rs/6).
- **uv-pep440/4** (low) — `MIN_VERSION` (`0a0.dev0`) is above `0.dev0` (pep440_rs/7).
- **uv-pep440/5** (medium) — `===` takes only a PEP 440 version; `===foobar`, `===1.0-custom`,
  `===1.0.*` are rejected (pep440_rs/11).

## Not bugs

- The fork reserves `u64::MAX` and rejects any number equal to it at parse time with "expected
  number less than or equal to 18446744073709551614" — a documented limit; the generators treat
  it like a number beyond `u64` (both are rejected). This also makes pep440_rs/3 (range overflow
  on `u64::MAX`) and pep440_rs/9 (a dev number of `u64::MAX` compares as no dev) unreachable
  through parsing, and the builders that could reach them are `pub(crate)`.
- Numbers beyond `u64` are rejected while `packaging` accepts them (Python integers): documented.
- `Version` ordering and `==` matching differ on local versions by design (`1.0+local > 1.0`
  while `==1.0` matches `1.0+local`), as the crate's docs say.

## History

- 2026-09-14: created at c0df400 (0.0.80); 5 bugs (inherited from pep440_rs).
- 2026-09-14: base bumped c0df400a4cf4 → 83d556d712c7 (2026-09-14, "Scope required-environment checks to the current fork (#21672)"; 0.0.80); 5 bug(s) still reproduce. 83 tests pass.
- 2026-09-14: base bumped 83d556d712c7 → c40e652bc385 (2026-09-14, "Exclude backports-zstd from the Sentry PGO corpus (#21678)"; 0.0.80); 5 bug(s) still reproduce. 83 tests pass.
- 2026-09-14: base bumped c40e652bc385 → 595c8e2c6812 (2026-09-14, "Use cargo codspeed via astral-dev-toolchain (#21674)"; 0.0.80); 5 bug(s) still reproduce. 83 tests pass.
- 2026-09-14: base bumped 595c8e2c6812 → 85fe61435fe5 (2026-09-14, "Use cargo bloat via astral-dev-toolchain (#21681)"; 0.0.80); 5 bug(s) still reproduce. 83 tests pass.
- 2026-09-15: base bumped 85fe61435fe5 → 941b557a69d7 (2026-09-14, "Remove unused Serde derives from index locations (#21685)"; 0.0.80); 5 bug(s) still reproduce. 83 tests pass.
- 2026-09-15: base bumped 941b557a69d7 → ffc98b158bad (2026-09-14, "Forbid install-action via zizmor (#21682)"; 0.0.80); 5 bug(s) still reproduce. 83 tests pass.
- 2026-09-15: base bumped ffc98b158bad → 6f7795bb4f6e (2026-09-14, "Update Rust crate axoupdater to v0.10.2 (#21658)"; 0.0.80); 5 bug(s) still reproduce. 83 tests pass.
- 2026-09-15: base bumped 6f7795bb4f6e → b8aff80900e7 (2026-09-15, "Update dependency astral-sh/uv to v0.12.13 (#21655)"; 0.0.81); 5 bug(s) still reproduce. 83 tests pass.
- 2026-09-15: base bumped b8aff80900e7 → 000a665b745a (2026-09-15, "Batch HTTP cache writes in blocking tasks (#21675)"; 0.0.81); 5 bug(s) still reproduce. 83 tests pass.
- 2026-09-15: base bumped 000a665b745a → fd89f638d15f (2026-09-15, "Add regression test for symlinks inside install directory (#21693)"; 0.0.81); 5 bug(s) still reproduce. 83 tests pass.
- 2026-09-15: base bumped fd89f638d15f → a064ab2f6761 (2026-09-15, "Add regression test for `--target .` (#21695)"; 0.0.81); 5 bug(s) still reproduce. 83 tests pass.
- 2026-09-15: base bumped a064ab2f6761 → 2c35bb31de15 (2026-09-15, "Use Packse scenarios to speed up tool tests (#21634)"; 0.0.81); 5 bug(s) still reproduce. 83 tests pass.
- 2026-09-15: base bumped 2c35bb31de15 → ad552557b635 (2026-09-15, "Preserve local path intent when merging dependency metadata (#20631)"; 0.0.82); 5 bug(s) still reproduce. 83 tests pass.
- 2026-09-15: base bumped ad552557b635 → 694dfd8155ec (2026-09-15, "Verify distribution hashes (#21562)"; 0.0.82); 5 bug(s) still reproduce. 83 tests pass.
- 2026-09-15: base bumped 694dfd8155ec → ac9201b10433 (2026-09-15, "Allow manually specifying build dependency hashes in configuration (#21467)"; 0.0.82); 5 bug(s) still reproduce. 83 tests pass.
- 2026-09-15: base bumped ac9201b10433 → 1f245a625114 (2026-09-15, "Cover packaged editable self-dependency name mismatches (#21714)"; 0.0.82); 5 bug(s) still reproduce. 83 tests pass.
- 2026-09-15: base bumped 1f245a625114 → b44bd4561d97 (2026-09-15, "Use a small native extension in system Python tests (#21713)"; 0.0.82); 5 bug(s) still reproduce. 83 tests pass.
- 2026-09-15: base bumped b44bd4561d97 → bf12c8e61b2d (2026-09-15, "Enable Renovate updates for the release workflow (#21722)"; 0.0.82); 5 bug(s) still reproduce. 83 tests pass.
- 2026-09-15: base bumped bf12c8e61b2d → 7752bc92b53e (2026-09-15, "Update astral-sh/setup-uv action to v10.1.0 (#21666)"; 0.0.82); 5 bug(s) still reproduce. 83 tests pass.
- 2026-09-15: base bumped 7752bc92b53e → a265915acf9e (2026-09-15, "Expand Debian and official Python system-test images (#21726)"; 0.0.82); 5 bug(s) still reproduce. 83 tests pass.
- 2026-09-15: base bumped a265915acf9e → 27e80c1498d9 (2026-09-15, "renovate: update uv hashes correctly with setup-uv (#21724)"; 0.0.82); 5 bug(s) still reproduce. 83 tests pass.
- 2026-09-15: base bumped 27e80c1498d9 → 9d8d76f4a13d (2026-09-15, "Use cargo-deny from toolchain (#21730)"; 0.0.82); 5 bug(s) still reproduce. 83 tests pass.
- 2026-09-16: base bumped 9d8d76f4a13d → c202b35405f1 (2026-09-15, "Encapsulate resolver metadata requests (#21735)"; 0.0.82); 5 bug(s) still reproduce. 83 tests pass.
