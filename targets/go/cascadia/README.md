# cascadia

[andybalholm/cascadia](https://github.com/andybalholm/cascadia) (BSD-2-Clause), pinned at
`154416a` (v1.3.5 plus three commits, 2026-09-15): the Go CSS selector engine over
`golang.org/x/net/html` trees, used by goquery and many scrapers - Selectors Level 3 and 4
(attribute operators with the `i` flag, `:not`, `:has` with relative selectors, the `nth-*`
family, `:empty`, `:root`, `:link`, `:lang`, `:enabled`, `:disabled`, `:checked`) plus its own
extensions (`:contains`, `:containsOwn`, `:matches`, `:matchesOwn` on regular expressions,
`:haschild`, `:input`, `[attr!=val]`, `[attr#=regexp]`), pseudo-elements, specificity and
serialisation.

The patch adds the `hegel.dev/go/hegel` requirement to `go.mod` and eleven test files (package
`cascadia_test`): `hegel_test.go` (plumbing, the collector, the case judge and the `known`
value of the fourteen recorded bugs' switches), `hegel_idioms_test.go` (the generator idioms
shared with the other rewritten Go targets), `hegel_doc_test.go` (the `dnode` document record,
the pools, serialisation and parsing), `hegel_docs_test.go` (the documents of the matching
properties as records drawn from package-level generators), `hegel_sel_test.go` (the selector
records, their canonical and variant spellings, the model matcher and the specificity model),
`hegel_selectors_test.go` (the selectors of the matching properties as records), `hegel_oracle_test.go`
(the soupsieve child process), `hegel_match_test.go` (the classifier, the shared judge and the
two matching properties), `hegel_match_shapes_test.go` (the ten narrow matching properties),
`hegel_props_test.go` (the four other properties, still over the old draw-helper generators
until part 2 of the rewrite) and `hegel_pins_test.go` (fourteen pins). **Needs `python3` with
the `soupsieve` and `beautifulsoup4` packages on PATH**: soupsieve is the second implementation
the standard selectors are compared with. The whole run takes about fifteen seconds; the
library's own tests run in the same `go test`.

## Properties

| Test | Checks |
|---|---|
| `TestHegelSelectorsAgreeWithSoupsieve` | Standard selector lists (type, universal, id, class, every attribute operator with and without `i`, the pseudo-classes above, `:not`, `:has` with explicit combinators, all four combinators, escaped identifiers and strings) over generated documents (nested containers, form controls, links, options, comments, text, attributes chosen to exercise `:lang`, `:checked`, `:enabled`/`:disabled`) select the same nodes, in the same order, as soupsieve 2.9 over BeautifulSoup's parse of the same HTML and as the model; the model agrees with soupsieve. The cases carry the shapes of the matching bugs at the pools' natural rates (see below): mapped intermittent to its plurality basin. |
| `TestHegelSelectorsAgreeWithTheModel` | The full grammar, extensions included, selects the nodes a model of Selectors Level 4 and the HTML pseudo-class definitions says, over every node of the document (so a non-element node in a result is named); `QueryAll`, `Query`, `Selector.MatchAll`, `MatchFirst`, `Filter` and `Match` agree with the model. Mapped intermittent to its plurality basin. |
| `TestHegelSelectorsMatchOnlyElements` and nine more (`TestHegelOptionsInDisabledOptgroupsAreDisabled`, `TestHegelHasIsAnchoredAtTheSubject`, `TestHegelLinksAreNotEnabled`, `TestHegelBlankValuesMatchSubstrings`, `TestHegelLangIsCaseInsensitive`, `TestHegelLangUsesTheNearestAttribute`, `TestHegelEmptyKeepsNonBreakingSpace`, `TestHegelHTMLAttributeValuesAreCaseInsensitive`, `TestHegelNestedFieldsetsAreDisabled`) | One narrow property per matching bug: a drawn document with the bug's ingredient forced at one point (a cased `lang`, a `lang` under a `lang`, a text of Unicode white space, a disabled optgroup, a fieldset inside a disabled one, a link with `href`, a white-space-only value, a cased `type`/`dir`, an element whose first kid is text, a `:has` subject inside the element its argument names) and a selector drawn from the document to reach it, judged like the wide properties; each fails every run while its bug is open and, under `HEGEL_NO_KNOWN=1`, draws the region next to the shape and passes. |
| `TestHegelSerializationRoundTrips` | `ParseGroup(s).String()` parses again to a selector list with the same matches and specificities, and `String()` is idempotent. |
| `TestHegelParserIgnoresSpelling` | The same selector written with other whitespace, `/* comments */`, upper-case names, single or double quotes, bare or quoted attribute values, hex and literal escapes, `odd`/`even`/`n`/`-n` spellings parses to the same selector (same `String()`, same matches). |
| `TestHegelSpecificityFollowsTheSpec` | `Specificity()` of each selector equals the specification's count (ids; classes, attributes and pseudo-classes; types; the most specific argument for `:not`/`:has`). |
| `TestHegelPseudoElements` | A trailing `::pseudo-element` is refused by `Parse`/`ParseGroup`, accepted by the `WithPseudoElement(s)` parsers, reported by `PseudoElement()`, adds (0,0,1) to the specificity, changes no match, and survives `String()`. |
| `TestHegelPin...` | One plain test per recorded bug. |

## Bugs

Fourteen, see `bugs.toml`: `:lang`, `:contains` and `:matches` match text, comment and document
nodes, which `QueryAll`, `:has` and `~` then see (1); `String()` does not escape quotes and
backslashes in attribute values (2) nor a leading digit of a class name (3); `:hover` and the
other never-matching pseudo-classes have specificity 0 (4); an option in a disabled optgroup is
`:enabled`, and an option inside a disabled fieldset is `:disabled` (5); `:has()` is not anchored
at its subject, so `span:has(div b)` matches a span inside the div (6); `:enabled` matches links
(7); `^=`, `$=` and `*=` never match a white-space-only value (8); `:lang` is case-sensitive (9)
and looks past an element's own `lang` to its ancestors (10); `:empty` ignores a non-breaking
space (11); `[type=checkbox]` misses `type="CHECKBOX"` although HTML defines these attributes as
case-insensitive (12); `\0` gives U+0000 rather than U+FFFD (13); a fieldset inside a disabled
fieldset is `:enabled` (14).

## Drawn shapes

The matching properties draw the shapes of the ten matching bugs (1, 5-12, 14) by default and
judge them against the documented behaviour: the model takes the set of switches it follows as
a value (`known`, all off by default), and with a switch on it is a replica of the library's
rule for that bug (`:lang` compared raw and climbing past the element's own attribute, `:empty`
trimming Unicode white space, the fieldset ancestry applied to options and not to fieldsets, the
`:has` argument unbound, the text pseudo-classes tested on every node, ...). The shape of a case
is named before the library is called, from the records alone: the case departs from the
documentation where the model with every switch on differs from the model with none, and the
bug is the first in bug order whose switch alone reproduces the departure (else the first whose
switch is necessary to it; the counters `shape via sufficiency`/`necessity`, `shape hole` and
`replica agreement` are in the collector's output under `HEGEL_COLLECT=1`). The documents and
selectors are drawn at the nominal rates of the pools and tables (the weights beside each choice
carry the measured realised rate, since the engine favours a choice's first alternative); the
shapes meet at the rates the pools give them, and the two wide properties are mapped to the
plurality basin of forty rounds at a hundred cases (the soupsieve property fails 12 of forty:
bugs 9 and 7 three each, 1 and 8 two, 5 and 6 one, the tie broken by the thirty-round figure to
7; the model property 24 of forty: bug 1 nineteen, 12 two, 7, 8 and 9 one). Under `HEGEL_NO_KNOWN=1` the shapes are not
drawn: `lang` values are lower-cased and never nested, no Unicode-space text, no disabled
optgroup, no fieldset inside a disabled one, `:has` arguments a single compound, a compound of
`:lang` and the text pseudo-classes alone takes a type, no blank operand with the substring
operators, the `i` flag on the HTML case-insensitive attributes, `:disabled` for `:enabled` when
the document has a link; a case that has a shape even so is filtered (counted `filtered shaped`,
about 0.2 % at three thousand cases).

## Notes

- The generated documents avoid every HTML parsing rule that could make `x/net/html` and
  Python's `html.parser` disagree (no `p`, `li`, `table`, nested `a` or `button`, options only
  inside optgroups, no entities beyond `&quot;`, no duplicate attributes); the property compares
  the two parsers' element sequences before comparing matches.
- soupsieve is asked with the `html` element detached from its BeautifulSoup document: the
  document object otherwise behaves as an element for the ancestor combinators (`* > html`
  selects `html`). BeautifulSoup parses `class` as a list and soupsieve matches its
  single-space join, so only `~=` and presence are compared on `class`; hidden inputs are not
  generated (soupsieve excludes them from `:enabled`, HTML does not). Cascadia's `:contains` is
  case-insensitive and soupsieve's is not, so the extensions are checked against the model only.
- Three soupsieve choices on which the model is not compared with it (the library is compared
  with both as usual): soupsieve folds the case of `type` alone among the HTML case-insensitive
  attributes (the model follows HTML's list, so the shape of bug 12 on `dir` or `lang` is found
  by the model comparison); it climbs past `lang=""` to an ancestor's language (HTML makes the
  language unknown); and it matches `:lang` by RFC 4647 extended filtering as Selectors Level 4
  asks (`:lang(en-us)` matches `lang="en-Latn-US"`), where cascadia and the model use the Level 3
  prefix rule, which cascadia's documentation does not go beyond.
- Not judged: cascadia accepts `#1a` (an id beginning with a digit, which soupsieve rejects) and
  does not support `:is()`, `:where()`, `:nth-child(An+B of S)` or the `s` attribute flag, which
  the generator therefore never writes; `String()` normalises `:nth-child(odd)` to `2n+1` and
  `:first-child` spellings, which the round-trip property accepts.

## History

- 2026-10-10, part 1 of the rewrite: the switches a `known` value off by default with replica
  rules under them, the documents and selectors of the matching properties records drawn from
  package-level generators at the nominal rates, the classifier, the two matching properties
  drawing the ten matching shapes, ten narrow properties; the notes of bugs 5, 6 and 10
  corrected and bug 5's fieldset instance pinned. Part 2 (the serialisation, spelling,
  specificity and pseudo-element properties with the shapes of bugs 2, 3, 4 and 13, the old
  generators removed) follows.
