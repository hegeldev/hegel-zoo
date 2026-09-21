# go/gin

[gin-gonic/gin](https://github.com/gin-gonic/gin) (v1.12.0): the most used Go web framework
(85k stars); its router is a radix tree taken from httprouter and extended with static and
wildcard segments at one position (since v1.7) and with escaped colons. Tested here: the
tree's matching of requests to routes with `:param` and `*catch-all` wildcards, the conflicts
it refuses at registration, `cleanPath`, and the `Engine` options that decide what happens
when nothing matches - `RedirectTrailingSlash`, `RedirectFixedPath`, `HandleMethodNotAllowed`,
`RemoveExtraSlash`, `UseRawPath`, `UnescapePathValues`.

## Build

The patch adds `hegel.dev/go/hegel` to `go.mod` (and lets `go mod tidy` move `golang.org/x/sys`
from v0.41.0 to v0.44.0) and five `hegel_zoo_*_test.go` files in package `gin` itself: the
tree and `cleanPath` are unexported. Every identifier carries the `hz` prefix to stay clear of
the upstream tests. `go test -count=1 -run TestHegel -v .`

## Oracles

- A model of matching: routes are tokenized the way `tree.go` reads a pattern (static text,
  `:param` up to the next `/`, `*catch-all` at the end after a `/`, `\:` a literal colon); a
  request is matched by a depth-first walk over the tree the routes make - node by node, the
  static child first, then the `:param` child (the text up to the next `/`, never empty at the
  very end of the path), then the `*catch-all` (the rest, starting with `/`) - abandoning a
  failing static branch for the wildcard sibling of the nearest node above (backtracking),
  as the README describes ("matches static routes before params and params before catch-all",
  "supports routes with parameters and static segments at the same position"). The node
  structure is derived from the routes (a node ends where a route ends, a wildcard starts or
  two routes differ), because the tree's stopping and redirect rules depend on it.
- The set of routes a tree accepts, and what it serves, do not depend on the order of
  registration.
- `path.Clean` (trailing slash kept) as the oracle of `cleanPath`.
- A model of the engine's answer to a request from the documentation of the options: 200 when
  a route matches; else, unless the method is CONNECT or the path is `/`, a 301 (307 for
  other methods) to the path with the trailing slash toggled when a route exists for it
  (`RedirectTrailingSlash`), then to the case-insensitively matching cleaned path
  (`RedirectFixedPath`, the same walk with folded static text, also trying the toggled slash);
  then 405 with a sorted `Allow` header of the other methods that serve the path
  (`HandleMethodNotAllowed`); else 404. `RemoveExtraSlash` cleans the path first; `UseRawPath`
  matches `URL.RawPath` when set, unescaping params if `UnescapePathValues`. The Location is
  what `http.Redirect` makes of the new path.

## Properties

- `TestHegelMatch`: 1-6 routes (static, `:param`, mixed `text:param`, `*rest`, escaped colons,
  trailing slashes, some shapes the tree rejects) and 3 requests per case, many built from the
  routes' own tokens with static segments of other routes as param values, against the model
  (route and params, or 404); a registration panic must be one the model predicts.
- `TestHegelRouteOrder`: the accepted routes shuffled and re-registered give the same
  acceptance and the same answers.
- `TestHegelCleanPath`: `cleanPath` against `path.Clean`, and idempotence.
- `TestHegelEngine`: every combination of the six options, requests including escapes, `.`,
  `..`, doubled slashes and case changes, against the engine model (status, body, Location,
  Allow); the engine's panic is a possible answer.
- `TestHegelPin…`: one pin per recorded bug, asserting the documented behaviour (expected
  failures).

## Bugs

Seven, recorded in `bugs.toml`: a static route one slash away from the request shadows a
matching `:param` route (gin/1); a `:param` branch that dead-ends is not abandoned for the
wildcard sibling of an earlier node (gin/2) - both make `RedirectFixedPath` redirect a
request to itself; `RedirectTrailingSlash` (gin/3) and `RedirectFixedPath` (gin/6) redirect a
path ending in a slash to a path with no route; `RedirectFixedPath` never finds a `*catch-all`
after a `:param` (gin/4); `UseRawPath` turns `+` into a space (gin/5); the skipped-nodes stack
leaks between the method trees of one request, giving a 405 with a wrong `Allow` and, with four
or more method trees, a panic (gin/7, fixed upstream by 3b08cd7 two days before this pin).

## Modelled as recorded

The tree's stopping rules (where it does not backtrack: gin/1, gin/2), its trailing-slash
recommendations (gin/3, gin/6), the unreachable catch-all after a param (gin/4),
`url.QueryUnescape` for values (gin/5) and the shared stack across trees, including its
overflow (gin/7), are in the model behind `HZKnown` switches, so the properties agree with the
package while the bugs exist; `ZOO_KNOWN_OFF=name` turns a switch off and each then fails.

Design notes on the tree that the model follows:

- `\:` in a pattern is unescaped in the node paths on the first request (`updateRouteTrees`),
  so it matches a literal colon; until then the tree holds the backslash.
- `cleanPath` keeps a trailing slash, including for a path ending in `/.`, not for `/..`.
- An empty `:param` value is accepted in the middle of a path (`/a//b` matches `/a/:id/b`) but
  never at the very end.
- A static node's children are tried by exact first byte, so the case-insensitive lookup tries
  the lower-case then the upper-case child.
- The other method trees are consulted in the order the methods were first registered.

## Not tested

The `binding` package (form, query, JSON, URI binding: a candidate for a second part),
`UseEscapedPath`, `X-Forwarded-Prefix` in redirects, `NoRoute`/`NoMethod` handlers,
`HandleContext`, middleware, rendering.

## History

- 2026-09-21: new target, four properties, 7 bugs.
