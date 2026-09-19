# cascadia

[andybalholm/cascadia](https://github.com/andybalholm/cascadia) (BSD-2-Clause), pinned at
`154416a` (v1.3.5 plus three commits, 2026-09-15): the Go CSS selector engine over
`golang.org/x/net/html` trees, used by goquery and many scrapers - Selectors Level 3 and 4
(attribute operators with the `i` flag, `:not`, `:has` with relative selectors, the `nth-*`
family, `:empty`, `:root`, `:link`, `:lang`, `:enabled`, `:disabled`, `:checked`) plus its own
extensions (`:contains`, `:containsOwn`, `:matches`, `:matchesOwn` on regular expressions,
`:haschild`, `:input`, `[attr!=val]`, `[attr#=regexp]`), pseudo-elements, specificity and
serialisation.

The patch adds the `hegel.dev/go/hegel` requirement to `go.mod` and six test files (package
`cascadia_test`): `hegel_test.go` (plumbing, the `Known` gates), `hegel_doc_test.go` (generated
HTML documents), `hegel_sel_test.go` (selector ASTs, their canonical and variant spellings, the
model matcher and the specificity model), `hegel_oracle_test.go` (the soupsieve child process),
`hegel_props_test.go` (the six properties) and `hegel_pins_test.go` (fourteen pins). **Needs
`python3` with the `soupsieve` and `beautifulsoup4` packages on PATH**: soupsieve is the second
implementation the standard selectors are compared with. The whole run takes about a second;
the library's own tests run in the same `go test`.

## Properties

| Test | Checks |
|---|---|
| `TestHegelSelectorsAgreeWithSoupsieve` | Standard selector lists (type, universal, id, class, every attribute operator with and without `i`, the pseudo-classes above, `:not`, `:has` with explicit combinators, all four combinators, escaped identifiers and strings) over generated documents (nested containers, form controls, links, options, comments, text, attributes chosen to exercise `:lang`, `:checked`, `:enabled`/`:disabled`) select the same elements, in the same order, as soupsieve 2.9 over BeautifulSoup's parse of the same HTML. |
| `TestHegelSelectorsAgreeWithTheModel` | The full grammar, extensions included, selects the elements a model of Selectors Level 4 and the HTML pseudo-class definitions says; `QueryAll`, `Query`, `Selector.MatchAll`, `MatchFirst`, `Filter` and `Match` agree with each other and non-element nodes never match. |
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
`:enabled` (5); `:has()` is not anchored at its subject, so `span:has(div b)` matches a span
inside the div (6); `:enabled` matches links (7); `^=`, `$=` and `*=` never match a
white-space-only value (8); `:lang` is case-sensitive (9) and looks past an element's own `lang`
to its ancestors (10); `:empty` ignores a non-breaking space (11); `[type=checkbox]` misses
`type="CHECKBOX"` although HTML defines these attributes as case-insensitive (12); `\0` gives
U+0000 rather than U+FFFD (13); a fieldset inside a disabled fieldset is `:enabled` (14).

## Notes

- The generated documents avoid every HTML parsing rule that could make `x/net/html` and
  Python's `html.parser` disagree (no `p`, `li`, `table`, nested `a` or `button`, options only
  inside optgroups, no entities beyond `&quot;`, no duplicate attributes); the property compares
  the two parsers' element sequences before comparing matches.
- soupsieve is asked with the `html` element detached from its BeautifulSoup document: the
  document object otherwise behaves as an element for the ancestor combinators (`* > html`
  selects `html`). BeautifulSoup parses `class` as a list and soupsieve matches its
  single-space join, so only `~=` and presence are compared on `class`; hidden inputs are not
  generated (soupsieve excludes them from `:enabled`, HTML does not); `:enabled` is left to the
  model while bug 7 is open. Cascadia's `:contains` is case-insensitive and soupsieve's is not,
  so the extensions are checked against the model only.
- Not judged: cascadia accepts `#1a` (an id beginning with a digit, which soupsieve rejects) and
  does not support `:is()`, `:where()`, `:nth-child(An+B of S)` or the `s` attribute flag, which
  the generator therefore never writes; `String()` normalises `:nth-child(odd)` to `2n+1` and
  `:first-child` spellings, which the round-trip property accepts.
