# sqlparser

[apache/datafusion-sqlparser-rs](https://github.com/apache/datafusion-sqlparser-rs).

## What is tested

**`src/tokenizer.rs`**
- `hegel_tokenizer_never_panics`: Property: the tokenizer returns `Ok` or `Err` but never panics, for any input, any dialect, and either unescape setting. Evidence: `tokenize` returns `Result<_, TokenizerError>` and the crate's fuzz target feeds arbitrary strings through the parser (which starts with the tokenizer) for every dialect.
- `hegel_token_spans_are_ordered_and_nonoverlapping`: Property: token spans are internally ordered (`start <= end`) and consecutive tokens do not overlap and appear in source order. Evidence: `Span` is documented as "a linear portion of the input string (start, end)" and `tokenize_with_location` is documented to attach the location of each token in the input string.
- `hegel_span_union_commutes`: Property: `Span::union` is commutative. Evidence: `union` is documented as "the smallest Span that contains both `self` and `other`", which is a symmetric specification, and the empty-span rule ("If either span is `Span::empty`, the other span is returned") is symmetric too.
- `hegel_span_union_contains_operands`: Property: for non-empty spans, `Span::union` contains both of its operands. Evidence: `union` docs — "Returns the smallest Span that contains both `self` and `other`".

**`tests/sqlparser_common.rs`**
- `hegel_parse_never_panics_on_arbitrary_input`: Property: `Parser::parse_sql` returns `Ok` or `Err` but never panics, for any input and any dialect. Evidence: this is exactly the property the crate's own fuzz target (`fuzz/fuzz_targets/fuzz_parse_sql.rs`) checks.
- `hegel_parse_display_reparse_is_identity`: Property: for any parseable statement, serializing the AST with `Display` and reparsing yields the same AST. Evidence: `src/lib.rs` ("The original SQL text can be generated from the AST") and `TestedDialects::one_statement_parses_to` in `src/test_utils.rs`, which asserts this for every `verified_stmt` call in the test suite.
- `hegel_pretty_print_reparses_to_same_ast`: Property: pretty-printed SQL (`{:#}`) parses back to the same AST as the compact form. Evidence: `src/lib.rs` "Pretty Printing" section and `tests/pretty_print.rs` (pretty output is shown as real SQL).
- `hegel_number_literal_roundtrip`: Property: an integer literal round-trips through the parser with its textual representation intact. Evidence: `Value::Number(String, bool)` stores the literal text verbatim (src/ast/value.rs), so parsing `SELECT <n>` must preserve `n.to_string()` exactly, for the full `u128` range.
- `hegel_quoted_identifier_roundtrip`: Property: a quoted identifier constructed with `Ident::with_quote` round-trips through Display + parse with its value and quote style intact, for the quote styles that have an escape mechanism (`"` and `` ` ``), over the domain `EscapeQuotedString` documents as round-trippable. Evidence: `Ident::with_quote` documents valid quote characters, `impl Display for Ident` escapes the quote character via `escape_quoted_string` (src/ast/mod.rs), and the tokenizer folds doubled quotes back.
- `hegel_bracket_quoted_identifier_roundtrip`: Property: a bracket-quoted identifier (`Ident::with_quote('[', ..)`, the MSSQL style) round-trips through Display + parse. Evidence: `Ident::with_quote` lists `[` as a valid quote character and the crate documents that "the original SQL text can be generated from the AST" (src/lib.rs). KNOWN FAILURE (suspected library bug, kept failing on purpose): `impl Display for Ident` writes `[{value}]` without escaping `]` (src/ast/mod.rs, `Some('[')` arm), so any value containing `]` produces SQL that cannot be reparsed, e.g. value `]0` displays as `SELECT []0]`. T-SQL escapes `]` by doubling it (QUOTENAME), and the MsSql tokenizer has no `]]` unescaping either, so the round-trip is broken in both directions.
- `hegel_string_literal_roundtrip`: Property: a single-quoted string literal round-trips through Display + parse with its content intact (GenericDialect, which does not treat backslash as an escape character), over the domain `EscapeQuotedString` documents as round-trippable (see `strip_preescaped_sequences`). Evidence: `Value::SingleQuotedString` Display escapes `'` by doubling (src/ast/value.rs `escape_single_quote_string`) and the tokenizer folds `''` back to `'`.
- `hegel_statement_sequences_parse_individually`: Property: parsing `k` statements joined by `"; "` yields exactly the concatenation of parsing each statement individually. Evidence: `Parser::parse_sql` docs ("Parse the specified tokens") and `TestedDialects::statements_parse_to` in `src/test_utils.rs`, which joins canonical statements with `"; "`.
- `hegel_parser_token_navigation_matches_model`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-07-21: predecessor base commit `bef86dd6826e` (Snowflake: parse CREATE WAREHOUSE (#2388)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/sqlparser.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped bef86dd6826e → b5950628a53d (2026-09-10, "Add NOTICE file (#2496)"; 0.63.0); 1 bug(s) still reproduce. 1528 tests pass.
- 2026-09-14: base bumped b5950628a53d → 9296011a1c2b (2026-09-14, "Databricks: support INSERT BY NAME (#2403)"; 0.63.0); 1 bug(s) still reproduce; add/add conflicts in tests/sqlparser_common.rs resolved by keeping both sides. 1531 tests pass.
