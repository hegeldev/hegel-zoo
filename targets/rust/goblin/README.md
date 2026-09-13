# goblin

[m4b/goblin](https://github.com/m4b/goblin).

## What is tested

**`tests/hegel_robustness.rs`**
- `object_parse_arbitrary_bytes_never_panics`: (no doc comment)
- `format_parsers_arbitrary_bytes_never_panic`: (no doc comment)
- `elf_crafted_header_counts_and_offsets_never_panic`: (no doc comment)
- `valid_binary_byte_corruption_never_panics`: (no doc comment)
- `truncated_binary_never_panics`: (no doc comment)
- `object_dispatch_matches_magic`: (no doc comment)
- `archive_member_offsets_within_bounds`: (no doc comment)
- `archive_magic_prefixed_arbitrary_never_panics`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-06-13: predecessor base commit `dca2e753b2ab` (Fix Actions badge (#540)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/goblin.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
