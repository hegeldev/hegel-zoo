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
