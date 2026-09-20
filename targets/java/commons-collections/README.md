# commons-collections

[Apache Commons Collections](https://github.com/apache/commons-collections) (`org.apache.commons:commons-collections4`;
the pom carries 4.6.1-SNAPSHOT after the 4.5.0 release; pinned at the master commit of 2026-09-07): some 80 000 lines of
collection types and utilities beyond `java.util` — bags and multisets, bidirectional maps, the PATRICIA trie, ordered,
LRU, multi-key, flat and case-insensitive maps, bloom filters, list and queue variants, iterators, comparators, and the
`CollectionUtils`/`ListUtils`/`SetUtils` toolbox. This target covers the parts with a crisp oracle in `java.util` or in
a formula; the iterators, functors, multimaps, splitmap and properties packages are not exercised.

The tests are a Maven module `hegel/` added by the patch; `[run] setup` installs the library from the pinned tree into
the local Maven repository (Javadoc, sources, checkstyle, PMD, SpotBugs, RAT, japicmp, CycloneDX, the enforcer, animal
sniffer and signing skipped; about 20 s). The ASF Generative Tooling Guidance applies to contributions (disclosure), the
PR template asks for it, nothing stricter.

## The oracles

- **`java.util` twins under the same operation script**: `TreeMap` for `PatriciaTrie` and its ordered/prefix views (a
  prefix view is the `TreeMap` filtered by `startsWith`), `LinkedHashMap` (access-ordered with a size cap for `LRUMap`)
  for the maps, `ArrayList` for `TreeList`/`SetUniqueList`/`GrowthList`, `ArrayDeque` with a capacity rule for
  `CircularFifoQueue`, a `Map<List<K>, V>` for `MultiKeyMap`, a forward/inverse pair kept by the documented `put` rule
  for the bidi maps, `Map<E, Integer>` counts for bags and multisets.
- **Formulas and set models**: `CollectionUtils`' set operations against per-element cardinality arithmetic
  (`max`/`min`/`|a-b|`/`max(0, a-b)`), the Myers diff (`SequencesComparator`) against a dynamic-programming LCS and by
  replaying the script, bloom filters against the set of indices produced by the enhanced-double-hashing recurrence
  (`h1 - i*h2 + T(i) mod m`, verified against the hasher first) with the `Shape` estimates recomputed from the class
  Javadoc's formulas.

## Properties (`CommonsUtilsTest`, 3; `BloomFilterTest`, 5; `TrieTest`, 1; `MapsTest`, 5)

- `collectionOpsRespectCardinality`: `union`/`intersection`/`disjunction`/`subtract`/`retainAll`/`removeAll`,
  `isSubCollection`/`isProperSubCollection`/`isEqualCollection`/`containsAll`/`containsAny`/`cardinality`/
  `getCardinalityMap`, `collate` (with and without duplicates), `partition`, `permutations`, `ListUtils`'
  `intersection`/`sum`/`subtract`/`union`/`retainAll`/`removeAll`/`isEqualList`, and the four live `SetUtils` views.
- `bagsAndMultiSetsCountLikeTheModel`: `HashBag`, `TreeBag`, `HashMultiSet`, `TreeMultiSet` under add/remove (one or n
  copies), `setCount`, `removeAll`/`retainAll` (the bag's cardinality-respecting "violations" and the multiset's plain
  semantics), `containsAll`, iterator removal, `uniqueSet`, `entrySet`, sorted order and `first`/`last`, and equality
  with a copy built in reverse.
- `myersScriptIsShortestAndTransformsTheSequence`: the edit script turns the first sequence into the second,
  `getLCSLength` equals the LCS, `getModifications` equals `|a| + |b| - 2·LCS`; `ListUtils.longestCommonSubsequence` for
  lists and char sequences.
- `hasherIndicesFollowTheRecurrence`, `filtersMatchTheSetModel`, `countingFilterCountsLikeTheModel`,
  `layeredFilterTracksItsLayers`, `shapeArithmeticMatchesTheFormulas`: `EnhancedDoubleHasher` against the recurrence
  (k values, range, determinism, `uniqueIndices`, early exit, bit-map/index/cell conversions); `SimpleBloomFilter`,
  `SparseBloomFilter`, `ArrayCountingBloomFilter` and a `LayeredBloomFilter` merged from hashers, index arrays, bit maps
  and other filters against the index set (`cardinality`, `isEmpty`, `isFull`, `contains` in all four forms,
  `asBitMapArray`, `processIndices`, `copy` independence, `clear`, `estimateN`/`estimateUnion`/`estimateIntersection`,
  `SetOperations`); the counting filter's cells, `getMaxInsert`, validity after underflow; layer advance and cleanup
  rules (`advanceOnCount`, `advanceOnPopulated`, `onMaxSize`), `get(depth)`, `find`, `flatten`; `Shape.fromNP/fromNM/
  fromNMK/fromPMK/fromKM`, `getProbability`, `estimateN`, `estimateMaxN`, `isSparse`, the documented refusals.
- `trieMatchesTreeMap`: keys over a small alphabet including the empty string, NUL, non-ASCII and a surrogate pair;
  put/remove/get/entry-iterator removal, `firstKey`/`lastKey`, `nextKey`/`previousKey` (present keys only, as
  documented), `select`, `headMap`/`tailMap`/`subMap` (entries, order, bounds, inverted range), `prefixMap` (entries,
  liveness, iterator removal), the ordered map iterator both ways, serialization, `equals`/`hashCode`.
- `mapsMatchJavaUtil`: `HashedMap`, `LinkedMap` (with `asList`/`get(int)`/`indexOf`), `ListOrderedMap` (with
  `keyList`/`valueList`/`put(index, k, v)` under the documented "relative to the original state" rule), `Flat3Map` (across
  the flat/delegate switch), `CaseInsensitiveMap`, `LRUMap` (`get(k, false)`, `isFull`, eviction order) under
  put/remove/get/putAll/iterator removal/entry `setValue`/clear; `multiKeyMapMatchesAListKeyedMap` (arities 2–5,
  `removeMultiKey`, prefix `removeAll`, `MultiKey` access); `bidiMapsKeepTheInverse` (`DualHashBidiMap`,
  `DualLinkedHashBidiMap`, `DualTreeBidiMap`, `TreeBidiMap`: put/remove/removeValue/iterator `setValue`, both directions,
  `getKey`, sorted orders, `nextKey`/`previousKey` of present keys, read-only sub-map views); `listsMatchArrayList`
  (`TreeList` incl. `addAll` of another `TreeList`, list-iterator removal/set, backward walks; `SetUniqueList`'s add/set
  rules and `asSet`; `GrowthList`'s padding); `ringQueueMatchesArrayDeque` (`CircularFifoQueue`: overwrite when full,
  `get(i)`, `poll`/`remove`/`element`/`peek`, iterator removal after wrap-around, `isAtFullCapacity`).

Known-bug shapes are skipped, never worked around: `LRUMap` gets no null keys (1); bidi keys are small cached
`Integer`s (2); `nextKey`/`previousKey` are asked for present keys only (3); the `DualTreeBidiMap` sub-map views are read
only (4); `MultiKeyMap` is not layered over an `LRUMap` (5); bloom shapes have at least two bits (8) and the layered
filter's `uniqueIndices()` is not compared (7); `lastKey()` is not asked of a trie holding only `""` (10) nor of a
`headMap` of an empty trie (9); prefix sub-views are not taken (11); the prefix view is never emptied through its
iterator (12); the trie's map iterator is not walked backwards after a removal (13); the empty key is not put after a
removal (14).

## Not tested

The `iterators`, `functors`, `multimap`, `multiset` decorators, `splitmap`, `properties`, `keyvalue` (except `MultiKey`
through `MultiKeyMap`) and `sequence.ReplacementsFinder` classes; `PassiveExpiringMap`, `ReferenceMap`, `StaticBucketMap`,
`CompositeMap`/`CompositeCollection`, `SingletonMap`; `CursorableLinkedList`, `NodeCachingLinkedList`, `LazyList`; the
`Unmodifiable*`, `Predicated*`, `Transformed*`, `Synchronized*` decorators; `TrieUtils`, `IterableUtils`,
`IteratorUtils`, `MapUtils`, `QueueUtils`; concurrency.

## Bugs found

| id | severity | summary |
|---|---|---|
| commons-collections/1 | medium | a null key that enters an `LRUMap` through an eviction is unreachable, and a second `put(null)` adds a second entry |
| commons-collections/2 | low | dual bidi maps: `setValue` of the entry's own value throws after the key was re-put with an equal key object |
| commons-collections/3 | low | `DualTreeBidiMap.previousKey` finds a lower key for an absent key while `nextKey` returns null |
| commons-collections/4 | medium | a `put` through a `DualTreeBidiMap` sub-map view of a value mapped outside the view leaves the value twice |
| commons-collections/5 | low | `MultiKeyMap`'s multi-key `get` bypasses the decorated `LRUMap`'s recency |
| commons-collections/6 | low | `ArrayCountingBloomFilter.clear()` leaves the filter invalid |
| commons-collections/7 | low | `LayeredBloomFilter.uniqueIndices()` repeats indices across layers |
| commons-collections/8 | low | `EnhancedDoubleHasher` leaves the range for a one-bit shape with k ≥ 4, so every merge throws |
| commons-collections/9 | low | `headMap(x).lastKey()` of an empty `PatriciaTrie` returns null |
| commons-collections/10 | low | `PatriciaTrie.lastKey()` throws when the only key is `""` |
| commons-collections/11 | medium | sub-maps of a `PatriciaTrie` prefix view include entries outside the prefix |
| commons-collections/12 | low | emptying a prefix view through its iterator throws `NullPointerException` |
| commons-collections/13 | low | after `remove()` the trie's map iterator has a previous entry with a null key |
| commons-collections/14 | medium | after any removal, `put("", v)` hides every other trie entry from iteration while `size()`/`get` still see them |

Observed, not recorded: `ListUtils.intersection` keeps one copy of each element present in both lists (a `HashSet` of the
smaller list) while `CollectionUtils.intersection` respects cardinality — upstream's tests fix the list behaviour, and
`ListUtils.sum` is defined in its terms; `Bag.add(e, 0)` returns false and bumps `modCount`; `SimpleBloomFilter` keeps a
stale cached `cardinality()` (and `isEmpty()` true) after a merge that threw half-way, and `SparseBloomFilter` keeps the
out-of-range index, so `asBitMapArray()` then throws — the class Javadoc declares such filters invalid; `estimateIntersection`
throws when only the union is full (documented); `LayeredBloomFilter.processBloomFilters`' Javadoc says "most recent
first" while the layers come oldest first; `prefixMap("")` and `prefixMap(null)` return the trie itself; a prefix view's
`containsKey(null)` throws `NullPointerException` while the trie's returns false; overwriting a value during iteration
throws `ConcurrentModificationException` on `PatriciaTrie` (a value `put` counts as a modification); the entry returned by
the trie's iterator is the node itself and has a null key after `remove()`; `CircularFifoQueue.isFull()` is always false by
documentation while `isAtFullCapacity()` reports the capacity; `SetUniqueList.set(i, e)` shrinks the list when `e` was
elsewhere (documented); `LRUMap.get` during iteration throws `ConcurrentModificationException` (documented).

## History

- 2026-09-16: created (turn 182) at 21d6821190e0 (4.6.1-SNAPSHOT of 2026-09-07, after 4.5.0); 14 bugs.
- 2026-09-20: base bumped 21d6821190e0 → e68a90bcbe55 (2026-09-19, "Bump github/codeql-action/* from 4.37.9 to 4.38.1"; 4.6.1-SNAPSHOT); 14 bug(s) still reproduce. 14 tests pass.
