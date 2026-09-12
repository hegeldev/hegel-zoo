# simd-json

[simd-lite/simd-json](https://github.com/simd-lite/simd-json).

## What is tested

**`src/tests/serde.rs`**
- `hegel_prop_differential_junk_bytes`: (no doc comment)
- `hegel_prop_differential_generated_json`: (no doc comment)
- `hegel_prop_number_parse_matches_serde_json`: (no doc comment)
- `hegel_prop_out_of_range_int_rejected`: (no doc comment)

**`src/tests.rs`**
- `hegel_prop_parse_paths_agree`: Property: all of simd-json's parsing entry points agree on whether an arbitrary input is valid JSON, and (duplicate keys aside) produce equal values: `to_owned_value`, `to_borrowed_value`, `to_tape`, and the serde-Deserialize path.
- `hegel_prop_whitespace_padding_invariance`: Property: surrounding a document with arbitrary whitespace (lengths 0..=130, crossing the 64-byte SIMD block boundaries at every offset) never changes the parse result.
- `hegel_prop_string_escapes_across_simd_boundaries`: Property: escape sequences and multi-byte characters are decoded correctly regardless of their byte offset relative to the 64-byte SIMD blocks stage1/stage2 operate on. The expected string is constructed alongside the literal, giving an exact oracle.
- `hegel_prop_encode_parse_roundtrip`: (no doc comment)
- `hegel_prop_tape_handles_deep_nesting`: Property: the tape stage (stage1 + stage2) is fully iterative and must handle arbitrarily deep nesting without crashing — unlike the DOM builders (see owned_value_deep_nesting_stack_overflow below).

## Oracles

## Not tested

## History

- 2026-07-14: predecessor base commit `c8cece05a69a` (Add approx integer parsing error-path test coverage (#466)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/simd-json.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
