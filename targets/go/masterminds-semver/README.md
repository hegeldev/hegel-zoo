# masterminds-semver

[Masterminds/semver](https://github.com/Masterminds/semver) v3 is the semantic-version library
behind Helm, Glide and much Go tooling: `StrictNewVersion`/`NewVersion` parsing (with optional
coercion of a `v` prefix, missing segments and leading zeros), spec precedence, `Collection`
sorting, `IncMajor/Minor/Patch`, JSON/text/SQL marshalling, and the npm/Cargo-style constraint
language (`=`, `!=`, `<`, `<=`, `>`, `>=`, `~`, `^`, `x`/`X`/`*` wildcards, hyphen ranges,
blank/comma AND, `||` OR, pre-releases excluded unless a comparator names one or
`IncludePrerelease` is set). About 1 500 lines without tests. The pinned commit is the August
2026 head, just past v3.5.0 (the no-panic increment functions). MIT; no CONTRIBUTING.md and no
AI policy at the pin (the `.github` directory holds dependabot and workflows; SECURITY.md
mentions daily fuzzing).

## Oracle

Semantic Versioning 2.0.0 for what it covers — the grammar of a version (numeric segments
without leading zeros, `[0-9A-Za-z-]` identifiers, no empty identifiers, no leading zeros in
numeric pre-release identifiers) and precedence item 11 (numeric identifiers numerically and
before alphanumeric ones, alphanumeric in ASCII order, fewer identifiers first, build metadata
ignored) — implemented as a small model in the test file. The README for the rest: the
coercions `NewVersion` performs (`v1.2` is `1.2.0`, leading zeros allowed only while
`CoerceNewVersion` is set), the meaning of every constraint form (`1.2.x` is `>= 1.2.0, < 1.3.0`,
`~1.2.3` is `>= 1.2.3, < 1.3.0`, `~1` is `>= 1, < 2`, `^0.2.3` is `>= 0.2.3, < 0.3.0`, `^0.0.3` is
`>= 0.0.3, < 0.0.4`, `>= 1.2.x` is `>= 1.2.0`, `<= 2.x` is `< 3`, `A - B` is `>= A <= B`, `*` is
`>= 0.0.0`), the pre-release rule of constraint checking, and the doc comments of the
increment and set functions.

## Properties

- `TestHegelStrictVersionsParseByTheSpec` — random spec versions (segments from tiny to
  MaxUint64, pre-release and build identifiers of every shape) parse identically with
  `StrictNewVersion`, `NewVersion` with and without coercion, `MustParse`, `json.Unmarshal`,
  `UnmarshalText` and `Scan`; parts, `Original`, `String`, `MarshalJSON`, `MarshalText`,
  `Value` and self-comparison are as expected.
- `TestHegelLooseVersionsAreCoerced` — the same versions written loosely (`v` prefix, missing
  patch or minor and patch, zero-padded segments) coerce to the model; without
  `CoerceNewVersion` a zero-padded segment is `ErrSegmentStartsZero` and the rest still parses;
  `String()` is a strict version that reads back equal.
- `TestHegelInvalidVersionsAreRefused` — sixteen mutations (a `v` or `V` prefix, zero-padded
  segments, missing segments, four segments, empty or zero-padded numeric identifiers, an
  invalid or non-ASCII character anywhere, a sign, a segment beyond uint64, a second `+`,
  surrounding blanks, a trailing separator, the empty string): each parser refuses exactly the
  ones its documented grammar excludes and returns nil; `MustParse` panics.
- `TestHegelPrecedenceFollowsTheSpec` — pairs of related versions (shared core, derived
  pre-releases, different metadata): `Compare` and the six comparison methods agree with the
  model in both directions; `sort.Sort(Collection)` orders 2–6 related versions as the model
  does and loses nothing. Numeric identifiers beyond uint64 are drawn (a quarter of the numeric
  ones), so the property lands on masterminds-semver/1 when such an identifier meets a `-`, a
  `0` or another huge number (most 1000-case runs, not every 100-case one; intermittent).
- `TestHegelIncrementsFollowTheDocs` — `IncPatchE/MinorE/MajorE` and their panicking variants
  follow the doc comments (a pre-release version's patch stays, metadata and pre-release are
  cleared, lower segments zeroed), overflow at MaxUint64 is `ErrIncrementOverflow` / a panic
  with the receiver unchanged, `Original()` keeps the `v` prefix; `SetPrerelease`/`SetMetadata`
  accept valid identifiers and refuse malformed ones.
- `TestHegelConstraintsMatchTheReadmeRanges` — random constraints (1–3 OR groups of 1–3
  comparators or hyphen ranges, every operator including the `=>`, `=<`, `~>` aliases,
  wildcards `x`/`X`/`*` and missing segments, `v` prefixes, pre-release comparators, blank or
  comma separators, `IncludePrerelease` on or off) against versions near their own:
  `Check` agrees with the README model, `Validate` agrees with `Check` and returns messages
  exactly when it fails, and the constraint survives `String()` → `NewConstraint` and
  `MarshalText` → `UnmarshalText` with the same verdict. A known shape is in about a quarter
  of the constraints, so the property lands on masterminds-semver/5 in most runs (a hyphen
  range after a blank-separated comparator), on /3, /4 or /7 in the rest.

## Known bugs

The generators draw the shape of every recorded bug (STYLE.md rule 11): the two wide
properties above are expected failures mapped to the bugs they land on, and each bug has a
narrow property over its own shape region in `hegel_shapes_test.go`, the deterministic
expected failure beside the pin: `TestHegelHugeNumericIdentifiersCompareNumerically`
(masterminds-semver/1), `TestHegelCaretWildcardIsAnyVersion` (/2),
`TestHegelBareWildcardIsNotZero` (/3), `TestHegelTildeZeroIsAPatchRange` (/4),
`TestHegelHyphenRangeAfterBlankSeparatedComparator` (/5), `TestHegelOrGluedToHyphenRange` (/6)
and `TestHegelNotEqualWildcardsAgreeOnPrereleases` (/7). `HEGEL_NO_KNOWN=1` (read once)
switches the known shapes off: numeric identifiers stay within uint64, a bare wildcard comes
only with `=`, `>=`, `<`, `~`, `~` never gets a 0.0.0 core, a hyphen range follows a comma,
`||` is blank-separated beside a hyphen range and `!=` with a wildcard is not checked against
pre-releases; every property then passes at 3000 cases with no skips. At the default 100
cases the run takes well under a second. `MASTERMINDS_SEMVER_COLLECT=1` makes the properties
record mismatches instead of failing and print them shortest-first.

## Bugs (7; details in bugs.toml)

| id | summary | severity |
|----|---------|----------|
| masterminds-semver/1 | Numeric pre-release identifiers beyond uint64 compare as text (1e20 < 99999999999999999999; after `-` and `0a`) | low |
| masterminds-semver/2 | `^*` accepts only 0.0.0 (code says "any") | low |
| masterminds-semver/3 | Bare wildcard is 0.0.0 under `<=`, `>`, `!=`: `<= *` accepts 0.0.z only, `> *`/`!= *` accept everything but 0.0.0 | low |
| masterminds-semver/4 | `~0.0.0` (and `~0.0.0-alpha`) accepts every version | low |
| masterminds-semver/5 | Hyphen range after a blank-separated comparator is an "improper constraint" | low |
| masterminds-semver/6 | `||` glued to a hyphen range is read as version characters (`[0-9|x|X|\*]`) and the constraint is "improper" | low |
| masterminds-semver/7 | With IncludePrerelease `!= 1.2.x` accepts 1.2.3-alpha but `!= 1.x` rejects it | low |

How they were found: /1, /2, /3, /4 and /7 from reading `comparePrePart` and the constraint
functions while writing the model, each confirmed by a probe (the properties draw the shapes
since 2026-09-25); /5 by the probe that checked how hyphen ranges combine with other comparators; /6 by
the constraint property's first 20 000-case run ("improper constraint: \"3.3 .1\"" for
`2.3.1 - 0.*||3.3.1`, and `"<2.>= 3"` for `<2.3||0.1.2 - 3.1.1`), traced to the `|` in the
character class.

## Not bugs (documented, design, or the spec's silence)

- `Compare` and `Equal` ignore build metadata; `String()` drops the `v` prefix (`Original()`
  keeps it); `New()` does not validate — all documented.
- `StrictNewVersion` refuses the `v` prefix and partial versions; `NewVersion` refuses a
  zero-padded segment only when `CoerceNewVersion` is false; a zero-padded *numeric pre-release
  identifier* is refused in every mode. Documented in the README and asserted as such.
- Versions over 256 bytes and constraints over 512 bytes or 32 OR groups are refused
  (`MaxVersionLen`, `MaxConstraintLen`, `MaxConstraintGroups`): a documented guard, not
  generated.
- `1.2-1.4.5` without blanks is a version with pre-release `1.4.5`, per the README.
- Which versions a wildcard, `~` or `^` comparator admits when the *version* is a pre-release
  (`1.2.x` vs `1.2.0-alpha`, `< 1.3.x` vs `1.3.0-alpha`) is not defined by the README, and
  the code's answers differ from npm's; only `!=`'s internal inconsistency (/7) is recorded.
  The property checks pre-release versions against full-version comparators only, except
  that `!=` takes a version of any shape (masterminds-semver/7's region; full versions only
  under `HEGEL_NO_KNOWN=1`).
- The empty constraint and a trailing `||` are "improper constraint" errors; `1|2.3` is a
  "constraint parser error" (mentioned under /6). Error texts are not compared.
- A trailing hyphen after a pre-release or build identifier (`1.2.3-1-`) is a valid identifier
  `1-`, not a malformed version; the invalid-text generator only appends `-` to a bare core.
- `Validate` reports the pre-release exclusion once per call and per-comparator messages
  otherwise; only the count being non-zero is asserted.
- Not covered: `Constraints` with IncludePrerelease semantics for `~`/`^`/wildcards on
  pre-release versions (above), `New()`, the `Collection` type beyond sorting.
