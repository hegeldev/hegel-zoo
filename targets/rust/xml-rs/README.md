# xml-rs

[kornelski/xml-rs](https://github.com/kornelski/xml-rs).

## What is tested

**`tests/event_reader.rs`**
- `parser_never_panics_on_arbitrary_input`: Property: fully driving `EventReader` never panics and always terminates with `EndDocument` or an error, on arbitrary bytes, text, and XML-shaped soup, under arbitrary parser configurations. The documented terminal-event contract also holds: after `Err` or `EndDocument`, `next()` returns the same event again.
- `event_stream_is_well_nested`: Property: the event stream is always well-nested — every `EndElement` matches the most recent unclosed `StartElement` (same name, LIFO), and `EndDocument` is only reached with no elements left open. This must hold for every prefix of events the parser produces, even when it later errors out.
- `deeply_nested_documents_never_crash`: Property: deeply nested documents (`<a><a>…</a></a>`) never crash the process — the parser keeps its element stack on the heap. A properly closed document of depth N produces exactly N starts and N ends; a truncated one ends in an error, not a panic. The depth is capped at 1200 to keep the test's runtime sane: parsing is O(depth^2) (see `known_issue_deep_nesting_quadratic_time` below). The cap protects the test's runtime, not any library contract.
- `entity_expansion_bombs_are_rejected`: Property: "billion laughs" entity-expansion bombs are rejected with an error (`EntityTooBig`), never a hang, OOM, or panic. Whenever the full expansion would exceed the default `max_entity_expansion_length`, the parser must return `Err`; whatever the outcome, it must not deliver unbounded output. Small, benign expansions must still expand correctly.
- `malformed_documents_are_rejected`: Property: ill-formed documents — mismatched tags, duplicate attributes, invalid names, truncation, stray end tags, invalid characters — are rejected with `Err`, never a panic and never a successful parse.
- `config_variations_agree_on_canonical_stream`: Property: parser configuration options that only re-shape the event stream (CDATA→characters, whitespace→characters, comment reporting, coalescing) never change the canonical document content: element structure, attributes, and merged text are identical under every such configuration. (`trim_whitespace` is excluded — it deliberately changes text content.)

**`tests/event_writer.rs`**
- `document_write_read_roundtrip`: Property (the crown round-trip): a document built from arbitrary well-formed elements, attributes, text (PCDATA and CDATA), and comments, written with `EventWriter`, reads back with `EventReader` as exactly the same canonical structure — element names, attribute names/values (in order), and text content all survive, which requires the writer to escape every character the reader would otherwise mis-parse.
- `pcdata_text_write_read_roundtrip`: Property: arbitrary text (generated at the PCDATA encode-set boundary: `<`, `>`, `&`, quotes, `]]>`, entity-reference look-alikes) written as `Characters` is recovered exactly by the reader. `\r` is excluded — its loss is pinned by `known_bug_pcdata_carriage_return_lost_in_roundtrip`.
- `attribute_write_read_roundtrip`: Property: arbitrary attribute names and values — including quotes, `<`, `&`, and `\r`/`\n` (which the writer must escape as character references to survive attribute-value normalization) — round-trip exactly through write→read. `\t` is excluded from the generator; its loss is pinned by `known_bug_attribute_tab_lost_in_roundtrip`.

## Oracles

## Not tested

## History

- 2026-07-11: predecessor base commit `6def29fd97a1` (Perform end-of-line normalization).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/xml-rs.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped 6def29fd97a1 → e2b391aba4ed (2026-08-11, "Support for ATTLIST CDATA default attribute value definitions."; 1.4.0); 1 bug(s) still reproduce; 1 ignored reproducer(s) not run; add/add conflicts in tests/event_reader.rs, tests/event_writer.rs resolved by keeping both sides. 168 tests pass.
- 2026-09-20: base bumped e2b391aba4ed → 45504757c87d (2026-09-19, "Expose element's own declared namespaces via an accessor"; 1.4.0); 1 bug(s) still reproduce; 1 ignored reproducer(s) not run; add/add conflicts in tests/event_reader.rs resolved by keeping both sides. 172 tests pass.
