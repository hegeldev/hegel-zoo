# slotmap

[orlp/slotmap](https://github.com/orlp/slotmap).

## What is tested

**`src/basic.rs`**
- `hegel_slotmap_model`: (no doc comment)
- `hegel_removed_key_invalid_after_heavy_slot_reuse`: lib.rs promises: "once a key is removed, it stays removed, even if the physical storage inside the slotmap is reused". Hammer a single slot with hundreds of insert/remove cycles (each cycle reuses the freelist head and bumps the slot version) and check the original key never comes back to life.
- `hegel_get_disjoint_mut_agrees_with_key_validity`: Documented on get_disjoint_mut: "All keys must be valid and disjoint, otherwise None is returned". Check both directions, and that the returned references point at (and mutate) the right slots.
- `hegel_slotmap_serde_roundtrip_preserves_validity`: (no doc comment)

**`src/dense.rs`**
- `hegel_dense_slotmap_model`: (no doc comment)
- `hegel_removed_key_invalid_after_heavy_slot_reuse`: ABA safety under heavy reuse of a single slot; see the equivalent test in basic.rs.

**`src/hop.rs`**
- `hegel_hop_slotmap_model`: (no doc comment)
- `hegel_removed_key_invalid_after_heavy_slot_reuse`: ABA safety under heavy reuse of a single slot; see the equivalent test in basic.rs. For HopSlotMap this also churns the vacant-block freelist.

**`src/lib.rs`**
- `hegel_key_ffi_roundtrip`: Promised by from_ffi's docs: "Iff `value` is a value received from `k.as_ffi()`, returns a key equal to `k`." Checked for real keys of varied indices and versions, live and removed, plus the null key.
- `hegel_from_ffi_arbitrary_u64_is_safe`: from_ffi on arbitrary u64 input is documented "safe but unspecified": constructing a key from garbage and using it with the checked map API must not panic, and the resulting key must be FFI-stable (as_ffi/from_ffi converges after one normalization).
- `hegel_is_older_version_window`: is_older_version implements a wrapping half-range comparison: b is newer than a exactly when it is 1..=2^31 steps ahead of a (the concrete cases are pinned by check_is_older_version above).
- `hegel_key_serde_roundtrip`: (no doc comment)
- `hegel_keydata_deserialize_normalizes`: (no doc comment)

**`src/secondary.rs`**
- `hegel_secondary_map_model`: (no doc comment)

**`src/sparse_secondary.rs`**
- `hegel_sparse_secondary_map_model`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-05-09: predecessor base commit `0d130ed5bbd6` (Add MSRV-compatible lockfiles (#151)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/slotmap.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-12: base bumped 0d130ed5bbd6 → eccedefc5e09 (2026-09-04, "Remove the build script (#162)"; 1.1.1); 0 bug(s) still reproduce. 225 tests pass.
