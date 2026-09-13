# pep440_rs

[pep440_rs](https://github.com/konstin/pep440-rs) implements PEP 440 version numbers and
version specifiers (the crate behind uv's `uv-pep440`, which has since diverged). Written in the
zoo at 0.7.3 (commit `87a728c`), differential against **Python's `packaging`** (26.3), the PEP
440 reference implementation.

## The oracle

The tests start one `python3` child process running a small inline script and talk to it over
stdin/stdout (hex-encoded, space-separated fields, one request per line, behind a `Mutex`):

- `V <text>` — `packaging.version.Version(text)`: validity, `str(v)`, epoch, release, pre, post,
  dev and local;
- `C <a> <b>` — the ordering of two versions;
- `S <spec> <v>…` / `SS <set> <v>…` — `Specifier(spec).contains(v, prereleases=True)` and the
  same for `SpecifierSet`. The crate implements the operator semantics and leaves the
  pre-release policy to the caller, hence `prereleases=True`.

`[run] setup` installs `packaging` with pip if `python3 -c 'import packaging.version'` fails.

## Properties

- **Parsing** (`versions_parse_and_normalize_like_packaging`, `wildcard_patterns_parse_like_packaging_specifiers`):
  generated texts cover every PEP 440 spelling — `alpha/beta/preview/pre/rc/a/b/c` in any case,
  `post/rev/r` and the implicit `-N`, `dev`, the separators `.`/`-`/`_`, leading `v`, epochs,
  leading zeros, whitespace, locals with mixed segments, numbers at the u8/u16/u21/u64
  boundaries of the crate's compact representation — plus a dose of junk. Validity, the
  normalized form and every field must match `packaging`; the normalized form must round-trip
  and be a fixed point; `VersionPattern` agrees with `Specifier("==" + text)` on `.*` patterns.
  Numbers beyond `u64` (a documented limit; `packaging` uses Python integers) must be
  `NumberTooBig` errors and are otherwise excluded.
- **Ordering** (`versions_order_like_packaging`, `versions_built_from_parts_equal_parsed_ones`):
  `Ord` against Python's comparison on random pairs and on variants of one base version
  (neighbouring numbers, extra/dropped segments, other epochs, other suffixes, locals) — this
  exercises the small-vs-full representation boundaries; `Eq` ⇔ `Equal`, equal versions hash
  equally, trailing zeros never matter, the `with_*` builders equal the parsed version in any
  order, `without_local`/`only_release`.
- **Specifiers** (`specifiers_parse_and_contain_like_packaging`, `specifier_sets_parse_and_contain_like_packaging`,
  `specifier_builders_validate_like_the_parser`): validity and containment against
  `packaging` for all operators but `===` (the crate can only compare normalized forms, the
  reference compares raw strings) on candidates near the specifier's version; Display and
  serde round trips, sets sorted by version, containment as conjunction, the documented build
  errors (`~=` with one segment, locals with ordered operators, wildcards with other
  operators), `Operator` parsing and `negate` (checked across releases only — pre-/post-release
  exclusions make `<`/`>=` not complements within one release).
- **`version-ranges`** (`ranges_agree_with_contains`, `release_only_ranges_agree_with_contains_on_release_only_versions`):
  `Ranges::<Version>::from(spec).contains(v) == spec.contains(v)` on non-local candidates (a
  local version sits above its public version in the total order, which a range cannot fold
  back — uv handles locals before resolution), and the release-only conversion against
  `contains` on release-only specifiers and candidates.

## Bugs (10, all zoo-original)

`packaging` 26.3 disagrees with the crate in ten places; four of them are already fixed in uv's
fork, none in the published crate. See `bugs.toml`.

- **pep440_rs/1** (medium) — `<V` rejects every same-release pre-release, not just the
  pre-releases of `V`: `<1.0a2` ∌ `1.0a1`, `<1.0.post1` ∌ `1.0a1`. (Fixed in uv.)
- **pep440_rs/6** (medium) — `>V` rejects every same-release post-release: `>1.0a1` ∌
  `1.0.post1`.
- **pep440_rs/8** (medium) — `==1.2.*` contains `1`: the prefix match does not zero-pad a
  shorter candidate. (Fixed in uv.)
- **pep440_rs/2** (medium) — the range of `<1.0.post1` excludes `1.0`, `1.0.post0`, `1.0a1`
  (`with_min` sorts below the whole release). (Fixed in uv.)
- **pep440_rs/10** (low) — the range of `>1.0.post0` starts at `1.0.post1` and skips
  `1.0.post1.dev0`. (Fixed in uv.)
- **pep440_rs/3** (low) — the range conversions overflow on `u64::MAX` numbers.
- **pep440_rs/4** (low) — `VersionSpecifiers::from_str(">=1.0,")` fails; `packaging` skips
  blank items.
- **pep440_rs/5** (low) — `1.0+18446744073709551616` gets a *string* local segment and sorts
  below `1.0+1`.
- **pep440_rs/7** (low) — `MIN_VERSION` = `0a0.dev0` is above `0.dev0`.
- **pep440_rs/9** (low) — `1.0.post2.dev18446744073709551615 == 1.0.post2` (`u64::MAX` is the
  "no dev" sentinel of the sort key), with unequal hashes.

The general properties skip exactly the inputs each bug covers (`hits_*` helpers); each bug
has its own pinned test asserting the PEP 440 / `packaging` behaviour.

## Not bugs

- `===` compares normalized forms (the crate holds parsed versions), `packaging` raw strings.
- `1.0\x0B` (vertical tab): `packaging`'s `\s` accepts it, the crate's `is_ascii_whitespace`
  does not; PEP 440 does not define "whitespace". Not generated.
- `>V` and `>=V` for a local `V`, `===`: excluded from the range comparison (not expressible
  as a range over the total order).
