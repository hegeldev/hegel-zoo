# pest

[pest-parser/pest](https://github.com/pest-parser/pest).

## What is tested

**`src/parser.rs`**
- `parse_never_panics_on_arbitrary_input`: The grammar parser must never panic, whatever the input — the same property the upstream fuzz target checks.
- `pipeline_never_panics_on_grammar_shaped_soup`: The full pipeline (parse, validate, consume to AST) must never panic on grammar-shaped token soup: `parse` may reject it, and a successfully parsed grammar may fail validation or AST construction, but always via `Err`, never via panic.
- `deeply_nested_expressions_never_panic`: Deeply nested expressions must not crash the parser or the AST builder. The depth is capped at 150 because `consume_rules` stack-overflows (aborting the process) at roughly depth 460+ in dev builds — the cap protects the test process, not any documented contract; see `pinned_stack_overflow_in_consume_rules_on_deep_nesting`. The global call limit is intentionally not touched here: if another test has set it, deep inputs may parse to `Err("call limit reached")`, which this property tolerates — it only demands "no panic, no abort" for every nesting shape and depth.
- `generated_valid_grammars_pass_the_full_pipeline`: Every generated valid grammar must pass the whole pipeline — parse, validate, AST construction, optimization — with the rule names preserved in definition order at every stage. Generated grammars are small (a handful of rules, expression depth <= 3), so they parse well within the 5000-call limit that other tests in this binary set process-wide.
- `stray_trailing_token_is_rejected`: Rejection converse of the pipeline property: appending a token that cannot start a new grammar rule to a valid grammar must produce a parse error (not a panic, and not silent acceptance).

## Oracles

## Not tested

## History

- 2026-07-22: predecessor base commit `81eeedbae691` (ci toolchain in release update + bump version (#1181)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/pest.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
