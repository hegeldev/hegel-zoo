# typescript/tough-cookie — salesforce/tough-cookie (against a model of RFC 6265)

`tough-cookie` is the cookie jar of the Node ecosystem (~95M weekly downloads: `jsdom`,
`axios-cookiejar-support`, the old `request`): `Cookie.parse` reads a `Set-Cookie` header,
`Cookie#toString` writes one, `toJSON`/`fromJSON` serialize, and `CookieJar` implements the
storage model (`setCookie`) and the retrieval algorithm (`getCookies`, `getCookieString`) over a
`Store`, with public-suffix rejection, SameSite and the `__Secure-`/`__Host-` prefixes. The
README calls it "RFC 6265 Cookies and CookieJar for Node.js". The patch checks it against a
model of RFC 6265 written from the text — parsing (§5.2), cookie dates (§5.1.1), domain and path
matching (§5.1.3, §5.1.4), storage (§5.3) and retrieval (§5.4), with rfc6265bis's SameSite and
prefixes — on scenarios of headers and requests under a stopped clock, and pins 17 bugs.

## How it is built

`lib/` is TypeScript (ESM specifiers, one runtime dependency: `tldts` for the public suffix
list); upstream builds with tsup. The setup installs Hegel, TypeScript, Node's types and tldts
under `.hegel/` (`npm install --prefix .hegel`, so the target's package.json and lock file stay
untouched) and compiles `lib/` to `.hegel/dist` with `hegel/tsconfig.json` (ES2020 modules,
upstream's strict options). Node 22.

## How it is tested

`hegel/hegel.test.mjs` runs under `node --test`; `hegel/hegel-zoo.mjs` is the zoo's shared
harness, `hegel/model.mjs` the RFC 6265 model (`parseSetCookie`, `parseCookieDate`,
`domainMatch`, `defaultPath`, `pathMatch`, `canonicalHost` via `url.domainToASCII`,
`isPublicSuffix` via tldts, and `ModelJar` with `set(header, url, now)` / `get(url, now)`),
`hegel/gen.mjs` the generators (hosts around a few sites — `example.com`, `foo.co.uk`,
`bar.github.io`, `localhost`, IDN, IPs, public suffixes, trailing dots —, URLs over http/https
with shared paths, Set-Cookie headers with Domain attributes drawn from the host's suffixes,
Path, Max-Age, Expires rendered from the clock, Secure, HttpOnly, SameSite and unknown
attributes in random order and case, syntax-varied Set-Cookie strings, cookie-date strings from
shuffled tokens, host-like strings) and `known(ops, model)`, which names the recorded bugs
whose shapes a scenario contains.

The jar runs under a stopped clock: `Date` is replaced by a subclass whose `now()` and no-argument
constructor return the scenario's time while a tough-cookie call runs, and `setCookie` gets the
same instant as `now`. Two shape spaces: `CLEAN` leaves out every shape a recorded bug is about
and the jar must agree with the RFC outright (one shape the generator cannot avoid — a Max-Age
cookie read before its expiry and asked for after it, bug 1 — is skipped); `FULL` has them all,
and a mismatch there must be explained by a recorded bug's shape.

| Property | What it checks |
|---|---|
| `TestHegelJarFollowsRfc6265` | on `CLEAN` scenarios, every `setCookieSync` is stored or ignored as the model stores or ignores it, and every `getCookieStringSync` equals the model's Cookie header (membership and order); then `CookieJar.fromJSON(JSON.stringify(jar.toJSON()))` gives the same headers |
| `TestHegelJarFollowsRfc6265Everywhere` | the same on `FULL`; a mismatch must carry a recorded bug's shape |
| `TestHegelParseFollowsRfc6265` | `Cookie.parse` of a syntax-varied Set-Cookie string equals the model's §5.2 result (key, value, expires, max-age, domain, path, secure, httponly, samesite, extensions) or both ignore it |
| `TestHegelParseDateFollowsRfc6265` | `parseDate` equals the model's §5.1.1 algorithm on shuffled date tokens with junk and odd delimiters |
| `TestHegelToStringAndJsonRoundTrip` | `Cookie.parse(c.toString())` and `Cookie.fromJSON(JSON.stringify(c))` reproduce a parsed cookie |
| `TestHegelMatchingFollowsRfc6265` | `domainMatch(host, domain, false)`, `pathMatch` and `defaultPath` equal the model's §5.1.3/§5.1.4 on host-like strings and paths |
| `TestHegelCanonicalDomainIsIdnaToAscii` | `canonicalDomain` never throws and, for host names, equals `url.domainToASCII` (lower case, A-labels) |

`TestHegelPin…` are plain tests, one per bug in `bugs.toml`.

Accepted differences, not recorded: tough-cookie refuses control characters in a cookie's name
or value and truncates the name-value pair at CR, LF and NUL (Chromium's behaviour; RFC 6265
has no rule, so the model skips such strings); empty cookie-avs (`;;`) are skipped by both;
unknown attributes are kept as `extensions` (the RFC ignores them); `localhost` and the other
special-use names are registrable domains (tough-cookie's `allowSpecialUseDomain` default) and
Secure cookies go to loopback and `localhost` over http (`allowSecureOnLocal`); Secure cookies
set over http are stored (RFC 6265 does, rfc6265bis does not); IPv4 hosts in forms the URL
parser normalizes (`0x7f.1`) are left out of the canonicalization property.

## Bugs

See `bugs.toml`. Three with teeth: **a Max-Age cookie's expiry slides forward with every read**
(`expiryTime()` is computed from `lastAccessed`, which `getCookies` updates), so a cookie that
is used regularly never expires (1, medium); **a Domain attribute with an IDN label is accepted
and the cookie is never sent** — the domain-match check uses the canonicalized form but the
cookie is stored with the raw one, which never matches the canonical request host (2, medium;
the same for `Domain=[::1]`); **`toString()` drops `SameSite=None`**, turning a cross-site
cookie into a default (Lax) one when re-emitted (11, medium).

Storage and retrieval: the request path is percent-decoded before path matching, so an explicit
`Path=/caf%C3%A9` never matches (3); `Domain=1.2.3.4` from that address is rejected as a
public suffix while IPv6 is accepted (4); a Domain attribute that is a public suffix identical
to the host rejects the cookie instead of making it host-only, RFC 6265 §5.3 step 5 (5);
cookies set from a host with a trailing dot are stored and never sent back (6); `Domain=localhost`
is accepted as registrable and then treated as a public suffix at lookup, so `www.localhost`
never receives it (17); the `__Secure-`/`__Host-` prefix checks are case-sensitive (16).
`Cookie`: `canonicalDomain` runs a non-ASCII name through `new URL()`, so `é@evil.com`
canonicalizes to `evil.com` and some names throw TypeError (7); `maxAge = 'Infinity'` gives an
expiry of -Infinity and the jar drops the cookie while `TTL()` says Infinity (8); `validate()`
throws for special-use domains (9), rejects the grammar's empty and quoted values and accepts
paths with CTLs through an unanchored regex (10); `toString()` writes `Max-Age=1e+21`,
`Max-Age=-Infinity`, out-of-range years and re-dotted domains that `parse` cannot read back
(12); `fromJSON` accepts an unparseable date and the cookie's own `toJSON` then throws (13);
`parse` trims Unicode whitespace where the RFC removes SP and HTAB (14); `parseDate` rejects a
non-digit above U+00FF after a token (15).

## History

- 2026-09-20: created against 0f7ed24 (6.0.2); 17 bugs.
