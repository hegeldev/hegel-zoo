# lenient_semver

[knutwalker/lenient-semver](https://github.com/knutwalker/lenient-semver): a lenient parser for
semantic version texts — optional minor/patch, a leading `v`, surrounding whitespace, `.`-separated
pre-release identifiers, additional numeric identifiers folded into build metadata, `Final`/
`Release`/`r` in pre-release position folded into build metadata, numbers that overflow `u64`
treated as strings — implemented as a table-driven DFA (`lenient_semver_parser`) over a
`VersionBuilder` trait, with builders for `semver` 1.x/0.11/0.10 and the crate's own
`lenient_version::Version` (additional numbers, pre-release/build texts, ordering, serde), plus
`parse_partial` for reading a version off the front of a longer text. 0.4.3, last upstream commit
2022-11.

Written in the zoo (not imported from the predecessor). Built with `--all-features` (the doc tests
demand it; the root crate's features are the three `semver` builders, `parse_partial` and the
`version_*` flags). The crate's own tests run alongside `tests/hegel.rs`; the tests use the
workspace's existing `semver_v100` dev-dependency for the strict parser.

## What is tested

**`tests/hegel.rs`** — three oracles:
- a second implementation of the documented lenient grammar (plain recursive code over the
  byte classes the DFA uses, recording the `VersionBuilder` calls `Major/Minor/Patch/Add/Pre/Build`
  and the error kind + byte span), with a partial-mode variant that mirrors the documented
  `parse_partial` contract (errors before or in the major number are kept; any later error ends
  the version, the segment being read is committed, and the input from the offending character
  — or from the separator when a segment was expected — is the remainder);
- the strict `semver` crate: every valid semver text must parse identically (the one documented
  deviation, a pre-release that *is* `Final`/`Release`/`r`, is generated with a `.0` suffix);
- `lenient_version::Version`'s own `Display`, `Ord`, `From<Version> for semver::Version` and serde
  forms, checked against the recorded calls and against `semver`.

Inputs: a token soup of numbers (including `0…`, `u64::MAX` and 20-digit overflows), words (`rc`,
`alpha`, `Final`, `RELEASE`, `r`, …), `.`, `-`, `+`, whitespace kinds and junk (`,`, `*`, `?`,
emoji, `ä`, `/`, …); structured lenient texts `v? major (.seg){0..4} (-pre)? (+build)?`; and
strict semver texts — each optionally decorated with a leading `v`/`V` and whitespace.
- `the_parser_agrees_with_the_model`, `partial_parsing_agrees_with_the_model`: `parse`,
  `parse_into`, `parse_partial` versus the model (calls, or error kind and span, and the
  remainder).
- `errors_describe_their_kind_and_position`: `input`, `erroneous_input`, `error_line` texts,
  `Display`/`{:#}` layout, `indicate_erroneous_input` (tildes and carets counted in bytes — a
  multi-byte character gets one caret per byte), `owned()`/`borrowed()` round trip.
- `strict_texts_parse_as_semver_does`: strict texts (with `v`, whitespace) parse to the
  `semver::Version`; `Version::parse` + `Display` round trip; `M` and `M.m` shorthands.
- `the_semver_and_lenient_version_builders_agree_with_the_calls`: the `semver` builder's
  sanitising (additional numbers → leading build identifiers, illegal pre-release characters →
  `-`, leading zeros of numeric pre-release identifiers dropped, empty identifiers dropped) and
  `lenient_version::Version`'s fields, `Display` re-parse, `is_pre_release`, both roads to
  `semver::Version`, serde JSON round trip.
- `lenient_versions_order_like_semver_where_both_apply`: `Ord`/`Eq` against `semver` (without
  build metadata, which the lenient type ignores) on texts both agree on; `bump_*`/`bumped_*`.
- `partial_parsing_walks_a_list_of_versions`: whitespace-separated strict versions read one after
  another with `parse_partial`, the remainder and the final error.
- Pinned: `overflowing_numbers_are_strings_whatever_follows` (lenient_semver/1),
  `release_identifiers_may_be_followed_by_build_metadata` (lenient_semver/2),
  `a_second_plus_in_the_build_metadata_is_an_error` (lenient_semver/3). The three general
  model properties skip exactly the inputs of the pinned bugs (`hits_known_bug`).

## Oracles

The crate's documented grammar (README list and the railroad diagram) re-implemented; the
`semver` 1.x crate; the crate's own `Display`/`Ord`/`From` implementations checked against each
other and against `semver`.

## Not tested

The `semver` 0.10/0.11 builders (compiled, not exercised); the `strict` and `generator`
parser features (workspace-internal, not exposed by the root crate); `lenient_version`'s
deserialisation from owned strings (it implements only `visit_borrowed_str`, so escaped JSON
strings fail — by design); comparison of `Additional` identifiers beyond what `Display`
round-tripping covers.

## Bugs

The lenient DFA's main path is right; the bugs are in the arms of its transition table for
inputs the railroad diagram does not draw.
- **lenient_semver/1** (medium): a numeric segment that overflows `u64` is documented to be a
  string (`1.99999999999999999999` → `1.0.0-99999999999999999999`), but when whitespace or `+`
  follows it is silently dropped: `1.18446744073709551616 ` → `1.0.0`, `1.2.3.99999999999999999999+x`
  → `1.2.3+x`.
- **lenient_semver/2** (low): a release identifier in pre-release position followed by build
  metadata is refused — `1.2.3-Final+sha`, a valid semver text, fails with "Unexpected `+`"
  (deliberate branch; recorded because the crate is documented as more lenient than `semver`).
- **lenient_semver/3** (medium): a second `+` in the build metadata makes the parse succeed with
  the whole build gone: `1.2.3+build+rest` → `1.2.3`, `0+0+` → `0.0.0`.

Quirks noted, not recorded: the error indicator is byte-based (`0 ä` → `~~^^`); partial parsing
of `1.2.3-Final+sha` yields `(1.2.3, "+sha")`, dropping the `Final` (the partial face of
lenient_semver/2).

## History

- 2026-09-13: written in the zoo against `3585c592a885` (2022-11-30, 0.4.3) with hegeltest
  0.44.1. The parser was read first and the grammar re-implemented as the model; the first
  100-case run of the partial-mode comparison found lenient_semver/1 (` V0.99999999999999999999 `)
  and lenient_semver/2 (` V0.Final+`), the first 1 000-case run lenient_semver/3 (`0+0+`), each
  confirmed by probes in full mode. Model corrections on the way: overflow of the major number is
  reported before the following character is classified; an unexpected character right after the
  major number ends a partial parse rather than failing it. Clean at 100 + 3 × 1 000 + 10 000
  cases with the three pins. Upstream issues (#19 open, #26 closed) are unrelated.
