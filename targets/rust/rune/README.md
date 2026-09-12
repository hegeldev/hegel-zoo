# rune

[rune-rs/rune](https://github.com/rune-rs/rune).

## What is tested

**`tests/derive_from_value.rs`**
- `value_roundtrip_preserves_primitives`: Property: converting a primitive Rust value into a Rune [`Value`] and back yields the original value, over the full domain of each type.
- `value_roundtrip_preserves_compound_values`: Property: converting compound Rust values (strings, vectors, maps, options, tuples) into a Rune [`Value`] and back yields the original.

## Oracles

## Not tested

## History

- 2026-07-20: predecessor base commit `20b26957f18e` (Make indentation configurable and honor LSP formatting options).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/rune.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
