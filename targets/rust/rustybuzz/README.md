# rustybuzz

[harfbuzz/rustybuzz](https://github.com/harfbuzz/rustybuzz).

## What is tested

**`tests/shaping/main.rs`**
- `spec_string_parsers_never_panic`: Property: the `FromStr` spec-string parsers (`Feature`, `Variation`, `Language`, `Direction`) return an error rather than panicking, for both arbitrary strings and strings shaped like feature/variation specs.
- `feature_from_str_parses_constructed_feature_strings`: Property: `Feature::from_str` parses the documented spec forms (`kern`, `+kern`, `-kern`, `kern=2`, `kern[3:5]`, `kern[3:5]=2`, `kern=on/off`) into the documented tag/value/range.
- `guess_segment_properties_is_idempotent`: Property: `guess_segment_properties` always resolves a direction and is idempotent — a second call never changes direction, script or language.

## Oracles

## Not tested

## History

- 2025-06-09: predecessor base commit `51d99b83ae78` ([buffer] Fix buffer size enlargement (harfruzz PR #62)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/rustybuzz.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped 51d99b83ae78 → 9faca9674086 (2026-07-26, "Deprecate in preference to HarfRust"; 0.20.1); 2 bug(s) still reproduce. 10 tests pass.
