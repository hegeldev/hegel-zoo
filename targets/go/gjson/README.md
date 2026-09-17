# gjson

[gjson](https://github.com/tidwall/gjson) is the Go "get a value from a JSON document by path"
library (15k stars; used by tile38, redcon-based servers, Caddy plugins, Grafana, many CLIs).
It scans the document without building a tree and has its own path language (SYNTAX.md):
keys, indices, wildcards, `#` counts and maps, `#(...)` queries, pipes, modifiers, multipaths
and literals. The pin is the default branch at `8d89927` (2026-08-27, just past v1.9.4).

The repository has README.md, SYNTAX.md and LICENSE (MIT) only; nothing restricts AI-written
tests, and the zoo keeps its tests in its own patch and files nothing upstream.

## Build

`go test -count=1 -v .` in the module root. The patch adds `hegel_test.go` (properties) and
`hegel_pins_test.go` (one plain test per bug) and requires `hegel.dev/go/hegel v0.6.33` in
go.mod. No external oracle process: everything runs in-process.

## Oracles

- **encoding/json** — `json.Valid` for validity, `Unmarshal` into `interface{}` for `Value()`
  and for string decoding, `Marshal` for `AppendJSONString`.
- **strconv / math/big** — exact integer parsing for `Int()`/`Uint()` (saturating), `ParseFloat`
  and `ParseBool` for `Float()`/`Bool()`/`String()`.
- **A path model** — the tests generate an ordered JSON tree (keys and strings drawn from an
  alphabet full of path metacharacters, numbers in every textual form, escapes chosen at random,
  random whitespace) and then *construct* a path from the tree together with the value it must
  select: exact and `Escape`d keys, wildcard patterns derived from a real key (matched by a
  small glob, first key in document order wins), in- and out-of-range indices, `#`, `#.key` and
  `#.index` maps, `#(key op value)` / `#(key op value)#` queries restricted to members of one
  kind, existence queries, `.`/`|` separators, `|#`/`|N`/`|@reverse` after computed arrays,
  the modifiers `@reverse @keys @values @flatten(:deep) @join @group @dig @this @ugly @valid
  @tostr|@fromstr @pretty|@ugly` with models, `[...]` and `{...}` multipaths with explicit and
  automatic names, and `!` literals.

## Method

| Property | Checks |
|---|---|
| GetFollowsThePathModel | `Get(doc, path)` returns the modelled value (Type, compact Raw, Str, Num); `GetBytes`, `GetMany` agree |
| ValueMatchesEncodingJson | `Valid` true; `Parse(doc).Value()` marshals to the same bytes as `Unmarshal`'s tree; ForEach values equal the map's members |
| ValidAgreesWithEncodingJson | `Valid`/`ValidBytes` equal `json.Valid` on generated documents and on up to three random byte deletions/insertions/replacements/truncations |
| IndexesAndPathsLocateTheValue | `doc[Index:Index+len(Raw)] == Raw`; `Path()` round-trips (Raw and Index); `Get(head).Get(tail)` equals `Get(path)`; `#.key` results have one `Indexes` entry per value, ForEach's elements carry the right Index, `Paths()` round-trips |
| ForEachMatchesTheTree | ForEach/All/Keys/Values/Array/Map visit the members in order with the right keys; IsObject/IsArray |
| NumberAccessorsMatchTheirModels | Int/Uint (exact big.Int, saturating), Float, Bool, String on numbers and numeric strings against strconv models of gjson's documented rules |
| StringDecodingMatchesEncodingJson | every escape form, surrogate pairs and lone surrogates: `Str` equals `Unmarshal`'s string; the key is found again through `Escape`; a `#(=="…")` query finds the string |
| AppendJSONStringMatchesEncodingJson | byte-for-byte `json.Marshal` (including invalid UTF-8 → U+FFFD, `<>&`, U+2028/9); parses back |
| LessIsAStrictWeakOrder | `Less` against its model (type order, ASCII-case-insensitive strings, Num, Raw) and irreflexive/asymmetric/transitive |
| ForEachLineSplitsJsonLines | values separated by LF/CRLF/blank lines come back one by one |
| NothingPanicsOnArbitraryInput | random bytes, corrupted documents and random paths through Get/Parse/Value/String/Int/…/ForEach/GetMany/ForEachLine/Path |
| WhitespaceDoesNotChangeTheValue | the same tree rendered with different whitespace gives the same result for the same path |

Mismatches are classified before they count: a `Known` switch per recorded bug gates the input
shape (three-digit integer wraparounds, surrogate-then-escape tokens, escaped keys as automatic
multipath names, escaped wildcards in patterns, `Path()` on invalid documents, literals with a
dot). With everything gated the properties run clean at 1000 cases; `ZOO_COLLECT=1` makes the
path property print class counts and the first 25 mismatches instead of failing.

## Accepted differences (not bugs)

- gjson does not validate: `Parse` accepts `+1`, `Infinity`, `NaN`, junk after a value, raw
  control characters inside strings, and reads what it can. `Valid` is the check.
- Duplicate keys: `Get`, `Value()` and `Path()` take the first occurrence (encoding/json's
  `Unmarshal` takes the last). The properties use unique keys except where noted.
- `Valid` has no nesting limit (encoding/json refuses depth > 10000); `1E400` parses with
  `Num = +Inf` and `String() == "+Inf"` (encoding/json refuses). The generators stay within
  depth 5 and exponent 300.
- Number results: `String()` is the raw text for integers and `FormatFloat(Num, 'f', -1, 64)`
  otherwise, so `1e2` prints as `100` and `0.10` as `0.1`; `Int()` of `9007199254740993` is
  exact (parsed from the text) while `Int()` of `9007199254740993.0` is rounded through float64.
- A wildcard component followed by `.rest` is a search: the first matching key *under which
  `rest` exists* wins (`?.0` on `{"a":0,"b":[7]}` is `7`); with `|rest` or as the last
  component the first matching key wins. The generator writes `|` after wildcard steps.
- Query values compare across types by gjson's own rules (`#(a==1)#` and `#(a=="1")#` both match
  `1` and `"1"`, `#(a==true)#` matches `"true"`); the model only generates same-kind queries.
- A query without a key (`#(>"x")`) applied to an object element compares the element's `""`
  member, because the query path is the empty component; array elements never match.
- Whitespace around the key inside `#(...)` is trimmed, so a key that is a tab cannot be
  queried (`#(\t)#` is the keyless existence query).
- Query string values are JSON-unescaped before comparison, so `\*` inside `#(a=="x\*")` ends
  the pattern — write `\\*`.
- Automatic multipath names come from the raw last component: `{a.@reverse}` has the key
  `"@reverse"`, `{@this}` the key `"@this"`, `{a.#}` and `{a.#(b>1)}` the key `"_"`, `{a.0}`
  the key `"0"`; `{x,x}` writes the key twice.
- `#.a|@reverse` reverses the collected array (and drops `Indexes`); `#.a.@reverse` applies
  the modifier to every element (`Indexes` kept). `a.#.b.#.@this` reports `Indexes=[0 0]`.
- `Index` is 0 for computed results (counts, multipaths, modifiers, literals) and for the root.
- An empty component is the empty key: `a.` selects `a`'s `""` member, `.x` selects key `x` of
  the root's `""` member, `.` is two empty components, `{}` is a multipath of one empty path
  (`{"":…}` when the root has an empty key, else `{}`), `a|` is nothing. A path starting with
  `..` switches to JSON Lines mode (documented in the README), so the generators write `|`
  between two leading empty components.
- `@fromstr` on a string that is not JSON yields no result; on `" 1 "` yields `1`.
- `ForEachLine` accepts CRLF, blank lines, several values per line and values spanning lines.
- `a.01` is index 1 (leading zeros ignored); `-1` is a key, not an index.

## Bugs

Seven; see `bugs.toml`. Two in number and string decoding (1: `Int()`/`Uint()` wrap instead
of saturating for some 20-digit inputs; 2: a surrogate escape swallows the next `\uXXXX`), four
in the path language (3: escaped keys become escaped multipath names; 4: escaped `*`/`?` in a
pattern with another wildcard act as wildcards; 6: `{!7.5}` is named `"5"`; 7: `Escape` leaves
`:` alone, which names a multipath member) and one panic (5: `Result.Path` on `{"b:"2}`).

## Not tested

The `%`/`!%` pattern operators and `~` tilde operators in queries, nested queries, `@pretty`
options, custom modifiers (`AddModifier`), `@dig` with multi-component paths, `Time()`,
`DisableModifiers`/`DisableEscapeHTML`, and the deprecated `#[...]` query form.
