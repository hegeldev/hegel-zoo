# jotdown

[hellux/jotdown](https://github.com/hellux/jotdown).

## What is tested

**`tests/properties.rs`**
- `parse_never_panics_arbitrary_text`: (no doc comment)
- `parse_never_panics_djot_shaped`: (no doc comment)
- `deep_nesting_bounded_no_abort`: (no doc comment)
- `event_balance_arbitrary_text`: (no doc comment)
- `event_balance_djot_shaped`: (no doc comment)
- `spans_valid_arbitrary_text`: (no doc comment)
- `spans_valid_djot_shaped`: (no doc comment)
- `html_render_never_panics_and_deterministic`: (no doc comment)
- `render_apis_agree`: (no doc comment)
- `str_content_is_subsequence_arbitrary`: (no doc comment)
- `str_content_is_subsequence_djot`: (no doc comment)
- `attributes_parse_never_panics_arbitrary`: (no doc comment)
- `attributes_parse_never_panics_shaped`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-07-06: predecessor base commit `56d6d1b3d707` (.gitignore: add afl output dir).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/jotdown.patch`).
- 2026-09-11: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped 56d6d1b3d707 → cf898a37746d (2026-08-13, "tests/parse_events: rm redundant .into()"; 0.10.0); 0 bug(s) still reproduce; 1 ignored reproducer(s) not run. 346 tests pass.
