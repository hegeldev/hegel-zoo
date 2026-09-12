# swash

[dfrg/swash](https://github.com/dfrg/swash).

## What is tested

**`tests/property_tests.rs`**
- `fontref_from_arbitrary_bytes_no_panic`: `FontDataRef::new` and `FontRef::from_index` must never panic on arbitrary bytes, and any font they hand back must survive the full accessor sweep.
- `wire_shaped_sfnt_no_panic`: The "wire-shaped garbage" pattern: build bytes with a valid sfnt version and a generated table directory (arbitrary tags, offsets, and lengths), so we get past the `is_font` gate and drive the table-parsing paths with structurally plausible but semantically arbitrary content.
- `corrupted_real_fonts_no_panic`: Bit-flipped / truncated copies of real fonts must not panic. Real fonts get us deep into every table parser; corruption then stresses the bounds checks.
- `charmap_map_in_glyph_count_bounds`: `Charmap::map` must not panic for any `u32` codepoint, and the returned nominal glyph id must index into the font's glyph set (`< glyph_count`). A cmap that hands out glyph ids past `maxp.numGlyphs` would produce out-of-bounds lookups downstream.
- `charmap_enumerate_agrees_with_map`: Consistency between the two charmap query paths: every (codepoint, glyph) pair produced by `enumerate` must map back to the same glyph via `map`. enumerate only ever yields non-zero glyph ids, so the symbol-remap fallback in `map` (which only fires when the primary lookup is 0) does not interfere.
- `glyph_metrics_finite_and_no_panic`: Glyph metric accessors must not panic for any glyph id across the full u16 range, and for glyph ids within the font's glyph count they must return finite values.
- `variation_normalize_in_range`: `Variation::normalize` must accept any `f32` (including NaN, infinities and values far outside the axis range) without panicking, and the resulting normalized coordinate must lie within the valid 2.14 normalized range [-1.0, 1.0], i.e. bits in [-16384, 16384].
- `normalized_coords_no_panic`: `Variations::normalized_coords` must accept arbitrary settings (arbitrary tags and non-finite values) without panicking, and every produced coordinate must be a valid normalized 2.14 value.
- `shaper_cluster_invariants`: Shaping arbitrary text with a real font must not panic, and the resulting glyph clusters must satisfy the documented cluster invariants:   * every source range lies within the input byte range;   * cluster source starts are monotonically non-decreasing (LTR shaping);   * all glyph positions and advances are finite.
- `shaper_arbitrary_variations_no_panic`: Building a shaper with arbitrary variation settings (including non-finite values) and shaping text must not panic.
- `scaler_outline_no_panic`: (no doc comment)
- `glyph_advance_underflow_on_zero_long_metrics`: KNOWN FAILURE: `GlyphMetrics::advance_width` panics with "attempt to subtract with overflow" for any glyph id when the font's long-metric count is 0. Root cause: `internal::xmtx::advance` (and `sb`) compute `(long_metric_count - 1)` on a `u16`. When the count is 0 — which happens when a font has an `hhea` table reporting `numberOfHMetrics == 0` (`CMAP4_SYMBOL_PUA` is such a real font) or when metric extraction bails early on malformed data, leaving `hmtx_count` at its default of 0 — this underflows and panics in debug builds (and reads out of the intended slot in release). The condition `glyph_id < 0` is never true, so *every* glyph id takes the underflowing branch. The correct behavior is to return 0 (or the first metric) without panicking. This test asserts that the call completes; it fails deterministically until the bug is fixed. It is NOT `#[ignore]`d because it panics cleanly (it does not abort or hang the process).
- `check_range_underflow_on_truncated_font`: KNOWN FAILURE: `internal::parse::Bytes::check_range` panics with "attempt to subtract with overflow" when queried with an offset beyond the end of the buffer. Root cause (src/internal/parse.rs:39): ```ignore pub fn check_range(&self, offset: usize, len: usize) -> bool {     let end = self.0.len();     (offset < end) & (end - offset >= len)   // `&` is NOT short-circuiting } ``` The bitwise `&` evaluates both operands, so `end - offset` is computed even when `offset >= end`, underflowing `usize`. A short-circuiting `&&` (or `end.checked_sub(offset)`) would be correct. This is reachable from the public API on truncated/corrupted fonts: e.g. `CMAP12_FONT1` truncated to 138 bytes places a format-12 cmap subtable so near the end of the buffer that `Charmap::map` calls `ensure_range` with an offset past the (now shorter) subtable slice. Fails deterministically until fixed; panics cleanly (no abort/hang), so it is not `#[ignore]`d.

## Oracles

## Not tested

## History

- 2026-07-17: predecessor base commit `7773843df0d6` (Bump version number to 0.2.10 (#132)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/swash.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
