# smallvec

[servo/rust-smallvec](https://github.com/servo/rust-smallvec).

## What is tested

**`src/tests.rs`**
- `hegel_model_smallvec_vs_vec`: (no doc comment)
- `hegel_from_vec_into_vec_roundtrip`: (no doc comment)
- `hegel_from_slice_and_from_elem_match_oracle`: (no doc comment)
- `hegel_spill_despill_preserves_elements`: (no doc comment)
- `hegel_insert_from_slice_matches_splice`: (no doc comment)
- `hegel_extend_from_slice_and_within_match_vec`: (no doc comment)
- `hegel_drain_matches_vec`: (no doc comment)
- `hegel_capacity_invariants`: (no doc comment)
- `hegel_into_iter_matches_vec`: (no doc comment)
- `hegel_truncate_resize_across_boundary`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-02-16: predecessor base commit `bc8a854926a8` (Improved const evaluation for ZST checks. (#401)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/smallvec.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1. Five upstream
  `assert_eq!(x, [])`-style asserts in `src/tests.rs` rewritten as `assert!(x.is_empty())`: with
  hegeltest's `serde_json` in scope the element type of the empty array is ambiguous (E0282/E0283).
- 2026-09-13: base bumped bc8a854926a8 → 053f1a7b71b4 (2026-09-11, "refactor: create `src/iterators/` folder and move `rayon.rs` (closes #598) (#600)"; 2.0.0-alpha.13); 0 bug(s) still reproduce. 90 tests pass. Upstream moved its unit tests from `src/tests.rs` to `tests/main.rs` (and dropped the `assert_eq!(x, [])` sites the zoo had to disambiguate), so the hegel module now lives at the end of `tests/main.rs` as an integration test (`smallvec::` paths instead of `crate::`/`alloc::`).
- 2026-09-14: base bumped 053f1a7b71b4 → aefeac3d090a (2026-09-14, "refactor: remove deprecated usage in bench (#611)"; 2.0.0-alpha.13); 0 bug(s) still reproduce. 90 tests pass.
- 2026-09-14: base bumped aefeac3d090a → ed4b23aa0191 (2026-09-14, "fix: overflow on length on not-64-bit (#616)"; 2.0.0-alpha.13); 0 bug(s) still reproduce. 90 tests pass.
