# rustybuzz

[harfbuzz/rustybuzz](https://github.com/harfbuzz/rustybuzz).

## What is tested

**`tests/shaping/main.rs`**
- `spec_string_parsers_never_panic`: Property: the `FromStr` spec-string parsers (`Feature`, `Variation`, `Language`, `Direction`) return an error rather than panicking, for both arbitrary strings and strings shaped like feature/variation specs.
- `feature_from_str_parses_constructed_feature_strings`: Property: `Feature::from_str` parses the documented spec forms (`kern`, `+kern`, `-kern`, `kern=2`, `kern[3:5]`, `kern[3:5]=2`, `kern=on/off`) into the documented tag/value/range.
- `guess_segment_properties_is_idempotent`: Property: `guess_segment_properties` always resolves a direction and is idempotent — a second call never changes direction, script or language.
- `shaping_with_mutated_fonts_never_panics`: Property: a test font, optionally truncated and with a few bytes mutated, either fails `Face::from_slice` or shapes random text under random settings and features without panicking (one mutated byte in a cmap count reaches rustybuzz/3, drawn by default).
- `oversized_cmap_subtable_count_never_panics`: the region of rustybuzz/3 with random contents: one of the five 32-bit cmap count fields of the test fonts set to a count whose byte size exceeds `u32::MAX`, then `from_slice`, shaping and serialisation with random text, settings and features. Fails every run; under `HEGEL_NO_KNOWN=1` ttf-parser's assertion is caught and counted as a rejected font.
- `known_failure_cmap_count_above_u32_max_bytes_panics`: pin of rustybuzz/3: Zycon.ttf with byte 580 (the high byte of a format-12 `numGroups`) set to 22 panics in `Face::from_slice`.
- `nonempty_text_shapes_to_at_least_one_glyph`: Property: non-empty text shapes to at least one glyph, unless the text is all default ignorables on a font without a space glyph (rustybuzz, like HarfBuzz, then deletes them) and `PRESERVE_DEFAULT_IGNORABLES` is off.

## Oracles

## Not tested

## Known bugs (drawn by default)

rustybuzz/3: `Face::from_slice` panics in debug builds on a font whose cmap format 12/13/14 subtable declares a 32-bit count whose byte size exceeds `u32::MAX` (ttf-parser's `Stream::read_bytes` asserts `offset + len <= u32::MAX` before its bounds check; root cause in ttf-parser, like rustybuzz/2). The wide property `shaping_with_mutated_fonts_never_panics` keeps mutating any byte and is mapped to rustybuzz/3 as intermittent (about one case in a few thousand; found by the weekly 1000-case run); `oversized_cmap_subtable_count_never_panics` draws only those counts and fails every run; `HEGEL_NO_KNOWN=1` (read once) makes both catch that one assertion and reject the font, and the pin stays. rustybuzz/1 and /2 keep their `known_failure_*` pins.

## History

- 2025-06-09: predecessor base commit `51d99b83ae78` ([buffer] Fix buffer size enlargement (harfruzz PR #62)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/rustybuzz.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped 51d99b83ae78 → 9faca9674086 (2026-07-26, "Deprecate in preference to HarfRust"; 0.20.1); 2 bug(s) still reproduce. 10 tests pass.
- 2026-10-06: rustybuzz/3 found by the weekly run's 1000-case budget on `shaping_with_mutated_fonts_never_panics` (ttf-parser's `read_bytes` assertion on an oversized cmap count); mapped intermittent, narrow property `oversized_cmap_subtable_count_never_panics` and pin `known_failure_cmap_count_above_u32_max_bytes_panics` added, `HEGEL_NO_KNOWN=1` gate; `nonempty_text_shapes_to_at_least_one_glyph` corrected for all-default-ignorable text on fonts without a space glyph.
