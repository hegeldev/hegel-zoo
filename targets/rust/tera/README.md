# tera

[Keats/tera](https://github.com/Keats/tera).

## What is tested

**`tests/basic.rs`**
- `compile_arbitrary_text_never_panics`: (no doc comment)
- `compile_token_soup_never_panics`: (no doc comment)
- `deep_guarded_nesting_returns_err_not_overflow`: (no doc comment)
- `integer_arithmetic_matches_i128_oracle`: (no doc comment)
- `division_matches_f64_oracle`: (no doc comment)
- `autoescape_escapes_all_special_chars`: (no doc comment)
- `safe_filter_is_verbatim`: (no doc comment)
- `render_is_deterministic`: (no doc comment)
- `string_filters_match_rust`: (no doc comment)
- `undefined_variable_errors`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-07-23: predecessor base commit `15e0c6e6f1ab` (Fix typo).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/tera.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped 15e0c6e6f1ab → 6ead3c0ffa1e (2026-09-11, "Fix some Value::deserialize issues"; 2.4.0); 0 bug(s) still reproduce; 1 ignored reproducer(s) not run. 136 tests pass.
