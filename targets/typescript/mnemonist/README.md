# mnemonist

[mnemonist](https://github.com/Yomguithereal/mnemonist) (MIT), pinned at `1f2c752` (0.40.4,
2026-04-30): a collection of data structures for JavaScript - heaps, stacks, queues, deques and
circular buffers, vectors and bit vectors, sets, multisets, multimaps, bimaps, sparse sets and
maps, LRU caches, disjoint sets, tries, crit-bit trees, interval, k-d, vantage-point and BK trees,
a Passjoin index, SymSpell, suffix arrays, an inverted index, fuzzy maps, a Bloom filter, and
helpers for sorted-array merges, binary search and typed arrays.

The patch adds `hegel/`: `hegel.test.mjs` (the entry, run with `node --test`), `structures.mjs`,
`indices.mjs`, `pins.mjs`, the shared harness `hegel-zoo.mjs` and `known.mjs` with one switch per
recorded bug. The package is plain CommonJS at the repository root, loaded through
`createRequire`; its one runtime dependency (obliterator) is installed from the lock file and
Hegel under `.hegel/` so `package.json` stays untouched.

## Oracles

Every structure is driven by a random sequence of operations and compared, after each step, with
the obvious implementation of the same abstract type: a sorted array for the heaps, an array for
the stacks, queues, deques, buffers, lists and vectors, an array of bits for the bit sets and
vectors, a `Map` of counts for `MultiSet`, a `Map` in recency order for the LRU caches, a `Map`
and its inverse for `BiMap`, BFS components for `StaticDisjointSet`, the mathematical definitions
for the set algebra, and the exhaustive scan of the same items for every index: all keys with a
prefix for the tries, all intervals containing a point or overlapping an interval, the k nearest
points (by squared distance, ties allowed), all strings within a Levenshtein radius (VP tree, BK
tree, Passjoin), all terms within an unrestricted Damerau-Levenshtein distance that SymSpell's
delete-based indexing can reach, the sorted list of suffixes and the longest common substring,
the documents containing every query token. Failing cases print the operation log so they can be
replayed by hand.

## What is tested

- `hegel.test.mjs` - `Heap`/`MinHeap`/`MaxHeap` and the static heap helpers (`heapify`, `push`,
  `pop`, `consume`, `nsmallest`, `nlargest`), `FixedReverseHeap`; `FixedDeque`, `CircularBuffer`,
  `Queue`, `Stack`, `FixedStack`, `LinkedList` (with typed and plain backing arrays, capacity
  exceeded, overwrite on wrap-around, `from`); the `set` helpers; `MultiSet` (add/set/remove/
  delete/edit, multiplicities, frequencies, `top`, subset relations); `BitSet` and `SparseSet`
  (set/reset/flip, rank/select, iteration); `LRUCache`, `LRUMap` and the `WithDelete` variants
  (eviction order, `setpop`, delete/remove, most-recent-first iteration); `BiMap` and `MultiMap`
  (Array and Set containers); `StaticDisjointSet`.
- `structures.mjs` - `SparseMap`, `SparseQueueSet` (capacities around 256), `BitVector` (push/pop/
  grow, set/reset/flip, rank/select, iteration), `Vector`, the typed vectors and
  `HashedArrayTree` (push/pop/set/grow, bounds), the Fibonacci heaps, `merge`/`unionUnique`/
  `intersectionUnique` on two or more sorted arrays and the binary searches, `BloomFilter` (no
  false negatives, not everything positive), `DefaultMap` (factory receives the key and the
  current size, `autoIncrement`), `getMinimalRepresentation` and `getPointerArray`.
- `indices.mjs` - `Trie`/`TrieMap` with string and array keys (add/set/delete/has/get/find,
  iteration), `CritBitTreeMap` (ordered `forEach`, Latin-1 and wider alphabets),
  `StaticIntervalTree` (closed intervals, custom getters), `KDTree` (1-3 dimensions, `nearestNeighbor`,
  `kNearestNeighbors`, `linearKNearestNeighbors`), `VPTree` and `BKTree` and `PassjoinIndex`
  under Levenshtein, `SymSpell` (three verbosities), `SuffixArray` and `GeneralizedSuffixArray`,
  `InvertedIndex`, `FuzzyMap`/`FuzzyMultiMap`.
- `pins.mjs` - one plain test per recorded bug, asserting the correct behaviour so that it fails
  while the bug exists; listed as expected failures in `target.toml`.

## Known bugs (46, see bugs.toml)

Wrong results: `select` skips the positions of an all-zero word (2), `MultiSet.set` adds instead of
replacing (5), `MultiSet.delete` of an absent key returns true and makes size NaN (6), `edit`
leaves dimension stale or deletes the key (7, 8), `reset` of a clear bit decrements size when bit
31 is set (9), `select` bounded by the length (10), the `WithDelete` LRU caches corrupt their list
(11), `SparseMap.delete` loses a value (12), `SparseQueueSet` of capacity 256 (13), `BitVector.pop`
(14) and iteration over the capacity (15), `HashedArrayTree.pop` (18), `intersectionUnique`'s
shortcut (22), `LinkedList` stale tail (23), the Bloom filter with no hash functions (24),
`getMinimalRepresentation` on mixed signs (25), SymSpell counts and ordering under verbosity 0/1
(26, 27), LRUCache and `Object.prototype` names (28), `setpop` with a falsy key (29), `MultiArray`
past 255 items (34), the suffix array at lengths 1 mod 3 (35) and the longest common substring
of three strings (36), `InvertedIndex.forEach` (37), tries with NUL in keys (41) or tokens named
like prototype properties (42), crit-bit trees beyond Latin-1 (45), `nsmallest(1, [])` (1),
`FixedStack.forEach` (3) and deque `get` (4) beyond the size. Crashes: k-way merges with an empty
array (20) or exactly 256 items (33), unique merges of typed arrays (21), `from` on a Set (31),
the empty interval tree (38), the empty k-d tree (39), `VPTree.nearestNeighbors(0)` (40),
`HashedArrayTree.get(length)` (19). Contract: indices equal to the length accepted (16, 17),
`from` over capacity (30), `FixedReverseHeap` capacity check (32), typings declaring missing
members (43), `Vector.resize` deallocating (44), an undeclared global in the insertion sort (46).

The properties skip a known-bug shape as narrowly as it lets them (`known mnemonist/N` in the
collect output): a check whose result is wrong is counted and skipped, an operation that would
corrupt the structure (5-9, 11, 12, 14) is counted and not applied so the rest of the sequence
stays checked, and a shape that throws or poisons every later step (38-40, 42, 45) is left out of
the generator while its switch in `known.mjs` is on. Only the SparseQueueSet dequeue at capacity
(13) still ends the case, about one in a hundred.

## Conventions followed, not recorded

`FixedStack`, `Stack` iterate and `toArray` from the top; `BitSet`/`BitVector` iteration yields
every bit (0 or 1) in index order and `select` is 1-based; a capacity must be positive, so `from`
of an empty iterable needs an explicit capacity; `MultiSet.top(0)` throws; `MultiSet.add`/`remove`
with a count of 0 are no-ops and negative counts flip the operation; `DefaultMap`'s factory gets
the current size as its second argument; `LRUCache` (object-backed) coerces keys to strings, the
`LRUMap` variants do not; `StaticIntervalTree` intervals are closed; `BKTree` needs an integer
metric; `SuffixArray` on arrays orders tokens by their string form; SymSpell never indexes the
deletes of one-letter words nor the empty string (as the reference), so a pair whose only common
delete is the empty string is unreachable, and its verbosity-2 output is unsorted;
`PassjoinIndex.size` counts duplicates; `GeneralizedSuffixArray.longestCommonSubsequence` computes
the longest common substring; `StaticDisjointSet.union` reads the ranks of the arguments rather
than of their roots (results stay correct, only the heuristic suffers); `SemiDynamicTrie.has` is
unexported and marked TODO in the source.
