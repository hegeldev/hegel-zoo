# btree

[tidwall/btree](https://github.com/tidwall/btree) is a B-tree package with four faces: the
generic ordered `Map[K, V]` and `Set[K]`, `BTreeG[T]` with a caller's `less` (thread-safe
unless `Options.NoLocks`, path hints for clustered keys, `DeleteRange`, `DeleteAscend`,
copy-on-write `Copy`/`IsoCopy`), and the older `interface{}`-typed `BTree`. All offer
ordered scans in both directions from a pivot, array-like `GetAt`/`DeleteAt`, `Min`/`Max`
and `PopMin`/`PopMax`, bulk `Load` of pre-sorted items, and iterators with
`Seek`/`First`/`Last`/`Next`/`Prev`. About 3 800 lines, MIT, pinned at `34be4b8` (v1.8.1,
2026-05-16). README and LICENSE are the project documents and say nothing about AI-written
code. The package's own tests are large example-based suites.

## Build

`go test -count=1 -race -run TestHegel -v .` in the module root: the race detector is part
of the check (btree/1 is a data race, so its pin fails only under `-race`). The patch adds
`hegel_test.go` (the model, the cursor model and the properties) and `hegel_pins_test.go`
(one plain test per bug) and requires `hegel.dev/go/hegel v0.6.33` in go.mod.

## Oracles

- **A sorted-slice model** of an ordered map (`set`, `get`, `del`, `deleteAt`, `at`,
  `ascend`/`descend` from a pivot, `deleteRange` inclusive or exclusive of the upper bound)
  applied to `Map`, `Set`, `BTreeG` and `BTree` in lock step; copies get a cloned model.
- **A cursor model** of the iterators written from their documentation and upstream's own
  tests: `First`/`Last`/`Seek` reposition, `Next`/`Prev` step, a step that fails (empty tree,
  past either end) reports false and leaves the cursor where it was; `Key`/`Value`/`Item`
  report the item last stepped to.
- **Documented contracts**: `Len` after every operation; `Height` zero for an empty tree and
  at most `log2(n+1)+1` otherwise (every node has at least two children); `Load` of
  pre-sorted keys equals `Set`, and of unsorted keys too (it falls back); `Copy`/`IsoCopy`
  give an independent tree (copy-on-write: mutations on either side, iterators on one
  side while the other mutates); `Walk` visits the items in order in non-empty slices;
  `DeleteRange` deletes `[min, max)` (or `[min, max]` with `MaxInclusive`) and returns an
  ordered `List` that scans the same twice, or nothing with `NoReturn`; `DeleteAscend`
  visits every item from the pivot in order until `Stop`, deleting those answered `Delete`;
  path-hinted operations equal the plain ones with a hint reused across random keys; the
  `BTree` wrapper returns nil where `BTreeG` returns false; a released iterator can be
  re-initialised with `Init`; `BTreeG` and `BTree` are thread-safe (the race detector on
  concurrent writers and readers).

## Properties

| Property | Checks |
|---|---|
| MapModel | up to four `Map[int,string]` trees (degrees 0/1/2–8/32, the zero value, copies) through Set/Load/Delete/DeleteAt/PopMin/PopMax/Get/GetAt/Ascend/Descend with early stops/Clear/bursts of deletions, an optional pre-sorted load and a bulk of up to 600 random keys; every tree against its model: Len, Keys, Values, KeyValues, Scan, Reverse, Min, Max, GetAt at every index, Height |
| MapIterator | a map of up to 70 keys (optionally a copy of a mutated original, or the mutated original itself) walked by a random sequence of First/Last/Seek/Next/Prev against the cursor model, `Key`/`Value` after each step |
| SetModel | `Set[int]` through Insert/Load/Delete/DeleteAt/PopMin/PopMax/Contains/Ascend/Descend; Keys, Scan, Reverse, GetAt, Min, Max, Height, the iterator, and a Copy surviving Clear |
| BTreeGModel | up to four `BTreeG[item]` trees (random degree, with and without locks, copies) through Set/SetHint/Load/Delete/DeleteHint/Get (four forms)/DeleteAt/PopMin/PopMax/Ascend/Descend (plain and hinted)/DeleteRange (both bounds, both options, `DeleteRangeReuse`)/DeleteAscend with random actions/Clear, iterators with Seek and SeekHint, Release and Init; Items, Walk, Scan, Reverse, Height, Min, Max, GetAt, the iterator |
| AnyBTree | the `BTree` wrapper (New, NewNonConcurrent, NewOptions) through the same operations, `Seek`, `Ascend(nil)`, `Walk`, a Copy surviving Clear |
| ConcurrentWriters | 2–6 goroutines inserting disjoint keys (some hinted) and deleting their own, 0–3 readers scanning and iterating meanwhile; the final tree against the model, under the race detector |

`Known` switches gate the two recorded bugs: the readers do not call `Len` (btree/1), and
the iterator properties stop a case when the implementation's leftover at-start/at-end
flags differ from the documented state (btree/2). With them on, the six properties run
clean at 1000 cases in about six seconds (`BTREE_COLLECT=1` records mismatches instead of
failing and prints them shortest-first; `HEGEL_VERBOSE=1` turns on the engine's log).

## Bugs (2; details in bugs.toml)

| id | summary | severity |
|----|---------|----------|
| btree/1 | `BTreeG.Len`/`BTree.Len` read the count without the lock: a data race on a type documented thread-safe | low |
| btree/2 | `Seek` and `Last` keep the at-start/at-end flags of an earlier failed `Prev`/`Next`; after a later failed step the iterator returns the second item from the wrong end (`First, Prev, Seek(past the end), Next` yields an item) | low |

How they were found: btree/1 by the concurrent-writers property under `go test -race` on
its first run (the readers called `Len`); btree/2 by the iterator property once the cursor
model treated `Seek` as repositioning, reduced by a probe to a four-step sequence. The trees
themselves held up: 8 000 random operation sequences over all four types, deep trees from
bulk loads, copies mutated on both sides, range deletions and hinted operations all agreed
with the model, and nothing else raced.

## Accepted differences (not bugs)

- **A failed step keeps the cursor**: after `Next` fails at the last item, `Prev` returns
  the second-to-last (upstream's tests assert this), and symmetrically for `Prev` then
  `Next`. Undocumented but consistent, so the cursor model follows it. The same convention
  applied to a `Seek` past the end makes the following `Prev` return the second-to-last item
  rather than the last; that is noted here rather than recorded, since nothing documents
  where a failed `Seek` leaves the cursor.
- `Map` and `Set` are not documented thread-safe and are not exercised concurrently.
- `Ascend`/`Descend` with a callback that returns false at once still deliver the first
  item (the callback decides after seeing it), as documented by the examples.
- `Load` of an item not greater than the current maximum is an ordinary `Set`; the
  package documents `Load` for pre-sorted items only.

## Not tested

Performance and the path hints' effect on it, `Generic` (the deprecated alias of
`BTreeG`), and behaviour when a `less` function is inconsistent.
