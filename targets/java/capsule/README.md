# capsule

[Capsule](https://github.com/usethesource/capsule) (`io.usethesource:capsule`, 0.7.3-SNAPSHOT, pinned at the main commit
of 2026-09-10, BSD-2-Clause): persistent hash tries — the CHAMP `PersistentTrieSet`/`PersistentTrieMap`, the
specialised small sets and maps (`Set0`..`Set5`, `Map0`..`Map5`) that grow into tries, the heterogeneous set-multimap
`PersistentTrieSetMultimap` (a key maps to one value or to a set of values) and the bidirectional
`PersistentBidirectionalTrieSetMultimap` relation, each immutable and as a transient builder.

The tests are a Maven module `hegel/` added by the patch; `[run] setup` installs the library from the pinned tree
(license-header check, JaCoCo and sources skipped; about half a minute). Upstream has its own junit-quickcheck suite
(59 `@Property` methods over `Abstract{Set,Map,SetMultimap,BinaryRelation}Properties`); its `DEFAULT_TRIALS` is
`SQRT_TRIALS ^ 2`, an XOR, so it runs 102 trials per property rather than the intended 10 000.

## The oracles

- **`java.util.HashSet`/`HashMap` twins** under the same operation script (`SetTest`, `MapTest`): every Capsule set
  and map kind (trie, specialised, `Set.Immutable.of()`) is driven immutably and through transients with insert, remove,
  insertAll/removeAll/retainAll, putAll, union/subtract/intersect against keys whose hash codes are plain, fully
  colliding, differing only above bit 25, or only in the top two bits; after every step size, membership, `get`,
  `hashCode`, `equals` in both directions, the key/value/entry views, all iterators, streams, `toArray`, the previous
  version's immutability, the transients' return values, `freeze()`, serialization and the collectors are compared.
- **A `HashMap<K, HashSet<V>>` model** for the multimaps and the relation (`MultimapTest`): insert/put/remove of tuples,
  value sets and key sets, `complement`, tuple count vs distinct keys, `get`, `containsEntry/Value`, the views and
  iterators, equality and hash against the same tuples inserted in another order and into the other kind, the
  relation's `inverse()` against the inverted model and `inverse().inverse()`, transients and `freeze()`.
- **The java.util contracts** (`MiscTest`): iterators end in `NoSuchElementException`, immutable views refuse every
  mutator with `UnsupportedOperationException` and stay unchanged, nulls are refused atomically, frozen transients refuse
  every mutator, the factories (`of`, `setOf`, `mapOf`, `transientOf`, the interface statics) agree with the builders.
- Two read-only surveys of the source (sets/maps/utilities and the multimap family), each verifying its suspicions in
  jshell, fed the shapes; a differential fuzz of the core trie operations found no fault in insert/remove/collision
  handling, canonical form, depth-7 tries, transient ownership or serialization.

## What the properties found

The 14 recorded bugs (`bugs.toml`, pinned in `CapsulePinsTest`) are bookkeeping and contract faults around a sound
core: the multimap's cached `size()` goes wrong when a set of values is inserted onto a key holding one value (and
`equals` with it), the bidirectional relation's `__put` desynchronises its two sides, `Set.Immutable.of(a, a)` builds a
set holding the element twice, a transient map is left unusable by `__put(key, null)`, `entrySet().contains` tests keys,
the specialised `Map.Entry` compares classes, transient mutators misreport their return values (`__put` of an equal value
in a collision node, `__putAll`, the multimap `__put`, the relation's `__insert(key, set)`), and the iterators break the
`Iterator`/`ListIterator` contracts (`ArrayView`, transient `remove()`, the specialised iterators' end and `get()`).

Design choices the tests respect rather than record: `Set.Immutable.of()`/`Map.Immutable.of()` return tries, not
specialised collections; `PersistentTrieSet.__insertAll`/`__removeAll`/`__retainAll` and `__putAll` return a new instance
even when nothing changed while the specialised versions return `this`; the specialised sets replace a re-inserted
equal element by the argument; nulls are refused with `NullPointerException`; `SetMultimap.size()` counts tuples and
`keySet()` is a plain view; `complement(other)` yields the tuples of `other` absent from `this`; `union`/`intersect` on
multimaps and `__remove(key)`/`__put(key, set)` on the immutable relation throw `UnsupportedOperationException`; the
transient relation's `inverse()` is a live view; bulk operations with nothing to do on a frozen transient return false
instead of throwing; `Collection.removeIf` with nothing to remove does not throw on an immutable (the JDK default).
