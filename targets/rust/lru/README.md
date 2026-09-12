# lru

[jeromefroe/lru-rs.git](https://github.com/jeromefroe/lru-rs.git).

## What is tested

**`src/lib.rs`**
- `test_lru_agrees_with_vecdeque_model`: Property 1 (stateful model test): a random sequence of cache operations applied to both `LruCache` and a VecDeque-based model must agree on every return value and, after every step, on the full MRU->LRU order.
- `test_put_over_capacity_evicts_exactly_lru`: Property 2: a `put` of a new key into a full cache evicts exactly the least-recently-used entry and nothing else.
- `test_get_moves_to_mru_but_peek_preserves_order`: Property 3: `get` moves exactly the touched key to the MRU position (preserving the relative order of all other keys), while `peek` leaves the recency order completely unchanged.
- `test_absent_key_ops_are_noops`: Property 4: operations on an absent key return None/false and do not perturb the cache contents or recency order.
- `test_capacity_one_holds_exactly_last_put`: Property 5: a capacity-1 cache always holds exactly the last inserted pair. (Capacity 0 is unrepresentable: `LruCache::new` takes `NonZeroUsize`.)
- `test_resize_evicts_lru_down_to_new_cap`: Property 6: `resize` to a smaller capacity evicts LRU entries down to the new capacity, keeping exactly the most-recently-used prefix; `resize` to a larger capacity keeps everything.
- `test_pop_lru_drains_in_reverse_iter_order`: Property 7: repeatedly calling `pop_lru` drains the cache in exactly the reverse of `iter()`'s MRU->LRU order (sibling-API consistency), even after gets have shuffled the recency order.

## Oracles

## Not tested

## History

- 2026-07-09: predecessor base commit `c6620d1165dd` (Merge pull request #237 from jeromefroe/jerome/prepare-0-18-1-release).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/lru.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-12: base bumped c6620d1165dd → 2504ad088ad7 (2026-09-02, "Merge pull request #245 from jeromefroe/jerome/prepare-0-18-4-release"; 0.18.4); 0 bug(s) still reproduce; add/add conflicts in src/lib.rs resolved by keeping both sides. 112 tests pass.
