# go/chi

Hegel property tests for [go-chi/chi](https://github.com/go-chi/chi), the net/http router: a
radix tree of static, `{param}`, `{param:regexp}` and `*` segments, sub-router mounting, and
the `middleware` package.

## Build

The patch adds a `hegel/` package; `go test -count=1 -run TestHegel -v ./hegel` needs nothing
beyond the module.

## Oracle

A model of the documented rules. For routing: chi.go's "URL patterns" (a placeholder matches
up to the next `/` or the end, a regexp placeholder matches the value and never a slash, `*`
takes the rest), the Mux and Context documentation (Mount registers `P`, `P/` and `P/*`; the
sub-router routes the rest of the path; URL parameters stack; 405 with Allow when the path is
routed for other methods), and the tree's own precedence (static, then regexp, then param,
then catch-all; a placeholder followed by a suffix before one ending its segment). The model is
a byte trie built from the same route table; generated tables (one to nine routes, a mounted
sub-router in half of them, CleanPath, StripSlashes or GetHead in some) answer generated
requests (paths spelled from the patterns with values, empty values, extra slashes, mutations;
methods including HEAD, custom ones and an unknown one), and the router must agree on status,
handler, `r.Pattern`, the URL parameter list, the Allow set and `Find`. For the middleware:
the doc comments of `ClientIPFrom*` (right-to-left walk, trusted prefixes, fail-closed), of
`RealIP`, `AllowContentEncoding`, `ContentCharset`, `Compress` and `RouteHeaders`, and the RFC
9110 syntax they handle (`mime.ParseMediaType`, Accept-Encoding weights).

## Properties

- `TestHegelRoute`: route tables against the model; also `Mux.Find`.
- `TestHegelClientIP`: `ClientIPFromXFF`, `ClientIPFromXFFTrustedProxies`,
  `ClientIPFromHeader`, `ClientIPFromRemoteAddr`, `RealIP`.
- `TestHegelContentChecks`: `AllowContentEncoding`, `ContentCharset`.
- `TestHegelCompress`: `Compress`, encoding choice, compressibility, the body decodes, Vary.
- `TestHegelRouteHeaders`: `RouteHeaders` with `Route`, `RouteAny`, `RouteDefault`.

## Bugs

Sixteen, in `bugs.toml`: a regexp placeholder with a top-level alternation is anchored per
alternative (1, medium); a regexp placeholder with a suffix matches across a slash (2, medium);
an empty regexp value is tried only on the last regexp node, unchecked, so the result depends
on the registration order (3, medium); `RouteHeaders` routes in Go map order when two routed
headers are present (4, medium); the precedence among sibling regexp placeholders depends on
the registration order (5); an unknown method is a 405 without Allow for every path (6); URL
parameters are decoded only when the path has no non-canonical escape (7); `r.Pattern` drops
a route's trailing slash (8); `Match`/`Find` accept the bare mount path for every method, so
`GetHead` does not fall back there (9); `AllowContentEncoding` reads a comma list as one coding
(10); `ContentCharset` rejects a quoted charset (11); `Compress` ignores `q=0` and `*` (12) and
compares the media type case-sensitively (13); `RouteHeaders` never matches a pattern with a
capital (14); `Deprecation` is an HTTP-date, not RFC 9745's `@seconds` (15); `RealIP` does not
trim the first X-Forwarded-For entry (16).

## Modelled as recorded, not counted

- A `{name}` placeholder in the middle of the path may be empty (`/users///c` binds x = "" and
  y = ""; TestMuxEmptyParams asserts it) but not at the end (`/users/` is a 404 for
  `/users/{id}`); the model does the same.
- A pattern registered twice replaces the earlier handler for its methods; `Handle` sets every
  known method; a route's Allow lists them all.
- Static, regexp, param and catch-all children are tried in that order with backtracking; a
  `405` is remembered from any leaf reached with the whole path and the search goes on.
- `Mount` panics on an existing `P/*`; the generator keeps mounts under a reserved prefix.
- `URLFormat`, `StripSlashes` (one slash), `RedirectSlashes`, `PathRewrite`, `Throttle`,
  `Timeout` and the logging middlewares are not exercised.
