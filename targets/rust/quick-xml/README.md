# quick-xml

[tafia/quick-xml](https://github.com/tafia/quick-xml).

## What is tested

**`src/escape.rs`**
- `normalize_xml10_eols_matches_reference`: (no doc comment)
- `normalize_xml11_eols_matches_reference`: (no doc comment)

**`tests/escape.rs`**
- `escape_unescape_roundtrip`: `unescape` must be a left inverse of every escape function: whatever characters an escape function decides to (not) escape, unescaping the result must return the original string.
- `escaped_text_contains_no_unescaped_specials`: Each escape function documents an exact escape set. The output must not contain any raw character of that set, and every `&` in the output must begin one of the five predefined entities. (The roundtrip property alone cannot detect an unescaped `<` because `unescape` passes it through.)
- `char_ref_roundtrip`: Any Unicode scalar value (except NUL, which the parser rejects) written as a decimal or hexadecimal character reference must unescape to exactly that character.
- `numeric_char_ref_resolves_exactly_valid_codepoints`: Numeric character references over the full `u32` range must never panic, must resolve exactly the codepoints that are Unicode scalar values (except 0, documented by `ParseCharRefError::IllegalCharacter`), and must reject everything else.
- `unescape_never_panics`: `unescape` must never panic, whatever `&`/`;`/`#` soup it is fed.

**`tests/fuzzing.rs`**
- `reader_never_panics_on_arbitrary_input_and_config`: Whatever bytes and whatever `Config` the reader is given, it must not panic, must not loop forever, and its event payloads must survive the content accessors (mirrors `fuzz_53`/`fuzz_101` above, but generated).

**`tests/reader-attributes.rs`**
- `attribute_values_roundtrip_modulo_documented_normalization`: Attribute values written through the writer (which escapes `<`, `>`, `&`, `'`, `"`) must come back from `Attribute::normalized_value` equal to the original value after the *documented* whitespace normalization — quotes and entity-looking content must survive unchanged. Note: raw `\t`/`\r`/`\n` in attribute values do NOT roundtrip — the XML specification requires parsers to normalize them to spaces, and the writer does not escape them as `&#9;`/`&#13;`/`&#10;` (which would preserve them).

**`tests/reader-config.rs`**
- `trim_text_equals_trimming_the_untrimmed_stream`: `trim_text_start`/`trim_text_end` must produce exactly the default stream with `Text` events trimmed (via the crate's own public trimming methods) and events that became empty dropped. Empty `Text` events are filtered out of both streams before comparison, because of the known bug pinned by `trim_text_end_does_not_push_empty_text_events` above (the reader pushes empty `Text` events when `trim_text_end` trims a whitespace-only text that is not at EOF); everything else about trimming remains asserted.
- `expand_empty_elements_equals_rewriting_empty_as_start_end`: `expand_empty_elements` must produce exactly the default stream with every `Empty` event replaced by the same `Start` event plus an `End` event with the same name.

**`tests/reader.rs`**
- `chunked_reads_equal_whole_input_reads`: The observable event stream (including any error and the reported positions) must not depend on how the underlying `BufRead` chunks the input. Regressions of this kind happened before (issues #950, #957), where parser state was lost at `fill_buf` window boundaries.

**`tests/roundtrip.rs`**
- `read_write_identity_on_generated_documents`: Documents produced by [`Writer`] must be accepted by [`Reader`], and writing the events read back must reproduce the document byte-for-byte (the generalization of the example-based tests in this file).

## Oracles

## Not tested

## History

- 2026-07-20: predecessor base commit `56ae43f82792` (Bound NamespaceResolver nesting depth).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/quick-xml.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1. One upstream `&mut Vec::new()` buffer argument in `#[cfg(test)]` code (`src/reader/buffered_reader.rs`, `check!` macro) rewritten as `Vec::<u8>::new()`: hegeltest 0.44 pulls in `serde_json`, whose `PartialEq<Value> for u8` makes the element type ambiguous (E0282/E0283).
- 2026-09-13: base bumped 56ae43f82792 → 2eaa844b4b40 (2026-09-02, "Fix changelog"; 0.42.0); 1 bug(s) still reproduce. 1281 tests pass. Porting to 0.42: `Event::Comment` now carries `BytesComment` (#1009), the decode API is gone (#963: `normalized_value` instead of `decoded_and_normalized_value`, attribute keys are `&str`), and the writer escapes `\t`/`\r`/`\n` as character references (#670/#990), so two oracles changed: the escape test accepts numeric character references and the attribute-normalization model no longer maps those three characters to spaces (they now roundtrip; XML 1.1's `\x85`/`\u{2028}` still normalize).
