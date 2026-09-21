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
the models of Satisfies and Validate), `hegel_props_test.go` (generators, properties) and
`hegel_pins_test.go` (one plain test per bug), and requires `hegel.dev/go/hegel v0.6.33` in
go.mod.

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

Each recorded bug has a `Known` switch: the model reproduces the behaviour or the generator
avoids the shape while it is on; the pins assert the documented behaviour and fail while the
bug exists. `ZOO_COLLECT=1` records mismatches instead of failing and prints the agreement
classes: in SatisfiesFollowsTheModel about 5% of the cases get a verdict that differs from the
documented meaning (bugs 1-3), in MutationsAgree about 15% of the mutated strings stay valid.

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
