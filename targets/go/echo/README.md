# go/echo

[labstack/echo](https://github.com/labstack/echo) v5 (v5.3.1): a widely used Go web framework
(30k stars) whose router is a radix tree with static, `:param` and `*` nodes, "smart route
prioritization" (static > param > wildcard, with backtracking), per-node method tables (405
with an `Allow` header, a default `OPTIONS` answer), `RouteNotFound` routes, `Any` routes,
escaped colons (`\:`), and the options `AutoHandleHEAD`, `UnescapePathParamValues` and
`UseEscapedPathForMatching`. Tested here: `DefaultRouter` through `Echo.ServeHTTP`, its
`Remove`, and `RouteInfo.Reverse`; and the binder - the struct binder (`bind.go`: tags
`query`/`param`/`form`/`header`, `DefaultBinder.Bind`), the `ValueBinder` chains
(`binder.go`) and the generic accessors (`binder_generic.go`: `ParseValue`, `QueryParam[T]`
and friends).

## Build

The patch adds `hegel.dev/go/hegel` to `go.mod` and a `hegel/` package of seven
`hegel_zoo_*_test.go` files that drive the public API (`echo.NewWithConfig` with a
`NewRouter(RouterConfig{...})`, `AddRoute`, `ServeHTTP` on `httptest` requests; the handlers
echo the route path and the path values; for the binder, `e.NewContext` on `httptest`
requests with a query, a form body, headers or `SetPathValues`). `go test -count=1 -run
TestHegel -v ./hegel`

## Oracles

- A model of matching from the README ("Priority is static -> param -> wildcard"), the
  `RouterConfig` and `Route` doc comments and the shapes the package's own tests establish: the
  routes make a trie (a byte trie: the radix tree's node boundaries only group bytes), walked
  static child first, then the `:param` child (the text up to the next `/`; a parameter that
  ends its route takes the rest of the path; empty in the middle, never at the end), then the
  `*` child (the rest, possibly empty), abandoning a failing branch for the next kind of the
  nodes above. At a node whose path is consumed, the method's route or the `Any` route serves
  (a HEAD falls back to GET with `AutoHandleHEAD`, the body dropped); the first such node
  without the method is remembered for a 405 (`Allow` = OPTIONS plus the node's methods, all
  of them for `Any`; a 204 with `Allow` for an OPTIONS request), unless it carries a
  `RouteNotFound` route, which answers instead; else the default 404 (`{"message":"Not
  Found"}`; no body for HEAD). The path matched is `URL.Path` or `URL.RawPath` per the option;
  values are `url.PathUnescape`d per the option.
- Registration order does not matter for routes that do not replace one another.
- `RouteInfo.Reverse` as documented: each `:name` or `*` (to the next `/`) replaced by the next
  value, `\:` a literal colon; the reversed URL served against the matching model.
- `Remove`: the removed route is gone, the others answer as if only they had been registered,
  `Routes()` lists them; an absent route is an error.
- The struct binder as `bind.go` documents it and the package's tests establish: fields with
  the source's tag, in declaration order, the first failure ending the binding with a 400
  naming the parameter; the exact parameter name first, else a case-insensitive match;
  untagged struct fields flattened, structs implementing `BindUnmarshaler` bound only with a
  tag, nil embedded pointers skipped, a tag on an embedded struct an error; values by kind
  (`strconv`, `""` as the zero value), slices from all the values, pointers allocated,
  `BindUnmarshaler` / `UnmarshalParams` / `TextUnmarshaler` / a `format` tag on `time.Time`;
  `Bind` = path values, then the query for GET/DELETE/HEAD/QUERY, then the body (a form here:
  `ParseForm`'s body-then-URL values). The model is a second reflect-driven implementation of
  these rules, compared by a canonical dump of the bound struct and the error text.
- `ValueBinder` per its comment block: each call binds if the parameter exists (`Must` errors
  otherwise), `FailFast` stops the chain at the first error, `BindErrors` lists them all, the
  error messages of `binder.go`.
- The generic accessors per their doc comments: an empty value is the default (the zero value
  without `Or`), a missing key `ErrNonExistentKey` or the default, `TimeOpts`/`TimeLayout` for
  `time.Time` only, a parse error a `BindingError` naming the key.
- `Context.QueryParam`'s raw-query fast path equals `url.ParseQuery(RawQuery).Get(name)`.

## Properties

- `TestHegelRoute`: 1-6 routes (static, `:param` incl. empty names, `text:param` segments,
  `*` incl. text after it, escaped colons, trailing slashes, paths without a leading slash;
  methods GET..PATCH, HEAD, OPTIONS, custom, `Any`, `RouteNotFound`), the three options at 30%
  each, 3 requests per case built from the routes' tokens (values with `/`, `%2F`, `%20`, case
  changes, a byte short, an extra segment) against the model: status, body (route and values),
  `Allow`.
- `TestHegelRouteOrder`: a permutation of the routes gives the same answers.
- `TestHegelReverse`: `Reverse` with 0..n+1 values against its model; the reversed URL served.
- `TestHegelRemove`: some routes removed, then `Routes()` and 3 requests against the model of
  the rest; an absent route's removal is an error.
- `TestHegelBindData`: a struct type built with `reflect.StructOf` (1-4 fields per level, two
  levels: 13 leaf types x plain/slice/pointer/pointer-to-slice/slice-of-pointers, nested,
  embedded and embedded-pointer structs, tags from a pool of names differing in case) bound
  from a query, path values, headers or a form body by `BindQueryParams` / `BindPathValues` /
  `BindHeaders` / `BindBody`, against the model.
- `TestHegelBind`: `c.Bind` for GET/POST/PUT/DELETE with path values, a query and a form body
  (or none), against the composed model.
- `TestHegelValueBinder`: a chain of 1-6 calls (24 kinds, `Must` or not: scalars, slices,
  `Time`, `Duration`, `UnixTime*`, the three unmarshaler interfaces, `BindWithDelimiter` into
  six slice types, `CustomFunc`) on a `QueryParamsBinder`, `PathValuesBinder` or
  `FormFieldBinder`, `FailFast` on or off: every destination and `BindErrors()`.
- `TestHegelParseValue`: `ParseValue[T]`, `ParseValueOr`, `ParseValues`, `ParseValuesOr`,
  `QueryParam[T]`/`QueryParamOr`/`QueryParams`/`QueryParamsOr`, `PathParam`/`PathParamOr`,
  `FormValue`/`FormValueOr`/`FormValues`/`FormValuesOr` for nine `T`s with time options.
- `TestHegelQueryParamFastPath`: `QueryParam(name)` before and after `QueryParams()` on raw
  queries built from tricky atoms (`;`, bad escapes, empty segments) against `url.ParseQuery`.
- `TestHegelPin…`: one pin per recorded bug, asserting the documented behaviour (expected
  failures).

## Bugs

Nine, recorded in `bugs.toml`: an escaped colon and a `:param` at one position corrupt the tree -
both routes lost and a panic in `ServeHTTP` (echo/1); a wildcard node without the method ends
the search, so a matching `:param` route above is not tried (echo/2); a `RouteNotFound` route
shadows a matching route - a `Group` with middleware makes `/:param` routes at its prefix
unreachable (echo/3); `UseEscapedPathForMatching` does the opposite of its documentation
(echo/4); text after `*` is silently dropped (echo/5); `Remove` panics for a custom method
(echo/6), deletes another route's entry for a path registered without a leading slash, which
is also listed under its original path (echo/7), does not find routes after a parameter, with
an escaped colon, under another parameter name or after an earlier removal (echo/8), and
prunes `RouteNotFound` routes on its way up (echo/9).

Four more from the binder: the case-insensitive fallback picks a random parameter when several
names match (echo/10); `ValueBinder`'s slice methods do not bind after an earlier error although
`FailFast` is off (echo/11); `QueryParamOr` and `FormValueOr` return the zero value on a parse
error where their examples say the default (echo/12); `Bind` with a non-pointer destination
panics when the request has query or path values (echo/13).

## Modelled as recorded

The wildcard stop (echo/2), the `RouteNotFound` stop (echo/3), the inverted option (echo/4),
`Remove`'s walk (its `prefixLen` accounting over the radix nodes as built, `originalPath` per
node, no re-merging) and its pruning (echo/8, echo/9) are in the model behind `HZKnown`
switches; the collision (echo/1), the custom-method panic (echo/6) and the slash-less paths
(echo/7) are skipped by the generators while their switches are on. `ZOO_KNOWN_OFF=name`
turns a switch off and the property then fails. Text after `*` (echo/5) is modelled as the
router reads it (dropped); the pin asserts the documented syntax.

Binder switches: `caseFoldRandom` (echo/10: the model skips a lookup with several inexact
matches), `slicesNeedNoErrors` (echo/11), `orReturnsZero` (echo/12). The non-pointer panic
(echo/13) is only pinned.

Design notes the model follows (the package's tests assert them):

- A parameter that ends its route takes the rest of the path, slashes included
  (`/a/:b/c/d/:e` serves `/a/1/c/d/2/3` with e = "2/3"); adding a route that continues after
  the parameter changes that.
- A parameter may be empty in the middle of a path (`/a//b` matches `/a/:id/b`), never at the
  end; `/users/*` matches `/users/` with `*` = "", `/assets` does not match `/assets/*`.
- Routes of one shape (parameter names erased) share a node: the later route replaces the
  earlier one's handler and reported path for its method.
- The first node reached with the path consumed and handlers for other methods gives the 405,
  even when a deeper or later alternative would give a 404.
- The `Allow` header lists the custom methods in map order (compared as a set here).
- Paths without a leading slash are served under the normalised path.
- Binder: an empty data set binds nothing and checks nothing (a tag on an embedded struct is
  an error only when there is data); `time.Duration` fields are integers of nanoseconds
  (`strconv.ParseInt`), the `format` tag applies to `time.Time` and `*time.Time` fields only
  (slice elements parse RFC3339); a tagged struct, array, map or interface field is "unknown
  type"; a pointer field is allocated as soon as its parameter is present, even when the value
  then fails to parse; `MustString` treats `?a=` as missing, `MustStrings` binds `[""]` and
  `MustInt64s` fails parsing `""`; a GET with a form body binds `form` tags from the query
  (`ParseForm` reads no body for GET). Generic: `ParseValuesOr` returns nil, not the default,
  on a parse error (its example prints `[]`, which nil does too).

## Not tested

Groups beyond the pin, middleware, `NewConcurrentRouter`, JSON/XML bodies and multipart files
in the binder, `BindHeaders` beyond the property's pool, rendering, the static file handlers,
`Context` helpers.

## History

- 2026-09-21: new target, four properties, 9 bugs.
- 2026-09-21: part 2, the binder: five properties, 4 more bugs.
