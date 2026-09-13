# yaml-rust2

[Ethiraric/yaml-rust2](https://github.com/Ethiraric/yaml-rust2).

## What is tested

**`tests/basic.rs`**
- `pbt_load_arbitrary_text_never_panics`: The loader must return `Ok` or `Err`, but never panic, whatever the input.
- `pbt_emitted_documents_reparse_to_same_value`: Any document the loader accepts must be re-emittable as valid YAML that parses back to the same value (load → emit → load is the identity on loaded values).
- `pbt_alias_resolves_to_anchored_value`: An alias (`*a`) resolves to the same value as its anchor (`&a`).
- `pbt_decoder_never_panics_on_arbitrary_bytes`: (no doc comment)

**`tests/test_round_trip.rs`**
- `pbt_roundtrip_generated_document`: Any document built from scalars, arrays and hashes survives an emit/load roundtrip unchanged.
- `pbt_roundtrip_generated_document_multiline`: Same roundtrip with the multiline-strings (literal block) emitter mode.
- `pbt_string_scalar_type_and_content_preserved`: A string scalar comes back as `Yaml::String` with identical content, no matter how much it looks like a number/boolean/null or contains YAML syntax.
- `pbt_number_scalar_roundtrip`: Number scalars roundtrip unchanged, including `i64` extremes and exotic float shapes.
- `pbt_multi_document_stream_roundtrip`: A stream of several documents, each emitted with its own `---` header, loads back as the same sequence of documents.
- `pbt_array_of_weird_strings_roundtrip`: Port of the quickcheck property `test_check_weird_keys` (formerly in `tests/quickcheck.rs`): an array of arbitrary strings survives an emit/load roundtrip.
- `known_bug_octal_like_string_changes_type`: KNOWN FAILURE: `need_quotes` (src/emitter.rs) quotes strings starting with `0x` but not `0o`, while the loader (`Yaml::from_str`) parses `0o…` as an octal integer. `String("0o7")` is emitted as bare `0o7` and reloads as `Integer(7)`.
- `known_bug_plus_dot_inf_string_changes_type`: KNOWN FAILURE: `+.inf` is parsed as a float by the loader (`parse_f64`) but not quoted by `need_quotes`. `String("+.inf")` is emitted bare and reloads as `Real("+.inf")`.
- `known_bug_integer_looking_real_changes_type`: KNOWN FAILURE: `Yaml::Real` nodes are emitted verbatim without checking that the text still reads back as a float. `!!float 5` loads as `Real("5")`, which is emitted as bare `5` and reloads as `Integer(5)`.
- `known_bug_multiline_leading_space_line`: KNOWN FAILURE (multiline mode): a literal block scalar line starting with a space breaks block indentation detection. The emitted document either fails to parse (`" a\nb"`) or silently drops the space (`"\n a"`).
- `known_bug_multiline_trailing_newlines_lost`: KNOWN FAILURE (multiline mode): literal blocks are emitted with clip chomping (`|`), so trailing empty lines are lost: `"a\n\n\n"` reloads as `"a\n\n"` and `"\n\n"` reloads as `"\n"`.
- `known_bug_multiline_string_as_hash_key`: KNOWN FAILURE (multiline mode): a multiline string used as a mapping key is emitted as a block scalar in key position, which changes the meaning of the document: `{"a\nb": ~}` is emitted as `|-\n  a\n  b: ~`, which reloads as the single string `"a\nb: ~"`.

## Oracles

## Not tested

## History

- 2025-12-16: predecessor base commit `9f39918876eb` (tests: fix clippy warnings).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/yaml-rust2.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped 9f39918876eb → e12069447073 (2026-09-10, "yaml-rust2 v0.13.0"; 0.13.0); 3 bug(s) still reproduce; 1 ignored reproducer(s) not run. 184 tests pass. yaml-rust2/1 (the YamlDecoder hang on short UTF-16 input, an ignored reproducer the bump does not run) was checked by hand and is fixed: v0.11.1 (issue #78) makes decode_loop reserve at least 4 bytes per iteration; the reproducer now asserts the decoded document.
