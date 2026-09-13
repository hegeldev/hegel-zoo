# rasn

[librasn/rasn.git](https://github.com/librasn/rasn.git).

## What is tested

**`tests/fuzz.rs`**
- `open_roundtrip_ber`: (no doc comment)
- `open_roundtrip_der`: (no doc comment)
- `open_roundtrip_cer`: (no doc comment)
- `model_roundtrip_all_codecs`: (no doc comment)
- `choice_roundtrip_ber_der`: (no doc comment)
- `der_encoding_decodes_under_ber`: (no doc comment)
- `der_is_canonical_fixpoint`: (no doc comment)
- `arbitrary_bytes_never_panic`: (no doc comment)
- `corrupted_encoding_never_panics`: (no doc comment)
- `huge_declared_length_is_rejected`: (no doc comment)
- `nested_length_bomb_is_graceful`: (no doc comment)
- `integer_roundtrip`: (no doc comment)
- `integer_der_fixpoint`: (no doc comment)
- `octet_string_roundtrip`: (no doc comment)
- `safe_oid_roundtrip`: (no doc comment)
- `bug_oid_low_first_arc_roundtrip_corruption`: (no doc comment)
- `bug_oid_second_arc_overflow`: (no doc comment)

## Oracles

## Not tested

## History

- 2026-05-04: predecessor base commit `0e45728195d9` (chore: fmt).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/rasn.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped 0e45728195d9 → dd1a65948089 (2026-08-22, "fix(aper): APER byte-alignment for constrained strings inside CHOICE + SEQUENCE(OPTIONAL) nesting (#564)"; 0.28.14); 1 bug(s) still reproduce. 40 tests pass.
