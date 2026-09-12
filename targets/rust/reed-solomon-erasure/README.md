# reed-solomon-erasure

[darrenldl/reed-solomon-erasure](https://github.com/darrenldl/reed-solomon-erasure).

## What is tested

**`src/galois_8.rs`**
- `hegel_mul_slice_matches_scalar_mul`: `mul_slice(c, input, out)` must equal element-wise scalar `mul`.
- `hegel_mul_slice_xor_matches_scalar_mul`: `mul_slice_xor(c, input, out)` must equal out[i] ^ mul(c, input[i]).
- `hegel_mul_div_roundtrip`: Multiplication and division are inverse for non-zero divisors: div(mul(a, b), b) == a. Complements the existing exhaustive identity/associativity tests by tying `div` to `mul` directly.

**`src/tests/galois_16.rs`**
- `hegel_encode_erase_reconstruct_roundtrip_gf16`: Encode k data shards into k+m total over GF(2^16), erase any subset of up to m shards, then `reconstruct` must recover every shard exactly and the result must verify.

**`src/tests/mod.rs`**
- `hegel_encode_erase_reconstruct_roundtrip`: Crown property: encode k data shards into k+m total, erase any subset of up to m shards (data and/or parity), then `reconstruct` must recover every shard exactly and the result must verify.
- `hegel_reconstruct_too_many_erasures_fails_cleanly`: When more than m shards are erased, `reconstruct` must fail with `Error::TooFewShardsPresent` — and per its docs ("if the method returns an `Error`, then nothing is touched") it must leave every shard exactly as it found it.
- `hegel_reconstruct_data_recovers_only_data_shards`: `reconstruct_data` must recover the data shards exactly while leaving erased parity shards missing (it only reconstructs data).
- `hegel_verify_detects_single_byte_corruption`: `verify` returns true for a correctly encoded set, and false after any single byte of any shard (data or parity) is changed. The encode matrix is MDS (every parity coefficient is non-zero), so a single-byte change must always be detected.
- `hegel_encode_deterministic_regardless_of_parity_prefill`: Encoding is a pure function of (k, m, data): two independently constructed codecs must produce identical parity, regardless of what the parity buffers contained beforehand (the docs promise the parity slots are completely overwritten).
- `hegel_encode_is_columnwise`: Shard-size independence: encoding operates on each byte position independently, so parity byte j of the full-length encoding must equal the parity produced by encoding just column j as 1-byte shards.
- `hegel_single_data_shard_parity_equals_data`: k = 1 edge case: with a single data shard the systematic Vandermonde construction makes every encode-matrix row equal to [1] (`vandermonde` entry [r][0] = nth(r)^0 = 1, and the top 1x1 submatrix is [1]), so every parity shard is an exact copy of the data shard.
- `hegel_single_parity_recovers_any_single_erasure`: m = 1 edge case: a single parity shard must be able to recover any one erased shard, for any data shard count up to the field limit.

## Oracles

## Not tested

## History

- 2022-11-11: predecessor base commit `ac2b561e406f` (Change recommended benchmarking to `cargo bench`).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/reed-solomon-erasure.patch`).
- 2026-09-11: imported into the zoo; ported to hegeltest 0.44.1.
