# koanf

[knadh/koanf](https://github.com/knadh/koanf) (module `github.com/knadh/koanf/v2`, with the
repository's `maps` module) is a configuration library: nested maps from providers are merged
into one configuration, addressed by delimited key paths (`parent.child.key`), with `Load`,
`Merge`, `MergeAt`, `Set`, `Delete`, `Cut`, `Copy`, `Slices`, `Keys`/`KeyMap`/`All`/`Raw`,
`Exists`/`Get`/`MapKeys`, the typed getters (`Int64`, `Float64`, `Bool`, `String`, `Duration`,
`Time`, their slice and map forms and the `Must*` variants), `Unmarshal` via mapstructure, and
strict merging. The pin is `6ad56fe` (2026-08-09, after v2.3.6).

The repository is MIT; there is no CONTRIBUTING file, the README says nothing about AI-written
code, and there are no agent instructions. The zoo keeps its tests in its own patch and files
nothing upstream.

## Build

`GOWORK=off go test -count=1 -run TestHegel -v .` in the module root (Go 1.23+). The patch
adds, in the external test package, `hegel_test.go` (harness, the `noKnown` switch, a map
provider), `hegel_model_test.go` (the model, the conversions, the generators),
`hegel_props_test.go` (the wide properties), `hegel_shapes_test.go` (one narrow property per
recorded bug) and `hegel_pins_test.go`, and in go.mod requires
`hegel.dev/go/hegel v0.6.33` and replaces `github.com/knadh/koanf/maps` by the repository's
`./maps` (the workspace file is switched off, so the pinned `maps` is tested rather than the
released v0.1.2).

## Oracle

A model of the configuration as a set of leaf paths (the parts of a key) with their values,
built from the package's documentation:

- a leaf is anything but a non-empty `map[string]any`: a scalar, a slice, a typed map, or an
  empty map (which `Flatten` keeps as a value); no leaf path is a prefix of another;
- `Load`, `Merge` and `MergeAt` merge the incoming nested map: a nested map merges into a
  nested map, anything else replaces what is at the key (a value under a map replaces the
  map, a map over a value replaces the value, an empty map merges nothing); `map[any]any`
  keys become strings first; `Set(key, v)` is the merge of `{key: v}` (see bug 2); `MergeAt`
  of an empty instance creates an empty map at the path;
- strict merging refuses an incoming leaf whose type differs from the existing one, a map over
  a value or a value over a map (an empty map over a map is fine), and changes nothing;
- a custom merge function (`WithMergeFunc`) that adds only missing top-level keys;
- `Delete` removes the path and everything under it, and every parent map it empties;
  `Cut` re-roots the sub map at a path (empty when the path is not a map); `Copy` is
  `Cut("")`; `Slices` is one instance per map element of a slice;
- `Keys` are the sorted leaf keys, `KeyMap` every prefix of them, `Exists` membership in it,
  `Get` the leaf value, the sub map of a prefix, the whole map for `""`, nil otherwise;
- the getters convert as toInt64/toFloat64/toBool document: integers as they are (unsigned
  ones that fit), anything else through `%v` and strconv (an integer, else a float truncated),
  `Duration` a non-zero integer as nanoseconds else `time.ParseDuration` of the string, `Time`
  a non-zero integer as a Unix time else `time.Parse`; the slice and map getters accept the
  typed slices and maps the code lists and `[]any`/`map[string]any` element-wise, returning
  nothing on the first element that does not convert; `Must*` panic exactly on the zero value.

Generators draw trees of 0-4 keys per level up to depth 3 over a small key alphabet (never
containing the delimiter), with leaf values of every type the getters handle (ints, uints past
int64, floats including Inf and huge values, numeric and junk strings, bools, nil, `[]any`
with nested maps, typed slices, `map[string]string`, `map[string][]string`, empty maps,
`map[any]any` with string and int keys), delimiters `.`, `/` and `::`, and key paths that
exist, extend an existing key, or are fresh.

## Method

| Property | Checks |
|---|---|
| OperationsFollowTheModel | 1-8 random operations (Load plain / strict / with a merge function, Set, Merge, MergeAt, Delete, Cut, Copy, Slices) each followed by Keys, KeyMap, Raw, All, Sprint, Delim and Exists/Get/MapKeys on every key, prefix and an absent extension of each; strict errors as the model, the map unchanged after one; Unmarshal of a map path into a map |
| GettersConvert | every getter and Must variant on a leaf of each type, a sub map, a missing key and the root |
| ValuesAreCopied | writing into what Get and the getters return changes nothing; Copy and Cut are independent of the original both ways; the provider's map after a second Load |

`ZOO_COLLECT=1` records mismatches instead of failing and prints the agreement classes.

## Known bugs

The generators draw the shape of every recorded bug but koanf/6 (STYLE.md rule 11), so the
wide properties are expected failures mapped to the bug they land on: OperationsFollowTheModel
on koanf/1 in most runs (a failed strict Load that has already written a key; the failed
merge is repeated on up to twenty fresh copies so that Go's map order cannot hide it), on /2
or /5 in the rest; ValuesAreCopied on koanf/3 (the provider's map rewritten in place); and
GettersConvert on koanf/4 (`Float64` of `"1e400"`; about 2.6 % of cases, intermittent). Each
bug also has a narrow property over its own shape region in `hegel_shapes_test.go`, the
deterministic expected failure beside the pin: `TestHegelStrictLoadIsAtomic` (koanf/1),
`TestHegelSetWithAMapReplacesTheValue` (/2), `TestHegelLoadCopiesTheProvider` (/3),
`TestHegelFloat64OutOfRangeIsZero` (/4), `TestHegelNestedSliceMapsAreConverted` (/5) and
`TestHegelSetOnAKeyWithTheDelimiterIsDeterministic` (/6, the one shape the flat-key model
cannot hold, so it is covered by the narrow property alone). `HEGEL_NO_KNOWN=1` (read once)
switches the shapes off: the model then reproduces each recorded behaviour (the partial merge
is counted and the instance rebuilt, `Set` with a map merges, the alias is accepted, Inf and
the unconverted map are expected) and every property passes at 3000 cases with no skips.

## Accepted differences

- Keys containing the delimiter and an empty top-level key are not generated: the empty path
  names the whole map, and a key with the delimiter in it flattens to the same string as a
  nested path (bug 6 records what `Set` then does).
- `StringsMap` keeps a nil entry for an empty `[]string` and none for an empty `[]any`; the
  test drops empty entries on both sides.
- `Bools` returns nil rather than an empty slice for a missing key; compared by length.
- After a failed strict merge the instance is rebuilt from the model under `HEGEL_NO_KNOWN=1`
  (bug 1 leaves it half-merged with stale flattened keys); by default the property fails there.
- The documentation of `All`, `Raw` and `Get` still says numbers come back as float64 from
  `json.Marshal`; `maps.Copy` uses copystructure and keeps the types, which the model follows.

## Bugs found

Six, in bugs.toml: a strict `Load` that fails has already merged part of the map and `Keys()`
no longer matches `Raw()` (medium); `Load` keeps the provider's maps and slices by reference,
so a second `Load` writes into the first provider's map and the provider's slice is the
configuration's (medium); `Set` on an existing path whose key contains the delimiter creates
a second structure and `Get` returns either value at random (medium); `Set` with a map value
merges instead of setting (low); `Float64` returns Inf for an out-of-range numeric string
while `Float64s` returns nothing (low); a `map[any]any` inside a slice inside a slice is not
converted (low). The rest agreed at 2000 cases: merging, strict refusal, the custom merge
function, Delete's cascade, Cut/Copy/Slices, the key map, every getter and Must variant, and
the copies on the way out.

## History

- 2026-09-21 (turn 346): target added at 6ad56fe with three properties and 6 pins.
- 2026-09-25: generators rewritten in combinator style; the properties draw the known shapes
  and six narrow properties were added; three latent model bugs fixed (the strict conflict
  check ran after the removal of the existing subtree, the koanf/5 shape test missed a
  `map[any]any` under a `map[string]any` in a slice in a slice, the Copy/Cut comparisons
  lacked the koanf/2 shape).
