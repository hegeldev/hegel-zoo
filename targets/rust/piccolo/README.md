# piccolo

[kyren/piccolo](https://github.com/kyren/piccolo).

## What is tested

**`tests/scripts.rs`**
- `load_arbitrary_source_never_panics`: (no doc comment)
- `load_token_soup_never_panics`: (no doc comment)
- `load_deeply_nested_source_never_aborts`: (no doc comment)
- `long_flat_chains_compile_and_evaluate`: (no doc comment)
- `integer_arithmetic_matches_puc_lua`: (no doc comment)
- `float_arithmetic_matches_rust_ieee`: (no doc comment)
- `float_modulo_matches_puc_lua`: (no doc comment)
- `number_comparisons_match_puc_lua`: (no doc comment)
- `string_ops_match_reference`: (no doc comment)
- `tostring_tonumber_roundtrip`: (no doc comment)
- `table_length_of_sequences`: (no doc comment)
- `execution_is_deterministic`: (no doc comment)

## Oracles

## Not tested

## History

- 2025-07-10: predecessor base commit `ce709eb1dae5` (Revert #[error(transparent)] in CompilerError to fix downcasting (#...).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/piccolo.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
