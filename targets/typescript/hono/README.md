# hono (routers)

[Hono](https://github.com/honojs/hono) is a small web framework for every JavaScript runtime; its
routing layer is five interchangeable routers behind one interface (`add(method, path, handler)`,
`match(method, path)`): RegExpRouter, TrieRouter, LinearRouter, PatternRouter and SmartRouter (the
default: RegExpRouter, falling back to TrieRouter when RegExpRouter rejects a table). Pinned at
4.13.8, 52febbc (2026-09-20), MIT. Only the routers are tested here.

The source is TypeScript with extensionless imports and a bun-only build, so the setup bundles
`src/router/*` and `src/utils/url.ts` with esbuild (`hegel/routers-entry.ts` ->
`hegel/routers.mjs`); Hegel and esbuild go under `.hegel/`. Tests: `hegel/hegel.test.mjs`, run with
`node --test`. `ZOO_FULL=1` opens the gates around the known bugs and adds regexp patterns
RegExpRouter rejects (`(a|b)`, `.*`, single characters); `ZOO_COLLECT=1` prints mismatch statistics.

## Oracle

The routing rules documented at hono.dev/docs/api/routing and fixed by the routers' shared test
cases (`src/router/common.case.test.ts`), written as a regular expression per route
(`hegel/model.mjs`): a literal segment matches itself; `:name` one non-empty segment; `:name{re}`
the regexp, which may span slashes; a middle `*` one segment; a trailing `/*` nothing or a slash and
anything; a suffix `*` (`/assets*`) any tail; `*` everything; `:name?` expands into the shorter
routes the way `checkOptionalParameter` documents; a trailing slash does not match (LinearRouter and
PatternRouter allow it, as their own tests record); handlers come back in registration order for the
request's method or ALL; a duplicated parameter name takes the first value. A router that throws
`UnsupportedPathError` for a table is not judged on it (RegExpRouter is documented to reject
ambiguous patterns; LinearRouter rejects labels mixed with wildcards; PatternRouter rejects
duplicate group names).

Route tables are one to six routes over a tiny alphabet (literals `a`, `b`, `ab`, `foo`, `x.js`,
`$`, `-`; parameters `id`, `name`, `x`, `y`; regexps `[0-9]+`, `[a-z]+`, `\d{1,3}`, `[a-z]+\.js`,
`(?:foo|bar)`, `.+`, `[^/]+`), methods GET/POST/ALL; requests instantiate one of the routes and are
then sometimes bent (segment dropped or appended, trailing slash, empty segment, literal changed).

## Properties

| Test | Checks |
| --- | --- |
| `TestHegelTrieRouterFollowsTheRoutingRules` | TrieRouter (documented to support every pattern) returns the model's handlers and parameters |
| `TestHegelRegExpRouterFollowsTheRoutingRules` | RegExpRouter, on the tables it accepts, returns the model's handlers and parameters (stash resolved) |
| `TestHegelLinearRouterFollowsTheRoutingRules` | LinearRouter, on the tables it accepts, requests without a trailing slash |
| `TestHegelPatternRouterFollowsTheRoutingRules` | PatternRouter, on the tables it accepts, requests without a trailing slash |
| `TestHegelSmartRouterFollowsTheRoutingRules` | SmartRouter over [RegExpRouter, TrieRouter] (Hono's default) returns the model's answer |

In the default run the shapes of the recorded bugs are counted and skipped (duplicate parameter
names, a slash-spanning regexp before a dynamic segment, `*/*`, empty segments against `*`, a
metacharacter literal after a regexp parameter, a `/` inside a regexp of a middleware route, an
optional parameter after `*`, a middle `*` meeting a parameter or `P/*` beside `P*` under RegExpRouter, a
literal after `.+` that begins twice in the request). Pins (`TestHegelPin*`) reproduce the bugs in `bugs.toml` and are
listed as expected failures.

## Not tested

- The `Hono` app itself (`app.get`, `basePath`, `route`, `c.req.param`), `getPath` and the query
  helpers of `utils/url.ts`, `mergePath`.
- Hostname routing (`www1.example.com/hello`), percent-encoded paths (routers see decoded paths),
  routes with `*` glued to a parameter (`/:x*`).
- Error messages and the ambiguity rules of RegExpRouter (which tables it rejects is not judged).

## History

- 2026-09-20: created (turn 320); 7 bugs recorded.
- 2026-09-23: generators rewritten in combinator style; the long runs found hono/8-10.
