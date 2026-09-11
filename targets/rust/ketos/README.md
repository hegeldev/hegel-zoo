# ketos

[murarth/ketos](https://github.com/murarth/ketos).

## What is tested

**`tests/hegel_props.rs`**
- `parse_eval_arbitrary_text_no_panic`: (no doc comment)
- `parse_eval_sexpr_soup_no_panic`: (no doc comment)
- `deep_nesting_with_restrict_is_rejected`: (no doc comment)
- `integer_arithmetic_matches_i128_oracle`: (no doc comment)
- `division_by_zero_is_error`: (no doc comment)
- `ratio_reciprocal_identity`: (no doc comment)
- `printer_reader_roundtrip`: (no doc comment)
- `restrict_call_stack_bounds_recursion`: (no doc comment)

## Oracles

## Not tested

## History

- 2020-01-17: predecessor base commit `011287590ebe` (Merge pull request #66 from murarth/github-ci).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/ketos.patch`).
- 2026-09-11: imported into the zoo; ported to hegeltest 0.44.1.
