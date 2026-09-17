# starlark

[facebook/starlark-rust](https://github.com/facebook/starlark-rust).

## What is tested

**`src/tests/basic.rs`**
- `test_prop_int_binop_matches_bigint_reference`: Every Starlark integer binary operator agrees with an independent `num_bigint` reference implementation, across inline-int boundaries and values wider than any machine integer. Evidence: docs/types.md says Starlark ints are arbitrary precision; `//` and `%` follow Python floor semantics (see `test_arithmetic` / `test_bitwise` above for hand-picked instances of the same claims).
- `test_prop_int_shift_matches_bigint_reference`: Left/right shifts agree with `num_bigint` (which, like Starlark, shifts negative numbers with floor semantics).
- `test_prop_int_comparison_matches_bigint_reference`: Integer comparison operators agree with `num_bigint`'s `Ord`.
- `test_prop_nested_int_arithmetic_matches_bigint_reference`: (no doc comment)
- `test_prop_sorted_matches_rust_sort`: `sorted` on a list of ints agrees with Rust's slice sort. Evidence: stdlib docs for `sorted` promise the sorted elements.
- `test_prop_string_repr_parse_eval_roundtrip`: `repr` of a string produces a literal that parses and evaluates back to the same string. The writer is `StarlarkStr::repr` (the same code as the `repr()` builtin); the reader is the independent lexer path.
- `test_prop_string_len_matches_char_count`: `len` of a string counts chars, consistently with Rust's `str::chars().count()` (see `StarlarkStr::length`, which uses `fast_string::len`).
- `test_prop_equal_dict_keys_collide`: The eq/hash contract, observed through dicts: inserting `x` and `y` as keys leaves one entry iff `x == y`. This catches any type pair that compares equal but hashes differently (e.g. `1` vs `1.0` vs `340282366920938463463374607431768211456`), and any hash collision mishandling in the dict itself. Evidence: `pointer_i32.rs` and `float.rs` both hash through `NumRef::get_hash_64` precisely so that equal numbers hash equal.

**`src/tests/call.rs`**
- `test_prop_unbounded_recursion_errors_gracefully`: Unbounded Starlark recursion always fails with the documented "Starlark call stack overflow" error (a graceful `Err`, not a native stack overflow aborting the process), whatever the shape of the call cycle and whatever (documented-valid) callstack limit is configured. Evidence: `funcall_test` above checks the `rec1`/`rec2` cases; `Evaluator::set_max_callstack_size` documents the configurable limit; the error text is from `cheap_call_stack.rs`.

**`src/tests/uncategorized.rs`**
- `test_prop_parse_never_panics`: `AstModule::parse` returns `Err` rather than panicking on arbitrary input, and the returned error can be Debug-formatted. Evidence: parse returns `crate::Result`; the `test_fuzzer_*` tests above pin past oss-fuzz panics of exactly this shape (including panics that only fired when formatting the error).
- `test_prop_parse_print_reparse_roundtrip`: Pretty-printing a parsed module yields text that (a) is valid Starlark, and (b) pretty-prints to itself after re-parsing. Evidence: `Display for Stmt`/`Expr` in `starlark_syntax/src/syntax/ast.rs` prints programs in concrete syntax; the pinned `test_*_display_reparses` tests above show maintainer-visible cases where this is violated.
- `test_prop_moderately_nested_expressions_evaluate`: Nested expressions of any shape parse and evaluate correctly up to a conservative depth (well below the crash thresholds measured above). The depth bound protects the test process from the KNOWN BUG pinned by `test_parser_stack_overflow_on_deeply_nested_parens` and `test_eval_stack_overflow_on_deeply_nested_unary` above — it is not a documented library limit.

## Oracles

## Not tested

## History

- 2026-07-22: predecessor base commit `dd23c83b49ff` (Preserve `FrozenHeapName` across paging).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/starlark.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped dd23c83b49ff → d596084ab5f6 (2026-09-12, "Bump either 1.17.0 -> 1.18.0"; 0.14.2); 0 bug(s) still reproduce; fixed upstream: starlark/1, starlark/2, starlark/3; 2 ignored reproducer(s) not run. 985 tests pass. starlark/1, /2 and /3 (the AST Display bugs) are all fixed in this range: slices, f-strings and attribute access on integer literals print as valid Starlark, the three pins pass and the parse→print→re-parse property generates those constructs again. starlark/4 and /5 (process-aborting reproducers) were not run.
- 2026-09-13: base bumped d596084ab5f6 → 13227c01be64 (2026-09-12, "Bump indexmap 2.14.0 -> 2.14.2"; 0.14.2); 0 bug(s) still reproduce; 2 ignored reproducer(s) not run. 988 tests pass.
- 2026-09-14: base bumped 13227c01be64 → c9aecfd21249 (2026-09-14, "Bump textwrap 0.16.2 -> 0.16.3"; 0.14.2); 0 bug(s) still reproduce; 2 ignored reproducer(s) not run. 988 tests pass.
- 2026-09-14: base bumped c9aecfd21249 → 108ffc75ea24 (2026-09-14, "Run the focused Miri suite in GitHub CI (#239)"; 0.14.2); 0 bug(s) still reproduce; 2 ignored reproducer(s) not run. 988 tests pass.
- 2026-09-14: base bumped 108ffc75ea24 → 59d371e92bf2 (2026-09-14, "Suppress unreachable-code warnings in UnpackValue derive"; 0.14.2); 0 bug(s) still reproduce; 2 ignored reproducer(s) not run. 988 tests pass.
- 2026-09-15: base bumped 59d371e92bf2 → 241c58d0e441 (2026-09-15, "Hoist the stack write-back out of the branches in `repr_stack_push`"; 0.14.2); 0 bug(s) still reproduce; 2 ignored reproducer(s) not run. 989 tests pass.
- 2026-09-16: base bumped 241c58d0e441 → fc7a4188d112 (2026-09-15, "Stop overflowing the chunk size for a heap with many chunks"; 0.14.2); 0 bug(s) still reproduce; 2 ignored reproducer(s) not run. 990 tests pass.
- 2026-09-16: base bumped fc7a4188d112 → cc22bd69390f (2026-09-15, "Split the Starlark wait-for graph's hot map out from its lock"; 0.14.2); 0 bug(s) still reproduce; 2 ignored reproducer(s) not run. 992 tests pass.
- 2026-09-17: base bumped cc22bd69390f → 5d1aa66b7870 (2026-09-17, "lifetimes: Comments stop contrasting with the unbranded world"; 0.14.2); 0 bug(s) still reproduce; 2 ignored reproducer(s) not run. 992 tests pass.
- 2026-09-17: base bumped 5d1aa66b7870 → 5a27850a2fe7 (2026-09-17, "lifetimes: `frozen_only` asks nothing of the fields"; 0.14.2); 0 bug(s) still reproduce; 2 ignored reproducer(s) not run. 992 tests pass.
