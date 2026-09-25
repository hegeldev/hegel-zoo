# fasthttp

[valyala/fasthttp](https://github.com/valyala/fasthttp), the fast HTTP/1.x implementation, against
Go's standard library: generated requests, responses, Set-Cookie headers, query strings and URIs
must be read by fasthttp as `net/http` and `net/url` read them; what fasthttp writes, `net/http`
must read as written.

## What is tested

**`hegel/hegel_http_test.go`**
- `TestHegelRequestReadMatchesNetHTTP`: an HTTP/1.1 or 1.0 request (methods GET to M-SEARCH and
  lower case; origin, absolute and asterisk form targets with escapes, queries and fragments; Host
  first or last, mixed case, ports, IPv6; zero to six headers from a list of 26 with mixed-case
  keys, values with commas, quotes, tabs, double spaces, obs-text bytes, 300 characters, written
  `key:value`, `key:   value  ` or over an obs-fold continuation line, and repeated; a Connection
  header with close/keep-alive/other tokens in any case, sometimes twice; a Cookie header with one
  to three cookies, quoted or not, `;` with or without a space; a body with no framing,
  Content-Length or chunked in one to many chunks with extensions, upper-case sizes and trailers
  announced or not) read by `fasthttp.Request.Read` and `http.ReadRequest` gives the same method,
  target, version, host, close flag, headers, body, cookies and trailers, or both reject it.
- `TestHegelResponseReadMatchesNetHTTP`: a response (status 200 to 599 with the standard, an odd or
  no reason phrase; headers as above; zero to three Set-Cookie headers; Connection; body framings
  as above, none for 204 and 304) read by `fasthttp.Response.Read` and `http.ReadResponse` gives
  the same status, close flag, headers, body, trailers and Set-Cookie cookies (each parsed with
  `fasthttp.Cookie.ParseBytes` and compared field by field with `Response.Cookies`).

**`hegel/hegel_cookie_test.go`**
- `TestHegelSetCookieMatchesNetHTTP`: a Set-Cookie header (name, value plain or quoted, Path,
  Domain, Max-Age from a list of numeric and odd texts, Expires in http.TimeFormat, the legacy
  dashed form or RFC 1123 with a UTC zone, Secure/HttpOnly/Partitioned bare or with a value,
  SameSite with known, odd, empty or no value, an unknown attribute, lower-case attribute names,
  `;` without spaces) parsed by `fasthttp.Cookie.Parse` gives net/http's cookie, or both drop it.
- `TestHegelCookieWrittenReadByNetHTTP`: a `fasthttp.Cookie` built from fields (`SetPath`
  normalises the path, `SetSameSite(None)` and `SetPartitioned` set Secure and Path, by their
  documentation) is read back by net/http from `Cookie.String()` with those fields.
- `TestHegelNetHTTPCookieReadByFasthttp`: an `http.Cookie` written with `String()` is read by
  `fasthttp.Cookie.Parse` with the fields net/http itself reads back.

**`hegel/hegel_write_test.go`**
- `TestHegelRequestWrittenReadByNetHTTP`: a `fasthttp.Request` with method, URI, headers, cookies
  and body, written with `WriteTo`, is read by `http.ReadRequest` with fasthttp's own `RequestURI`
  and `Host` and the headers, cookies and body as set.
- `TestHegelResponseWrittenReadByNetHTTP`: a `fasthttp.Response` with status, headers, cookies
  (`SetCookie` replaces a cookie of the same name) and body, written with `WriteTo`, is read by
  `http.ReadResponse` as set (Date excluded: `Response.Write` sets it itself).

**`hegel/hegel_uri_test.go`**
- `TestHegelArgsMatchParseQuery`: a query string (keys and values with escapes, `+`, `=`, empty
  pairs, keys without value, leading and trailing `&`) that `url.ParseQuery` accepts gives the same
  keys and values in `fasthttp.Args`; `Args.String()` parses back the same in net/url;
  `url.Values.Encode()` parses the same in fasthttp; `Has` and `Peek` agree.
- `TestHegelQuotedArgMatchesQueryEscape`: `AppendQuotedArg` is `url.QueryEscape` and
  `AppendUnquotedArg` is `url.QueryUnescape`, for any bytes.
- `TestHegelURIMatchesNetURL`: an absolute URI (schemes in any case, userinfo, hosts with ports,
  IPv6 and zones, up to four path segments from a list of escaped, reserved, non-ASCII, dot and
  `%2F` segments, a query, a fragment) parsed by `fasthttp.URI.Parse` and `url.Parse` gives the
  same scheme, host (lower-cased), user, path (as written, and decoded when there is nothing to
  normalise), query and fragment; `FullURI` re-parsed by net/url means the same; `RequestURI` is
  a request-target with the same path and query.

**`hegel/hegel_conv_test.go`**: `AppendHTTPDate`/`ParseHTTPDate` against `http.TimeFormat` and
`http.ParseTime` (case and zone variations), `ParseUint`/`AppendUint` against strconv (digits
only, int range), `ParseIPv4`/`AppendIPv4` against `netip.ParseAddr`, `AppendHTMLEscape` against
`html.UnescapeString`.

**`hegel/hegel_pins_test.go`**: one deterministic reproducer per recorded bug.

## Oracles and normalisations

Go's `net/http` (ReadRequest, ReadResponse, Cookies), `net/url`, `net/netip`, `strconv` and `html`.
Both parsers' readings are put in one shape: headers as canonical key to values (Host,
Content-Length, Transfer-Encoding, Trailer, Connection, Cookie and Set-Cookie compared through
fields of their own), trailers by the generated keys (fasthttp appends them to the headers,
net/http keeps them in `Trailer`), hosts lower-cased (fasthttp lower-cases), the status line
without a trailing space when there is no reason phrase. Not generated, because the libraries
differ by design: LF-only line ends (fasthttp needs CRLF); repeated Content-Type, User-Agent,
Server or Content-Encoding (fasthttp keeps the last, as single-valued fields) and empty values
for them (unset to fasthttp; a response without Content-Type reports fasthttp's default
text/plain, which is dropped from the comparison); Transfer-Encoding on HTTP/1.0 (fasthttp
rejects, net/http ignores it); Expect: 100-continue (fasthttp leaves the body to the caller);
trailer keys fasthttp forbids for safety (Host, X-Forwarded-*, ...); cookies whose names or
values are not cookie-octets (net/http drops them, fasthttp keeps them), a space after `=` in a
Cookie header (fasthttp trims), cookies without `=`, a Path with `"` (net/http drops the
attribute, fasthttp keeps it); `;` in query strings and `%` that starts no escape (net/url
rejects, fasthttp keeps the byte); `=` alone as a query pair; `+` with a sign in ParseUint;
`FullURI` has no userinfo (its documented form is scheme://host/request-uri#hash); fasthttp
normalises paths (dot segments, duplicate slashes, `%2F`), so `Path()` is compared only for
paths with none of those; RFC 850 and asctime dates (ParseHTTPDate reads RFC 1123 only).

## Known bugs

Seven bugs (`bugs.toml`): a negative Max-Age rejects the cookie; an unparsable Max-Age or Expires
(or an RFC 1123 date with a non-GMT zone) drops the cookie instead of the attribute; the Connection
close token is matched only as the whole value `close`; ParseIPv4 accepts leading zeros; SameSite
with an unknown or empty value is read as absent; FullURI writes an IPv6 zone identifier
unescaped; Secure/HttpOnly/Partitioned with a value are not recognised. The properties draw
these shapes and are the expected failures mapped to the bugs (STYLE.md rule 11): one narrow
property per bug in `hegel/hegel_shapes_test.go` draws only the bug's shape and fails every run
(`NegativeMaxAgeKeepsTheCookie` /1, `UnparsableAttributeKeepsTheCookie` /2,
`CloseTokenAnywhereInConnectionCloses` /3, `LeadingZeroOctetsAreRejected` /4,
`UnknownSameSiteValueIsDefault` /5, `ZoneIdentifierStaysEscapedInFullURI` /6,
`FlagAttributesWithValuesAreSet` /7); the wide properties reach them at their natural rates
(`SetCookieMatchesNetHTTP` lands on /1, `ResponseReadMatchesNetHTTP` on /3,
`RequestReadMatchesNetHTTP` on /3 in most runs, `ParseIPv4MatchesNetip` on /4,
`URIMatchesNetURL` on /6). `HEGEL_NO_KNOWN=1`, read once, switches the known shapes off:
the pools lose their bug-shaped values, the narrow properties are skipped and every property
passes. The pins in `hegel_pins_test.go` stay as regression examples. One tolerance of the
narrow properties: net/http ignores a `Max-Age` with a leading zero (RFC 6265 4.1.1 grammar)
where fasthttp reads it (the 5.2.2 algorithm), so the narrow Max-Age digits have no leading
zero; the wide pool's `00` agrees on both sides.

## Not tested

The server and client (connections, timeouts, pipelining, streaming bodies, compression), the
`fasthttpadaptor`, `fasthttputil`, `fasthttpproxy`, `fs` and `expvarhandler` packages, multipart
forms, `Args` numeric getters, `URI.Update`, header parameter parsing (`VisitHeaderParams`),
`ParseUfloat`, HTTP/1.0 keep-alive semantics beyond the close flag, `DisableNormalizing` and
`DisableSpecialHeader` modes.

## History

- 2026-09-20: written against 0e13c85e8ed5b41b489c502eeccdf90a45eb8dfe (2026-09-19, after
  v1.69.0) with hegel.dev/go/hegel v0.6.33; 7 bugs.
- 2026-09-20: base bumped 0e13c85e8ed5 → 5687435d22d1 (2026-09-20, "fix: request time left at zero, and an opt in Server.LazyRequestTime (#2404)"; v1.74.0+); 7 bug(s) still reproduce. 14 tests pass.
- 2026-09-25: generators rewritten in combinator style (STYLE.md) and unsteered: the
  properties draw the recorded bugs' shapes and are mapped to them, `known.go` is gone, seven
  narrow properties added; `HEGEL_NO_KNOWN=1` now means "known shapes off" (until today it
  lifted the gates instead).
