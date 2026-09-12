# priority-queue

[garro95/priority-queue](https://github.com/garro95/priority-queue).

## What is tested

**`tests/double_priority_queue.rs`**
- `double_pq_agrees_with_hashmap_model`: (no doc comment)
- `interleaved_pop_min_pop_max_agree_with_model`: Fully draining a large DoublePriorityQueue by an arbitrary interleaving of pop_min/pop_max must always yield the current minimum/maximum priority of the remaining elements. Hundreds of elements force deep min-max heaps.
- `sorted_vecs_agree_with_reference_sort`: With all-distinct priorities, `into_ascending_sorted_vec` must equal the items sorted by priority, and `into_descending_sorted_vec` must be exactly its reverse.

**`tests/priority_queue.rs`**
- `pq_agrees_with_hashmap_model`: (no doc comment)
- `pop_drains_in_non_increasing_priority_order`: After an arbitrary mix of pushes and priority changes (which exercise bubble_up/up_heapify at deep positions), fully draining the queue with `pop` must yield priorities in non-increasing order and return every element exactly once. Hundreds of elements force deep heaps.
- `into_sorted_vec_sorted_by_priority`: `into_sorted_vec` must return every pushed item exactly once, ordered from the highest associated priority to the lowest.
- `push_increase_takes_max`: Documented `push_increase` contract: the resulting priority is the max of the old and offered priorities; returns None when absent, Some(old) when increased, Some(offered) when not increased.
- `push_decrease_takes_min`: Documented `push_decrease` contract: the resulting priority is the min of the old and offered priorities; returns None when absent, Some(old) when decreased, Some(offered) when not decreased.
- `iter_yields_exact_contents`: `iter` visits exactly the (item, priority) pairs currently in the queue, each once (order is documented as arbitrary).
- `from_iter_equals_push_loop`: Building a queue with `FromIterator` (possibly with repeated items, where the docs say the item is updated so the last pair wins) is equivalent to pushing every pair in order, and the built queue is a valid heap: draining it yields non-increasing priorities.
- `serde_json_roundtrip_preserves_queue`: serde round-trip: deserializing a serialized queue yields an equal queue whose heap is valid (drains in non-increasing priority order).

## Oracles

## Not tested

## History

- 2025-10-15: predecessor base commit `95499ebb38f2` (Prepare version).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/priority-queue.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
