# rhai

[rhaiscript/rhai](https://github.com/rhaiscript/rhai).

## What is tested

**`tests/float.rs`**
- `test_float_literal_debug_roundtrip`: Property: any finite FLOAT value printed with Rust's shortest-roundtrip `{:?}` format parses back (as a rhai float literal) to the bit-identical value. Evidence: the tokenizer parses float literals with `FloatWrapper::from_str` (a thin wrapper over `FLOAT::from_str`, src/tokenizer.rs), including scientific notation, and folds a leading `-` in unary position into the literal; Rust guarantees `{:?}` output round-trips through `from_str`.

**`tests/math.rs`**
- `test_int_arithmetic_matches_checked_reference`: (no doc comment)

**`tests/number_literals.rs`**
- `test_int_literal_display_roundtrip`: Property: any INT value printed in decimal parses back (as a rhai number literal) to the same value. Evidence: the tokenizer parses decimal literals with `INT::from_str` (src/tokenizer.rs) and folds a leading `-` in unary position into the literal, so every `INT`, including `INT::MIN`, has a literal spelling.

**`tests/operations.rs`**
- `test_max_operations_terminates_infinite_loop`: Property: any positive `max_operations` limit actually terminates an infinite loop with `ErrorTooManyOperations` (and never panics or hangs). Evidence: `set_max_operations` docs ("Set the maximum number of operations allowed for a script to run to avoid consuming too much resources") and `test_max_operations` above.
- `test_eval_arbitrary_input_with_limits_never_panics`: Property: with resource limits configured (as in `fuzz/fuzz_targets/scripting.rs`), compiling and evaluating arbitrary script-shaped input never panics, at any optimization level. The operations limit guarantees termination.

**`tests/optimizer.rs`**
- `test_optimization_levels_agree`: Property: the same well-formed script produces the same result (value, or error kind) under OptimizationLevel::None, Simple and Full. Evidence: optimization is documented as semantics-preserving — the optimizer only folds constants, prunes dead code and eagerly calls pure built-ins (src/optimizer.rs); `test_optimizer_run` above runs the same scripts at all three levels expecting identical results. The generated scripts are side-effect-free, terminating and result in an INT. `set_fast_operators` is part of the generated configuration.

**`tests/stack.rs`**
- `test_expr_depth_limit_never_panics`: Property: with expression-depth limits configured anywhere up to the build's own defaults, compiling an arbitrarily deeply nested (but syntactically valid) expression never panics or overflows the stack — it either compiles or fails with `ParseErrorType::ExprTooDeep`. Evidence: `set_max_expr_depths` exists to bound parser recursion, and `test_stack_overflow_parsing` above pins specific instances. The drawn limits are capped at the build's *default* limits: an earlier version of this property drew limits up to 200 and found that e.g. `set_max_expr_depths(187, 187)` with a 185-term `1 + 1 + ...` chain overflows a standard 2 MiB test-thread stack in a debug build (see `test_expr_depth_reproducer_stack_overflow` below). That is not a violation of a documented contract — the safe limit is deliberately build-dependent (debug default 32 vs release 64, src/api/limits.rs), and matching the limit to the available stack is the caller's job — but it is why this generator does not exceed the defaults.

**`tests/string.rs`**
- `test_string_literal_escape_roundtrip`: Property: a rhai string literal built by escaping the characters of an arbitrary Rust string evaluates back to exactly that string. Evidence: the tokenizer implements `\x`/`\u`/`\U` hex escapes plus `\\`, `\"`, `\t`, `\r`, `\n` (src/tokenizer.rs, `parse_string_literal`), and `test_string` above pins individual examples (e.g. `❤`). Each character is either escaped as `\U????????` or, when it does not require escaping, included verbatim (chosen per character), exercising both the escape decoder and the verbatim path.

**`tests/tokens.rs`**
- `test_compile_never_panics_on_arbitrary_input`: Property: `Engine::compile` never panics, whatever the input text — arbitrary Unicode or script-shaped token soup. Evidence: `compile` returns `ParseResult` (it promises errors, not panics), and `fuzz/fuzz_targets/scripting.rs` feeds arbitrary strings to `compile` for exactly this reason.
- `test_compact_script_preserves_semantics`: Property: `Engine::compact_script` output is semantically identical to its input, per its documentation ("The output script is semantically identical to the input script, except smaller in size."). Evidence: doc-comment on `compact_script` (src/api/formatting.rs); commit fcb384fd fixed compact_script fusing adjacent operators (`< -` -> `<-`), which is exactly the bug class this property targets.
- `test_compact_script_output_recompiles`: Property: if a script compiles, then its compacted form also compiles. Runs on token soup with randomized whitespace, which explores exactly the token-adjacency space where compact_script previously produced invalid output (commit fcb384fd: `< -` fused into `<-`).

**`tests/var_scope.rs`**
- `test_scope_push_then_eval_roundtrip`: Property: a value pushed into a `Scope` under an arbitrary valid identifier is returned unchanged when a script evaluates that identifier, and remains in the scope afterwards. Evidence: `Scope::push` / `eval_with_scope` docs and `test_var_scope` above; `fuzz/fuzz_targets/scripting.rs` pushes arbitrary named variables into scopes the same way.

## Oracles

## Not tested

## History

- 2026-07-18: predecessor base commit `950b724b8f1d` (Merge pull request #1106 from yuvalrakavy/fix-compact-script-operat...).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/rhai.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped 950b724b8f1d → 4d9e4d80809f (2026-09-09, "Merge pull request #1162 from rhaiscript/vm-refine-switch-stmt"; 1.26.0); 0 bug(s) still reproduce. 389 tests pass.
- 2026-09-13: base bumped 4d9e4d80809f → ef2092d49523 (2026-09-13, "Move Ident out of AST."; 1.26.0); 0 bug(s) still reproduce. 389 tests pass.
- 2026-09-13: base bumped ef2092d49523 → 74bf227ff4c9 (2026-09-14, "Merge pull request #1164 from rhaiscript/vm-revise-walk-property"; 1.26.0); 0 bug(s) still reproduce. 389 tests pass.
- 2026-09-14: base bumped 74bf227ff4c9 → d8bff1070ee8 (2026-09-14, "Merge pull request #1163 from rhaiscript/vm-speed-up-chaining-assign"; 1.26.0); 0 bug(s) still reproduce. 389 tests pass.
- 2026-09-14: base bumped d8bff1070ee8 → 470610f692b7 (2026-09-14, "Merge branch 'fix'"; 1.26.1); 0 bug(s) still reproduce. 390 tests pass.
- 2026-09-14: base bumped 470610f692b7 → eee50e8f15be (2026-09-14, "Merge pull request #1169 from rhaiscript/vm-optimize-loops"; 1.26.1); 0 bug(s) still reproduce. 390 tests pass.
- 2026-09-14: base bumped eee50e8f15be → 9ff002f33f6f (2026-09-14, "Fix bug in loop lowering."; 1.26.1); 0 bug(s) still reproduce. 390 tests pass.
- 2026-09-14: base bumped 9ff002f33f6f → c7848752c2c8 (2026-09-14, "Use walk API to detect `break` in loops."; 1.26.1); 0 bug(s) still reproduce. 390 tests pass.
- 2026-09-15: base bumped c7848752c2c8 → 354ba7407f38 (2026-09-15, "Show source error line when running Grain bytecodes"; 1.26.1); 0 bug(s) still reproduce. 390 tests pass.
- 2026-09-15: base bumped 354ba7407f38 → 2925e069f89e (2026-09-15, "Fix errors under no_ast."; 1.26.1); 0 bug(s) still reproduce. 390 tests pass.
- 2026-09-16: base bumped 2925e069f89e → 847a842affb9 (2026-09-16, "Merge pull request #1170 from schungx/master"; 1.26.1); 0 bug(s) still reproduce. 390 tests pass.
