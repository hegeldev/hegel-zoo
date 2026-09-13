# rkyv

[rkyv/rkyv](https://github.com/rkyv/rkyv).

## What is tested

**`src/impls/alloc/collections/btree_map.rs`**
- `roundtrip_generated_btree_map_deep`: (no doc comment)

**`src/impls/alloc/string.rs`**
- `roundtrip_generated_string`: (no doc comment)

**`src/impls/alloc/vec.rs`**
- `roundtrip_generated_vec_i64`: (no doc comment)
- `roundtrip_generated_vec_u8`: (no doc comment)

**`src/impls/core/primitive.rs`**
- `roundtrip_f32_bit_exact`: (no doc comment)
- `roundtrip_f64_bit_exact`: (no doc comment)
- `roundtrip_char_full_domain`: (no doc comment)

**`src/impls/mod.rs`**
- `roundtrip_rich_derived_type`: (no doc comment)
- `roundtrip_recursive_type_at_depth`: (no doc comment)

**`src/impls/std/collections/hash_map.rs`**
- `roundtrip_generated_hash_map`: (no doc comment)

**`tests/fuzz.rs`**
- `from_bytes_arbitrary_bytes_never_panics`: (no doc comment)
- `access_bit_flipped_archive_never_panics`: (no doc comment)
- `access_truncated_archive_never_panics`: (no doc comment)
- `checked_and_unchecked_access_agree`: (no doc comment)
- `access_misaligned_buffer_errors`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-07-02: predecessor base commit `46e143d6e4c8` (Release 0.8.17).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/rkyv.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped 46e143d6e4c8 → 4845668ae973 (2026-09-09, "Fix unused import in test"; 0.8.18); 0 bug(s) still reproduce; 1 ignored reproducer(s) not run. 192 tests pass.
