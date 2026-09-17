# taffy

[DioxusLabs/taffy](https://github.com/DioxusLabs/taffy).

## What is tested

**`src/tree/taffy_tree.rs`**
- `hegel_tree_mutations_match_model`: (no doc comment)

**`tests/hand_written/min_max_overrides.rs`**
- `hegel_leaf_size_is_clamped_by_min_and_max`: Property: for a leaf with definite `size`, `min_size` and `max_size`, the computed size is the styled size clamped by max then min - i.e. `max(min(size, max), min)`, with min taking precedence over max (evidence: the `min_overrides_max`, `max_overrides_size` and `min_overrides_size` unit tests above).

**`tests/hand_written/parse.rs`**
- `hegel_style_from_str_never_panics`: Property: the `FromStr` impls provided by the `parse` feature return `Err` on invalid input - they never panic (evidence: `FromStr::Err = ParseError` signatures; the feature is documented as "Implement `FromStr` trait for Taffy style types").

**`tests/hand_written/relayout.rs`**
- `hegel_relayout_is_stable`: Property: computing layout twice in a row with the same available space produces identical layouts for every node (evidence: the `relayout` test above).
- `hegel_relayout_after_mark_dirty_is_stable`: Property: marking an arbitrary node dirty and recomputing (with nothing changed) reproduces the identical layout. Exercises the cache-invalidation path (evidence: `mark_dirty` docs + the caching tests).
- `hegel_layout_outputs_are_finite`: Property: for finite style inputs, every value in the computed layout is finite (no NaN, no infinity). Renderers downstream rely on this.
- `hegel_display_none_root_zeroes_entire_subtree`: Property: a `Display::None` root hides the entire subtree - every node's size and location are zero (evidence: `toggle_root_display_none_with_children` above and `compute_hidden_layout`).
- `hegel_incremental_relayout_matches_fresh_tree`: Property: after an arbitrary tree mutation (style change, node removal, adding a child, detaching a child), recomputing layout produces exactly the same result as computing layout on a fresh tree with the same final structure. This is the incremental-layout / cache-consistency contract (evidence: `set_style`, `add_child`, `remove`, `remove_child_at_index` all promise to invalidate affected caches, and the `relayout`/`caching` tests).

**`tests/hand_written/rounding.rs`**
- `hegel_rounded_layout_values_are_whole_numbers`: Property: with rounding enabled (the default), every rounded layout value (location, size, content_size, scrollbar_size, border, padding) is a whole number (evidence: `round_layout` docs - "Rounds the calculated layout to exact pixel values"). Note that `Layout::margin` is deliberately not asserted on: `round_layout` does not round margins.
- `hegel_rounding_leaves_no_gaps_between_adjacent_children`: Property: rounding does not open gaps (or create overlap) between adjacent children of a flex row - each child's right edge is exactly the next child's left edge, even for fractional sizes (evidence: the `rounding_doesnt_leave_gaps` test above and the `round_layout` doc comment).

## Oracles

## Not tested

## History

- 2026-07-15: predecessor base commit `bb351fcc056c` (Prepare for v0.12.2 release (#979)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/taffy.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped bb351fcc056c → 887a847484ab (2026-09-13, "round_layout: round positions in cumulative coordinates to avoid 1px gaps (#1189)"; 0.14.0); 2 bug(s) still reproduce. 6368 tests pass.
- 2026-09-17: base bumped 887a847484ab → 46c4e9cdf05b (2026-09-17, "Add `Position::Static`, `Position::Fixed` and `Position::Sticky`. Make `Static` default. (#1140)"; 0.14.0); 2 bug(s) still reproduce; add/add conflicts in tests/hand_written.rs resolved by keeping both sides. 6370 tests pass.
- 2026-09-17: base bumped 46c4e9cdf05b → a742a46959a5 (2026-09-17, "gentest: Use computed `position. Measure out-of-flow boxes against their containing block. (#1192)"; 0.14.0); 2 bug(s) still reproduce. 6370 tests pass.
- 2026-09-17: base bumped a742a46959a5 → 996b1c0f2186 (2026-09-17, "flexbox: resolve relative inset at item generation (#1195)"; 0.14.0); 2 bug(s) still reproduce. 6370 tests pass.
