# diamond-types

[josephg/diamond-types](https://github.com/josephg/diamond-types).

## What is tested

**`src/list/encoding/tests.rs`**
- `hegel_encode_decode_roundtrip`: Encode -> decode round trip: an oplog with arbitrary (possibly concurrent) history, encoded with full fidelity, must decode to an equivalent oplog with identical checkout text.
- `hegel_encode_options_roundtrip`: Generate the encoding *configuration* too, not just the payload: any combination of the EncodeOptions flags must produce bytes which decode without error, and which reproduce the document text whenever the inserted content was stored.
- `hegel_encode_patch_composes`: Incremental save/load: a snapshot plus a patch (encode_from the snapshot's version) must recompose, via decode_and_add, into the full oplog.
- `hegel_corrupt_decode_errors_or_unrolls`: Corrupt an encoded document arbitrarily. Decoding the corrupted bytes must never panic, and when it errors, it must leave the target oplog untouched (matching `error_unrolling` above).
- `hegel_load_from_garbage_never_panics`: Decoding arbitrary garbage must return an error, never panic. (Parse robustness for `ListOpLog::load_from`.)

**`src/list/list.rs`**
- `hegel_local_edits_match_string_model`: Local edits applied through the CRDT must behave exactly like the same edits applied to a naive Vec<char>: same text and same (char) length after every operation.
- `hegel_checkout_reproduces_history`: Time travel: checking out the version recorded after each edit must reproduce the document text as it was at that moment.
- `hegel_agent_assignment_doesnt_affect_content`: Which agent (or how many agents) performed a linear sequence of edits must not affect the resulting document content.

**`src/list/oplog_merge_fuzzer.rs`**
- `hegel_concurrent_merge_converges`: CRDT convergence: any interleaving of concurrent inserts/deletes on 3 replicas, synced pairwise in any order, must converge to identical oplogs and identical document text.
- `hegel_oplog_merge_idempotent`: Merging the same remote operations a second time (or merging an oplog into itself) is a no-op: add_missing_operations_from must be idempotent.
- `hegel_oplog_merge_commutes`: The order in which remote oplogs are merged must not matter: merging b then c gives the same result as merging c then b.

## Oracles

## Not tested

## History

- 2026-05-29: predecessor base commit `ad48b9cced1d` (More cleanups).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/diamond-types.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped ad48b9cced1d → 89ae3a0ab8d9 (2026-09-02, "Added span helpers for i32, fixes tests"; 2.0.0); 2 bug(s) still reproduce; add/add conflicts in src/list/encoding/tests.rs resolved by keeping both sides. 157 tests pass.
