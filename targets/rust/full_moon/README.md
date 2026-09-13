# full_moon

[Kampfkarren/full-moon](https://github.com/Kampfkarren/full-moon).

## What is tested

**`src/tokenizer/structs.rs`**
- `lexer_never_panics_on_arbitrary_text`: The lexer must handle any input text without panicking, whatever the LuaVersion — bad input is reported through LexerResult, never a crash. Backticks are stripped from the input: they DO panic the lexer — see the canonical KNOWN FAILURE test `lexing_backtick_returns_error_for_lua51`.
- `lexer_tokens_reprint_to_source`: Losslessness at the token level: when the lexer tokenizes a string cleanly, reprinting every token in order must reproduce the input byte-for-byte.
- `lexer_token_positions_tile_the_source`: Token positions from a clean lex must tile the source exactly: the first token starts at byte 0, every token starts where the previous one ended, each token's byte range slices the source to that token's own text, and the trailing Eof ends at source.len().
- `symbol_with_whitespace_roundtrips`: TokenReference::symbol_specific_lua_version documents that it accepts a symbol surrounded by whitespace, storing the whitespace as trivia — so the constructed TokenReference must display as the exact input.

**`tests/fail_cases.rs`**
- `parse_fallible_never_panics_on_arbitrary_input`: parse_fallible documents that it "always produces some Ast, regardless of errors" — so it must never panic, whatever the input text and whatever the LuaVersion configuration, and the partial Ast it produces must be printable. (Deeply *nested* input is excluded from this guarantee in practice: see the KNOWN FAILURE reproducer `parse_deeply_nested_parens_overflows_stack` below. Uniform random text has no realistic chance of producing hundreds of consecutive `(`s, so no generator constraint is needed here.)

**`tests/pass_cases.rs`**
- `generated_lua_roundtrips_byte_identical`: Crown property: any structurally valid Lua chunk parses successfully, and printing the resulting Ast reproduces the source byte-for-byte, including all whitespace and comment trivia.
- `arbitrary_text_roundtrips_when_parse_succeeds`: Losslessness is not limited to code our generator produces: for *any* string that full_moon::parse accepts, printing the Ast must reproduce it.
- `generated_lua_parses_under_every_version_config`: The generator only emits core Lua 5.1 syntax, which every supported version is a superset of — so the same chunk must parse cleanly (and roundtrip) under every LuaVersion configuration this build supports.
- `generated_lua_update_positions_is_noop_on_fresh_parse`: Ast::update_positions recomputes positions from scratch. For an Ast that came straight from the parser the positions are already correct, so updating them must be a no-op (same check the pass cases make).

**`tests/visitors.rs`**
- `default_visitor_mut_is_identity`: A VisitorMut that overrides nothing must pass the Ast through unchanged: visit_mut rebuilds every node, so this checks that the plumbing preserves every token and every piece of trivia byte-for-byte.
- `rename_visitor_preserves_unrelated_trivia`: Mutating one kind of node through the visitor API must leave everything else — including whitespace and comment trivia — intact. PrefixRenamer prepends `v_` to every local-assignment name (and strips it if present), replacing the token via TokenReference::with_token. Since no generated identifier starts with `v_` (see lua_gen::IDENTIFIERS), applying the visitor twice is an involution: print -> reparse -> rename again must reproduce the original source byte-for-byte, comments and all.

## Oracles

## Not tested

## History

- 2026-04-15: predecessor base commit `47d4bf94104c` (2.2.0).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/full_moon.patch`).
- 2026-09-11: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped 47d4bf94104c → 60f02d5dc223 (2026-08-25, "Shrink AST nodes to fix recursive-parse stack overflows (#346) (#355)"; 3.0.0); 1 bug(s) still reproduce; 1 ignored reproducer(s) not run. 59 tests pass.
