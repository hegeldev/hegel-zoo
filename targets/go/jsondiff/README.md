# jsondiff

[wI2L/jsondiff](https://github.com/wI2L/jsondiff) computes RFC 6902 JSON patches between two
Go values or two JSON documents (`Compare`, `CompareJSON`, `CompareWithoutMarshal`, a reusable
`Differ`), with options: `Factorize` (moves and copies instead of remove/add pairs),
`Rationalize` (replace a whole value when that is shorter than the operations), `Equivalent`
(arrays equal up to order), `LCS` (longest-common-subsequence array diff), `Invertible`
(a `test` before each `remove`/`replace` so `Patch.Invert` can reverse it), `Ignores`,
`SkipCompact`, `InPlaceCompaction`, `MarshalFunc`/`UnmarshalFunc`; and RFC 7386 merge
patches (`MergePatch`, `MergePatchJSON`). About 2 000 lines, MIT, pinned at `cc66287`
(v0.7.1, 2026-04-01). README and LICENSE are the project documents and say nothing about
AI-written code. The package's own tests are tables plus a few fuzz seeds.

## Build

`go test -count=1 -run TestHegel -v .` in the module root. The patch adds `hegel_test.go`
(generators, the model applier, the properties) and `hegel_pins_test.go` (one plain test per
bug) and requires `hegel.dev/go/hegel v0.6.33` and `github.com/evanphx/json-patch/v5 v5.9.11`
in go.mod.

## Oracles

- **The RFC 6902 model applier**, written from the RFC: pointers per RFC 6901 (`~0`, `~1`,
  `-` only for `add`), `add` inserts or replaces, `remove`/`replace` require the member,
  `move` is remove-then-add and may not move into its own child, `copy`, `test` by deep
  equality. A patch's meaning is what this applier makes of it.
- **evanphx/json-patch v5**, an independent applier, used where it is dependable (see
  Accepted differences): both documents are containers, no operation addresses the root or
  a key that is empty or `-`, no `test` of `null`. Its `MergePatch` judges merge patches when
  the source is an object and the target contains no `null`.
- **RFC 7386 model**: a merge patch applied by the RFC's algorithm must give the target, the
  expected patch (recursive for object-object pairs, `null` for removed keys, the target
  value otherwise) must equal the package's, and the patch is `null`-free except for
  removals.
- **Documented contracts**: `Rationalize` keeps the smaller patch; `Invertible` puts a
  `test` at the path before every `remove` and `replace` (a `move` elsewhere may intervene), `Factorize` emits no `copy`, and `Invert`
  reverses such a patch and rejects others; `Ignores` keeps the listed paths out of the
  patch and their values as in the source; `Compare`, `CompareJSON`, `CompareWithoutMarshal`,
  `MarshalFunc` with the standard functions and a reused `Differ` agree; `SkipCompact`
  changes nothing; `Equivalent` makes arrays equal up to order (the result is compared
  after sorting arrays canonically).

## Properties

| Property | Checks |
|---|---|
| RoundTrip | random documents (depth ≤ 3, keys including `""`, `-`, `~`, `a/b`, `"q"`, `\`, numbers as strings) and a mutation of them (replace, delete, add, copy, move, permute, reverse, tweak) or an unrelated document, under random option sets: the patch is well formed for the options, applies to the source with the model and with evanphx to give the target (up to array order under Equivalent), Rationalize never enlarges it |
| Invert | the same pairs: a patch that has the invertible shape inverts, one that has not is rejected, and the inverse applied to the target gives the source (model and evanphx) |
| Ignores | a pair and a random set of object-key paths whose ancestors are objects in both documents: no operation touches an ignored path or a descendant, and the patch applied to the source gives the target with the ignored subtrees as in the source |
| EntryPoints | Compare, CompareWithoutMarshal, Compare with MarshalFunc/UnmarshalFunc, a reused Differ (Reset between uses) and CompareJSON agree; the reverse pair's patch applies to the target and gives the source |
| MergePatch | MergePatchJSON and MergePatch: valid JSON, equal to the RFC 7386 model's patch, applied by the model (and by evanphx) gives the target |

`Known` switches gate the twelve recorded bugs: with Factorize a patch whose `copy` takes a
value that differs from the added one is not applied (jsondiff/1); under Equivalent a
mismatch is skipped when the same pair round-trips without Equivalent (jsondiff/2), and a
patch that does not apply is skipped when a document has an array of two or more elements,
as are the comparisons between entry points (jsondiff/3); the null-target merge patch is not
checked for validity (jsondiff/4); Rationalize is not exercised on documents with keys that
need JSON escaping (jsondiff/5) and its size check is off under Invertible (jsondiff/6);
Invert is not exercised when the root types differ (jsondiff/7) or the patch appends with
`-` (jsondiff/8); a patch with a `test` after a `move` from the same path is not applied
(jsondiff/9), nor is a Factorize+LCS patch that moves array elements (jsondiff/10);
Rationalize is not combined with Equivalent (jsondiff/11) and its size check is off with
Factorize+LCS (jsondiff/12). With them on, the five properties run clean at 1000 cases in about four
seconds (`JSONDIFF_COLLECT=1` records mismatches instead of failing and prints them
shortest-first; `HEGEL_VERBOSE=1` turns on the engine's log).

## Bugs (12; details in bugs.toml)

| id | summary | severity |
|----|---------|----------|
| jsondiff/1 | Factorize copies from an unchanged value whose hash collides with the added one (`[]` for `[[]]`, `null` for `false`, `"1"` for `true`, `["ab"]` for `["a","b"]`): the patch builds the wrong document | high |
| jsondiff/2 | Equivalent gives an empty patch for arrays whose elements' hashes collide (`[null]`/`[false]`, `[[]]`/`[[[]]]`) | medium |
| jsondiff/3 | Equivalent sorts the input arrays in place: the caller's value is reordered, and the patch's paths and test values follow the reordered document, so an invertible patch fails to apply | medium |
| jsondiff/4 | `MergePatchJSON(x, null)` returns no bytes instead of `null` | low |
| jsondiff/5 | Rationalize panics on a key that is a backslash and treats a value under any key that needs escaping as free, producing a larger patch | high |
| jsondiff/6 | Rationalize does not count the `test` it adds under Invertible and so chooses a larger patch | low |
| jsondiff/7 | with differing root types the patch is a bare `add` at `""`; `Invert` turns it into `test` + `remove ""` | medium |
| jsondiff/8 | `Invert` keeps the `-` index of an append (`add` or `move`), producing `test`, `remove` or `move from` at `/-` that RFC 6902 forbids | medium |
| jsondiff/9 | with Factorize, LCS and Invertible the `test` guarding a moved array element comes after the `move` and fails (`[null,[1]]`→`[[1],null]`) | medium |
| jsondiff/10 | Factorize+LCS emit `move`s with wrong array indices: `["x",{},1]`→`[1,{}]` gives a patch that applies and yields `["x",1]` | high |
| jsondiff/11 | Rationalize+Equivalent panics in `findIndex` on about a third of calls (arrays reordered in place before the text is searched by index) | high |
| jsondiff/12 | Rationalize+Factorize+LCS replaces a whole array where the two operations were smaller | low |

How they were found: jsondiff/1 by the round-trip property on the first collect round (a
`copy` from `/x` to `/z` giving `[]` for `[[]]`), then the hasher read and the other
collisions confirmed by probes; jsondiff/2 by the round-trip under Equivalent; jsondiff/3 by
the entry-point property (Compare and CompareJSON disagreeing, differently on each run) and
the model rejecting test operations, then `CompareWithoutMarshal` seen to reorder its
argument; jsondiff/4 by `json.Valid` on the merge patch; jsondiff/5 and 6 by the "Rationalize
never enlarges" check, the panic by a probe on the escaped keys the check pointed at;
jsondiff/7 and 8 by the Invert property on its first rounds (every root type change, every
append); jsondiff/9 and 10 by the entry-point property's reverse patch at 1000 cases (the
wrong result of 10 came out as `[[],[-1.25,"foo","foo!"]]` for `[[],[-1.25,"foo",{}]]`);
jsondiff/11 as a panic under Hegel at 1000 cases, jsondiff/12 by the size check. Everything else agrees with the appliers and the models: LCS diffs without Factorize,
moves between object members, Ignores, the merge patch on ordinary documents, the marshal hooks, `Differ` reuse.

## Accepted differences (not bugs)

- **evanphx/json-patch's limits** are the oracle's, not the package's: it rejects scalar
  root documents and root-path operations, panics on some root replacements, misreads the
  object keys `""` and `-`, fails a `test` of `null`, and prunes `null`s inside arrays when
  merging; those shapes are judged by the model applier alone.
- **InPlaceCompaction** compacts the target in the caller's slice, whose length is not
  changed, so the caller's bytes are no longer the document; documented, not checked.
- **Equivalent** compares array contents up to order, so a patch under it is judged up to
  array order too; the package does not promise which order the replaced value carries.
- **Which equal member a `copy` takes its value from** varies between calls under Factorize
  (the candidates come from a hash table): the entry points are compared by applying their
  patches when they differ only in that.
- **A patch is not promised to be minimal**: a mutation of one element can come back as a
  replace of the containing value, several operations, or a move; only what the patch
  produces is checked (and, under Rationalize, that it is not larger than without).
- **Merge patch with `null`s**: RFC 7386 cannot express setting a member to `null`, so pairs
  where the target has a `null` the source lacks are expected to give a merge patch that
  removes the key, and the check follows the RFC's algorithm.

## Not tested

Performance, the `MarshalFunc`/`UnmarshalFunc` hooks with third-party codecs, and the
`String` rendering of patches beyond its use as JSON.
