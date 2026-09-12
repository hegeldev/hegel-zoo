# evalexpr

[ISibboI/evalexpr.git](https://github.com/ISibboI/evalexpr.git).

## What is tested

**`tests/integration.rs`**
- `hegel_eval_never_panics_on_arbitrary_text`: Property: eval never panics on completely arbitrary text. Garbage must be rejected with an Err, not a crash.
- `hegel_eval_never_panics_on_token_soup`: Property: eval never panics on "token soup" — sequences of valid lexical tokens in arbitrary order, which reach much deeper into the parser than plain garbage does. `shl`, `shr` and `str::substring` are deliberately absent from the vocabulary: they can panic on inputs this test could assemble, which is pinned by known_failure_shift_panics_on_shift_overflow and known_failure_substring_panics_inside_multibyte_char.
- `hegel_arithmetic_matches_reference_interpreter`: Property: arithmetic over int/float literals matches an independent reference interpreter implementing the documented semantics (checked i64 arithmetic, float promotion, `^` always float).
- `hegel_precedence_matches_explicit_parenthesization`: Property: an unparenthesized operator chain evaluates exactly like the explicitly parenthesized version dictated by the documented precedence table (^ 120 > * / % 100 > + - 95) with left-to-right associativity.
- `hegel_int_literal_roundtrip`: Property: every i64 round-trips through its literal forms (decimal, and hex/octal/binary for the non-negative range those notations cover).
- `hegel_float_literal_roundtrip`: Property: every finite f64 round-trips bit-exactly through its shortest decimal/scientific literal form.
- `hegel_comparison_operators_match_rust_on_ints`: Property: comparison operators on integer literals agree with Rust's i64 comparisons.
- `hegel_boolean_operators_match_rust`: Property: `&&`, `||` and `!` on boolean literals agree with Rust's boolean operators. (evalexpr evaluates both operands eagerly — this asserts truth-table agreement, not short-circuiting.)
- `hegel_string_operators_match_rust`: Property: binary operators on string literals match Rust's String semantics: `+` concatenates, comparisons use lexicographic order. This exercises string-literal tokenization (including escapes) end-to-end.
- `hegel_substring_matches_rust_on_char_boundaries`: Property: `str::substring` with byte indices on char boundaries returns exactly the Rust slice `&s[start..end]`. Indices are restricted to char boundaries because non-boundary indices make the builtin panic — pinned by known_failure_substring_panics_inside_multibyte_char.
- `hegel_context_variable_read_returns_stored_value`: Property: a variable stored in a context via the API is read back unchanged by evaluating the bare identifier.
- `hegel_assignment_roundtrip`: Property: an assignment expression writes the value into the context, and a chained read returns it.

## Oracles

## Not tested

## History

- 2025-11-26: predecessor base commit `45e9634dab34` (Release (#195)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/evalexpr.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
