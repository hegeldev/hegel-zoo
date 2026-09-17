# ycrdt

[y-crdt/y-crdt/](https://github.com/y-crdt/y-crdt/).

## What is tested

**`src/alt.rs`**
- `hegel_merge_updates_v1_equivalent_to_sequential_apply`: Property: applying the result of [merge_updates_v1] is equivalent to applying the merged updates one after another. Evidence: docs say the returned binary "is a combination of all input `updates`, compressed".
- `hegel_state_vector_from_update_matches_doc`: Property: the state vector extracted from a full-state update via [encode_state_vector_from_update_v1] equals the state vector of the document that produced the update.
- `hegel_diff_updates_v1_completes_prefix`: Property: for a document whose history is split at an arbitrary point, applying the prefix update followed by [diff_updates_v1] of the full update against the prefix state vector reproduces the full document. Evidence: diff_updates_v1 docs - the result "contains all changes from A which have not been observed by B (based on its state vector)".

**`src/doc.rs`**
- `hegel_full_state_update_roundtrip`: Property: a full-state update (v1 or v2) applied to a fresh document reproduces the source document's state exactly. Evidence: the lib.rs quick-start documents this encode-diff/apply-update synchronization flow.
- `hegel_apply_update_idempotent`: Property: applying the same update twice is the same as applying it once. Evidence: state vectors describe already-observed blocks precisely so that redundant (re-delivered) updates are ignored - a core CRDT contract.

**`src/encoding/mod.rs`**
- `hegel_encoding_any_roundtrip`: Property: any [Any] value round-trips through lib0 encoding (`Any::encode` / `Any::decode`) unchanged.
- `hegel_encoding_primitives_roundtrip`: Property: every lib0 primitive write operation is read back unchanged by the corresponding read operation (hegel port of `encoding_prop`).

**`src/lib.rs`**
- `hegel_uuid_v4_format`: Property: [uuid_v4_from] produces a well-formed v4 UUID for any input. Evidence: doc comment references RFC 4122 section 4.4 (random UUIDs have the version nibble fixed to `4` and the variant nibble in `8..=b`).

**`src/state_vector.rs`**
- `hegel_state_vector_encode_decode_roundtrip`: Property: a [StateVector] round-trips through both v1 and v2 lib0 encodings. Evidence: `Encode`/`Decode` impls above; `StateVector: Eq`.
- `hegel_state_vector_merge_commutative`: Property: [StateVector::merge] is commutative. Evidence: merge docs say the highest clock value wins per client - `max` is commutative.
- `hegel_state_vector_merge_upper_bound`: Property: merging state vectors produces an upper bound of both inputs (per merge docs: "a highest of these two is considered to be the most up-to-date"), observable through `PartialOrd`.

**`src/types/array.rs`**
- `hegel_array_concurrent_convergence`: Property (CRDT convergence): concurrent insert/remove operations on [ArrayRef] replicas converge to the same content once all peers exchanged updates, regardless of operation interleaving and exchange order. Evidence: lib.rs documents that concurrent inserts are ordered deterministically by [ClientID]; the seeded `fuzzy` test checks the same property via `run_scenario`.
- `hegel_array_matches_vec_model`: (no doc comment)

**`src/types/map.rs`**
- `hegel_map_concurrent_convergence`: Property (CRDT convergence): concurrent insert/remove operations on [MapRef] replicas converge to the same entries once all peers exchanged updates. Keys are drawn from a small set to force concurrent updates of the same entry - lib.rs documents that such conflicts are resolved deterministically (peer with the higher [crate::block::ClientID] wins).

**`src/types/text.rs`**
- `hegel_text_concurrent_convergence`: Property (CRDT convergence): concurrent insert/remove operations performed on multiple replicas converge to the same text once every pair of peers has exchanged updates, regardless of operation interleaving and exchange order. Evidence: this is the core contract of the library (lib.rs quick start); the existing seeded `fuzzy` test checks the same property via `run_scenario`.
- `hegel_text_matches_string_model`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-07-13: predecessor base commit `67b0513fe6cf` (Merge pull request #638 from Horusiath/release-v0.27.3).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/ycrdt.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped 67b0513fe6cf → 37dfed7eaeed (2026-09-09, "Merge pull request #644 from weironz/harden-untrusted-decode"; 0.27.4); 0 bug(s) still reproduce. 399 tests pass.
- 2026-09-17: base bumped 37dfed7eaeed → ba8f2d3eab9e (2026-09-17, "Merge pull request #658 from Horusiath/fix/branch-by-val-eq"; 0.27.4); 0 bug(s) still reproduce. 399 tests pass.
- 2026-09-17: base bumped ba8f2d3eab9e → 22890d631a1c (2026-09-17, "Merge pull request #659 from kavinsood/fix/ywasm-utf16-offset-docs"; 0.27.4); 0 bug(s) still reproduce. 399 tests pass.
- 2026-09-17: base bumped 22890d631a1c → 1610ff2b1714 (2026-09-17, "Merge pull request #663 from y-crdt/release-v0.28.0"; 0.28.0); 1 bug(s) still reproduce. 400 tests pass.
