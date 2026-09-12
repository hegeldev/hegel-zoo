# boa

[boa-dev/boa](https://github.com/boa-dev/boa).

## What is tested

**`src/builtins/json/tests.rs`**
- `json_parse_stringify_roundtrip_agrees_with_serde_json`: (no doc comment)

**`src/builtins/number/tests.rs`**
- `number_literals_roundtrip_exactly_through_the_lexer`: (no doc comment)
- `number_to_string_roundtrips_through_to_number`: (no doc comment)

**`src/builtins/string/tests.rs`**
- `string_literal_concatenation_matches_rust`: (no doc comment)

**`src/tests/mod.rs`**
- `parsing_arbitrary_text_never_panics`: (no doc comment)
- `parsing_js_shaped_text_never_panics`: (no doc comment)
- `evaluation_is_deterministic_across_fresh_contexts`: (no doc comment)
- `parsing_deeply_nested_source_never_panics`: (no doc comment)

**`src/tests/operators.rs`**
- `arithmetic_expressions_match_rust_f64_semantics`: (no doc comment)

**`src/value/conversions/serde_json.rs`**
- `from_json_to_json_roundtrip`: (no doc comment)

**`src/vm/tests.rs`**
- `loop_iteration_limit_is_a_tight_bound`: (no doc comment)
- `recursion_limit_is_a_tight_bound`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-07-22: predecessor base commit `5718cc81111c` (Add console.exception() as alias for console.error() (#5425)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/boa.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
