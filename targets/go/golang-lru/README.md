# go/golang-lru

[hashicorp/golang-lru](https://github.com/hashicorp/golang-lru) v2 is the most-used Go LRU
cache: a plain LRU (`simplelru.LRU`), its thread-safe wrapper (`lru.Cache`, with
`ContainsOrAdd`/`PeekOrAdd` and eviction callbacks run outside the lock), a 2Q cache
(`TwoQueueCache`, recent/frequent/ghost lists) and an expirable LRU (`expirable.LRU`, TTL with
a background cleanup goroutine, size 0 meaning unlimited). Pinned at `9c13c57` (v2.0.7,
2026-09-03, MPL-2.0; CONTRIBUTING.md's "AI Usage" section welcomes AI-assisted contributions).
The ARC cache is a separate module (`arc/v2`) and is not covered.

## Build

The tests live in a new package directory `hegel/` of the upstream module and use the library
as a black box; `go.mod` gains `hegel.dev/go/hegel`. The run command is
`go test -count=1 -run TestHegel -v ./hegel`. No oracle outside Go is needed.

## Oracle

An LRU cache is modelled as an ordered list of (key, value) pairs, oldest first, with a size
and a log of every entry removed; the 2Q cache as the published algorithm over three such
lists (recent, frequent, ghost) with the library's sizing rules. Keys are drawn from a space
of eight so that sequences revisit them; sizes are 1 to 8 (0 for the unlimited expirable
cache). Each cache is driven by a random sequence of up to forty or fifty operations and
compared with the model after every step.

## Properties

- `TestHegelLRU`: `simplelru.LRU`, `lru.Cache` and `expirable.LRU` (TTL off) against the
  model under Add, Get, Contains, Peek, Remove, RemoveOldest, GetOldest, Purge, Resize (and
  ContainsOrAdd/PeekOrAdd for `lru.Cache`): the result of every operation, Len, Cap, Keys and
  Values in order, Contains and Peek for every key, GetOldest, the cache never above its size,
  and the eviction callbacks in order (as a multiset for Purge), each callback finding the key
  already gone.
- `TestHegelConstructors`: sizes at or below zero refused by the fixed-size constructors and
  mapped to unlimited by the expirable one; 2Q ratios outside [0, 1] refused; a fresh cache is
  empty with the requested Cap.
- `TestHegelTwoQueue`: `TwoQueueCache` against the 2Q model (default and explicit ratios,
  Resize): Len, Cap, Keys (frequent first), Values, Contains, Peek, Get; the cache never
  above its size (independent of the model); and the 2Q promise that a key read twice
  survives a burst of fresh keys.
- `TestHegelConcurrent`: the thread-safe caches under concurrent Add/Get/Peek/Contains keep
  Len within the size and equal to the number of keys, callbacks name known keys.
- `TestHegelExpiry` (four cases, real time, 200ms TTL): entries older than the TTL are hidden
  by Get, Peek, Keys and Values; entries refreshed by Add within the TTL survive; after two
  more TTLs the cache is empty and every entry was reported to the callback exactly once.

## Bugs

Five recorded (bugs.toml), each with a pin, all low. One from the size invariant: a 2Q cache
with a recent ratio of 1 (documented valid) grows to size+1 when a key from the ghost list is
re-added while the recent list is full and the frequent list empty, since `ensureSpace` then
asks the empty frequent list to evict. The rest: Resize accepts a size of zero or below
(the constructors refuse it) and the cache then evicts every key as it is added, reporting
evictions from an empty cache for negative sizes; `New2Q(1)` and any 2Q whose ghost list
rounds to zero entries fail with the inner LRU's error although the documented validation
passes; after `Close` the expirable cache returns expired entries as live; and
`simplelru.LRU.Purge` calls the eviction callback before removing the entry, so the callback
still sees the key and a Remove from it evicts twice.

## Modelled as recorded, not counted

- Purge's callbacks come in map order; the property compares them as a multiset.
- The expirable cache's Len, GetOldest and RemoveOldest count expired entries until the
  cleanup goroutine reaches their bucket (about a hundredth of the TTL); only the documented
  filtering of Get, Peek, Keys and Values is checked, and Len only after three TTLs.
- The 2Q ghost list resized to zero entries keeps nothing (each key added is evicted at once,
  golang-lru/1); the model mirrors that so that Resize can be exercised.
