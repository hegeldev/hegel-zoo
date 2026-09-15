# immutable

[immutable-js/immutable-js](https://github.com/immutable-js/immutable-js) (npm `immutable`):
persistent List, Map, OrderedMap, Set, OrderedSet, Stack, Record, lazy Seq/Range/Repeat, value
equality (`is`, `hash`) and a functional API over plain objects. Pinned at 5.1.9 (686b8baf,
2026-09-02). Upstream's own jest suite already uses fast-check for a few List/Map/Range
properties against arrays. The tests are `test/hegel.test.mjs` with the zoo's harness
`test/hegel-zoo.mjs`.

The package publishes a rollup bundle and ships no build in the repository, so the setup installs
rollup with upstream's plugins (TypeScript, commonjs, json and buble — buble turns the classes
into ES5 functions, which is what lets `List([...])` be called without `new`) at the lockfile's
versions under `test/tools/` (they are devDependencies, so a root `npm install --omit=dev` would
skip them) and bundles `src/Immutable.js` to `test/.hegel/immutable.mjs` with
`test/tools/hegel-rollup.config.mjs`; the tests import that bundle.

## What is tested

The oracles are models on plain arrays under the documented equality: a List is an array; a Map
an array of `[key, value]` pairs where keys compare like `is` (primitives by SameValueZero, value
objects by `equals`, Immutable collections by value, other objects by identity); a Set an array
of unique keys. Keys and values mix small numbers (0, -0, NaN, 1e21), short strings (`"1"` next
to `1`), booleans, null, undefined, pooled plain objects, Lists and Maps of primitives, and a
`ValueObject` class whose `hashCode` maps six keys onto two buckets so hash collisions are
constant. Collections are usually small; 15% of Lists have up to 1500 items (past the 32-item
tail and the 1024-item trie level) and 10% of Maps/Sets up to 300 keys.

- **TestHegelListMatchesTheArrayModel** — up to 12 operations drawn from push/pop/unshift/shift,
  set (negative indices, indices past the end and before the start grow the List), delete,
  insert, splice, slice, setSize, reverse, concat, sort (default comparator, stable),
  sortBy, map, filter, take, skip, update, withMutations, asMutable/asImmutable, zip/zipAll,
  interleave, flatten(true); earlier Lists never change; then get/has/first/last,
  indexOf/lastIndexOf/includes, count/some/every/find*, reduce/reduceRight, min/max, groupBy,
  partition, the whole-List slice identity, toSeq/Seq equality, toSet/toMap, join, toJS, and
  `is`/`equals`/`hashCode` against a fresh List of the same values.
- **TestHegelMapsMatchTheEntryListModel** — Map or OrderedMap: set (also with an equal key
  built afresh), delete, update (the updater sees the current value), merge (Map, pairs, object),
  mergeWith, deleteAll, clear, filter, map, mapKeys, withMutations, sort (an OrderedMap;
  stable for an OrderedMap source), flip; OrderedMap keeps insertion order with re-sets in
  place; get/has; equality with the same entries in another order (Map yes, OrderedMap no) and
  equal hashCodes; a Map is never `is` an OrderedMap; keySeq/valueSeq/entrySeq agree.
- **TestHegelSetsMatchTheUniqueListModel** — Set or OrderedSet: add, delete, union, intersect,
  subtract, map, filter, withMutations, clear, sort (an OrderedSet); has/includes,
  isSubset/isSuperset, equality and hashCode, `Set.union`/`Set.intersect` statics.
- **TestHegelRangeRepeatSeqStackAndFromJS** — `Range(start, end, step)` in both directions
  against a loop (get, includes, indexOf, slice, reverse), `Range(start, Infinity).take`,
  `Repeat`; a `Seq(array).filter().map()` does no work until used and `get(i)` runs the filter
  up to the i-th hit and the mapper once (the docs' example); `cacheResult`; Stack
  push/pop/unshift/shift/pushAll/clear/peek against an array; `fromJS(json).toJS()` is the JSON,
  `is(fromJS(a), fromJS(b))` iff deep-equal with equal hashes, the reviver sees every collection;
  `hash` is a 32-bit integer consistent with `is` (0/-0, NaN, "1" vs 1).
- **TestHegelRecordsAndTheFunctionalApi** — a Record factory with defaults and a name:
  property access, set/remove (restores the default)/merge/mergeDeep, equality and hashCode,
  toJS, `getDescriptiveName`, unknown keys ignored; `getIn`/`hasIn`/`setIn`/`updateIn`/`removeIn`
  and `get`/`set`/`has`/`remove` on nests of plain objects/arrays and Immutable collections
  (inputs unchanged), `merge`/`mergeDeep` on plain objects against their Map counterparts.

Not covered: `Seq.Keyed` algebra beyond conversions, `Range` with negative or fractional steps
(undocumented; a negative step is read as its magnitude), `take` with a negative amount
(returns an empty List), `mergeDeepWith`, `Collection.Indexed` on strings, `toJSON`/`toString`
formats.

## Bugs

None found at this pin: 6 collect rounds (300–2000 cases per property) and the clean run agree
with the models everywhere. Two documentation nits: the `Range` doc comment still says `end`
"defaults to infinity" although 5.0 made it required (CHANGELOG: "Range function needs at least
two defined parameters"; `Range(0, Infinity)` is the infinite range), and `partition`'s pair is
`[falsy, truthy]`, which the docs do say but the reverse of what most libraries return.
