# koto

[koto-lang/koto](https://github.com/koto-lang/koto).

## What is tested

**`tests/koto_tests.rs`**
- `arithmetic_matches_rust_oracle`: (no doc comment)
- `operator_precedence_matches_explicit_parenthesization`: (no doc comment)
- `compound_assignment_matches_binary_op`: (no doc comment)
- `comparisons_match_rust_oracle`: (no doc comment)
- `number_display_roundtrip`: (no doc comment)
- `string_literal_roundtrip`: (no doc comment)
- `string_concatenation_matches_rust`: (no doc comment)
- `arbitrary_text_never_panics`: (no doc comment)
- `token_soup_never_panics`: (no doc comment)
- `token_soup_runs_deterministically`: (no doc comment)
- `modestly_nested_source_never_panics`: The same nesting shapes stay panic-free below the overflow threshold. The depth bound protects the test process from the known stack overflow pinned by `deeply_nested_parens_overflow_the_stack_known_failure`; it is not a documented contract.

## Oracles

## Not tested

## History

- 2026-07-05: predecessor base commit `4b433e7a7ce1` (Merge pull request #552 from koto-lang/koto-derive-improvements).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/koto.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped 4b433e7a7ce1 → c579dcd02f01 (2026-08-06, "Expose top-level assigned IDs and accessed non-locals in the AST (#554)"; 0.17.0); 1 bug(s) still reproduce; 1 ignored reproducer(s) not run. 45 tests pass.
