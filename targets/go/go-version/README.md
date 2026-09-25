# go-version

[hashicorp/go-version](https://github.com/hashicorp/go-version) is HashiCorp's version library
(Terraform, Vault, Nomad, Packer and their plugins): `NewVersion` (loose: `v` prefix, any number
of segments, leading zeros, a pre-release without its hyphen), `NewSemver` (documented as strict),
`WithPrefix`, `Compare` and friends, `Collection` sorting, `Core`, text and SQL marshalling, and
`Constraints` — a comma-separated AND of `= != > >= < <= ~>` comparators with a pre-release rule
and the RubyGems pessimistic operator. About 850 lines without tests. The pinned commit is the
September 2026 head, two weeks past v1.9.0 (it fixed comparing numeric identifiers beyond
int64, #212). MPL-2.0 (IBM). Its CONTRIBUTING.md has an "AI Usage" section: AI-assisted
contributions are welcome provided the contributor reviews and understands every change; the
PR template carries the matching checkbox. Checked 2026-09-14.

## Oracle

The README says "Versions used with go-version must follow SemVer", so Semantic Versioning
2.0.0 is the oracle for parsing and precedence: the grammar of identifiers and the
identifier-by-identifier precedence of item 11, as a small model in the test file. Where
go-version goes beyond the spec, its own documentation: any number of numeric segments,
compared left to right with the shorter list extended by zeros (`String`'s doc comment and the
`Compare` comments); `String()` canonicalises leading zeros, the `v` prefix and missing segments
(`1.04.0` → `1.4.0`, `v1.0.0` → `1.0.0`, `1.0` → `1.0.0`); `NewVersion` accepts a letter-first
pre-release without its hyphen and `NewSemver` does not. Constraints follow constraint.go's
comments (a constraint without a pre-release never matches a pre-release version; one with a
pre-release matches only pre-releases of the same segments; `~>` with a pre-release restricts to
pre-releases) and the upstream table for `~>` (`~> 1.0` is `>= 1.0, < 2.0`, `~> 1.0.7` is
`>= 1.0.7, < 1.1`, `~> 1.0.9.5` is `>= 1.0.9.5, < 1.0.10`) — RubyGems' definition, which also
settles the one case the table leaves out (`~> 1`).

## Properties

- `TestHegelVersionsParseAndPrint` — versions of one to five segments (small, up to a thousand,
  and anywhere in int64), spec pre-release identifiers of every shape including numerics beyond
  int64, build identifiers: the canonical text and a loose spelling (segments as written,
  zero-padded, `v` prefix, hyphen-less letter-first pre-release) parse to the same segments
  (padded to three), pre-release and metadata, with `Original` the input and `String` the
  canonical form; `NewSemver` accepts the canonical three-segment text and refuses every
  loose spelling; `Must`, `Core`, `MarshalText`/`UnmarshalText`, `Value`/`Scan` (strings and
  bytes), `NewVersion(String())` and `WithPrefix` (six prefixes; a missing prefix is an error)
  agree. Finds /4 (and /7).
- `TestHegelMalformedVersionsAreRefused` — twelve mutations (empty, surrounding blanks, `V`
  prefix, empty segment, empty pre-release or build identifier, an invalid or non-ASCII
  character anywhere, a sign, a segment beyond int64, a second `+`, trailing `+` or `.`):
  `NewVersion`, `NewSemver`, `UnmarshalText` and `Scan` refuse with a nil result; `Must` panics.
  Finds /6 (3% of its cases put the empty identifier first).
- `TestHegelPrecedenceFollowsSemver` — pairs of related versions (shared or neighbouring
  segments, the same value with more or fewer trailing zeros, derived pre-releases, different
  metadata): `Compare` and the five comparison methods agree with the model both ways;
  `sort.Sort(Collection)` orders 2–6 related versions as the model does. Finds /1 (and /2, /3).
- `TestHegelConstraintsFollowTheirRules` — one to three comparators with every operator
  (including the bare version), versions of one to four segments with optional pre-release,
  `v` prefix and zero padding, random blanks: `Check` of the whole and of each `Constraint`
  matches the model, `Prerelease()` and `String()` of each constraint are right, the printed
  constraints read back with the same verdict and are `Equals` to the original, and a
  re-spaced, reordered spelling with `=` for the bare operator is `Equals` too and checks the
  same. Finds /5 (and /2, /8, /1) in about 4% of its cases, so it is mapped intermittent.

The generators draw the shapes of the eight recorded bugs and the properties that meet them
are the expected failures mapped to the bugs (STYLE.md rule 11); every mismatch names the shape
it has. One narrow property per bug in `hegel_shapes_test.go` draws the bug's shape region with
random contents and fails every run: `PrereleasePrefixSortsLower` (/1, a pre-release that is a
proper prefix of the other followed by an alphanumeric identifier),
`PrereleaseCountsAcrossSegmentCounts` (/2, equal values of different segment counts, a
pre-release on one side), `LeadingZeroIdentifiersCompareNumerically` (/3),
`NewSemverRefusesLooseSpellings` (/4), `PessimisticSingleSegmentStaysInMajor` (/5, `~>` with
one segment), `EmptyLeadingIdentifierIsRefused` (/6), `ScanReadsBytes` (/7) and
`PessimisticMatchesShorterEqualVersion` (/8). `HEGEL_NO_KNOWN=1` switches the shapes off: the
generators draw the neighbouring regions (the same value written with the base's segment
count, `Scan` of strings, `~>` with two segments or more, no leading zeros) and all twelve
properties pass; the parse property then skips only its `NewSemver` refusal check on loose
spellings, which are half of its cases. `GO_VERSION_COLLECT=1` makes the properties record
mismatches instead of failing and print them shortest-first.

## Bugs (8; details in bugs.toml)

| id | summary | severity |
|----|---------|----------|
| go-version/1 | `1.0.0-alpha` > `1.0.0-alpha.beta` (spec: lower); upstream test asserts the inverted order | medium |
| go-version/2 | Pre-release ignored across segment counts: `1.0.0-alpha` = `1.0.0.0`, `= 1.0.0.0` matches `1.0.0-alpha`, intransitive order | medium |
| go-version/3 | Leading-zero numeric identifiers accepted and compared by length: `1.0.0-01` > `1.0.0-2` | low |
| go-version/4 | `NewSemver` accepts `v` prefix, 1/2/4 segments, leading zeros, `~` | low |
| go-version/5 | `~> 1` is unbounded (matches 2.0.0, 5.3.1) | low |
| go-version/6 | Trailing hyphen accepted as pre-release `-`: `NewVersion("1.2.3-")` prints `1.2.3--` | low |
| go-version/7 | `Scan` rejects `[]byte` | low |
| go-version/8 | `~> 0.3.0.0` rejects `0.3.0` although `~> 0.3.0` accepts `0.3.0.0` | low |

How they were found: /1, /2, /3, /4, /5 and /6 from reading version.go and constraint.go while
writing the model, confirmed by a probe file before the properties were written (the probe also
showed /7); /8 by the constraint property's first 20 000-case run (`~> 0.3.0.0+62F5` against
`0.3.0+A`).

## Not bugs (documented or design)

- Versions of more than three segments, zero-extension in comparisons, `1.0` = `1.0.0` =
  `1.0.0.0`, and `Core()` keeping the first three segments — documented.
- `NewVersion("1.2.3beta")` is `1.2.3-beta` — the loose grammar by design; `NewSemver` refuses
  it, asserted as such.
- `~` in identifiers (Debian-style) is accepted by `NewVersion` and sorts after `z` in byte
  order; only its acceptance by `NewSemver` is recorded (/4). The generators use spec
  characters.
- The pre-release rule of constraints (a constraint without a pre-release never matches one;
  `>= 1.0.0-beta` does not match `1.0.1-alpha`; `~> 1.0.0-beta` rejects `1.0.0`) — the code
  comments say so; modelled as documented.
- `Constraints.Equals` compares structurally after sorting (`>0.1,>0.2` ≠ `>0.2`) — documented.
- `Compare` with a zero-value `Version` treats it as 0.0.0 — documented in `bytes()`.
- A `WithPrefix` version compares without its prefix — the README says so.
- Segments are int64 (`9223372036854775808` is an error) and `Segments()` narrows to int —
  documented types; not compared.
- Error messages and types are not compared.
