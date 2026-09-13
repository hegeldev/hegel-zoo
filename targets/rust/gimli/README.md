# gimli

[gimli-rs/gimli](https://github.com/gimli-rs/gimli).

## What is tested

**`src/leb128.rs`**
- `hegel_unsigned_roundtrip`: (no doc comment)
- `hegel_signed_roundtrip`: (no doc comment)
- `hegel_padded_encoding_reads_same_value`: (no doc comment)
- `hegel_truncated_encoding_errors`: (no doc comment)
- `hegel_arbitrary_bytes_bounded_consumption`: (no doc comment)

**`tests/convert_self.rs`**
- `hegel_write_read_die_tree_roundtrip`: (no doc comment)
- `hegel_write_read_line_program_rows_roundtrip`: (no doc comment)
- `hegel_corrupted_written_dwarf_parses_gracefully`: (no doc comment)

**`tests/parse_self.rs`**
- `hegel_arbitrary_debug_info_never_panics_or_overruns`: (no doc comment)
- `hegel_arbitrary_debug_line_never_panics_or_overruns`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-07-06: predecessor base commit `843c38e886f5` (read/cfi: validate eh_frame_hdr fde_count against table length (#897)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/gimli.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1. Two upstream `assert_eq!(x, [])` on `&[u8]` in `#[cfg(test)]` code (`src/read/line.rs`, `src/write/str.rs`) rewritten as `assert!(x.is_empty())`: hegeltest 0.44 pulls in `serde_json`, whose `PartialEq` impls make the literal ambiguous (E0282/E0283). The `#[ignore]` on `known_bug_debug_line_address_size_zero_panics` (a panic, not an abort) was dropped and the test listed as an expected failure.
- 2026-09-13: base bumped 843c38e886f5 → 8817b2af596f (2026-09-04, "read: fix doc for Operation::Wasm* (#900)"; 0.34.0); 1 bug(s) still reproduce. 596 tests pass.
