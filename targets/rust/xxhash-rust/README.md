# xxhash-rust

[DoumanAsh/xxhash-rust](https://github.com/DoumanAsh/xxhash-rust).

## What is tested

**`tests/assert_correctness.rs`**
- `hegel_xxh32_oneshot_matches_c_reference`: (no doc comment)
- `hegel_xxh32_streaming_prefix_digests_match_oneshot`: (no doc comment)
- `hegel_const_xxh32_matches_runtime`: (no doc comment)
- `hegel_xxh64_oneshot_matches_c_reference`: (no doc comment)
- `hegel_xxh64_streaming_prefix_digests_match_oneshot`: (no doc comment)
- `hegel_const_xxh64_matches_runtime`: (no doc comment)
- `hegel_xxh64_seed_affects_hash`: (no doc comment)
- `hegel_xxh3_oneshot_matches_c_reference`: (no doc comment)
- `hegel_xxh3_streaming_prefix_digests_match_oneshot`: (no doc comment)
- `hegel_xxh3_with_secret_oneshot_matches_c_reference`: (no doc comment)
- `hegel_xxh3_streaming_with_secret_matches_oneshot`: (no doc comment)
- `hegel_const_xxh3_matches_runtime`: (no doc comment)
- `hegel_xxh3_seed_affects_hash`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-07-21: predecessor base commit `f93abc7ce036` (0.8.18).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/xxhash-rust.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
