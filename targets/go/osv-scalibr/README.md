# go/osv-scalibr: the semantic package against each ecosystem's own version comparator

[google/osv-scalibr](https://github.com/google/osv-scalibr) is Google's software composition
analysis library (the scanner behind OSV-Scanner). Its `semantic` package parses and orders
version strings for OSV's ecosystems - PyPI, Debian, Red Hat and its family, RubyGems, npm and
the semver-like ecosystems, Maven, NuGet, Alpine and its family, CRAN, Hackage, Packagist, Pub -
each a Go port of the ecosystem's own rules. This target compares the ports with the originals.

The tests live in `semantic/hegel/`, a package added by the patch. The oracles are the
ecosystems' own implementations, run as child processes speaking one line each way:

| ecosystem | oracle |
|---|---|
| PyPI | python `packaging.version` (PEP 440's reference) |
| Debian | `dpkg --compare-versions` |
| Red Hat | rpm's `rpmvercmp()`, built from `rpmio/rpmvercmp.c` of rpm 4.20.1 into a shared library the python oracle loads, with `parseEVR`'s split done in python |
| RubyGems | ruby's `Gem::Version` |
| npm | node-semver 7.8.5 |
| Maven | Maven's `ComparableVersion` (maven-artifact 3.9.11, a small Java driver) |
| Go | `golang.org/x/mod/semver`, in process |

Properties (`HEGEL_COLLECT=1` counts mismatches instead of failing, `HEGEL_TEST_CASES=n` sets the
case count):

- `TestHegelComparesLikeTheEcosystem`: a pair of generated versions the oracle accepts is ordered
  by `semantic.Parse` + `Compare` as the oracle orders it (pairs the oracle rejects are counted;
  for npm, disagreement with node-semver's loose mode is counted too).
- `TestHegelCompareIsAnOrder`: for every ecosystem `Parse` knows, `Parse` and `Compare` never
  panic, a version equals itself, `Compare` is antisymmetric, `CompareStr` agrees with `Parse` plus
  `Compare` and rejects what `Parse` rejects, and the order is transitive over three versions.

Versions are built from pieces every grammar knows (numbers of all sizes and with leading zeros,
the separators, pre- and post-release words in all cases, epochs, revisions, local and build
parts), shaped after each ecosystem's syntax most of the time and as free soup the rest; a pair is
mostly a version and a mutation of it.

Ten bugs, all found 2026-09-19 at commit 6aec485 (v0.5.2+), all low: RubyGems versions with
surrounding whitespace (1), a hyphen that `Gem::Version` reads as `.pre.` (2) and numeric segments
with leading zeros (7); Maven's MNG-7644 rule of 3.8.7/3.9.0 that a dot-introduced qualifier
followed by a digit or the end is a hyphen-introduced one (3), Maven's dropping of null items
before sub-lists, which orders `1-ga-1` below `1-1` where the package's own test data asserts
equality (4), and all-zero versions against unknown qualifiers (8); a Red Hat release split at the
first hyphen where rpm splits at the last (5) and empty components decided before `rpmvercmp`'s
separator stripping and tilde rule (9); and an Alpine `Compare` that is not an order when versions
apk would reject are involved (6) or when a missing component meets one with a leading zero (10).
PyPI, Debian, npm and Go agreed with their oracles over some 10,000 accepted pairs each.

Every one of the ten bugs is drawn by default and found by the properties (DESIGN.md decision 3):
the wide properties reach the shapes at their natural rates - a disagreement on a recorded shape in
`TestHegelComparesLikeTheEcosystem` in about half a percent of cases, a broken order in
`TestHegelCompareIsAnOrder` in about a quarter of a percent - and fail naming the bug (both are
intermittent expected failures, mapped to the basin the shrinker usually lands in: the Red Hat
release split (5) and the Alpine order (6)). The narrow properties of `hegel_shapes_test.go` draw
each shape region deterministically, one per bug, judged by the same oracles:
`TestHegelRubyGemsStripsSurroundingWhitespace` (1), `TestHegelRubyGemsHyphenReadsAsPre` (2),
`TestHegelMavenDotQualifierBeforeDigitOrEndIsHyphen` (3), `TestHegelMavenNullItemBeforeSublistNests`
(4), `TestHegelRedHatReleaseSplitsAtLastHyphen` (5), `TestHegelAlpineOrderHoldsWithInvalidVersions`
(6), `TestHegelRubyGemsZeroPaddedSegmentIsZero` (7), `TestHegelMavenZeroVersionSortsBelowUnknownQualifier`
(8), `TestHegelRedHatEmptyComponentsCompareByRpmvercmp` (9) and
`TestHegelAlpineMissingComponentOrderIsTransitive` (10). `HEGEL_NO_KNOWN=1` switches the shapes
off: the wide properties then consult the shape classifiers of `known.go` and assume a recorded
shape away (about 0.2% of cases), the narrow ones draw the neighbouring region, and every property
passes. Nothing else is excluded; shapes an oracle cannot judge are counted.

History: 2026-09-19 written at 6aec485 (v0.5.2+), hegel.dev/go/hegel v0.6.33; 2026-10-07 generators
rewritten in combinator style (STYLE.md): package-level generator values (`number`/`word`/`piece`/
`soup`, one shaped generator per ecosystem family as `cat` of `maybe` parts with the plain
alternative first, edits as data applied by a pure function with positions modulo the live
length, a pair as a version and a relation to it, one case record per property with a `GoString`),
the known shapes drawn by default with the ten narrow properties beside the pins, and the Maven
driver no longer trims its input line (an empty version is an empty base64 token, which the trim
turned into a crash of the driver).
