# fst

[BurntSushi/fst](https://github.com/BurntSushi/fst).

## What is tested

**`src/bytes.rs`**
- `prop_pack_in_out_hegel`: (no doc comment)

**`src/raw/tests.rs`**
- `prop_fst_bytes_roundtrip`: Property: writing an FST to bytes (Builder::into_inner) and reading it back (Fst::new) is lossless — the read FST has the same length, contents (in order), and per-key outputs, and its checksum verifies.
- `prop_fst_build_deterministic`: Property: building an FST is deterministic — two Builders fed the same sorted unique (key, value) pairs produce byte-identical FSTs. Evidence: construction is a pure function of the input sequence (the node registry hashes node contents, with no randomized seeds), and the CRC32C checksum footer (verify()) only makes sense for a deterministic serialization.
- `prop_builder_insert_order_contract`: Property: Builder::insert enforces its documented contract — keys must be inserted in strictly increasing lexicographic order. Inserting a key smaller than the previous one fails with OutOfOrder, a duplicate fails with DuplicateKey, and a larger key succeeds.

**`tests/test.rs`**
- `prop_set_agrees_with_btreeset`: Property: a Set built from sorted unique keys agrees with a BTreeSet oracle on len/is_empty, iteration order/content, and membership.
- `prop_map_agrees_with_btreemap`: Property: a Map built from sorted unique keys agrees with a BTreeMap oracle on len, iteration (keys and values), get, and contains_key.
- `prop_map_range_agrees_with_btreemap`: Property: range queries (any combination of ge/gt/le/lt/unbounded) return exactly the keys a BTreeMap oracle says are in range, in order.
- `prop_set_union_agrees_with_oracle`: Property: streaming union of several sets equals the BTreeSet union.
- `prop_set_intersection_agrees_with_oracle`: Property: streaming intersection of several sets equals the BTreeSet intersection.
- `prop_set_difference_agrees_with_oracle`: Property: streaming difference is "keys in the first set that are in no other set" (per the OpBuilder::difference docs).
- `prop_set_symmetric_difference_agrees_with_oracle`: Property: streaming symmetric difference yields keys that occur in an odd number of the input sets (per the OpBuilder docs).
- `prop_prefix_search_agrees_with_filter`: Property: searching with Str(query).starts_with() returns exactly the keys with `query` as a byte prefix, in lexicographic order.
- `prop_subsequence_search_agrees_with_filter`: Property: searching with a Subsequence automaton returns exactly the keys containing the query as a byte subsequence.
- `prop_levenshtein_search_agrees_with_naive`: (no doc comment)

## Oracles

## Not tested

## History

- 2024-09-25: predecessor base commit `5907b4739793` (github: add FUNDING).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/fst.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
