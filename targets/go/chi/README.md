# go/chi

Hegel property tests for [go-chi/chi](https://github.com/go-chi/chi), the net/http router: a
radix tree of static, `{param}`, `{param:regexp}` and `*` segments, sub-router mounting, and
the `middleware` package.

## Build

The patch adds a `hegel/` package; `go test -count=1 -run TestHegel -v ./hegel` needs nothing
beyond the module. A default run takes a few seconds (the zoo run about fifteen, most of it
the shrinking of the properties that reach a bug; under `HEGEL_NO_KNOWN=1` about four).

The properties are written to the repository's standard (STYLE.md rule 11): a `known` value
of seventeen switches, all off by default, one per recorded bug; each property's model
(`routeExpected` in `hegel_model_test.go`, `clientIPExpected`, `contentExpected`,
`compressExpected` and `headerRouteExpected` in `hegel_headers_test.go`, the Sunset model in
the shapes file) states the documented behaviour with every switch off and, with a switch
on, reproduces chi's rule for that bug as a replica of its code (`patNextSegment`'s
anchoring, `findRoute`'s empty-value fallback and regexp-only slash check, `tailSort`'s
single move, `routeHTTP`'s method map and its raw-path choice with net/url's `RawPath` rule,
`RoutePattern`'s trim, `Find`'s descent; `realIP`'s untrimmed cut, `AllowContentEncoding`'s
whole-field lookup, `contentEncoding`'s substring cuts, `matchAcceptEncoding`'s substring,
`isCompressible`'s cut at the semicolon, `HeaderRouter`'s case-sensitive pattern and its map
walk - whose value is the set of the headers' outcomes - and `Sunset`'s two formats); the
classifier runs the model per switch before the library is called and names the shape of
the bug a case is in, so the property fails naming it; under `HEGEL_NO_KNOWN=1` the shapes are
not drawn (the alternation regexp, the method BREW, the percent escapes, the trailing slash
of a route pattern, the second coding of a Content-Encoding field, the quoted charset and the
misleading parameter, the zero weights and `*`, the capitalised media types and header
patterns, the non-UTC zones) or are filtered out by the classifier (the routing property
about six percent of its cases: an empty regexp value, a slash in a regexp value, the bare
mount path, a sub-route with a trailing slash; the client-IP property its padded first
entries, the header-routing property its doubly routed requests), and the Deprecation check
of the Sunset property, whose every case is chi/15's shape, is dropped.

## Oracle

A model of the documented rules. For routing: chi.go's "URL patterns" (a placeholder matches
up to the next `/` or the end, a regexp placeholder matches the whole value and never a slash,
`*` takes the rest), the Mux and Context documentation (Mount registers `P`, `P/` and `P/*`;
the sub-router routes the rest of the path; URL parameters stack and are the decoded path
segments; 405 with Allow when the path is routed for other methods; 501 for a method the
router does not know, RFC 9110 9.1), and the tree's own precedence (static, then regexp, then
param, then catch-all; a placeholder followed by a suffix before one ending its segment). The
model is a byte trie built from the same route table; generated tables (one to six routes, a
mounted sub-router in 45 percent of them, a cluster of sibling regexp placeholders in 20,
CleanPath, StripSlashes or GetHead in 40) answer three generated requests each (paths spelled
from the patterns with values, empty values, extra slashes, percent escapes, mutations;
methods including HEAD, custom ones and an unknown one), and the router must agree on status,
handler, `r.Pattern`, the URL parameter list, the Allow set and `Find`. For the middleware:
the doc comments of `ClientIPFrom*` (right-to-left walk, trusted prefixes, fail-closed), of
`RealIP`, `AllowContentEncoding`, `ContentCharset`, `Compress` and `RouteHeaders`, and the RFC
9110 syntax they handle (`mime.ParseMediaType`, Accept-Encoding weights).

## Properties

- `TestHegelRoute`: route tables against the model; also `Mux.Find`. A quarter of the cases
  are in the shape of a recorded bug (per 3000 cases: chi/6 327, chi/8 197, chi/7 102, chi/3
  78, chi/1 20, chi/2 18, chi/9 14, chi/5 about one); over forty rounds at a hundred cases
  it shrinks to chi/6 (34 rounds; chi/8 5, chi/3 1), so it is mapped to chi/6.
- `TestHegelClientIP`: `ClientIPFromXFF`, `ClientIPFromXFFTrustedProxies`,
  `ClientIPFromHeader`, `ClientIPFromRemoteAddr`, `RealIP`; chi/16's padded first entry in
  nine percent of the cases; over forty rounds at a hundred cases it shrinks to chi/16 every time.
- `TestHegelContentChecks`: `AllowContentEncoding`, `ContentCharset`; chi/10 in 1.4 percent
  of the cases, chi/11 in 2.2; over forty rounds at a hundred cases it fails 36 to 38 times, shrinking to chi/11
  and chi/10 by turns (26 to 12 in one run of forty, 17 to 19 in another; chi/11 ahead in
  both runs of thirty at twenty cases), so it is mapped to chi/11 as intermittent.
- `TestHegelCompress`: `Compress`, encoding choice, compressibility, the body decodes, Vary;
  chi/12 in eleven percent of the cases, chi/13 in thirteen; over forty rounds it shrinks to chi/13 every time.
- `TestHegelRouteHeaders`: `RouteHeaders` with `Route`, `RouteAny`, `RouteDefault`; chi/14 in
  nine percent of the cases, chi/4's doubly routed request in eight. Each request is served
  thirty times and the set of answers is the value, since chi answers the other header's
  route about one time in eight and a single serve would make the failure irreproducible
  (Hegel's replay of the shrunk case then passes and prints nothing); thirty serves see both
  answers in 98 percent of the shaped cases; over forty rounds it shrinks to chi/14 (35 rounds; chi/4 5).

One narrow property per bug, in `hegel_route_shapes_test.go` and
`hegel_headers_shapes_test.go`, draws the bug's shape with random surroundings and is judged
by the same model, so it fails every run naming its bug by default and passes under
`HEGEL_NO_KNOWN=1`, where it draws the region past the shape. The routing ones:
`TestHegelAlternationMatchesTheWholeValue` (chi/1), `TestHegelRegexpValuesStopAtTheSlash`
(2), `TestHegelEmptyValuesFollowTheRegexp` (3: two regexp routes at one level with different
sources, one accepting the empty string, in either order), `TestHegelSuffixedRegexpsComeFirst`
(5: three sibling regexps, two ending the segment, the suffixed one rejecting the empty
value), `TestHegelUnknownMethodsAreNotImplemented` (6), `TestHegelParamsAreDecoded` (7: a
non-canonical escape or an escaped slash in a value), `TestHegelPatternsKeepTheirTrailingSlash`
(8: a route or a sub-route registered with a trailing slash, served),
`TestHegelBareMountPathsMatchOnlyServedMethods` (9: a sub-router with no `/` route for the
method, and GetHead with a GET `/` alone). The middleware ones:
`TestHegelRealIPTrimsTheFirstEntry` (16), `TestHegelContentEncodingListsAreSplit` (10),
`TestHegelQuotedCharsetsAreRead` (11: the quoted spelling and the quoted misleading
parameter), `TestHegelAcceptEncodingWeightsAreHonoured` (12),
`TestHegelMediaTypesCompareCaseInsensitively` (13),
`TestHegelHeaderPatternsCompareCaseInsensitively` (14),
`TestHegelTwoRoutedHeadersTakeTheFirstRoute` (4: both headers sent and both routed, served
thirty times), `TestHegelSunsetAnnouncesTheDateInBothForms` (15: Sunset, Deprecation and Link
of a drawn time; every case is the shape, the Deprecation check is dropped under
`HEGEL_NO_KNOWN=1`) and `TestHegelSunsetDatesAreInGMT` (17: a time in a fixed zone other than
UTC, checking Sunset and Link alone).

## Bugs

Seventeen, in `bugs.toml`: a regexp placeholder with a top-level alternation is anchored per
alternative (1, medium); a regexp placeholder with a suffix matches across a slash (2, medium);
an empty regexp value is tried only on the last regexp node, unchecked, so the result depends
on the registration order (3, medium); `RouteHeaders` routes in Go map order when two routed
headers are present (4, medium); the precedence among sibling regexp placeholders depends on
the registration order (5); an unknown method is a 405 without Allow for every path (6); URL
parameters are decoded only when the path has no non-canonical escape (7); `r.Pattern` drops
a route's trailing slash, a mounted route's too (8); `Match`/`Find` accept the bare mount path
for every method, so `GetHead` does not fall back there (9); `AllowContentEncoding` reads a
comma list as one coding (10); `ContentCharset` rejects a quoted charset (11); `Compress`
ignores `q=0` and `*` (12) and compares the media type case-sensitively (13); `RouteHeaders`
never matches a pattern with a capital (14); `Deprecation` is an HTTP-date, not RFC 9745's
`@seconds` (15); `RealIP` does not trim the first X-Forwarded-For entry (16); `Sunset`
formats a time in another zone as its local wall clock labelled GMT (17, found by the Sunset
property drawing times in fixed zones). The routing property draws the shapes of 1, 2, 3, 5,
6, 7, 8 and 9, the middleware properties those of 4, 10, 11, 12, 13, 14 and 16, the Sunset
properties 15 and 17; the replicas agree with the library on every shaped case in 3000 (for
chi/4, the answer is in the set).

## Modelled as recorded, not counted

- A `{name}` placeholder in the middle of the path may be empty (`/users///c` binds x = "" and
  y = ""; TestMuxEmptyParams asserts it) but not at the end (`/users/` is a 404 for
  `/users/{id}`); the model does the same.
- A pattern registered twice replaces the earlier handler for its methods; `Handle` sets every
  known method; a route's Allow lists them all.
- Static, regexp, param and catch-all children are tried in that order with backtracking; a
  `405` is remembered from any leaf reached with the whole path and the search goes on.
- `Mount` panics on an existing `P/*`; the generator keeps mounts under a reserved prefix.
- `StripSlashes` routes the decoded path whenever it ends in a slash (an escaped slash at the
  end is stripped as a real one; chi/7's note).
- `URLFormat`, `RedirectSlashes`, `PathRewrite`, `Throttle`, `Timeout` and the logging
  middlewares are not exercised.
