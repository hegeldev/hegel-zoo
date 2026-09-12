# liquid

[cobalt-org/liquid-rust](https://github.com/cobalt-org/liquid-rust).

## What is tested

**`tests/errors.rs`**
- `parse_never_panics_on_arbitrary_text`: Parsing (and, when parsing succeeds, rendering) arbitrary Unicode text must never panic. Errors are fine; panics are not.
- `parse_never_panics_on_liquid_token_soup`: Parsing Liquid-shaped token soup (delimiters, operators, keywords, identifiers, literals glued together in random order) must never panic. Numeric atoms are deliberately short: integer literals that overflow `i64` are a pinned parser panic, see `known_failure_parse_panics_on_out_of_range_integer_literal` below.
- `nested_blocks_parse_and_render_up_to_supported_depth`: Templates with nested blocks up to a moderate depth must parse and render successfully. The depth is capped at 64 because deeper nesting hits an unbounded recursion in the parser that aborts the whole process with a stack overflow -- see the `#[ignore]`d `known_failure_deep_block_nesting_overflows_stack` reproducer below. The cap documents the bug's blast radius; it is not a contract.

**`tests/filters.rs`**
- `integer_add_sub_mul_filters_match_i64_oracle`: `plus`/`minus`/`times` on integer operands match exact i64 arithmetic. Operands are bounded to the i32 range so that the exact result always fits in i64: the filters do unchecked `i64` arithmetic and panic on overflow, which is pinned separately in `known_failure_plus_panics_on_i64_overflow`.
- `float_arithmetic_filters_match_f64_oracle`: `plus`/`minus`/`times`/`divided_by`/`modulo` on float operands match Rust f64 arithmetic (including NaN/infinity operands), rendered via f64's `Display`. Division/modulo by (float) zero is a documented render error.
- `integer_division_by_zero_is_error_not_panic`: `divided_by`/`modulo` with an integer zero operand is a render error, never a panic, for any numerator.
- `integer_division_and_modulo_match_oracle_for_non_negative_operands`: `divided_by`/`modulo` on non-negative integer operands match Rust i64 division/remainder. The domain is restricted to `a >= 0`, `b >= 1` where truncating (Rust) and flooring (Ruby/Shopify) division agree: for negative operands the implementation deviates from Shopify's documented floor semantics, pinned in `known_failure_divided_by_rounds_toward_zero_not_down`. `i64::MIN / -1` (a panic) is pinned in `known_failure_divided_by_panics_on_min_by_minus_one`.
- `upcase_downcase_match_rust_unicode_case_conversion`: `upcase`/`downcase` match Rust's full Unicode case conversion.
- `append_prepend_concatenate_exactly`: `append`/`prepend` concatenate exactly, for arbitrary Unicode strings.
- `strip_filters_match_rust_trim`: `strip`/`lstrip`/`rstrip` match Rust's Unicode `trim` family.
- `size_of_array_is_element_count`: `size` of an array is its element count.
- `escape_fully_escapes_and_is_lossless`: `escape` output contains no unescaped `<`, `>`, `"`, `'`, every `&` starts one of the five entities it emits, and decoding those entities restores the input exactly (lossless).
- `escape_once_is_idempotent`: `escape_once` is idempotent: escaping its own output changes nothing.
- `escape_then_escape_once_is_fixed_point`: `escape` output is a fixed point of `escape_once`.
- `slice_matches_ruby_oracle_on_ascii`: `slice` on ASCII strings matches the Ruby `slice` oracle for the full i64 offset range; a length < 1 is a render error. The length is kept small because a huge length triggers a pinned overflow panic (`known_failure_slice_panics_on_length_overflow`); the bound avoids the pinned bug, it is not a contract. Non-ASCII slicing is pinned separately in `known_failure_slice_mixes_bytes_and_chars_for_unicode`.
- `truncate_matches_oracle_on_ascii`: `truncate` on ASCII strings never fails, and matches the documented semantics: unchanged when the length fits, otherwise a prefix plus the default "..." ellipsis, with the ellipsis counted in the length. The value is only checked for `n >= 0`; for negative lengths we only require no panic/error (the implementation casts `i64 as usize`). Non-ASCII truncation deviates (bytes vs graphemes), pinned in `known_failure_truncate_over_truncates_unicode`.
- `default_filter_selects_on_nil_false_and_empty`: `default` substitutes exactly when the input is nil, false, an empty string, or an empty array — and passes everything else through. The expected output is computed by rendering the value we expect `default` to select, so this tests the selection logic, not the formatting.

**`tests/syntax.rs`**
- `rendering_a_string_global_is_identity`: `{{ s }}` renders a string global back exactly, byte for byte, for arbitrary Unicode content (controls, NUL, non-BMP, line separators).
- `parse_and_render_are_deterministic`: Parsing and rendering are deterministic: parsing the same template twice and rendering each with the same globals produces identical output.

## Oracles

## Not tested

## History

- 2026-07-10: predecessor base commit `cd1e5ac838ad` (chore(deps): Update Rust Stable to v1.97 (#625)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/liquid.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
