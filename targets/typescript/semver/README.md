# typescript/semver — npm/node-semver (the semantic version parser used by npm)

Hegel property tests for [`semver`](https://github.com/npm/node-semver) 7.8.5, pinned at
`6e05b763` (main, 2026-06-19), npm's own version and range library (~400M weekly downloads).
Plain CommonJS, no runtime dependencies, no build step. Tests are `test/hegel.test.mjs` (ESM,
run by `node --test`) with the zoo's harness `test/hegel-zoo.mjs`; Hegel is `@hegeldev/hegel`
0.4.5, pinned in the harness (`HEGEL_PIN`, checked at load time) and installed with `npm
install --no-save`. Run with `node --test --test-reporter=tap test/hegel.test.mjs`
(`HEGEL_TEST_CASES=n` sets the budget, `ZOO_COLLECT=1` records mismatches and the shapes seen
instead of failing at the first). CONTRIBUTING.md (the npm template) has no AI-contribution
policy (checked 2026-09-15); the zoo only records bugs.

## Approach

- **Ordering against the spec.** Versions are generated in the strict grammar (small
  components, occasionally huge ones up to `MAX_SAFE_INTEGER`; prerelease identifiers numeric
  — 3% beyond 2^53 — and alphanumeric; build metadata) in triples that are often neighbours,
  and compared with an oracle written from SemVer 2.0.0 §11 with BigInt identifiers:
  `compare`, `rcompare`, `gt`/`lt`/`eq`/`neq`/`gte`/`lte`, `cmp` with every operator,
  `compareBuild` (the identifier rules applied to build metadata, as semver documents),
  `compareLoose`, `sort`/`rsort`, `satisfies` against an exact comparator, and parsing:
  components, `valid`, `clean`, the loose parser on strict input, and `format` round trips.
- **Range algebra by membership on candidates.** Two ranges are built from range.bnf
  (comparators with every operator, `~`/`~>`, `^`, x-ranges with `x`/`X`/`*`, hyphen ranges,
  `v`/`=v` prefixes, prereleases and build metadata on full versions, `||` unions, extra
  spaces, the empty range) with random `includePrerelease`/`loose`. The candidate versions are
  every comparator bound of both parsed ranges, one step up and down in each component, with
  and without prereleases (`-0`, `-alpha`, `-alpha.1`, `-zz`, the bound's own prerelease
  extended), plus a few random versions. On the candidates: `satisfies` agrees with
  `Range.test`, with the formatted range and with `toComparators` rejoined; `validRange` is
  idempotent; `includePrerelease` only widens; `subset(a, b)` is sound both ways (true means
  no candidate is in `a` and not `b`; a witness means false) and reflexive; `intersects` is
  symmetric, sound both ways (a common candidate means true; false means none) and reflexive
  on a non-empty range; `minVersion` satisfies the range and no candidate below it does (null
  only when no candidate matches); `maxSatisfying`/`minSatisfying` are the extremes of the
  matching candidates; `gtr`/`ltr` are false for a matching version and, when true, every
  matching candidate is on the other side; `simplifyRange` over the candidates is a valid range
  with the same membership on them and leaves its input alone. "subset false but no candidate
  witnesses it" and "intersects true without a common candidate" are only counted (the
  candidates are not exhaustive).
- **Increments.** For every release type with random identifiers and `identifierBase`,
  `inc` gives a valid, strictly higher version (null only where documented), the same from a
  string and a `SemVer`, a prerelease exactly for the `pre*` types, carrying the identifier;
  `diff` is symmetric, null on equal versions, the plain first-difference for two releases and
  `pre*` when the higher is a prerelease; `truncate` for every type; `coerce` on the version,
  on the version inside text, with `includePrerelease`, and right-to-left.
- The shapes of the recorded bugs are read off the inputs and results by a classifier; a case
  with a shape is counted and only checked where the shape does not apply; a case with none
  must hold exactly. Each bug shape has a pin.

## Properties

| Test | What it checks |
|---|---|
| `TestHegelOrderingMatchesTheSpec` | the comparison family and parsing against a SemVer 2.0.0 oracle |
| `TestHegelRangesAgreeOnMembership` | `satisfies`/`validRange`/`toComparators`/`subset`/`intersects`/`minVersion`/`maxSatisfying`/`minSatisfying`/`gtr`/`ltr`/`simplifyRange` on candidate versions |
| `TestHegelIncrementsGoUp` | `inc`, `diff`, `truncate`, `coerce` |

## Bugs (see `bugs.toml`)

| id | severity | title |
|---|---|---|
| semver/1 | medium | gtr and ltr report a prerelease that the prerelease rule excludes as beyond the range, both at once |
| semver/2 | low | numeric prerelease identifiers are compared as doubles, so identifiers beyond 2^53 that differ compare equal |
| semver/3 | low | simplifyRange sorts the caller's array of versions in place |
| semver/4 | low | minVersion ignores includePrerelease: it returns 0.0.0 for * and 2.0.3 for >2.0.2 where 0.0.0-0 and 2.0.3-0 satisfy the range |
| semver/5 | medium | simplifyRange returns the empty string, which as a range means any version, when no version matches |
| semver/6 | low | compareBuild returns 0 as soon as two build identifiers are numerically equal but textually different, without looking at the rest |
| semver/7 | medium | intersects is asymmetric for an exact prerelease comparator against *: true one way, false the other |
| semver/8 | medium | gtr and ltr keep the lowest lower bound of a set, so with two lower bounds a version between them is reported as greater than the range |
| semver/9 | medium | minVersion returns null when an unsatisfiable alternative carries the lowest lower bound |
| semver/10 | low | inc past MAX_SAFE_INTEGER returns a version string that valid rejects, instead of null |
| semver/11 | low | simplifyRange's hyphen ranges admit prereleases of their endpoints under includePrerelease that the original range excludes |
| semver/12 | low | a range with a component at MAX_SAFE_INTEGER throws Invalid minor/patch version from the desugaring, so validRange rejects it and satisfies is false for its versions |
| semver/13 | medium | subset and intersects take a set with an exact prerelease comparator and a bound as empty: a subset of everything, intersecting nothing |
| semver/14 | low | gtr and ltr with both bounds on one version (1.1.2 - 1.1.2) report a higher version as lower than the range |

/1, /2 and /3 came from a probe file written after reading the source (`classes/range.js`
577 lines, `classes/semver.js` 350, `ranges/subset.js` 249, `ranges/outside.js` 82 and the
rest); /4–/14 were found by the properties in three collect rounds (the membership property
found nine of them). With every shape excluded, 4 000 cases per property had no unexplained
mismatch.

## Not bugs (modelled as documented)

- `clean` drops build metadata; `compareBuild` orders build identifiers by the prerelease
  rules (semver's own contract, not the spec's).
- `~1.2.3` excludes `1.2.3-0` even with `includePrerelease` (the lower bound stays `>=1.2.3`;
  only x-ranges, tildes and carets with x parts get `-0`), while a hyphen range's lower bound
  becomes `>=a-0` (upstream's fixtures) — the model asks the library, not a desugaring.
- `inc(v, 'prerelease', id)` with an identifier that is not a prefix of the current one
  restarts the prerelease (`1.2.3-beta.1` → `1.2.3-alpha.0`, lower than before), and returns
  null for a `pre*` type without an identifier when `identifierBase` is `false` or when the
  identifier already exists without a number: documented.
- `diff('1.0.0-1', '1.1.1')` is `major` (the documented prerelease special cases); `diff` of a
  prerelease step is `prepatch`/`prerelease` as the code comments say.
- A `||` alternative that is `*` swallows the others in the formatted range; null sets drop
  out of unions: documented in `Range`.
- The loose parser accepts more; the tests only check that it agrees on strict input.

## Not covered (yet)

Loose-only syntax (`1.2.3alpha`, `=v 1.2`), the `rtl` coercion of longer strings, custom
`Comparator` objects passed to `Range`, `Range.intersects` with the `Comparator` fast path,
and the `bin/semver` CLI.

## History

- 2026-09-15: created at 6e05b763 (7.8.5); 14 bugs.
