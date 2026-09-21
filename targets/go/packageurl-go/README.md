# packageurl-go

[package-url/packageurl-go](https://github.com/package-url/packageurl-go) is the Go
implementation of the Package URL specification (purl, ECMA-427): `FromString` parses a
`pkg:type/namespace/name@version?qualifiers#subpath` string into a `PackageURL`, `ToString`
writes the canonical form, `Normalize` applies the specification's rules (case, empty
qualifiers, type-specific validation), with `Qualifiers` helpers. The pin is `3417966`
(2026-08-24, two commits after `v0.1.7`); its testdata submodule pins purl-spec `9d6b901`
(2026-07-16), whose test suite upstream passes.

The repository has LICENSE and mit.LICENSE (MIT); the README's contributing note says nothing
about AI-written code, there is no CONTRIBUTING.md and no agent instructions. The zoo keeps its
tests in its own patch and files nothing upstream.

## Build

`go test -count=1 -run TestHegel -v .` in the module root; no submodule is needed (the
specification's suite is upstream's own test, not run here). The patch adds, as the external
package `packageurl_test`, `hegel_test.go` (harness, the `Known` switches),
`hegel_model_test.go` (the specification model), `hegel_gen_test.go` (generators),
`hegel_props_test.go` and `hegel_pins_test.go` (one plain test per bug), and requires
`hegel.dev/go/hegel v0.6.33` in go.mod (the `go` directive rises to 1.26).

## Oracles

- **The specification's own procedures**, restated as a model: "How to build a PURL" and
  "How to parse a PURL" (`docs/specification/how-to-build.md`, `how-to-parse.md`), the
  character-encoding clause 5.4 (encode every byte but letters, digits, `.-_~` and `:`, as
  UTF-8, uppercase hex), the component rules of 5.6 (type and qualifier-key grammars, empty
  values dropped, keys lowercased, unique and sorted, subpath segments empty/`.`/`..`
  discarded, decoded segments without slashes), and the type definitions at `9d6b901`
  (`types/<type>-definition.json`: namespace required/optional/prohibited, `case_sensitive:
  false` meaning "the form shall be lowercase", required qualifiers, `permitted_characters`,
  the cpan and pypi rules). Where the procedure text and the specification's test suite
  disagree the suite wins: trailing slashes before the name are not stripped
  (`pkg:swift/github.com/Alamofire/@5.4.3` must fail), and golang namespaces and names are
  lowercased (the definition says `case_sensitive: true` and "must be lowercased" at once).
- **The laws the package documents**: `ToString` after `FromString` is a fixed point, a parsed
  value is a fixed point of `Normalize` and of `FromString`∘`ToString`, `String` equals
  `ToString`, `QualifiersFromMap` and `Map` are inverse and the result is sorted.

Generators draw components from pieces that need encoding (space, `/ @ ? # & = % + , ;`,
`é`, `日`), case pairs, `.`/`..`, leading and trailing slashes, registered, unregistered and
invalid types, valid and invalid qualifier keys, empty values and duplicates; strings are
spelled with or without percent-encoding per byte, lowercase hex, `PKG:`/`pkg://`, extra
slashes, empty and unsorted qualifiers, and a quarter are mutated (a separator or a bad escape
inserted, a byte removed, a prefix uppercased).

## Method

| Property | Checks |
|---|---|
| BuildFollowsTheSpec | `Normalize` accepts iff the build procedure does; the normalized components and `ToString` equal the model's; `String() == ToString()`; `FromString` of the string `ToString` writes before `Normalize` means the same purl |
| ParseFollowsTheSpec | `FromString` accepts iff the parse procedure does and yields the same components |
| RoundTrip | on any string `FromString` accepts: `ToString` parses back to the same value and is a fixed point; `Normalize` on a parsed value changes nothing |
| QualifiersRoundTrip | `QualifiersFromMap(m).Map() == m`, sorted by key; `Qualifiers.String` and `Qualifier.String` are the encoded, `&`-joined form |

Mismatches are classified before they count: a `Known` switch per recorded bug gates the input
shape (types and keys starting with punctuation, encoded slashes in segments, dotted and empty
subpath segments, slashes around the name and empty namespace segments, the unenforced
namespace and swid requirements, the case rules of eight types, chrome-extension letters,
empty-valued qualifiers before `Normalize`); the pins assert the specification and fail while
the bug exists. `ZOO_COLLECT=1` records mismatches instead of failing and prints the class
counts.

## Accepted differences

- An unencoded `@` at the start of the remainder (`pkg:npm/@scope/name`) is read by the
  procedure as the version separator and by upstream as an npm scope (its documented
  leniency, with tests); such strings are not judged.
- A second unencoded `?` or `#` is not a valid purl; the procedure text splits once from the
  right, upstream at the first occurrence; such strings are not judged.
- An unencoded `;` in the qualifiers is rejected ("invalid semicolon separator", as
  `url.ParseQuery` does); `;` is not a permitted character, so the string is not a valid purl
  either way; such strings are not judged.
- An empty qualifier key with an empty value: the build procedure's order would discard the
  pair, upstream rejects the key first; the model rejects too.
- golang namespaces and names are lowercased (see Oracles); hackage's "Apply kebab-case" and
  pub's "Replace non-[a-z] letters..." normalization rules are prose upstream does not
  implement and the model does not either.
- cpan: a lowercase namespace or a `::` in the name is rejected rather than normalized; the
  definition says "MUST be uppercase" and the suite expects failures.
- purl-spec has moved on since `9d6b901` (gem's `platform` and rpm's qualifiers validated,
  git's namespace split, brew added): upstream's own fixture test fails against the current
  suite, but the pin is judged against the suite it pins.

## Bugs found

Ten, in bugs.toml, all against the specification at the pinned suite: type and qualifier-key
grammars accept leading punctuation; an encoded slash in a namespace or subpath segment becomes
a separator; dotted and empty subpath segments are kept or rejected instead of discarded;
`Normalize` is not the canonical form (slashes around the name, empty namespace segments); the
case rules of hex, luarocks, oci, otp, pub, pypi, vscode-extension and yocto are not applied;
chrome-extension names accept q-z; the namespace requirement is checked for six of thirty-one
types that have one; `ToString` before `Normalize` writes empty-valued qualifiers with encoded
keys; swid's required `tag_id` is not checked.

## History

- 2026-09-21 (turn 338): target added at 3417966 (v0.1.7+2) with four properties, 10 pins.
