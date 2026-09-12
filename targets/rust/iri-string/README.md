# iri-string

[lo48576/iri-string](https://github.com/lo48576/iri-string).

## What is tested

**`tests/iri.rs`**
- `encode_to_uri_output_is_valid_uri_reference_pbt`: (no doc comment)
- `encode_to_uri_is_idempotent_pbt`: (no doc comment)
- `encode_to_uri_preserves_percent_decoded_bytes_pbt`: (no doc comment)

**`tests/normalize.rs`**
- `normalize_is_idempotent_pbt`: (no doc comment)
- `normalize_output_reports_is_normalized_pbt`: (no doc comment)

**`tests/percent_encode.rs`**
- `percent_encoding_roundtrips_through_percent_decoding`: (no doc comment)
- `percent_encoded_components_are_valid_for_their_component`: (no doc comment)

**`tests/resolve.rs`**
- `resolve_agrees_with_rfc3986_reference_implementation`: (no doc comment)
- `resolution_output_is_fixed_point_of_resolution`: (no doc comment)

**`tests/string_types_interop.rs`**
- `parse_never_panics_on_arbitrary_input`: Property: none of the eight IRI/URI string type parsers panic, whatever the input (they must return `Err` for invalid input instead).
- `parse_results_respect_type_hierarchy`: Property: parse successes across the eight string types respect the documented type hierarchy: * every URI type is a subset of the corresponding IRI type, * absolute IRI implies IRI implies IRI reference, relative implies reference, * a reference is exactly an IRI or a relative reference, never both, * an IRI is absolute exactly when it has no fragment part. KNOWN FAILURE (suspected library bug): `IriAbsoluteStr`/`UriAbsoluteStr` accept strings with an *empty* fragment part (a trailing `#`), e.g. `"a:#"` or `"AA://@?#"`, although the `absolute-IRI`/`absolute-URI` rules (RFC 3987 section 2.2 / RFC 3986 section 4.3) do not allow any fragment part, and the type documents itself as "RiStr without fragment part". Cause: `validate_after_path` in `src/parser/validate.rs` rejects a forbidden fragment via `!maybe_fragment.is_empty()`, which cannot distinguish "no `#` present" from "`#` present with empty fragment". The case count is raised because the failure needs a conjunction (valid absolute IRI and a trailing `#`) that the default count often misses.
- `components_recompose_to_original`: Property: the component getters (`scheme_str`, `authority_str`, `path_str`, `query_str`, `fragment_str`) of a parsed reference recompose to the original string by the RFC 3986 section 5.3 algorithm.
- `authority_components_recompose_to_authority`: Property: the authority sub-component getters (`userinfo`, `host`, `port`) recompose to exactly the `authority_str` value, and `authority_components` is present exactly when `authority_str` is.

## Oracles

## Not tested

## History

- 2026-07-22: predecessor base commit `07d982ed76ec` (doc: fix harmless typo).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/iri-string.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-12: base bumped 07d982ed76ec → 9b0eadf9690c (2026-07-27, "style: remove a needless blank line"; 0.7.14); 0 bug(s) still reproduce; fixed upstream: iri-string/1. 423 tests pass. iri-string/1 is fixed upstream in 0.7.14 (empty fragments now rejected for absolute IRI types).
