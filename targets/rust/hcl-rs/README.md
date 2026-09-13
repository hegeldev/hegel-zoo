# hcl-rs

[martinohmann/hcl-rs](https://github.com/martinohmann/hcl-rs).

## What is tested

**`tests/de.rs`**
- `prop_parse_never_panics_on_arbitrary_text`: `hcl::parse` / `hcl::from_str` must never panic on arbitrary input: they return `Err` for anything that is not valid HCL.
- `prop_parse_never_panics_on_hcl_shaped_text`: Fragments of HCL syntax, assembled in arbitrary order. This explores "almost valid" inputs (unclosed heredocs, dangling template markers, operators in odd positions) much more densely than uniform text.
- `prop_parse_never_panics_on_nested_input`: Nested arrays/objects/blocks/parens/templates must parse (or error) without crashing. The depth is capped at 40 because the parser's recursion overflows the stack and ABORTS THE PROCESS at surprisingly shallow depths (~100 for nested objects/blocks on a 2 MiB test thread). KNOWN BUG, pinned by the `#[ignore]`d reproducer `deeply_nested_input_overflows_stack` below; the cap protects this test's process, not the library's contract.
- `prop_parse_negated_integer_literal_is_nonpositive`: A negated integer literal `-N` (N a decimal u64 literal) must parse to a non-positive number. KNOWN FAILURE: the parser folds unary minus via `N::neg` (crates/hcl-primitives/src/number.rs), which negates through a wrapping/saturating `as i64` cast: - `a = -9223372036854775808` (i64::MIN) panics with "attempt to negate   with overflow" in debug builds; - `a = -9223372036854775809` silently parses as +9223372036854775807; - `a = -18446744073709551615` silently parses as +1. The sampled branch below makes the failure deterministic.
- `prop_from_body_agrees_with_parsing_serialized_body`: Deserializing a `Body` directly (`hcl::from_body`) must agree with serializing it to text and parsing that (`hcl::from_str`). Both routes apply the HCL JSON spec's block-merging rules, so they must produce identical `Value`s.
- `prop_attribute_vs_block_disambiguation`: `k = {}` must parse as an attribute named `k`; `k {}` and `k "label" {}` must parse as blocks — for every valid identifier, including keywords, dashes and unicode.

**`tests/format.rs`**
- `prop_format_value_roundtrip`: `hcl::format::to_string` (the `Format` trait path) on a `Value` must produce text that parses back to an equal `Value` when embedded as an attribute expression. KNOWN FAILURE: unlike the serde serializer (`hcl::to_string`), the `Format` impl for `Value` writes strings that merely *look* templated (`is_templated` in src/util.rs) verbatim, without escaping. For a string that is not a valid template — e.g. `"${x"` or a templated string containing a raw newline — the output is invalid HCL and fails to parse; roundtripping a valid `Value` through `format::to_string` errors out. The `just` branch below makes the failure deterministic.

**`tests/ser.rs`**
- `prop_body_serialize_parse_fixpoint`: Serializing an arbitrary `Body` and parsing the result must yield the same `Body`, and re-serializing must reproduce the exact same text (fixpoint).
- `prop_value_serialize_parse_fixpoint`: Serializing an arbitrary top-level `Value` and deserializing the result must yield the same `Value`, and re-serializing must reproduce the exact same text (fixpoint).
- `prop_string_escape_roundtrip`: String attribute values generated at the escape boundary (quotes, backslashes, control chars, `${` / `%{` template markers, unicode) must round-trip exactly through serialize + parse. KNOWN FAILURE: `hcl_primitives::template::escape_markers` consumes `$`/`%` pairs blindly while scanning, so a `$` run directly before `{` misaligns the scan and an escaped-marker sequence is left unescaped: `"${$${"` is escaped to `"$${$${"` (instead of `"$${$$${"`), which parses back as `"${${"` — silent string corruption. The sampled branch below makes the failure deterministic. Sibling properties avoid the buggy class via `gen::escape_safe_strings`.
- `prop_keyword_object_keys_roundtrip`: Object keys that are keyword identifiers (`true`, `false`, `null`, `for`) must round-trip through serialize + parse like any other identifier key. KNOWN FAILURE: keyword identifier keys are serialized bare, which changes their meaning on re-parse: - `ObjectKey::Identifier(Identifier::unchecked("true"))` serializes to   `{ true = ... }` and re-parses as the *literal expression key*   `ObjectKey::Expression(Expression::Bool(true))`. As a consequence   `hcl::from_str::<Value>` even fails on such documents ("invalid   type: boolean `true`, expected a string") while `hcl::from_body` on   the original body succeeds. Same for `false` and `null`. - An object key `for` serializes to `{ for = ... }`, which does not   parse at all (the parser starts a `for` expression). Sibling properties exclude keyword object keys in `gen::exprs`.
- `prop_number_serialize_parse_roundtrip`: Numbers must round-trip through serialize + parse with the same value and the same internal representation (integer vs float).
- `prop_number_from_f64_roundtrips_value`: `Number::from_f64` must preserve the value of any finite float: `Number::from_f64(f).as_f64() == Some(f)`. KNOWN FAILURE: whole-valued floats with magnitude >= 2^63 are corrupted by a saturating `as i64` cast in `N::from_finite_f64` (crates/hcl-primitives/src/number.rs): `Number::from_f64(1e300)` becomes `9223372036854775807`. This also corrupts `Value::from(f64)` and every serde serialization of large float fields. The sampled branch below makes the failure deterministic.
- `prop_value_json_roundtrip`: An `hcl::Value` must survive a round-trip through its serde JSON representation (HCL has a documented JSON interop story; `serde_json` is the reference JSON implementation).

**`tests/template.rs`**
- `prop_template_parse_never_panics`: The template sub-language parser must never panic: arbitrary text and template-shaped text (interpolations, directives, strip markers, in arbitrary order) either parse or return an error. The same input embedded as a quoted attribute value must not panic the main parser either.

## Oracles

## Not tested

## History

- 2026-07-02: predecessor base commit `2f0b1f87fbb4` (chore(deps): update dtolnay/rust-toolchain digest to 4be7066 (#546)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/hcl-rs.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped 2f0b1f87fbb4 → f7b17594f8d7 (2026-09-06, "chore(deps): update github actions (#564)"; 0.19.8); 4 bug(s) still reproduce; 1 ignored reproducer(s) not run. 156 tests pass.
