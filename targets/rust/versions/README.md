# versions

[fosskers/rs-versions](https://github.com/fosskers/rs-versions): parsing and comparison of
software version numbers of any shape — `SemVer` (prescriptive, `u32` parts), `Version`
(`[epoch:] chunks [-release] [+meta]` with an RC/post-letter aware `Last`), `Mess` (alphanumeric
groups joined by `.`, `:`, `-`, `+`, `_`, `~`), the `Versioning` sum type that tries them in
that order and compares across kinds, and `Requirement` (`=`, `>`, `>=`, `<`, `<=`, `~`, `^`, `*`).
Used by Aura and other package tooling (11 M downloads). 8.0.0, last upstream commit 2026-09.

Written in the zoo (not imported from the predecessor). Built with `--features serde`. The
crate's own tests run alongside `tests/hegel.rs`; `semver` and `serde_json` are already
dev-dependencies upstream.

## What is tested

**`tests/hegel.rs`** — three oracles:
- a second implementation of the three grammars and of `Versioning::new`'s choice, building the
  expected values from the crate's public fields (`SemVer { major, .. }`, `Version { epoch,
  chunks, last, .. }`, `Mess { chunks, next }`), including the `Last` patterns (`1rc2`, `7b`), the
  `Digits`/`Rev`/`Plain` classification with `u32` overflow, leading zeros and the `unsigned`
  parser's `"0"`-first rule;
- the `semver` crate for the ideal type: parsing of strict texts with `u32` parts, ordering
  (build metadata stripped, since `semver` 1.x compares it), and `~`/`^` via `semver::VersionReq`
  on release versions;
- the laws of `Ord`/`Eq`/`Hash` (antisymmetry, transitivity, `==` ⇔ `cmp == Equal`, equal ⇒
  equal hash) on each type and on `Versioning` across kinds, plus the documented ordering rules.

Texts come from strict semver values, a general-shape generator (epoch, 1–5 chunks of numbers,
words and mixtures, release, meta), a Mess generator, and a soup with junk.
- `parsing_agrees_with_the_grammar_model`: `SemVer/Version/Mess/Versioning::new`, `FromStr`,
  `TryFrom` (error texts), `Display` round trip, `is_ideal/general/complex`.
- `strict_texts_parse_as_the_semver_crate_does`, `semvers_order_like_the_semver_crate`,
  `semvers_order_totally`.
- `documented_ordering_rules_hold`: epochs first, numeric sequences (longer wins on an equal
  prefix), `1.0rc1 < 1.0`, `3.7b < 3.7`, release numbers, `1.003.0 == 1.3.0` as `Mess`, `r8 < r23`,
  a revision below a number.
- `conversions_are_lossless` (`to_version`, `SemVer::to_mess`, `nth` for the three kinds,
  defaults), `chunk_digit_helpers_follow_their_docs` (`single_digit*`, `Last::from`).
- `requirement_texts_parse_per_the_operator_table`, `requirements_match_per_their_definitions`
  (the five comparison operators against `Ord`, `~`/`^` on ideal versions against
  `semver::VersionReq`, mixed kinds never tilde/caret-match), `serde_round_trips` (derived forms,
  `deserialize_pretty`, `Requirement::serialize/deserialize`).
- Pinned: `requirements_accept_every_versioning` (versions/1),
  `general_tilde_and_caret_follow_the_documented_extension` (versions/2),
  `versioning_comparison_is_a_total_order` (versions/3),
  `versioning_orders_version_texts_like_version_does` (versions/4), `messes_order_totally`
  (versions/5), `to_mess_builds_what_mess_parsing_builds` (versions/6), `to_mess_keeps_the_metadata`
  (versions/7), `versions_order_totally` (versions/8).

## Oracles

The crate's documented grammars re-implemented; the `semver` crate; the `Ord`/`Eq`/`Hash`
contracts; the crate's own documentation of `Last`, epochs, `Mess` digits and the requirement
operators.

## Not tested

The exact cross-kind order beyond its laws and the numeric cases (the crate says a `Mess` "is
not guaranteed to have well-defined ordering behaviour"); `Chunk::cmp_lenient`'s alphanumeric
rules beyond the documented `r8 < r23` and `0rc1 < 1rc1`; `~`/`^` on alphanumeric general
versions (the code's TODO says "do our best"); `nom` parser composition beyond
`Versioning::parse`.

## Bugs

The parsers are right (the model agrees on everything); the bugs are in the hand-stitched
comparisons across kinds, the requirement matching of general versions and the conversions.
- **versions/1** (medium, upstream #31/#33 open): `Versioning::parse` is a nom `alt` that stops
  after a `SemVer`/`Version` prefix, so `Requirement::new("^1.2.3.4")` is `None`.
- **versions/2** (medium): `~`/`^` on general versions ignore the `last` component (`~1.2.3.4`
  matches `1.2.3.0`; `~7` matches nothing, not even `7`; `^0.1.2.3` matches `1.1.2.3`).
- **versions/3** (medium): `Versioning`'s `Ord` is not transitive (`0.0.0 < 4294967296 < a <
  0.0.0`); sorting 40 such values panics since Rust 1.81.
- **versions/4** (medium): a `SemVer` is `Equal` to a general version whose last part is an RC or
  post-letter with the same number (`1.2.3 == 1.2.3rc1 == 1.2.3-alpha` by `cmp`).
- **versions/5** (low): `Mess`'s `Ord` ignores the separator kind and the digits' spelling that
  its derived `Eq`/`Hash` include (`1-2` vs `1_2`, `1.01` vs `1.1`).
- **versions/6** (low): `Version::to_mess` makes `Plain("r3")` where `Mess::new` makes
  `Rev(3, "r3")`, so the two order differently (the code's own FIXME); a hyphenated release
  identifier stays one chunk.
- **versions/7** (low): `Version::to_mess` always, and `SemVer::to_mess` without a pre-release,
  drop `+meta` although documented lossless.
- **versions/8** (low): `Version` derives `Eq`/`Hash` over the metadata its `Ord` ignores.

Noted, not recorded: `Version` is not a subset of `Mess` (`0+-` is a `Version`, not a `Mess`);
`single_digit_lenient` reads a zero-led run as 0 (`01abc` → 0, the `unsigned` parser's rule,
upstream #34 open); leading zeros are rejected by `SemVer`/`Version` by design (`1.01.1` in the
crate's `bad_semvers`).

## History

- 2026-09-13: written in the zoo against `3ae61d089e38` (2026-09-05, 8.0.0) with hegeltest
  0.44.1. The source was read first: the `alt` prefix issue, the `chunks`-only tilde/caret, the
  `Equal` arm for RCs, the derived `Eq` over ignored fields and the `Plain`-for-`r` FIXME were all
  visible by eye and confirmed by the first 100-case run, which also produced the intransitive
  triple (versions/3); the 1 000-case run added versions/8. Test defects on the way: the model
  assumed `Version ⊂ Mess`; `Requirement::new("*")` is the wildcard even without an operator;
  a `chunk_of` on a non-chunk piece. Clean at 100 + 3 × 1 000 + 10 000 cases with the eight pins.
- 2026-09-14: base bumped 3ae61d089e38 → 4fdfd94332f6 (2026-09-14, "release: 8.0.1"; 8.0.1); 8 bug(s) still reproduce. 70 tests pass.
