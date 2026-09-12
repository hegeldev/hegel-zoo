# rustfft

[ejmahler/RustFFT](https://github.com/ejmahler/RustFFT).

## What is tested

**`tests/accuracy.rs`**
- `hegel_forward_inverse_roundtrip_is_identity_scaled_by_len`: Property: an unnormalized forward FFT followed by an unnormalized inverse FFT (in either order) reproduces the input scaled by n. This is the crown roundtrip and holds for every length.
- `hegel_planned_fft_matches_naive_dft_definition`: Property: for small lengths, the planned FFT matches the O(n^2) DFT definition (transcribed spec oracle), in both directions.
- `hegel_fft_is_linear`: Property: the DFT is linear: FFT(a*x + b*y) == a*FFT(x) + b*FFT(y).
- `hegel_parseval_energy_conservation`: Property (Parseval / energy conservation, unnormalized convention): sum |x[j]|^2 == (1/n) * sum |X[k]|^2.
- `hegel_constant_signal_transforms_to_dc_delta`: Property: the transform of a constant signal is a delta at DC: X[0] = n*c and X[k] = 0 for k != 0 (both directions).
- `hegel_circular_time_shift_multiplies_spectrum_by_phase`: Property (shift theorem): circularly left-shifting the input by s multiplies bin k of the spectrum by exp(sign * 2*pi*i * s*k / n), where sign is + for the forward transform and - for the inverse.
- `hegel_all_process_entry_points_agree`: Property: all three explicit process entry points (in-place, out-of-place, immutable) compute the same transform.
- `hegel_multi_chunk_buffer_equals_chunkwise_processing`: Property (documented contract): `process_with_scratch` divides a buffer of k*n elements into k chunks and computes an independent FFT on each chunk — identical to processing each chunk separately. Tolerance is 0 (bit equality): each chunk goes through the exact same deterministic computation either way.
- `hegel_planner_is_deterministic`: Property: planning the same length twice (in two fresh planners) yields FFTs that produce bit-identical output for the same input. Tolerance is 0 (bit equality): the planner is deterministic within a process, so both plans must run the same computation.
- `hegel_f32_and_f64_planners_agree`: Property: the f32 and f64 planners compute the same transform, within f32 accuracy, for the same (f32-representable) input.

## Oracles

## Not tested

## History

- 2025-09-17: predecessor base commit `4758ab0dd6f2` (Release v6.4.1 (#165)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/rustfft.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
