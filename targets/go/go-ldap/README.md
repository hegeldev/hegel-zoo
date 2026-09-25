# go-ldap

[go-ldap/ldap](https://github.com/go-ldap/ldap) is the Go LDAP client (module
`github.com/go-ldap/ldap/v3`, the `v3/` subdirectory). The zoo exercises its pure string
functions: `ParseDN`, `DN.String`, `Equal`/`EqualFold`/`AncestorOf`/`AncestorOfFold` and
`EscapeDN` (RFC 4514 distinguished names), and `CompileFilter`, `DecompileFilter` and
`EscapeFilter` (RFC 4515 search filters). No connection is made. The pin is `2f8603f`
(2026-09-07, v3.4.14).

The repository is MIT; `CONTRIBUTING.md` is about compatibility and testing, the README says
nothing about AI-written code, and there are no agent instructions. The zoo keeps its tests in
its own patch and files nothing upstream.

## Build

`go test -count=1 -run TestHegel -v .` in `v3/`. The patch adds, as the external package
`ldap_test`, `hegel_test.go` (harness, the `noKnown` switch), `hegel_shapes_test.go` (one narrow property per recorded bug), `hegel_dn_test.go` (DN model,
generators, properties), `hegel_filter_test.go` (filter model, generators, properties) and
`hegel_pins_test.go` (one plain test per bug), and requires `hegel.dev/go/hegel v0.6.33` in
go.mod.

## Oracle

The two RFC grammars, written as strict parsers, plus the godoc's semantics.

- DN: `distinguishedName = [RDN *(COMMA RDN)]`, `RDN = ATAV *(PLUS ATAV)`, type a descr or
  numericoid, value a string (pairs `\X` for the specials, space, `#`, `=`, `\`; `\XX` for any
  byte; no unescaped NUL, `"`, `;`, `<`, `>`, leading space or `#`, trailing space) or a
  hexstring (`#` + hex of one primitive BER element, the content as the value). The library's
  documented leniencies - insignificant spaces around types and values, `;` as an RDN separator -
  are rendered by the generator on request and excluded from the strict check. `String()` must
  be grammatical, parse back to an `Equal` DN, be idempotent, lower-case the types and keep the
  values; two renderings of one DN must give one `String()`. `Equal` is RFC 4517's
  distinguishedNameMatch as the godoc restates it (RDNs by position, attributes as a multiset,
  types case-insensitive, values exact; `EqualFold` folds values too), `AncestorOf` a strict
  suffix; `Equal` DNs have the same `String()`.
- Filter: `filter = "(" filtercomp ")"`, and/or lists (empty allowed, RFC 4526), not, and items:
  equality, `>=`, `<=`, `~=`, present (`=*`), substrings (`initial*any*...*final`, empty `any`
  components carrying nothing), extensible (`attr [":dn"] [":" rule] ":=" value`, an attribute or
  a rule required); attributes and rules as RFC 4512 attribute descriptions / OIDs; values with
  `\XX` escapes, no unescaped `(`, `)`, `*`, NUL, valid UTF-8. The BER packet is read back into
  the same structure (checking RFC 4511's shape: two children for an assertion, a non-empty
  substrings SEQUENCE, the extensible children by tag). `DecompileFilter` must produce the
  canonical form (values through `EscapeFilter`: `()*\`, NUL and non-ASCII bytes as `\xx`), which
  compiles back to the same packet.

Generators build DNs (0-4 RDNs, 15% multi-valued, values from pools of letters, spaces, `#`,
the specials, `=`, NUL, non-ASCII runes and an invalid byte, 8% empty) and filters (depth 3;
attributes from a pool of descrs, OIDs and options), rendered with random escaping choices
(`\X` or `\XX`, either hex case, raw or hex-escaped non-ASCII, 10% hexstring values). Mutations
(delete, insert, replace, swap, duplicate; the inserted pieces include the meta-characters,
`:dn:`, `**`, `\2a` and invalid bytes) probe the boundary of each grammar.

## Method

| Property | Checks |
|---|---|
| DNParsesGrammar | a grammatical (or leniently spaced) DN string parses to its structure; `String()` is canonical, stable and the same for every rendering |
| DNMutationsAreStable | grammar-valid mutations parse as the grammar says; whatever `ParseDN` accepts has a grammatical `String()` that reparses `Equal` |
| DNComparisons | `Equal`, `EqualFold`, `AncestorOf`, `AncestorOfFold` against the model on related pairs; `Equal` iff same `String()` |
| EscapeDNRoundTrip | `EscapeDN(v)` inside a two-valued RDN parses back to `v` |
| FilterCompilesGrammar | a grammatical filter compiles to the structure the grammar reads, decompiles to the canonical form, which recompiles to the same packet |
| FilterMutationsAreStable | grammar-valid mutations compile as the grammar says; whatever `CompileFilter` accepts is a well-formed packet whose decompiled form is grammatical and recompiles to the same packet |
| EscapeFilterRoundTrip | `EscapeFilter(v)` in equality and substring positions parses back to `v` |

## Known bugs

The generators draw the shape of every recorded bug (STYLE.md rule 11), so five of the wide
properties are expected failures mapped to the bug they land on, all intermittent because each
shape is a few percent of the cases: DNParsesGrammar on go-ldap/9 (a hexstring value with a
space, about 5 %), DNMutationsAreStable and EscapeDNRoundTrip on go-ldap/8 (a byte that is not
UTF-8, turned into U+FFFD by `ParseDN` and by `EscapeDN` alike; 9 % and 11 %),
FilterCompilesGrammar on go-ldap/4 (`(cn=\ufffd)`, 12 %; /3 in some runs) and
FilterMutationsAreStable on go-ldap/5 (`(*cn=)`, 13 %; /4, /3, /6, /1 and /2 at lower rates;
/7 is never reached by the mutations). DNComparisons and EscapeFilterRoundTrip have no bug
shape and pass. Each bug also has a narrow property over its own shape region in
`hegel_shapes_test.go`, the deterministic expected failure beside the pin:
`TestHegelFilterListClosersAreChecked` (go-ldap/1), `TestHegelStarOnlyConditionsAreNotEmptySubstrings`
(/2), `TestHegelDnattrsMarkerIsCaseInsensitive` (/3), `TestHegelReplacementCharacterCompiles`
(/4), `TestHegelFilterAttributesAreValidated` (/5), `TestHegelExtensibleMatchNeedsAttributeOrRule`
(/6), `TestHegelEmptyAttributeTypesAreRejected` (/7), `TestHegelDNRejectsOrKeepsBytesThatAreNotUTF8`
(/8) and `TestHegelHexstringValuesIgnoreInsignificantSpaces` (/9). `HEGEL_NO_KNOWN=1` (read
once) switches the shapes off: the model reproduces each recorded behaviour, the pools lose
`\xff` and U+FFFD, mutations stay on rune boundaries and off the protected head of a filter,
and the residual lenient acceptances that only a recorded bug explains are assumed away (0.4 %
of the filter mutations); every property then passes at 1000 cases. `ZOO_COLLECT=1` records
mismatches instead of failing and prints the agreement classes (in the mutation properties
about a third of the strings are grammar-valid and agreed, half are rejected by both, the rest
are lenient acceptances checked for stability).

## Accepted differences

- Insignificant spaces around types and string values, and `;` as an RDN separator, are
  accepted "for compatibility" (RFC 2253 forms); the model renders them only when asked.
- Attribute types in a DN are not validated (`c*n=a` parses); the mutation property counts such
  acceptances without checking their `String()`.
- Escapes are accepted inside attribute types (`c\6en=a`), and a hexstring for any type, not
  only dotted-decimal ones; the hexstring's BER element may carry any primitive tag.
- Unescaped `(`, `*` (outside substrings), `=` and NUL inside filter values are accepted and
  escaped on decompile; `((a=b))` compiles as `(a=b)`.
- `strings.EqualFold` is the model's case folding for `EqualFold`, as the godoc's "case ... is
  not significant" reads; values with bytes that are not UTF-8 are therefore not generated in
  folded comparisons.

## Bugs found

Nine, in bugs.toml: the byte closing an AND/OR/NOT list or a nested filter is never checked
(`(&(a=b)x` compiles); `(sn=**)` compiles to a Substrings filter with an empty SEQUENCE and
decompiles as `(sn=)`; `:DN:` is not dnattrs; a literal U+FFFD in a filter value is rejected; the
attribute description is not validated, and `DecompileFilter` escapes what `CompileFilter` took
literally; an extensible match with neither attribute nor rule compiles; a DN with an empty
attribute type parses (`=a=b` as `a=b`); bytes that are not UTF-8 in a DN become U+FFFD; spaces
around a hexstring value are not insignificant (leading: literal, trailing: error).

## History

- 2026-09-21 (turn 342): target added at 2f8603f (v3.4.14) with seven properties, 9 pins.
- 2026-09-25: generators rewritten in combinator style; the properties draw the known shapes and
  nine narrow properties were added; go-ldap/8's notes gained EscapeDN; a classifier defect fixed
  (lenient acceptances of compound filters were all reported as go-ldap/5).
