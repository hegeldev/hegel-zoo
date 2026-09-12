# edn-rs

[edn-rs/edn-rs](https://github.com/edn-rs/edn-rs).

## What is tested

**`tests/parse.rs`**
- `prop_serialize_parse_fixpoint`: ------------------------------------------------------------------ Property 1: serialize -> parse is the identity on parser-canonical values, and serialization is a fixpoint. ------------------------------------------------------------------
- `prop_parse_never_panics`: (no doc comment)
- `prop_deeply_nested_collections_parse`: ------------------------------------------------------------------ Property 3: deeply nested balanced collections parse successfully. Depth is capped at 300 because the parser recurses once per nesting level and overflows the 2 MiB test-thread stack at roughly depth 1000 (a real bug). The cap protects the test process, not the library's contract — see `known_bug_deep_nesting_stack_overflow` below. ------------------------------------------------------------------
- `prop_integer_decimal_roundtrip`: ------------------------------------------------------------------ Property 4: decimal integers parse to the correct value across the full i64/u64 range (boundaries included). The parser's canonical form is UInt for non-negative values and Int for negatives; a redundant leading '+' is allowed by the EDN spec. ------------------------------------------------------------------
- `prop_radix_integer_parse`: (no doc comment)
- `prop_string_escape_roundtrip`: ------------------------------------------------------------------ Property 6: strings round-trip through serialization, generated at the escape-set boundary (quotes, backslashes, \n \r \t, delimiters, comment characters, full Unicode). ------------------------------------------------------------------
- `prop_char_roundtrip`: ------------------------------------------------------------------ Property 7: char literals round-trip through serialization, including the named literals (\newline \return \tab \space) and delimiters. ------------------------------------------------------------------
- `prop_keyword_roundtrip`: ------------------------------------------------------------------ Property 8: keywords (including namespaced ones) parse to Edn::Key and serialize back to the same text. ------------------------------------------------------------------
- `prop_symbol_roundtrip`: ------------------------------------------------------------------ Property 9: symbols (including namespaced ones) parse to Edn::Symbol and serialize back to the same text. ------------------------------------------------------------------
- `prop_whitespace_comment_discard_insensitivity`: (no doc comment)
- `known_bug_whole_double_reparses_as_integer`: KNOWN FAILURE — real bug: `Edn::Double` of a whole number serializes without a ".0" suffix (`Edn::Double(3.0).to_string() == "3"`), so it reparses as `Edn::UInt(3)`/`Edn::Int(-3)`. EDN distinguishes `3` from `3.0`; the emitted text silently changes the value's type. (Related: `Double(f64::NAN)`/`Double(f64::INFINITY)` serialize as `NaN`/`inf`, which are not valid EDN and reparse as symbols.)
- `known_bug_control_char_in_string_does_not_reparse`: KNOWN FAILURE — real bug: `Edn::Str` serializes via Rust's `{:?}` formatting, which escapes control characters as `\u{7f}` etc. The parser only understands \t \r \n \\ \" and rejects `\u`, so any string containing a control character serializes to unparseable EDN.
- `known_bug_unicode_whitespace_char_does_not_reparse`: KNOWN FAILURE — real bug: `Edn::Char` of a non-ASCII whitespace character (U+00A0 NBSP, U+2028 LINE SEPARATOR, ...) serializes as `\<char>`, but the parser reads char literals with `take_while(!is_whitespace)`, sees an empty element, and errors.
- `known_bug_radix_digits_with_e_misparse_as_double`: KNOWN FAILURE — real bug: after stripping a `0x`/`NNr` radix prefix, the parser checks the remaining digits against float notation *first*, so hex/radix digit strings that happen to look like `<digits>e<digits>` are misparsed as doubles: `0x5e5` parses as `Double(500000.0)` instead of `UInt(0x5e5) == UInt(1509)`.
- `known_bug_single_char_symbol_at_eof_fails`: KNOWN FAILURE — real bug: a single-character symbol at the end of the input fails to parse: `Edn::from_str("a")` returns `Err(ParseEdn("Could not identify symbol index"))`. `read_symbol` (and `read_bool_or_nil`) unconditionally require a lookahead character to compute an error-message index, so a symbol whose last char is the last char of the document errors out. `"a "` (trailing space) parses fine. Also reproduces nested at end-of-document, e.g. `"#A A"` (a tagged element whose value is a single-char symbol).

## Oracles

## Not tested

## History

- 2026-06-18: predecessor base commit `557ac2732fb2` (Merge pull request #174 from naomijub/renovate/actions-checkout-7.x).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/edn-rs.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
