# ron

[ron-rs/ron](https://github.com/ron-rs/ron).

## What is tested

**`tests/307_stack_overflow.rs`**
- `prop_from_str_never_panics_on_arbitrary_text`: The parser must never panic on arbitrary text — it either parses or returns an error.
- `prop_from_str_never_panics_on_ron_token_soup`: The parser must never panic on RON-shaped token soup: syntactically suggestive fragments glued together in arbitrary order.
- `prop_deeply_nested_input_errors_gracefully`: Deeply nested input must be rejected gracefully via the recursion limit (default 128, `ron::Options::recursion_limit`) — never a stack overflow. Probes depths well past the limit and mixes nesting kinds.
- `prop_deeply_nested_value_serialization_errors_gracefully`: The serializer's recursion guard is the mirror image: serializing a `Value` nested past the limit must return `Error::ExceededRecursionLimit`, and one nested within it must succeed.

**`tests/escape.rs`**
- `prop_string_escape_roundtrip`: Strings built from escape-set-boundary characters must roundtrip through escaped serialization.
- `prop_char_escape_roundtrip`: Every char must roundtrip through char-literal serialization.
- `prop_unescaped_raw_string_roundtrip`: With `escape_strings(false)` the serializer falls back to raw strings (`r#"..."#`) whenever the string contains `"` or `\`, choosing the number of hash marks from the longest `#` run in the content. Strings made of quotes, hashes, backslashes, and line breaks target exactly that delimiter-selection boundary.

**`tests/extensions.rs`**
- `prop_roundtrip_under_all_extension_combinations`: Generated data must roundtrip under *every* combination of extensions (the powerset of `unwrap_newtypes`, `implicit_some`, `unwrap_variant_newtypes`, and `explicit_struct_names`): whatever the serializer emits under a set of extensions, the deserializer must accept back to an equal value.

**`tests/min_max.rs`**
- `prop_integer_roundtrip`: Typed integer roundtrip over every integer width, including MIN/MAX.
- `prop_f64_roundtrip`: Typed f64 roundtrip: bit-exact for every value except NaN, where the text form (`NaN`/`-NaN`) only preserves NaN-ness and the sign.
- `prop_f32_roundtrip`: Typed f32 roundtrip, same contract as for f64.
- `prop_untyped_integer_value_preserved`: The untyped parser must preserve the integer-vs-float distinction and the numeric value of serialized integers.

**`tests/value.rs`**
- `prop_value_roundtrip_compact`: The crown roundtrip property: any `Value` serialized to RON text parses back to the same value (modulo parse normalization of number types), and the roundtrip reaches a fixpoint after one pass.
- `prop_pretty_and_compact_parse_to_same_value`: Pretty and compact serialization of the same `Value` must parse back to the same value, for arbitrary `PrettyConfig` layout settings. (Compared canonically: `number_suffixes` legitimately preserves the original number type where compact serialization does not.)
- `prop_whitespace_and_comments_do_not_change_parse`: Whitespace and comment insensitivity: inserting arbitrary whitespace and (nested) comments between tokens must not change the parse.

## Oracles

## Not tested

## History

- 2026-07-16: predecessor base commit `31529b8b8d8c` (Fix quadratic escaped string parsing in escaped_byte_buf (#610)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/ron.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1. Eight upstream
  `from_str(&to_string(&std::T::MIN/MAX)...)` calls in `tests/min_max.rs` got an explicit `from_str::<T>`: with
  hegeltest's `serde_json` in scope the deserialized type is ambiguous (E0283).
- 2026-09-13: base bumped 31529b8b8d8c → 7cf000afe4de (2026-09-09, "Fix Miri aliasing UB in test_deeply_nested_struct (#620)"; 0.12.2); 1 bug(s) still reproduce. 470 tests pass. The patch's hunk for `tests/307_stack_overflow.rs` used to be a binary hunk (the upstream file carried a raw NUL byte in a fuzz string, which git cannot merge); upstream replaced the NUL with `\0`, the zoo's module was re-applied onto the text file, and the hunk is now a plain text diff.
