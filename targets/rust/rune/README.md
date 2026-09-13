# rune

[rune-rs/rune](https://github.com/rune-rs/rune).

## What is tested

**`tests/derive_from_value.rs`**
- `value_roundtrip_preserves_primitives`: Property: converting a primitive Rust value into a Rune [`Value`] and back yields the original value, over the full domain of each type.
- `value_roundtrip_preserves_compound_values`: Property: converting compound Rust values (strings, vectors, maps, options, tuples) into a Rune [`Value`] and back yields the original.

## Oracles

## Not tested

## History

- 2026-07-20: predecessor base commit `20b26957f18e` (Make indentation configurable and honor LSP formatting options).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/rune.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: a 10× budget run (`--test-cases 1000`) drew `i64::MIN / -1` in
  `arithmetic_matches_checked_i64_reference`: the VM correctly reports `Overflow`, but the
  reference oracle expected every failed `Div`/`Rem` to be `DivideByZero`. Test defect, not a
  bug: the oracle now distinguishes a zero divisor (`DivideByZero`) from `checked_div` failing
  with a non-zero one (`Overflow`); 610 tests pass at 10×.
- 2026-09-13: base bumped 20b26957f18e → bb8e69372353 (2026-08-29, "Fix nightly build"; 0.15.0); 0 bug(s) still reproduce; fixed upstream: rune/1, rune/2; 1 ignored reproducer(s) not run. 608 tests pass. rune/1 (checked negation in `op_neg`) and rune/2 (const evaluator rewritten as `compile/const_eval.rs`) were fixed upstream by 0.15.0; both pins pass. rune/3's ignored stack-overflow reproducer was not re-run.
