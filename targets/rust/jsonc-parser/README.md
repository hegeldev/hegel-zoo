# jsonc-parser

[dprint/jsonc-parser](https://github.com/dprint/jsonc-parser).

## What is tested

**`tests/test.rs`**
- `pbt_valid_json_differential_vs_serde_json`: (no doc comment)
- `pbt_arbitrary_text_never_panics`: (no doc comment)
- `pbt_jsonc_soup_never_panics`: (no doc comment)
- `pbt_whitespace_only_input_parses_to_none`: (no doc comment)
- `pbt_deep_nesting_rejected_not_crashed`: (no doc comment)
- `pbt_trivia_insensitivity`: (no doc comment)
- `pbt_number_lexeme_preserved`: (no doc comment)
- `pbt_number_differential_vs_serde_json`: (no doc comment)
- `pbt_hex_numbers_convert_to_decimal`: (no doc comment)
- `pbt_string_escape_decoding`: (no doc comment)
- `pbt_ast_ranges_well_formed`: (no doc comment)
- `pbt_cst_roundtrip_lossless`: (no doc comment)
- `pbt_cst_to_serde_value_agrees`: (no doc comment)
- `pbt_strict_mode_rejects_jsonc_extensions`: (no doc comment)
- `pbt_strict_mode_rejects_missing_array_commas`: KNOWN FAILURE: strict mode (all ParseOptions false, documented as "Parse Strictly as JSON") accepts missing commas between ARRAY elements, e.g. `[1 2]`, even though `allow_missing_commas: false` rejects them between object properties. serde_json rejects these inputs. Code path: `JsoncParser::scan_array_comma` (src/parser.rs) returns any non-comma token as the next element without consulting `allow_missing_commas`, and `parse_array` in src/parse_to_ast.rs has the same gap (its missing-comma check exists only in `parse_object`). The same code ships in upstream jsonc-parser 0.33.0, so this is an inherited contract bug, not a local regression. This test is expected to FAIL until that is fixed; it fails deterministically on every case.
- `pbt_cst_set_value_roundtrip`: (no doc comment)
- `pbt_json_object_typed_accessors`: (no doc comment)
- `pbt_parse_to_ast_agrees_with_parse_to_value`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-07-07: predecessor base commit `20d89e23b873` (0.33.0).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/jsonc-parser.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped 20d89e23b873 → e6e383704fd9 (2026-09-12, "0.33.2"; 0.33.2); 0 bug(s) still reproduce; fixed upstream: jsonc-parser/1. 194 tests pass. jsonc-parser/1 (strict mode accepted missing array commas) is fixed upstream in 0.33.2.
