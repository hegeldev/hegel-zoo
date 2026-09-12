# dyon

[pistondevelopers/dyon.git](https://github.com/pistondevelopers/dyon.git).

## What is tested

**`tests/lib.rs`**
- `prop_arithmetic_matches_rust_oracle`: (no doc comment)
- `prop_operator_precedence_matches_oracle`: (no doc comment)
- `prop_parenthesization_is_neutral`: (no doc comment)
- `prop_string_concat_matches_rust`: (no doc comment)
- `prop_boolean_logic_matches_rust`: (no doc comment)
- `prop_run_is_deterministic`: (no doc comment)
- `prop_array_indexing_and_bounds`: (no doc comment)
- `prop_float_literal_parse_correctly_rounded_KNOWN_FAILURE`: (no doc comment)
- `prop_load_never_panics_on_arbitrary_text`: (no doc comment)
- `prop_load_never_panics_on_token_soup`: (no doc comment)
- `prop_shallow_nesting_no_abort`: (no doc comment)

## Oracles

## Not tested

## History

- 2025-12-23: predecessor base commit `3fb34a313a37` (Merge pull request #797 from bvssvni/master).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/dyon.patch`).
- 2026-09-11: imported into the zoo; ported to hegeltest 0.44.1.
