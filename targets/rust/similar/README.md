# similar

[mitsuhiko/similar](https://github.com/mitsuhiko/similar).

## What is tested

**`src/common.rs`**
- `hegel_capture_diff_apply_roundtrip`: Crown property: diffing `a` against `b` and then applying the resulting ops to `a` must reconstruct `b` exactly, for every algorithm.  Evidence: this is the core contract of a diff (the crate docs describe ops as "ranges of the differences by index in the source sequence" that expand to the changes between the sequences).
- `hegel_ops_partition_both_inputs`: Op-sequence well-formedness: the captured ops partition both inputs. Old ranges tile `0..a.len()` and new ranges tile `0..b.len()`, in order, with no gaps or overlaps.  Evidence: the unit tests `test_compact_keeps_diffop_cursors_contiguous` and `test_regression_issue_95` assert exactly this contract on fixed inputs, and `UnifiedHunkHeader` relies on it.
- `hegel_equal_ops_reference_equal_slices`: Equal ops must reference slices that are actually equal, and no op may be completely empty (`Compact`/`Replace` are documented to clean up the raw hook output; an empty op encodes nothing).  Evidence: `DiffOp::as_tag_tuple` docs say `Equal`: `a[i1..i2]` is equal to `b[j1..j2]`; `test_regression_issue_95` asserts the same.
- `hegel_self_diff_is_all_equal`: Diffing a sequence with itself yields only Equal ops and a ratio of exactly 1.0, for every algorithm.  Uses the full u8 range: identity must hold regardless of alphabet.
- `hegel_grouped_ops_preserve_changes`: Grouping ops for context display must preserve every change: the non-Equal ops of the groups are exactly the non-Equal ops of the original op sequence (in order), and replaying the groups over `a` (copying the elided equal gaps from `a`) reconstructs `b`. Evidence: `group_diff_ops` docs ("Isolate change clusters by eliminating ranges with no changes") and its use by unified diffs.

**`src/text/mod.rs`**
- `hegel_ratio_bounds_and_equality`: `TextDiff::ratio` stays within `0..=1` and is exactly `1.0` iff the inputs are equal.  Evidence: `ratio` docs ("A ratio of 1.0 means the two sequences are a complete match, a ratio of 0.0 would indicate completely distinct sequences").  Token counts here are far below 2^24, so the f32 comparison with 1.0 is exact.
- `hegel_textdiff_changes_reconstruct_inputs`: Concatenating the Equal+Delete change values of a text diff yields the old input and Equal+Insert yields the new input, for every tokenization mode and algorithm.  This is the text-level diff-then-apply roundtrip; it also checks that the tokenizers partition their input.  Uses full-Unicode text as well as line-structured text.
- `hegel_iter_changes_index_consistency`: The changes yielded by `iter_all_changes` carry consistent indices: old indices walk `0..old_len()` and new indices walk `0..new_len()` in order, each index is present according to the tag, and the change value equals the token at that index.  Evidence: `Change` docs and the `iter_changes` doc examples.

**`src/udiff.rs`**
- `hegel_unified_diff_apply_roundtrip`: Unified-diff apply roundtrip: rendering a unified diff of `a` -> `b` and applying the textual patch to `a` with an independent applier reconstructs `b` exactly, for every algorithm and context radius. This exercises diffing, `grouped_ops`, hunk-header arithmetic and the missing-newline handling end to end.  Evidence: this is the documented purpose of the module ("This module provides unified diff functionality") and the format spec linked from `UnifiedDiff::header`.

**`src/utils.rs`**
- `hegel_utils_diffs_concat_to_inputs`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-05-24: predecessor base commit `0210f53830cc` (chore(release): prepare 3.1.1).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/similar.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-12: base bumped 0210f53830cc → 45136acfc28a (2026-08-30, "fix(merge): keep conflict marker labels on one line (#102)"; 3.2.0); 0 bug(s) still reproduce; fixed upstream: similar/1. 146 tests pass. The fix is upstream's own (3.2.0 reworked the algorithms; `lcs.rs` returns early when both inputs are empty), not traced to an issue.
- 2026-09-15: base bumped 45136acfc28a → 157037b12a62 (2026-09-15, "Add similar-rs to Related Projects (#103)"; 3.2.0); 0 bug(s) still reproduce. 148 tests pass.
- 2026-09-16: base bumped 157037b12a62 → 1c6428040122 (2026-09-16, "docs(changelog): describe diff performance and memory improvements"; 3.2.0); 0 bug(s) still reproduce. 160 tests pass.
