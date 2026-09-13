# debversion

[debversion](https://github.com/jelmer/debian-parsers/tree/main/debversion) parses, compares
and manipulates Debian package versions (`epoch:upstream-revision`, dpkg's comparison
algorithm, DEP-14 git tag mangling, binNMU/NMU and VCS-snapshot suffix helpers). Written in the
zoo at 0.5.3 (debian-parsers commit `4dc04da`, 2026-09-05; the old `debversion-rs` repository
is archived). The crate is a workspace member: `subdir = "debversion"`. The heavy, feature-gated
dev-dependencies (`sqlx`, `pyo3`) are dropped from the crate's `Cargo.toml` in the patch; their
tests are behind the `sqlx` / `python-debian` features and do not run here.

## The oracles

- **dpkg itself.** `dpkg --validate-version` says what is a version (an error), what is a
  policy "should" (a warning: not starting with a digit, an `_`) and what is clean; the strict
  parser may refuse what dpkg warns about and must refuse what dpkg refuses.
- **libapt's comparison** through python3-apt (`apt_pkg.version_compare`, the same algorithm as
  dpkg), driven as a persistent `/usr/bin/python3` child (hex-encoded fields, one request per
  line); if `apt_pkg` is missing the tests fall back to `dpkg --compare-versions` per pair.
  python-debian's `Version` (if installed) checks the epoch/upstream/revision split.
- **`git check-ref-format refs/tags/<tag>`** judges the DEP-14 tag mangling.

`[run] setup` checks dpkg is present and warns when `apt_pkg` is not.

## Properties

- **Parsing** (`parsing_agrees_with_dpkg_and_python_debian`): generated texts — epochs at the
  `i32`/`u32` boundaries, upstream parts with `.+~`, letters, colons and hyphens where policy
  allows them, revisions of the shapes seen in the archive (`0ubuntu1`, `1+b1`, `1+nmu1`,
  `1~bpo12+1`), junk — split as dpkg/python-debian split them; verbatim Display;
  `parse_lenient` ⊇ `FromStr`; `AsVersion`.
- **Ordering** (`ordering_agrees_with_dpkg`): `Ord` against libapt/dpkg on random pairs and on
  variants of one version (zero padding, appended `0`/`.`/`~`/`+`/letters, bumped digit runs,
  revision and epoch changes); `Eq` ⇔ `Equal`; transitivity on triples. A 40-line port of
  dpkg's `verrevcmp` is used only to locate the inputs of bug 1.
- **Helpers**: `canonicalize` keeps the version and is idempotent; `increment_debian` yields the
  next revision (or upstream number for native packages) and a greater version;
  `increment_bin_nmu` / `bin_nmu_count` / `nmu_count` round trips; `mangle_version_for_git`
  produces valid tag names and is reversible on `~`/`:`; `upstream_version_add_revision` /
  `get_revision` write and read the same suffixes and replace rather than stack them; dfsg
  suffixes strip and re-add in the old style; `Vendor` / `initial_debian_revision`.

## Bugs (10, all zoo-original)

- **debversion/1** (medium) — `1.0a < 1.0a0`, `1. < 1.0`: an empty digit run is ordered below a
  run of zeros; dpkg skips leading zeros and says equal.
- **debversion/9** (medium) — `canonicalize` drops `0:`/`-0` even when the upstream part has a
  colon/hyphen that needs them: `1.0-1-0` → `1.0-1`, a different version; `0:1.0:2` → `1.0:2`,
  not a version.
- **debversion/10** (medium) — `Hash` over the raw fields while `Eq` is by comparison
  (`0:1.0-1 == 1.0-1`, different hashes); the crate's own test asserts the inconsistency.
- **debversion/2** (low) — the strict parser accepts `1.0:2`, `1.0-`, `1:-1`, `1.0-:1` and
  epochs above `INT_MAX`, all refused by dpkg.
- **debversion/3** (low) — `increment_debian` panics at `i32::MAX` or on longer numbers.
- **debversion/4, /5** (low) — `+b`/`+nmu` found by `split_once`: `1.0+beta1+b1` is not a
  binNMU (although `increment_bin_nmu` made it), `1.0-1+nmu1+b1` is not an NMU.
- **debversion/6** (low) — three dots mangle to `.#..`, an invalid git ref.
- **debversion/7** (low) — `get_revision` cannot read `git<date>`, `git<sha>` or dotted `bzr`
  suffixes that `upstream_version_add_revision` writes, so updating stacks suffixes.
- **debversion/8** (low) — `get_revision` unwraps an svn revision into `usize`.

The general properties skip exactly the inputs each bug covers (`hits_*` helpers); each bug
has its own pinned test asserting dpkg's behaviour.

## Not bugs

- dpkg trims surrounding whitespace and only warns about `_` or a non-digit start; the strict
  parser refusing those is the right direction (texts with whitespace are not compared).
- Epochs print as numbers (`01:1.0` displays as `1:1.0`).
- Texts starting with `-` cannot be handed to the dpkg command line and are not validated.
