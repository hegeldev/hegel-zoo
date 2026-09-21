# go/publicsuffix-go

[weppos/publicsuffix-go](https://github.com/weppos/publicsuffix-go) (v0.50.3 plus 44 commits,
Public Suffix List 645b36): a domain name parser on the Public Suffix List, with a list parser
(`List.LoadString`), the lookup algorithm (`List.Find`, `Rule.Match`, `Rule.Decompose`), the
`Parse`/`Domain` decomposition into TLD/SLD/TRD, a `net/http/cookiejar` list (`CookieJarList`)
and a drop-in adapter for `golang.org/x/net/publicsuffix` (`net/publicsuffix`). Tested here:
lists parsed from generated list text and looked up with generated names, the packaged list
through every lookup API, and cookie jars built on `CookieJarList`.

## Build

The patch adds `hegel.dev/go/hegel` to `go.mod` and a `hegel/` package of four
`hegel_zoo_*_test.go` files that drive the public API. `go test -count=1 -run TestHegel -v ./hegel`

## Oracles

- A model of the list format and algorithm as https://publicsuffix.org/list/ documents them:
  one rule per line read up to the first whitespace, blank lines and `//` comments skipped,
  rules after `===BEGIN PRIVATE DOMAINS===` private (or the parse stopped there without
  `PrivateDomains`), U-labels converted to A-labels (`golang.org/x/net/idna`, as the package
  does); a name matches a rule label by label from the right, a wildcard needs one more label,
  an exception rule prevails, then the rule with the most labels, then the default rule; the
  public suffix is the rule's labels (one more for a wildcard, one fewer for an exception),
  a name with no more labels than its suffix is a suffix, the registrable domain is the suffix
  plus one label. Names are lowercased, blank names and a leading dot rejected, as the package
  documents. For a cookie jar, the public suffix of a name that is a suffix is the name.
- The packaged list itself (`DefaultRules()`), read into the model, for `Parse`, `Domain`,
  `DefaultList.Find`, `CookieJarList` and the `net/publicsuffix` adapter.
- `net/http/cookiejar`: a jar with `CookieJarList` and a jar with the model as its
  `PublicSuffixList` must return the same cookies.

## Properties

- `TestHegelList`: list text of 1-8 lines (normal, wildcard and exception rules over a small
  label alphabet with a few U-labels, repeated values, `*` lines, comments, blank lines, the
  private marker, leading/trailing whitespace, trailing text, CRLF, no final line break) with
  `ParserOption` drawn, loaded with `LoadString` (error, rules returned, `Size`); then 1-4
  names built from the rule values (extra labels, a suffix of a suffix, upper case, leading
  or trailing dot, an empty label, the empty string) with `FindOptions` drawn (nil,
  `IgnorePrivate`, a nil or own `*` `DefaultRule`): `Find`, `Decompose` of the rule found,
  `ParseFromListWithOptions` (error class or every field), `DomainName.String`,
  `DomainFromListWithOptions`, against the model.
- `TestHegelDefaultList`: names around a rule of the packaged list (the 296 wildcard and
  exception rules picked often): `Parse`, `Domain`, `DefaultList.Find`,
  `CookieJarList.PublicSuffix`, `net/publicsuffix.PublicSuffix` and `EffectiveTLDPlusOne`.
- `TestHegelCookieJar`: a host of 1-3 labels above a public suffix of the packaged list, 1-3
  cookies whose `Domain` is a suffix of the host at a label boundary (with or without a leading
  dot) or absent, set on two jars; `Cookies` for the host, a child and every parent must agree.
- `TestHegelPin…`: one pin per recorded bug, asserting the documented behaviour (expected
  failures).

## Bugs

Ten, recorded in `bugs.toml`: `CookieJarList.PublicSuffix` returns `""` for a public suffix, so
a jar accepts a `Domain=co.uk` cookie from `foo.co.uk` (publicsuffix-go/1); the `net/publicsuffix`
adapter returns `""` where x/net returns the suffix (2); rule lines are read whole, not up to
the first whitespace (3); rules with the same value overwrite each other (4); a longer normal
rule beats an exception rule (5); a `DefaultRule` other than the package's decomposes wrongly
(6); `NewRule("")` panics and `* b` is the wildcard `*.b` (7); `DefaultRule.Length` is 2 (8);
`NewRuleUnicode` reads an exception with a Unicode first label as a normal rule (9); a name
with an empty label is accepted and its `String` drops the TRD (10).

## Modelled as recorded

All ten are in the model behind `HZKnown` switches (`suffixPublicSuffixEmpty` for 1 and 2,
`wholeLineIsRule`, `sameValueOverwrites`, `longestBeatsException`, `foreignStarMisdecomposes`,
`starTakesTwoBytes`, `emptyValueHasOneLabel`, `unicodeExceptionPrefixEncoded`,
`emptySLDDropsTRD`); `ZOO_KNOWN_OFF=name` turns a switch off and the property then fails. The
panic of 7, the normal default rule of 6 and the acceptance of 10 are pinned only.

Design notes the model follows (undocumented, taken from the code):

- `Find`, `CookieJarList.PublicSuffix` and the adapter take the name as given (no lowercasing);
  `Parse` lowercases with `strings.ToLower` and does not convert U-labels (the README says
  Unicode names may misbehave), so a U-label name never matches a rule.
- A trailing dot leaves an empty last label that matches no rule; the default rule then makes
  the name "a suffix" (an error). A wildcard's label may be empty (`a..ck` under `*.ck`).
- The private marker is recognised anywhere in a line (`strings.Contains`), comments included;
  the load stops there without `PrivateDomains`. A load error leaves the rules read so far.
- With `ASCIIEncoded` the rule text is taken as is (upper case and U-labels kept).
- A `*` line loaded from a list is keyed under `""` and reached only through a trailing dot.

## Not tested

`LoadFile`/`Load` (thin over `LoadString`), the `cmd/` tools, `ToUnicode`, x/net's own list
(a different list version), the packaged list against the official PSL test file (the
package's `TestPsl` does that).

## History

- 2026-09-21: new target, three properties, 10 bugs.
