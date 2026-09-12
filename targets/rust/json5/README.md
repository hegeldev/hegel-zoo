# json5

[callum-oakley/json5-rs](https://github.com/callum-oakley/json5-rs).

## What is tested

**`tests/de.rs`**
- `json_is_a_subset_differential`: (no doc comment)
- `parse_never_panics_on_arbitrary_text`: (no doc comment)
- `parse_never_panics_on_json5_token_soup`: (no doc comment)
- `nested_input_parses_at_bounded_depth`: (no doc comment)
- `hex_literal_parses_exactly`: (no doc comment)
- `decimal_literal_matches_rust_float_parser`: (no doc comment)
- `leading_zero_is_rejected`: (no doc comment)
- `unpaired_surrogate_escape_is_rejected`: (no doc comment)
- `comments_and_whitespace_are_insensitive`: (no doc comment)
- `generated_json5_document_parses_to_expected_value`: (no doc comment)

**`tests/ser.rs`**
- `value_roundtrip_and_fixpoint`: (no doc comment)
- `float_roundtrip`: (no doc comment)
- `integer_roundtrip`: (no doc comment)
- `string_roundtrip_at_escape_boundary`: (no doc comment)
- `char_roundtrip`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-02-07: predecessor base commit `6905ad2ea7b0` (expose char).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/json5.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
