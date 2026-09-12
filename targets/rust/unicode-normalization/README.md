# unicode-normalization

[unicode-rs/unicode-normalization](https://github.com/unicode-rs/unicode-normalization).

## What is tested

**`src/test.rs`**
- `prop_nfc_idempotent`: (no doc comment)
- `prop_nfd_idempotent`: (no doc comment)
- `prop_nfkc_idempotent`: (no doc comment)
- `prop_nfkd_idempotent`: (no doc comment)
- `prop_canonical_roundtrip_stability`: (no doc comment)
- `prop_nfkc_subsumes_canonical`: (no doc comment)
- `prop_nfkd_subsumes_canonical`: (no doc comment)
- `prop_quick_check_nfc_consistent`: (no doc comment)
- `prop_quick_check_nfd_consistent`: (no doc comment)
- `prop_quick_check_nfkc_consistent`: (no doc comment)
- `prop_quick_check_nfkd_consistent`: (no doc comment)
- `prop_iterator_adapters_match_str_methods`: (no doc comment)
- `prop_concat_at_stable_code_point`: (no doc comment)
- `prop_hangul_algorithmic_roundtrip`: (no doc comment)
- `prop_compose_result_canonically_equivalent`: (no doc comment)
- `prop_nfd_output_fully_decomposed_and_ordered`: (no doc comment)
- `prop_nfkd_output_fully_decomposed_and_ordered`: (no doc comment)
- `prop_stream_safe_idempotent`: (no doc comment)
- `prop_stream_safe_only_inserts_cgj`: (no doc comment)

## Oracles

## Not tested

## History

- 2025-11-02: predecessor base commit `576ae0b1407d` (Merge pull request #116 from musicinmybrain/license).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/unicode-normalization.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
