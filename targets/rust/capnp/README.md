# capnp

[dwrensha/capnproto-rust](https://github.com/dwrensha/capnproto-rust).

## What is tested

**`src/serialize.rs`**
- `hegel_read_message_arbitrary_bytes_robust`: (no doc comment)
- `hegel_segment_table_limits_enforced`: (no doc comment)
- `hegel_flat_slice_alloc_and_no_alloc_agree`: (no doc comment)
- `hegel_write_read_roundtrip_consumes_exactly`: (no doc comment)
- `hegel_builder_write_read_roundtrip`: (no doc comment)

**`src/serialize_packed.rs`**
- `hegel_pack_unpack_roundtrip`: (no doc comment)
- `hegel_packed_read_arbitrary_bytes_robust`: (no doc comment)

**`tests/canonicalize.rs`**
- `hegel_canonicalize_is_fixpoint`: (no doc comment)

**`tests/total_size.rs`**
- `hegel_deep_pointer_chain_hits_nesting_limit`: Property: a message crafted as a deep chain of struct pointers is handled by the default `ReaderOptions::nesting_limit` (64): traversal returns an error for chains deeper than the limit instead of overflowing the stack, and succeeds for chains within the limit.

## Oracles

## Not tested

## History

- 2026-07-23: predecessor base commit `d1616946b6a5` (prepare for capnp-rpc-v0.26.2 release).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/capnp.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped d1616946b6a5 → 81bc1b815d0f (2026-09-08, "prepare for capnp-v0.27.2 release"; 0.27.2); 0 bug(s) still reproduce. 95 tests pass.
