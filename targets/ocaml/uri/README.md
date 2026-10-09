# uri

`Uri`'s parser, printer, reference resolution and percent-encoding, against RFC 3986.

## What is tested

- `string_roundtrip`: printing a parsed reference and parsing it again gives the same URI.
- `components_match_appendix_b`, `ip_future_host_matches_appendix_b`: the accessors against the
  Appendix B split of a reference drawn from the RFC's grammar.
- `path_keeps_its_segments`: the path keeps its segments, each re-encoded.
- `resolve_matches_rfc3986`: `resolve` against the §5.2 algorithm; `pin_rfc3986_section_5_4`
  holds the §5.4 examples.
- `resolve_keeps_reference_host`: resolving a reference with its own scheme keeps its host.
- `pct_encode_roundtrip`, `pct_encode_output_is_rfc3986`: per component, decoding inverts
  encoding and the output uses only the characters the RFC allows there.
- `query_roundtrip`, `decoded_components_survive_printing`: decoded queries, fragments and
  passwords survive printing.

## Not tested

`canonicalize`, `Absolute_http`, `uri-sexp`, `uri-re`, custom `pct_encoder`s, and what the parser
makes of input outside the RFC's grammar.

## History

- 2026-10-09: created at 46979cf1 (v4.4.0+), hegel-ocaml 0.26.1; uri/1-5.
