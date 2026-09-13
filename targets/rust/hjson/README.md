# hjson

[hjson/hjson-rust](https://github.com/hjson/hjson-rust).

## What is tested

**`tests/test_hjson.rs`**
- `hjson_parses_json_identically_to_serde_json`: Any valid JSON document must parse under hjson to exactly the value serde_json parses it to (both deserialized into serde_json::Value).
- `parse_never_panics_on_arbitrary_text`: from_str on arbitrary text returns Ok or Err, never panics.
- `parse_never_panics_on_arbitrary_bytes`: from_slice on byte input never panics. Bytes are passed through `from_utf8_lossy` so the input is always *valid* UTF-8: this still exercises from_slice with arbitrary structural garbage, but excludes invalid UTF-8, which is a genuine panic bug pinned by `known_failure_parse_panics_on_invalid_utf8` (the exclusion protects this sibling property, it is not a contract restriction). Evidence: the unit tests above pin four historical panics found by fuzzing (parse_int_error, removal_index, subtract_overflow, invalid_utf8).
- `known_failure_parse_panics_on_invalid_utf8`: KNOWN BUG (panic): invalid UTF-8 inside a quoteless key or value reaches `str::from_utf8(&self.str_buf).unwrap()` and panics instead of returning Err. There are two such sites: parse_keyname (de.rs:105, triggered by e.g. b"\x80:") and parse_tfnns (de.rs:246, triggered by a quoteless value starting with n/t/f then a bad byte, e.g. b"n\x80"). This is a robustness/security bug for from_slice on untrusted bytes. Every case drawn here (a key path and a value path) fails deterministically.
- `parse_never_panics_on_hjson_token_soup`: Hjson-shaped token soup (braces, quotes, comments, keywords, numbers, escapes glued together) never panics the parser.
- `nested_documents_parse_to_expected_depth`: Nested arrays/objects up to depth 100 parse correctly to the expected structure. The depth is capped at 100 because the parser's recursion is unbounded and *aborts the process* (stack overflow) at larger depths — around 400 on a 2 MiB stack in debug builds. That bug is pinned by `known_abort_stack_overflow_on_deep_nesting` below; the cap protects this test's process, it is not a contract.
- `value_roundtrips_through_hjson_text`: General value roundtrip: parse(format(v)) is semantically equal to v (numbers compared numerically, see hjson_semantic_eq), and the roundtrip is a fixpoint: a second format/parse cycle reproduces the first result exactly. The drawn value is wrapped under a fixed key ("root") so it is serialized in a normal value position rather than at the document root. A *top-level* quoteless string that looks like `key:value` (e.g. "0:0") re-parses as an object instead of a string — a real serializer/parser inconsistency pinned by `known_failure_toplevel_quoteless_string_reparses_as_object`. Wrapping keeps this property testing the value serializer without tripping that separate root-ambiguity bug; top-level scalars are covered by the JSON differential.
- `known_failure_cr_strings_roundtrip`: KNOWN BUG: strings containing a carriage return take the serializer's multiline ('''...''') path (NEEDS_ESCAPEML does not match \r), but the multiline *parser* silently drops \r — so the roundtrip loses data: Value::String("a\rb") serializes to '''a\rb''' and parses back as "ab". Every case drawn here contains a \r and fails deterministically.
- `known_failure_control_char_keys_roundtrip`: KNOWN BUG: object keys containing non-whitespace C0 control chars (e.g. "\x1f") are written *unquoted* by escape_key (its NEEDS_ESCAPE_NAME regex only checks `\s`, which does not match \x00-\x08/\x0e-\x1f), but parse_keyname treats every byte <= 0x20 as whitespace — so the serializer emits documents it cannot re-parse. Every case drawn here fails deterministically.
- `known_failure_huge_integral_floats_roundtrip`: KNOWN BUG: integral floats just outside the i64/u64 range (e.g. 2^64 = 18446744073709551616.0) are serialized by fmt_small as bare digit strings ("18446744073709552000"); on re-parse the u64/i64 parse overflows, ParseNumber errors, and the text falls through to the quoteless-string path — the number comes back as Value::String. Both sampled inputs fail deterministically.
- `known_failure_toplevel_quoteless_string_reparses_as_object`: KNOWN BUG: a top-level string value whose quoteless serialization looks like `unquotedkey:value` (e.g. "0:0", "a:b") re-parses as an object, not a string. quote_str only forces quotes when a string *starts* with `:`/`,`/etc. (NEEDS_QUOTES), so an interior colon after a valid bare key survives unquoted; at the document root the parser then reads it as `{key: value}`. Every sampled input fails deterministically. (Nested — inside an array or object value — the same string roundtrips correctly.)
- `integer_literals_parse_exactly`: Integer literals parse to the exact value with hjson's documented classification: negative -> I64, non-negative -> U64 (evidence: util.rs ParseNumber::parse). Covers i64::MIN, u64::MAX and the boundaries between them.
- `float_literals_parse_bit_exactly`: Float literals in exponent notation parse to the bit-exact f64: Rust's LowerExp prints a shortest representation that str::parse (which ParseNumber delegates to) must restore exactly, including -0.0 and subnormals.
- `typed_struct_roundtrips_from_json`: A typed model serialized as JSON (a valid hjson document) deserializes through hjson back to an equal model — structs, Option, Vec, maps, full-range numbers and arbitrary unicode strings. (Externally tagged enums are not exercised: the deserializer forwards deserialize_enum to deserialize_any and cannot deserialize derived enums at all — see HEGEL_REPORT.md.)
- `comments_between_tokens_do_not_change_value`: Inserting #, //, or /* */ comments at token boundaries (line breaks of pretty-printed JSON, plus leading/trailing position) does not change the parsed value.
- `relaxed_object_syntax_parses_to_expected_map`: Objects written with hjson's relaxed syntax — unquoted keys, quoteless string values, newline separators, optional trailing commas, and optional root braces — parse to the expected map.
- `relaxed_array_syntax_parses_to_expected_vec`: Arrays accept comma and/or newline separators and a trailing comma.
- `quoted_string_escapes_decode_exactly`: Quoted strings built from arbitrary chars — written raw, as named escapes (\n, \t, \", \\, \/, ...), or as \uXXXX (with surrogate pairs for astral chars) — decode to exactly the intended characters.

## Oracles

## Not tested

## History

- 2024-09-25: predecessor base commit `8b3b85cd7eee` (Release 1.1.0 (#37)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/hjson.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
