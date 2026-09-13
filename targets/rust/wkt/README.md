# wkt

[georust/wkt](https://github.com/georust/wkt).

## What is tested

**`src/geo_types_from_wkt.rs`**
- `prop_wkt_to_geo_types_and_back_is_identity`: Converting a geo-types-representable Wkt to `geo_types::Geometry` and back (via `ToWkt`) must be the identity: no coordinates gained, lost, or altered, and the structure preserved.

**`src/infer_type.rs`**
- `prop_infer_type_agrees_with_writer_and_parser`: `infer_type` must agree with the full parser on every WKT string the crate's own writer emits: same geometry type, same dimension.

**`src/lib.rs`**
- `prop_write_parse_roundtrip_is_fixpoint`: Write→parse must recover an equal geometry, and re-serializing must be a fixpoint (the second serialization is byte-identical to the first).
- `prop_point_coordinates_survive_roundtrip_bit_exact`: The writer must not lose precision: every finite f64 coordinate (including subnormals, ±0.0, and values at the extremes of the range) must survive write→parse bit-for-bit.
- `prop_parse_arbitrary_text_never_panics`: `Wkt::from_str` must never panic on arbitrary text — it returns Err.
- `prop_parse_wkt_shaped_soup_never_panics`: `Wkt::from_str` must never panic on WKT-shaped token soup either — keywords, parens, commas and numbers glued together in random order.
- `prop_parse_is_case_insensitive_and_whitespace_tolerant`: Parsing is case-insensitive in keywords and tolerant of extra whitespace around parens and commas: a mutated serialization parses to the same geometry as the canonical one.
- `prop_empty_geometries_roundtrip`: Every geometry type × dimension has an EMPTY form that round-trips.
- `prop_compact_dimension_headers_parse_identically`: The compact dimension headers (`POINTZ`, `LINESTRINGZM`, ...) must parse identically to the spaced forms (`POINT Z`, `LINESTRING ZM`, ...) that the writer emits (see `Wkt::from_word_and_tokens`).
- `prop_bounded_nested_geometrycollections_parse_and_roundtrip`: Bounded nesting: nested GEOMETRYCOLLECTIONs parse fine and round-trip up to depth 64, and truncated input at the same depth errors cleanly. The bound protects the test: the parser's recursion overflows the stack somewhere between depth 450 and 500 on a default 2 MiB test thread — see `known_failure_deeply_nested_geometrycollection_stack_overflow`.

## Oracles

## Not tested

## History

- 2026-01-01: predecessor base commit `85088d9279e5` (Fix doc build (#151)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/wkt.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped 85088d9279e5 → be86fc449d17 (2026-09-09, "Bound GeometryCollection nesting depth to prevent stack overflow"; 0.14.0); 1 bug(s) still reproduce; 1 ignored reproducer(s) not run. 143 tests pass. wkt/2 (the nested GEOMETRYCOLLECTION stack overflow, an ignored reproducer the bump does not run) was checked by hand and is fixed by this very commit: parsing is bounded at MAX_DEPTH = 128 and returns an error past it.
