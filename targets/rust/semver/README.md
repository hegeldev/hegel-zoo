# semver

[dtolnay/semver](https://github.com/dtolnay/semver).

## What is tested

**`tests/test_identifier.rs`**
- `hegel_prerelease_new_as_str_roundtrip`: (no doc comment)
- `hegel_build_metadata_new_as_str_roundtrip`: (no doc comment)

**`tests/test_version.rs`**
- `hegel_version_display_parse_roundtrip`: (no doc comment)
- `hegel_version_parse_never_panics`: (no doc comment)
- `hegel_version_ord_total_order_axioms`: (no doc comment)
- `hegel_prerelease_order_matches_spec`: (no doc comment)
- `hegel_version_display_honors_width_format`: (no doc comment)
- `hegel_version_parse_rejects_corruption`: (no doc comment)
- `hegel_cmp_precedence_ignores_build`: (no doc comment)

**`tests/test_version_req.rs`**
- `hegel_req_display_parse_roundtrip`: (no doc comment)
- `hegel_req_parse_agrees_with_comparator_parse`: (no doc comment)
- `hegel_req_parsers_never_panic`: (no doc comment)
- `hegel_full_comparator_matches_reference`: (no doc comment)
- `hegel_partial_comparator_matches_doc_equivalent`: (no doc comment)
- `hegel_prerelease_match_requires_pre_comparator`: (no doc comment)
- `hegel_matches_ignores_build_metadata`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-06-23: predecessor base commit `280ebcb6edac` (Update actions/upload-artifact@v6 -> v7).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/semver.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
