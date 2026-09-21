# go/gin

[gin-gonic/gin](https://github.com/gin-gonic/gin) (v1.12.0): the most used Go web framework
(85k stars); its router is a radix tree taken from httprouter and extended with static and
wildcard segments at one position (since v1.7) and with escaped colons. Tested here: the
tree's matching of requests to routes with `:param` and `*catch-all` wildcards, the conflicts
it refuses at registration, `cleanPath`, and the `Engine` options that decide what happens
when nothing matches - `RedirectTrailingSlash`, `RedirectFixedPath`, `HandleMethodNotAllowed`,
`RemoveExtraSlash`, `UseRawPath`, `UnescapePathValues`; and (part 2) the `binding` package's
mapping of form, query and URI values into structs and maps by their `form`/`uri` tags.

## Build

The patch adds `hegel.dev/go/hegel` to `go.mod` (and lets `go mod tidy` move `golang.org/x/sys`
from v0.41.0 to v0.44.0), five `hegel_zoo_*_test.go` files in package `gin` itself (the tree
and `cleanPath` are unexported) and three in package `binding`. Every identifier carries the
`hz` prefix to stay clear of the upstream tests. `go test -count=1 -run TestHegel -v . ./binding`

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
- A model of the form mapping (`MapFormWithTag`, behind `ShouldBind`, `ShouldBindQuery`,
  `ShouldBindUri`, `ShouldBindHeader`) from docs/doc.md ("Bind default value if none provided",
  "Collection format for arrays", "Bind Uri", the `time_format` examples, "Bind form-data request
  with custom struct") and the `BindUnmarshaler` doc: a field is set from the entry named by its
  tag (the field name without one; `-` skips it); a missing or empty value gives the `default=`;
  the value is parsed by its kind (whitespace trimmed except for strings, an empty value the
  zero), by `UnmarshalText` when `parser=encoding.TextUnmarshaler` says so, by `UnmarshalParam`
  when the type has it, `time.Time` by `time_format`/`time_utc`/`time_location` (the unix
  formats case-insensitively), structs and maps from JSON; a slice or array takes every instance,
  split by the `collection_format` separator (`;` separates the instances of a default for multi
  and csv), an array wanting exactly its length; pointers are allocated only when something below
  them is set; the fields of a nested struct, named or embedded, are looked up by their own keys.
  A `map[string][]string` destination receives every entry, a `map[string]string` the last value
  of each; other maps with string keys are an error.

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
- `TestHegelFormMapping`: struct types built at runtime with `reflect.StructOf` (1-4 fields,
  nested to depth 2, embedded structs and pointers to them, slices, arrays, pointers, maps,
  `time.Time`, `time.Duration`, a `BindUnmarshaler` and a `TextUnmarshaler` type, `any`) with
  generated tags (keys of their own or shared, `default=`, `parser=`, stray options,
  `collection_format`, the time tags, a tag of the other name) and a form drawn for the keys
  the type looks up, with values fit for each field and some bad ones, against the model (the
  value reached and the error, by message).
- `TestHegelFormMapDest`: map destinations of six types, by value and by pointer, nil or holding
  an entry, forms with keys without values, against the model (result, error, or panic).
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

Five more in the binding package: binding into a nil map panics, as does a key without values
(gin/8); a struct with a pointer field of its own type - a tree node, a linked list - binds
until the stack overflows, a fatal error no middleware recovers (gin/9); a destination passed
by value panics where the JSON binding returns an error (gin/10); an empty value for a struct
or map field is a JSON error where every other kind takes its zero (gin/11); an empty value for
a slice or array is not replaced by its `default=` as a scalar's is (gin/12).

## Modelled as recorded

The tree's stopping rules (where it does not backtrack: gin/1, gin/2), its trailing-slash
recommendations (gin/3, gin/6), the unreachable catch-all after a param (gin/4),
`url.QueryUnescape` for values (gin/5) and the shared stack across trees, including its
overflow (gin/7), the nil-map and empty-list panics (gin/8), the JSON error on an empty value
(gin/11) and the default not applied to an empty value (gin/12) are in the models behind
`HZKnown` switches (one struct per package), so the properties agree with the package while the
bugs exist; `ZOO_KNOWN_OFF=name` turns a switch off and each then fails. gin/9 and gin/10 have
pins only: the generated types have no cycles and are always addressed.

Design notes on the tree that the model follows:

- `\:` in a pattern is unescaped in the node paths on the first request (`updateRouteTrees`),
  so it matches a literal colon; until then the tree holds the backslash.
- `cleanPath` keeps a trailing slash, including for a path ending in `/.`, not for `/..`.
- An empty `:param` value is accepted in the middle of a path (`/a//b` matches `/a/:id/b`) but
  never at the very end.
- A static node's children are tried by exact first byte, so the case-insensitive lookup tries
  the lower-case then the upper-case child.
- The other method trees are consulted in the order the methods were first registered.

Design notes on the form mapping that the model follows:

- A scalar takes the first value of its key, a `map[string]string` destination the last.
- A whitespace-only value is not "empty": it is trimmed to nothing and parsed as the zero, not
  replaced by the default. The default of a scalar applies to a missing and to an empty value.
- A default of a collection is split at `;` for multi and csv (the docs' rule), and is one
  instance split by the separator for ssv, tsv and pipes; an empty default gives one zero
  element.
- A collection type that itself implements `BindUnmarshaler` (or `TextUnmarshaler` with the
  parser tag) takes the first instance whole; otherwise the element type does, per element.
- A named struct field whose key is present is filled from JSON and its fields are not looked
  up; without the key (and without a default) its fields are looked up by their own keys, in the
  flat namespace of the form; an embedded struct is never filled from JSON.
- Array elements are written in place until the first error; a slice is set only when every
  element parsed.
- `any`, `uintptr` and other kinds without a parse are "unknown type" errors when their key is
  present or they have a default, and are skipped otherwise. An unknown `collection_format` is
  an error only when the field has values or a default.
- `time_utc` is read with `strconv.ParseBool`, an unreadable value meaning false; the unix
  formats ignore `time_utc` and `time_location`.

## Not tested

In the `binding` package: multipart file fields, the validator (`binding:"required"` and the
rest of go-playground/validator), the JSON/XML/YAML/TOML/protobuf/msgpack decoders (thin
wrappers), header binding beyond the shared mapping. In the engine: `UseEscapedPath`,
`X-Forwarded-Prefix` in redirects, `NoRoute`/`NoMethod` handlers, `HandleContext`, middleware,
rendering.

## History

- 2026-09-21: new target, four properties, 7 bugs.
- 2026-09-21: part 2, the binding package's form mapping, two properties, 5 more bugs.
