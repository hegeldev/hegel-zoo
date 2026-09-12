# pulldown-cmark

[raphlinus/pulldown-cmark](https://github.com/raphlinus/pulldown-cmark).

## What is tested

**`src/parse.rs`**
- `plain_text_paragraph_content_is_preserved`: Property: for paragraphs of plain text (no markdown-significant characters, no leading/trailing spaces per line), the parser preserves the text exactly: concatenating `Text` events with a newline at each `SoftBreak` reconstructs the input.
- `atx_heading_level_matches_hash_count`: Property: `#` runs of length 1..=6 followed by a space produce an ATX heading of exactly that level (spec: ATX headings); longer runs are not headings at all.

**`src/utils.rs`**
- `text_merge_stream_matches_reference_model`: Hegel property: `TextMergeStream` agrees with a straightforward reference model of its documented behavior — runs of two or more consecutive `Text` events are merged into one (and dropped entirely if the merged text is empty), everything else passes through unchanged. In particular the merged stream never contains two adjacent `Text` events.

**`tests/errors.rs`**
- `parse_never_panics_on_arbitrary_input`: Property: fully consuming `Parser::new_ext` never panics, for arbitrary Unicode text and arbitrary option combinations.
- `parse_never_panics_on_markdown_shaped_input`: Property: fully consuming `Parser::new_ext` never panics on structured, mostly well-formed markdown documents exercising all extensions.
- `offset_iter_ranges_are_valid_slices`: Property: every event's source range is in-bounds and lies on UTF-8 character boundaries, so `&text[range]` is always a valid slice. This is the general form of the `test_bad_slice_*` regressions above (issue #521).
- `start_end_events_are_balanced_and_nested`: Property: Start/End events are properly balanced (LIFO, matching kinds, nothing left open at EOF), every event is contained in the source range of its enclosing Start tag, and an End event carries the same range as its matching Start.
- `deeply_nested_input_parses_in_bounded_time`: Property: parsing deeply nested single-line constructs (blockquotes, lists, emphasis, link/image/wikilink brackets, code/math delimiters, ...) terminates in bounded time with a linearly bounded number of events, and does not overflow the stack. Untrusted-markdown DoS is the classic bug class here; the dos-fuzzer/ directory exists because of it.
- `deeply_nested_multiline_input_parses_in_bounded_time`: Property: same as above, for constructs that nest across *lines* (indentation-nested lists, increasing blockquote chains, containers, nested GFM alerts) where input size grows with nesting depth.
- `repeated_pattern_has_linear_event_count_and_bounded_time`: Property: repeating a short adversarial pattern many times (the axis the dos-fuzzer/ tool explores, and the shape of the wikilink event blowup fixed in #1111) keeps the event count linear in input size and parse time bounded.

**`tests/html.rs`**
- `push_html_never_panics_and_is_deterministic`: Property: `html::push_html` never panics and is deterministic — rendering the same input with the same options twice yields byte-identical HTML.
- `push_html_appends_and_matches_write_html_fmt`: Property: `push_html` appends to the provided buffer without disturbing its existing contents, and `write_html_fmt` produces the same HTML.

## Oracles

## Not tested

## History

- 2026-07-08: predecessor base commit `68afb08c9014` (Merge pull request #1111 from teddytennant/fix-wikilink-overflow).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/pulldown-cmark.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
