# go-spdx

[github/go-spdx](https://github.com/github/go-spdx) (module `github.com/github/go-spdx/v2`,
package `spdxexp`) validates SPDX license expressions and decides whether an allowed list of
licenses satisfies an expression: `Satisfies`, `ValidateLicenses`,
`ValidateLicensesWithOptions`, `ValidateAndNormalizeLicensesWithOptions`, `ExtractLicenses`,
over the SPDX license, exception and deprecated lists and a table of version ranges
(`spdxlicenses`). The pin is `48a80b3` (2026-05-21, v2.7.0).

The repository is MIT; `CONTRIBUTING.md` is about setup and tests, the README says nothing
about AI-written code, and there are no agent instructions. The zoo keeps its tests in its own
patch and files nothing upstream.

## Build

`go test -count=1 -run TestHegel -v ./spdxexp` in the module root. The patch adds, as the
external package `spdxexp_test`, `hegel_test.go` (harness, the `Known` switches),
`hegel_model_test.go` (trees, tokenizer, parser, canonical rendering, compatibility, expansion,
the models of Satisfies and Validate), `hegel_props_test.go` (generators, properties),
`hegel_shapes_test.go` (the sixteen narrow properties) and `hegel_pins_test.go` (one plain
test per bug), and requires `hegel.dev/go/hegel v0.6.33` in go.mod.

## Oracle

The SPDX 2.3 license expression grammar (Annex D: `license-id`, `license-id+`, `license-ref`,
`WITH license-exception-id`, `AND`, `OR`, parentheses, AND binding tighter than OR) with the
leniencies the package documents - identifiers case-insensitive against the lists, spaces the
only whitespace, upper-case operators, `-only` / `-or-later` / `+` normalization - written as
a tokenizer and a right-recursive parser that mirror `scan.go` and `parse.go`; a canonical
rendering (canonical identifiers, `+` unless the identifier ends in `-or-later`, `WITH`,
upper-case operators, parentheses only where an OR is an operand of an AND), which is what
`ValidateAndNormalizeLicensesWithOptions` and `reconstructedLicenseString` produce; license
compatibility as node.go states it (same reference; same exception, then the same identifier
or, through `spdxlicenses.LicenseRanges` with `-or-later` stripped and the first matching
group, same group when both carry `+`, same-or-later version when the allowed one does,
same-or-earlier when the expression's does, same version otherwise); and two readings of
`Satisfies`: the documented meaning (AND/OR over "some allowed license covers this one") and
the package's own DNF expansion (`expand`/`expandOr`/`expandAnd`), reproduced with its
recorded bugs under `Known` so that the property compares against the expansion and counts how
often it departs from the meaning. The fast paths of `Satisfies` and `Validate...` (MIT, an
atomic identifier, `X WITH Y`) and the option checks are modelled as coded, each divergence
behind a switch.

Generators build trees of up to four licenses (the slice-aliasing bug needs five; `Known.
appendAliasing` lifts the limit) from a pool of active and deprecated identifiers (including
`-only`, `-or-later` and deprecated `+` forms), 25% with `+`, 15% with an exception, 15%
references (with and without DocumentRef); the text has random identifier case, one or two
spaces, optional parentheses around operands and atoms. Allowed lists mix the expression's own
atoms (as written or re-cased), pool atoms, and sometimes an invalid entry, an expression or
nothing. Mutations (delete, insert, replace, truncate, re-case one character; inserted pieces
include operators, parentheses, `+`, `-only`, `-or-later`, lower-case keywords, a bare
`DocumentRef-`) probe the grammar's boundary.

## Method

| Property | Checks |
|---|---|
| NormalizeFollowsTheGrammar | a generated expression is valid, `ValidateAndNormalize` returns the canonical rendering of its tree, `ExtractLicenses` returns the set of its atoms |
| ValidateOptions | `ValidateAndNormalizeLicensesWithOptions` / `ValidateLicensesWithOptions` on one to three inputs (generated or from a list of edge strings) with random options agree with the model: normalized list in order without duplicates, invalid list in order |
| SatisfiesFollowsTheModel | `Satisfies` on a generated expression and allowed list: error when the list is empty or has an invalid entry or an expression, otherwise the expansion's verdict; the cases where the expansion departs from the meaning are counted |
| SatisfiesMonotone | adding an allowed license never turns true into false |
| MutationsAgree | on a mutated expression, `ValidateLicenses` and the model agree on validity and `Satisfies` on error and verdict |
| PoolsAreKnown | the generator's identifiers are on this version's lists |

Sixteen narrow properties in `hegel_shapes_test.go`, one per bug, each over the bug's shape
region with random contents and judged by the same model: `LicenseRefAlternativesCount` (1),
`AndTermsKeepTheirOwnAlternatives` (2), `OrAlternativesKeepAllAndTerms` (3),
`SatisfiesNeverPanics` (4), `OptionsApplyInsideExpressions` (5), `WithExpressionsValidate`
(6), `MITIsSatisfiedLikeOthers` (7), `SatisfiesValidatesTheAllowedList` (8),
`UnlistedSuffixIdentifiersRejected` (9), `LicenseRefWithExceptionParses` (10),
`KeywordsNeedSeparation` (11), `LowercaseWithIsConsistent` (12),
`PlusNormalizationIsConsistent` (13), `ExtractLicensesIsOrdered` (14),
`MPLNoCopyleftExceptionIsInRange` (15), `ParserNeverPanics` (16). Each fails on its bug (10
and 13 name go-spdx/6 beside their own, since the WITH fast path changes the expectation on
those surfaces too); under `HEGEL_NO_KNOWN=1` it draws the neighbouring region and passes.

## Known shapes drawn by default

The sixteen `Known` switches are off by default (`HEGEL_NO_KNOWN=1`, read once, turns them
on): the model says what the documentation and the SPDX grammar say - `eval`, the meaning of
the expression, for `Satisfies`; every range group for the version table; the options as
documented; a sequence for `ExtractLicenses` - and the generators draw every recorded shape as
an explicit alternative of the expression tower (`refInOr`, `refOrUnderAnd`, `orOfAndWithOr`,
`orOfAndOfRefOr`, `nestedAndChain` beyond four licenses), of the atoms (deprecated `+`
identifiers, unlisted suffixes, `LicenseRef WITH`, lower-case `with`), of the spelling (glued
keywords, `X+ WITH Y`, parentheses around `WITH`) and of the allowed list (invalid entries,
padded entries, `MIT+` against `MIT`, range-group neighbours); a mismatch names the shapes the
case has (`mismatch(ht, shapes, ...)`), with `explains` flipping each bug's switches to see
which change the expectation (bug 4 needs 1 and 3, bug 12 needs 8). Over nine default
rounds Normalize shrank to go-spdx/9 six times, ValidateOptions to go-spdx/6 seven times and
SatisfiesFollowsTheModel to go-spdx/7 seven times (plain); SatisfiesMonotone splits between
go-spdx/10 (a `LicenseRef WITH exception` stranger in the valid list) and go-spdx/4 (the
panic) and passed once in some sixty runs, and MutationsAgree fails at a natural rate of
about 2% of the mutated strings, passing about one run in four (both intermittent). Under
`HEGEL_NO_KNOWN=1` the switches reproduce the package and the four-license cap steers as
before; no case is assumed away and every property passes (1000 cases).

The generators are package-level values in combinator style: atoms as `atomSpec` records with
a pure `text()` drawn from the pools, trees as records from a depth-indexed eager tower
(`nodeKit.levels`), the spelling as a record of gap and parenthesis tapes read modulo by a
pure `render` that also reports the marks it left (glued keywords, suffixes, a lower-case
`with`), the allowed list as a record derived from the tree (own atoms in a drawn form,
strangers, range neighbours, invalid extras, a rotation), mutations as edit records applied
modulo the live length; the judges `judgeSatisfies`/`judgeValidate`/`judgeNormalize` are
shared by the wide and the narrow properties. `ExtractLicenses` is memoised per input within a
run: hegel-go treats a non-deterministic failure as a pass, so go-spdx/14's random order would
otherwise hide itself. `ZOO_COLLECT=1` records mismatches instead of failing and prints the
classes.

## Accepted differences

- Identifiers are case-insensitive but `LicenseRef-`/`DocumentRef-` and their idstrings are
  exact, and references are compared exactly; the model follows.
- Only spaces are whitespace (a tab is "unexpected"), operators are upper-case only (a
  lower-case `and` is an unknown license); the model follows.
- Spaces around the `:` of `DocumentRef-d : LicenseRef-x` are accepted; `+` must follow the
  identifier directly ("unexpected space before +"); `(MIT)+` is a syntax error.
- An allowed `X WITH exception` does not cover the plain `X` and vice versa (node.go
  exceptionsAreCompatible); both `+` sides in the same range group are compatible whatever the
  versions (`Apache-2.0+` is satisfied by `Apache-1.0+`).
- `GPL-1.0-or-later` and `GPL-2.0-or-later` sit in the same version set as `GPL-3.0` in the
  range table; the code strips `-or-later` before the lookup, so the entries are dead, and the
  model does the same.

## Bugs found

Sixteen, in bugs.toml: a LicenseRef alternative of an OR is dropped from the expansion (false
negatives, and a false positive when the OR is under an AND); AND-terms built on a slice with
spare capacity all end with the last alternative; only the first AND-term of an OR alternative
is kept; Satisfies panics on an OR of references under an AND under an OR; the validation
options are decided from the string's shape and do not apply inside expressions; the WITH fast
path of ValidateLicenses rejects `MIT+ WITH X` and `(MIT WITH X)` without parsing; the MIT fast
path compares strings only; the fast paths skip the allowed-list validation the README
promises; `-only`/`-or-later` suffixes are accepted on any identifier and the rewrite swallows
a character; `LicenseRef-x WITH exception` is a syntax error; keywords are matched as prefixes;
a lower-case `with` is accepted by the fast paths only; a deprecated `+` identifier normalizes
differently alone and in an expression; `ExtractLicenses` order is random; the second MPL range
group is unreachable; the parser panics on input ending after `(` or a DocumentRef.

## History

- 2026-09-21 (turn 343): target added at 48a80b3 (v2.7.0) with five properties, 16 pins.
- 2026-10-07: generators rewritten in combinator style; the sixteen known shapes drawn by default (three wide properties plain, two intermittent); sixteen narrow properties added; the model's end-of-keyword inputs reclassified from the panic shape to a plain error, and the WITH fast path's deprecated `+` identifier gated by go-spdx/13.
