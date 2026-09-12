# gluon

[gluon-lang/gluon](https://github.com/gluon-lang/gluon).

## What is tested

**`tests/stack_overflow.rs`**
- `parse_token_soup_never_panics`: (no doc comment)
- `parse_arbitrary_text_never_panics`: (no doc comment)
- `parse_deep_parens_never_aborts`: (no doc comment)
- `int_arithmetic_matches_checked_i64_oracle`: (no doc comment)
- `evaluation_is_deterministic`: (no doc comment)
- `int_literal_roundtrips_through_eval`: (no doc comment)
- `float_literal_roundtrips_through_eval`: (no doc comment)
- `record_field_roundtrips_through_eval`: (no doc comment)
- `string_literal_roundtrips_through_eval`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-07-10: predecessor base commit `418c6b7de22b` (Merge pull request #978 from Marwes/more).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/gluon.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
