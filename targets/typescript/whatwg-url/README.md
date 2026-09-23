# whatwg-url

[jsdom/whatwg-url](https://github.com/jsdom/whatwg-url) (npm `whatwg-url`, ~170M weekly
downloads; jsdom's implementation of the URL Standard): the `URL` and `URLSearchParams`
classes, the URL-record API (`parseURL`, `basicURLParse`, `serializeURL`, `serializePath`,
`serializeHost`, `serializeURLOrigin`, `serializeInteger`, `hasAnOpaquePath`,
`cannotHaveAUsernamePasswordPort`, `parseURLWithValidationErrors`, `isValidURLString`) and
`percentDecodeString`/`percentDecodeBytes`. Pinned at 17.1.1 (37df073c, 2026-09-10). The tests
are `test/hegel.test.mjs` with the zoo's harness `test/hegel-zoo.mjs`.

The public classes are generated from WebIDL by `webidl2js` (a devDependency) in upstream's
`prepare` script, which npm does not run for a named install, so the setup installs the dev
tree (about 60 MB, a few seconds) and runs `node scripts/transform.js` by hand; the tests then
import `index.js` as any user does.

## What is tested

The oracle is Node 22's native `URL`/`URLSearchParams` — Ada, a second full implementation of
the same standard in the same process — so every property is a differential on generated
input: schemes special, non-special and invalid; hosts as domains (ASCII, uppercase, trailing
dots, IDNA labels, ideographic full stops), IPv4 in every notation the standard accepts or
rejects (hex, octal, fewer than four parts, one huge number, trailing dot, out of range),
IPv6 (compressed, embedded IPv4, malformed), opaque hosts and forbidden code points; userinfo,
ports (leading zeros, 65536, non-digits), paths with dots and encoded dots, Windows drive
letters, backslashes, percent-escapes valid and not, tabs and newlines inside, C0 and space
around, queries and fragments of every hostile character, relative references of every form,
and bases valid, absent or invalid.

- **TestHegelParsingAgreesWithNodeUrl** — both sides must accept the same inputs (with and
  without a base) and give the same `href`, `protocol`, `username`, `password`, `host`,
  `hostname`, `port`, `pathname`, `search`, `hash` and `origin`; `URL.canParse` and
  `URL.parse` must agree with the constructor; the record API must agree with the class
  (`parseURL` fails iff the constructor throws, `serializeURL`/`serializePath`/
  `serializeHost`/`serializeURLOrigin`/`serializeInteger` give the getters' values,
  `hasAnOpaquePath` and `cannotHaveAUsernamePasswordPort` match the record); the serialization
  must be a fixed point for both implementations; `parseURLWithValidationErrors` must give the
  same URL as `parseURL`, and `isValidURLString` must be true exactly when it reports no
  validation errors.
- **TestHegelSettersAgreeWithNodeUrl** — from a URL both sides read alike, up to five random
  assignments to `href`, `protocol`, `username`, `password`, `host`, `hostname`, `port`,
  `pathname`, `search`, `hash` with component-shaped hostile values: both must throw or not
  alike and read alike after every step.
- **TestHegelSearchParamsAgreeWithNode** — `URLSearchParams` from a string (with or without
  `?`, `+`, malformed escapes, NUL, non-ASCII, lone surrogates), a list of pairs or a record,
  then random `append`/`set`/`delete`(1 and 2 arguments)/`has`/`get`/`getAll`/`sort`: the
  list, `size` and `toString()` must agree after every step; the params appended to a URL's
  `searchParams` must change `href` as Node's do, and `url.search = …` must reflect into the
  params alike.
- **TestHegelPercentDecodingFollowsTheSpec** — `percentDecodeBytes`/`percentDecodeString`
  against the standard's algorithm written out (`%` + two hex digits → the byte, anything else
  as is, on the UTF-8 bytes).

## Divergences

Where the two implementations disagree, the URL Standard's text decides; every disagreement
seen so far is on Node's side or in IDNA, so none is counted against whatwg-url. Each is
skipped with a `limit/…` or `idna/…` count and the shape is narrow enough not to hide a
whatwg-url bug of another kind:

- `limit/ada-caret-in-path` — the path percent-encode set includes U+005E `^` (whatwg/url,
  2024): whatwg-url writes `%5E`, Node leaves `^` (`http://h/a^b`).
- `limit/ada-double-dot-on-empty-path` — a `..` segment on an empty non-special path appends
  an empty segment in the path state: `foo://h/..` is `foo://h/` for whatwg-url and the spec,
  `foo://h` for Node.
- `limit/ada-relative-to-opaque-base` — the no-scheme state fails for a base with an opaque
  path unless the input *starts* with `#`; Node resolves any input that *contains* a `#`
  (`x#q`, `?q#q`, `w%4s:/g#q`) against `a+b:a/b` as if the path were hierarchical
  (`a+b:a/x#q`).
- `limit/ada-trailing-space-in-opaque-path` — a trailing space of an opaque path before `?` or
  `#` is percent-encoded in the opaque path state (`x-y.z:a ?q` → `x-y.z:a%20?q`); Node keeps
  the space.
- `limit/ada-file-drive-letter-prefix-kept` — shortening a `file:` URL's path spares only a
  *normalized* Windows drive letter (exactly `C:`): `file:///C:a/../|` is `file:///|` for
  whatwg-url and the spec; Node keeps `C:a` (`file:///C:a/|`).
- `limit/ada-empty-host-stays-null` — `hostname = ""` on a non-special URL without a host sets
  the empty host, which is non-null, so the serialization gains `//` (`c:/x` → `c:///x`, as
  the host state with a state override says); Node leaves the host null (`c:/x`).
- `limit/ada-host-setter-empty-before-colon` — `host = ":80"` (or `":"`, `"::1]"`) on a
  non-special URL: the host state meets `:` with an empty buffer, a host-missing failure, so
  the setter changes nothing (whatwg-url); Node sets the empty host and takes the port
  (`blob://!:80/` then `host = ":"` → `blob://:80/`). On special URLs both leave the URL alone.
- `limit/ada-pathname-setter-drops-query-and-fragment` — `pathname = "//"` on a URL without
  a host gets the `/.` prefix in the serialization (`x:/a?q#f` → `x:/.//?q#f`, path start
  state with a state override leaves query and fragment alone); Node ends with `x:/.//`, the
  query and fragment gone.
- `limit/ada-drops-port` — after `protocol = "foo"` whatwg-url keeps `:0` (not the scheme's
  default, which is null), Node drops it; `host = "h:00000000080"` on a non-special URL sets
  port 80 in whatwg-url and no port in Node (parsing the same URL, Node agrees with whatwg-url).
- `limit/ada-file-normalizations-by-later-setter` — after `protocol = "file"` on
  `https://localhost/c|/x` (both sides give `file://localhost/c|/x`), Node applies the file host
  state's normalizations on the *next* setter call of any kind, even a refused `protocol =
  "foo"`: `localhost` becomes the empty host (`file:///c|/x`) and the drive letter `c|`
  becomes `c:` (and survives a later switch to `http`); no setter touches the host or path
  in the standard. Skipped when a `protocol = file` step precedes and Node's URL equals
  whatwg-url's after exactly those two rewrites.
- `limit/ada-file-localhost-keeps-scheme` — `https://localhost/x`, `protocol = "file"`,
  `protocol = "http"`: the scheme state refuses the switch away from `file` only for an
  empty host, and `localhost` is a non-empty host here (only the file host state maps it),
  so whatwg-url gives `http://localhost/x`; Node stays at `file://localhost/x`. Both agree
  on the parse-time cases (`file://localhost/x` → `file:///x`, refusing the switch).
- `limit/node-searchparams-escape-with-non-ascii` — `new URLSearchParams("a=é%8c")`: the
  standard UTF-8-encodes the string and then parses the bytes (`a=%C3%A9%EF%BF%BD`); Node's
  parser takes a name or value that has non-ASCII characters and percent-escapes which do not
  decode to UTF-8 (a lone `%8c`, a cut-short `%C3`, or `%20é%zz`, a valid escape next to a
  malformed one) through a byte path where each code unit is a byte (`a=%EF%BF%BD`; a `😀`
  comes out as `=` and NUL). `a=é%20`, `a=é%zz` and `a=é%C3%A9` agree.
- `idna/host-differs`, `idna/acceptance-differs` — domain-to-ASCII disagreements between tr46
  6.0 and Ada 2.9: `ẞ` (U+1E9E) is `xn--zca` (ß, the non-transitional mapping the standard
  asks for) in whatwg-url and `ss` in Node; Arabic-Indic digit labels (`٠١٢`) and a label
  ending in tatweel (`aـ`) are rejected by whatwg-url (Bidi rule / disallowed) and accepted by
  Node; `xn--`, `xn--zz`, `xn--a` are accepted by whatwg-url as they are and rejected by Node.
  Which side is right depends on the UTS #46 revision each implements; not counted either way.

## Not tested

- The `encoding` option of `parseURL`/`basicURLParse` (legacy query encodings through
  `@exodus/bytes`), `URLSearchParams.forEach`/iterator protocols beyond `[...params]`, the
  `webidl2js-wrapper` API (`install`, `create`, `convert`), the live viewer, `blob:` origins
  (whatwg-url documents that it does not resolve them).
- The record API is fed the input after `toWellFormed()`: it takes the scalar value string
  the class receives from its `USVString` conversion, so a lone surrogate is U+FFFD before
  the parser strips tabs and newlines (`"#\ud83d\r\ude00"` is `%EF%BF%BD%EF%BF%BD` for the
  class and would be `😀` if the raw string reached `parseURL`). Lone surrogates in a raw
  string are outside the parser's domain, not a bug.

## Bugs

None found (2026-09-15, 17.1.1): about 36 000 generated URLs and 24 000 setter sequences
agree with Node except in the shapes above.

## History

- 2026-09-15: created at 37df073c (17.1.1); no bugs, ten Node divergences recorded.
- 2026-09-23: generators rewritten in combinator style (`test/gen.mjs`); the setters' start
  URL is drawn valid instead of half the cases returning early; three gates that were too
  narrow widened (`host = ":80"` on a URL without a port, a bare `?` query under the
  pathname setter, a port beside an IDNA host difference); two more Node divergences
  recorded (`limit/ada-file-normalizations-by-later-setter`,
  `limit/ada-file-localhost-keeps-scheme`). Still no whatwg-url bug.
