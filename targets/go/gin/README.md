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
from v0.41.0 to v0.44.0), eight `hegel_zoo_*_test.go` files in package `gin` itself (the tree
and `cleanPath` are unexported) and seven in package `binding`. Every identifier carries the
`hz` prefix to stay clear of the upstream tests. `go test -count=1 -run TestHegel -v . ./binding`

In package `gin` (part 1, rewritten 2026-10-11): `hegel_zoo_idioms_test.go` (the harness idioms
shared with the other rewritten Go targets: weighted choices, fair-bit dice, `hzShaped`,
`hzOnly`, the tallies), `hegel_zoo_test.go` (the judge, the collector, the `known` value of
fifteen switches - one per recorded bug, all off by default - and the classifier that runs a
model per switch), `hegel_zoo_routes_test.go` (the records and generators: patterns, route
sets, requests, engine options, clean paths, with the realised rate beside every weight),
`hegel_zoo_router_test.go` (the tokenizer, the acceptance rule, the tree walk with the switch
set threaded, `TestHegelMatch` and `TestHegelRouteOrder`), `hegel_zoo_engine_test.go` (the
engine model and `TestHegelEngine`), `hegel_zoo_path_test.go` (`TestHegelCleanPath`),
`hegel_zoo_router_shapes_test.go` (ten narrow properties) and `hegel_zoo_pins_test.go`.

In package `binding` (part 2, rewritten 2026-10-11): the same idioms and harness files
(byte-identical but for the package line, since a test package cannot import another's test
files), `hegel_zoo_forms_test.go` (the type specs, tag specs, forms and the two case records
with the realised rate beside every weight), `hegel_zoo_form_model_test.go` (the models with
the replicas and the judges), `hegel_zoo_form_test.go` (the two wide properties),
`hegel_zoo_form_shapes_test.go` (five narrow properties) and `hegel_zoo_pins_test.go`.

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
  two routes differ), because the tree's stopping and redirect rules depend on it. The walk
  takes the switch set: with every switch off it is the documented walk; with a switch on it
  reproduces the tree's rule for that bug (the stops of gin/1 and gin/2, the recommendations
  of gin/3, 6, 13 and 15, the fold walk's gap of gin/4, the shared stack of gin/7 and the
  stack's capacity of gin/14, `url.QueryUnescape` for gin/5), transcribed from `tree.go`.
- The set of routes a tree accepts is predicted from the patterns alone: the tokenizer's
  rejections (two wildcards in a segment, an unnamed one, a catch-all not at the end or without
  a slash before it, a bad escape) and the conflicts `addRoute` panics on (a second handler for
  one path, different wildcards at one position, a catch-all against a static sibling), in
  registration order; the engine's rejections are checked against it.
- `path.Clean` (trailing slash kept) as the oracle of `cleanPath`.
- A model of the engine's answer to a request from the documentation of the options: 200 when
  a route matches; else, unless the method is CONNECT or the path is `/`, a 301 (307 for
  other methods) to the path with the trailing slash toggled when a route exists for it
  (`RedirectTrailingSlash`), then to the case-insensitively matching cleaned path
  (`RedirectFixedPath`, the same walk with folded static text, also trying the toggled slash);
  then 405 with a sorted `Allow` header of the other methods that serve the path
  (`HandleMethodNotAllowed`); else 404. `RemoveExtraSlash` cleans the path first; `UseRawPath`
  matches `URL.RawPath` when set, unescaping params if `UnescapePathValues`. The Location is
  what `http.Redirect` makes of the new path. A panic of the engine is a possible answer the
  model states ("panic") only under the switches of gin/7 and gin/14.
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

Every property draws its cases as records from package-level generators: the request set
(1-6 routes, or the same one to three patterns on two to seven methods one time in seven; the
patterns of 1-4 segments of static atoms, `:param`, mixed `text:param`, `*rest`, escaped
colons, a trailing slash, sometimes a shape the tree rejects) and three requests per case (half
built from a drawn route's tokens with its params filled - an atom, a static segment of another
route, or an empty or surprising value -, then a slash toggled, a suffix added or the path
upper-cased one time in ten each; half free paths of 0-5 atoms including escapes, `.`, `..`
and doubled slashes). The weights are drawn from fair-bit dice (`hzDie`, `hzChance`) because the
engine's integer draw favours small values at every scale; the realised rate over 3000 cases is
written beside every weight.

The shape of every recorded bug is computed before the library is called, by the model run per
switch: a case whose documented answer differs from the answer with every switch on is named by
the first switch that alone makes the difference (sufficiency), else by the first whose removal
does (necessity: the gin/1 and gin/2 stops that leak the stack into a gin/7 panic), and the
mismatch names the bug ("the shape of gin/N"). Under `HEGEL_NO_KNOWN=1` the requests whose
shape is named are filtered out of the generator (under two percent of Engine's requests, a
fifth of a percent of Match's) and every property passes.

- `TestHegelMatch`: with redirects off, a request is served by the route the model picks, with
  the model's params, or is a 404 when the model finds none; the engine's rejections equal the
  predicted ones. Draws the shapes of gin/1, 2 and 14; its forty rounds at a hundred cases:
  19 of 40 fail, gin/1 13, gin/2 5, gin/14 1; mapped intermittent to its plurality.
- `TestHegelRouteOrder`: the accepted routes shuffled (a drawn Fisher-Yates over the drawn
  routes) and re-registered give the same acceptance and the same answers. No bug lives here.
- `TestHegelCleanPath`: `cleanPath` against `path.Clean`, and idempotence.
- `TestHegelEngine`: every combination of the six options, requests including escapes, `.`,
  `..`, doubled slashes and case changes, against the engine model (status, body, Location,
  Allow, or the panic). Draws the shapes of gin/1 to 7 and 13 to 15 at their natural rates
  (per 3000 cases: gin/3 about 50, gin/6 about 25, gin/2 about 12, gin/1 about 8, gin/4 about
  5, gin/5 a few, gin/13 and gin/15 under one, gin/7 and gin/14 as good as never - their
  coverage is the narrow properties); its forty rounds: 39 of 40 fail,
  gin/3 18, gin/1 9, gin/6 6, gin/2 3, gin/4, 5 and 15 one each; mapped intermittent to its
  plurality.
- Ten narrow properties, one per router bug, each over the bug's shape region with random atoms
  and extra routes, judged by the same model, failing every run and naming its bug; under
  `HEGEL_NO_KNOWN=1` each draws the region past the shape and passes:
  `TestHegelStaticBranchesBacktrackToParams` (gin/1), `TestHegelDeadEndParamsBacktrack` (2),
  `TestHegelTrailingSlashRedirectsLandOnRoutes` (3), `TestHegelFixedPathReachesCatchAllsAfterParams`
  (4), `TestHegelPlusStaysInPathValues` (5), `TestHegelFixedPathRedirectsLandOnRoutes` (6),
  `TestHegelMethodTreesStartFresh` (7), `TestHegelSlashRedirectsSurviveParamSiblings` (13),
  `TestHegelMixedSegmentsDoNotOverflow` (14), `TestHegelEmptyParamPathsAreRecommended` (15).
- `TestHegelFormMapping`: struct types drawn as specs (1-4 fields, nested to depth 2, embedded
  structs and pointers to them, slices, arrays, pointers, maps, `time.Time`, `time.Duration`, a
  `BindUnmarshaler` and a `TextUnmarshaler` type, `any`) with drawn tags (keys of their own or
  shared, `default=`, `parser=`, stray options, `collection_format`, the time tags, a tag of
  the other name), built by a pure function with `reflect.StructOf`, the destination by value
  one time in twenty, and a form drawn for the keys the spec looks up, with values fit for each
  field and some bad ones, against the model (the value reached, the error by message - or
  "some error" where the documentation names none - and the panic). Draws the shapes of
  gin/10, 11 and 12 (per 3000 cases about 135, 265 and 15); its forty rounds at a hundred
  cases: 40 of 40 fail, gin/10 30 and gin/11 10; mapped plain to gin/10 (nine rounds at the
  default count had split them 5 to 4). Under `HEGEL_NO_KNOWN=1` the shaped cases are filtered
  out (eleven percent).
- `TestHegelFormMapDest`: map destinations of seven types, by value and by pointer, nil or
  holding an entry, forms with keys without values, against the model (result, error, or
  panic). Draws the shape of gin/8 in about one case in six; plain (40/40 at a hundred cases).
- Five narrow properties, one per binding bug: `TestHegelNilMapsAreAllocated` (gin/8),
  `TestHegelSelfReferencesStayNil` (9: a family of recursive named types - a node with its
  parent, a list, a mutual pair - with forms that never hold the recursive key, bound in a
  child process re-executed from the test binary, about 30 ms a case under a 16 MB stack cap;
  the documented answer is the pointer left nil, the shape a fatal stack overflow),
  `TestHegelValueDestinationsAreErrors` (10: a form that matches a field),
  `TestHegelEmptyValuesLeaveStructsAndMaps` (11), `TestHegelEmptyValuesTakeCollectionDefaults`
  (12: a default that differs from the zero and splits to the array's length).
- `TestHegelPin…`: one pin per recorded bug, asserting the documented behaviour (expected
  failures).

## Bugs

Ten in the router, recorded in `bugs.toml`: a static route one slash away from the request
shadows a matching `:param` route (gin/1); a `:param` branch that dead-ends is not abandoned for
the wildcard sibling of an earlier node (gin/2) - both make `RedirectFixedPath` redirect a
request to itself; `RedirectTrailingSlash` (gin/3) and `RedirectFixedPath` (gin/6) redirect a
path ending in a slash to a path with no route; `RedirectFixedPath` finds a `*catch-all` after
a `:param` only when a sibling route splits the static text right before the param's slash
(gin/4); `UseRawPath` turns `+` into a space (gin/5); the skipped-nodes stack leaks between the
method trees of one request, giving a 405 with a wrong `Allow` and, with enough other trees, a
panic (gin/7, fixed upstream by 3b08cd7 two days before this pin); a `:param` route beside a
static branch makes the tree roll back before it recommends the branch's trailing-slash
redirect, so `/a/*rest` with `/:q/x` answers `GET /a` with a 404 instead of a 301 to `/a/`
(gin/13, found by the replica's one disagreement with the tree in 3000 cases); mixed
`static:param` routes nested at one position (`/a:p`, `/ab:p`, `/abc`) push more roll-back
points than the stack has room for - one per path section - and `GET /abc` panics on an
engine with every option off (gin/14, found under `HEGEL_NO_KNOWN=1`); and the trailing-slash
recommendation ignores a `:param` child whose empty value leads to the `/` route, so `/ab:p/`
serves `GET /ab/` but answers `GET /ab` with a 404 (gin/15).

Five more in the binding package: binding into a nil map panics, as does a key without values
(gin/8); a struct with a pointer field of its own type - a tree node, a linked list - binds
until the stack overflows, a fatal error no middleware recovers (gin/9); a destination passed
by value panics where the JSON binding returns an error (gin/10); an empty value for a struct
or map field is a JSON error where every other kind takes its zero (gin/11); an empty value for
a slice or array is not replaced by its `default=` as a scalar's is (gin/12).

## Modelled as recorded

The fifteen recorded bugs are the constants of the `known` value (`kStaticShadowsParam` to
`kEmptyParamSlashUnrecommended`, in bug order), off by default; the ten router ones act in the
tree walk and the engine model: with every switch off the model states the documented
behaviour and the properties fail on the bugs' shapes, mapped to them in `target.toml`; with a
switch on the model reproduces the tree's rule for that bug, which is how the classifier names
a case and how the replicas are checked against the library (every shaped case by default
agrees with the model with every switch on: a disagreement would be a replica defect or a
further bug - that is how gin/13 was found). The five binding bugs act in the form-mapping
model the same way (the replicas of `setFormMap`, the pointer descent of `mapping`, the
unaddressable `Set` and `Addr`, the JSON unmarshal of an empty value and `setByForm`'s check for
no values at all). gin/9 is the one shape no generator of struct types can build
(`reflect.StructOf` makes no cycles) and its failure is a fatal error, not a panic: the wide
property does not draw it; its narrow property does, in a child process.

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
- 2026-10-11: part 1 rewritten to the standard (the switches off by default, every shape
  drawn, ten narrow properties, fair-bit dice, the acceptance rule); gin/13, gin/14 and gin/15
  found by the rewrite and recorded; the notes of gin/3, 4 and 7 corrected.
- 2026-10-11: part 2 rewritten to the standard (spec records, the five binding switches, five
  narrow properties, gin/9 in a child process); the note of gin/10 widened.
