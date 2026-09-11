# roxmltree

[RazrFalcon/roxmltree](https://github.com/RazrFalcon/roxmltree).

## What is tested

**`tests/properties.rs`**
- `parse_never_panics_on_arbitrary_text`: (no doc comment)
- `parse_never_panics_on_arbitrary_bytes`: (no doc comment)
- `parse_never_panics_on_xml_shaped_input`: (no doc comment)
- `node_ranges_are_valid`: (no doc comment)
- `tree_structure_is_consistent`: (no doc comment)
- `text_content_is_preserved`: (no doc comment)
- `names_and_attributes_roundtrip`: (no doc comment)
- `duplicate_attributes_are_rejected`: (no doc comment)
- `namespace_resolution_is_consistent`: (no doc comment)
- `entity_expansion_is_bounded`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-05-23: predecessor base commit `e8a27a70867b` (Fix a typo in and reword for clarity the docstring for `EntityResol...).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/roxmltree.patch`).
- 2026-09-11: imported into the zoo; ported to hegeltest 0.44.1.
