# gltf

[gltf-rs/gltf](https://github.com/gltf-rs/gltf).

## What is tested

**`gltf-json/src/root.rs`**
- `root_json_roundtrip`: Serializing a document to JSON text and deserializing it back yields a structurally identical document. Note: this relies on the `float_roundtrip` feature of serde_json (enabled in dev-dependencies). serde_json's default float parser is documented to be up to 1 ULP off, which shows up here as e.g. `1.1254340850495887e+27` reparsing as `...888e+27` in accessor `min`/`max` values — a serde_json artifact, not a gltf-json bug.
- `structurally_valid_root_passes_validation`: A document whose indices are all in bounds and whose enumerated values are all valid must pass validation with no errors.
- `out_of_bounds_index_is_reported`: Injecting a single out-of-bounds index anywhere in an otherwise valid document is reported as `IndexOutOfBounds` (and never panics).

**`src/binary.rs`**
- `glb_from_slice_never_panics_on_arbitrary_bytes`: (no doc comment)
- `glb_write_then_read_roundtrips`: (no doc comment)
- `glb_from_slice_rejects_truncation`: (no doc comment)
- `glb_from_slice_never_panics_on_corruption`: (no doc comment)
- `glb_from_slice_and_from_reader_agree`: (no doc comment)
- `glb_trailing_bytes_from_slice_from_reader_disagreement`: KNOWN FAILURE: `Glb::from_slice` and `Glb::from_reader` disagree on a valid GLB followed by trailing bytes. `from_reader` honors `header.length` and parses only the declared bytes, so it accepts the input. `from_slice` checks that the declared length fits the slice but then parses chunks across the *entire* slice, so after the JSON chunk it misinterprets the trailing bytes as a BIN chunk header and fails (minimal counterexample: a 20-byte GLB with an empty JSON chunk plus one trailing byte). The two entry points thus accept different input sets. This test deterministically pins the inconsistency and is expected to fail until the behavior is reconciled.

**`src/scene/mod.rs`**
- `decompose_roundtrip_generated`: Property behind all of the `decompose_*` examples above: converting a TRS transform to a matrix, decomposing the matrix back to TRS, and re-converting to a matrix reproduces the original matrix (up to the numeric tolerance the example-based tests already use). The value ranges mirror the envelope covered by the example-based tests (translations up to 1e5, scale magnitudes 1e-4..=1e4, any signs); decomposition of arbitrarily extreme floats is inherently lossy and not something the code promises.

**`tests/test_wrapper.rs`**
- `gltf_from_slice_never_panics_on_arbitrary_bytes`: (no doc comment)
- `import_buffers_decodes_base64_data_uri`: (no doc comment)
- `import_buffers_rejects_undersized_buffer`: (no doc comment)
- `accessor_iter_reads_back_written_f32_scalars`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-05-11: predecessor base commit `50d65229477f` (Merge pull request #471 from alteous/fix-panics).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/gltf.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
