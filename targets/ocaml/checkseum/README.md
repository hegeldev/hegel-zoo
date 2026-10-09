# checkseum

Both implementations of the virtual library, `checkseum.c` and `checkseum.ocaml`, each in its
own test executable (results `c::…` and `ocaml::…`).

## What is tested

- `digest_matches_reference`, `chained_digest_matches_reference`: CRC-32 and Adler-32 against
  Python's `zlib`, CRC-32C (RFC 3720) and CRC-24 (RFC 4880) against table-driven references,
  through strings, bytes and bigstrings, checked and unsafe, at offsets, chained.
- `digest_continues_from_any_value`: continuing from any 32-bit (24-bit for CRC-24) value.
- `bounds_are_checked`: `digest_*` raise `Invalid_argument` exactly outside the input.
- `int32_conversions_roundtrip`: `of_int32`/`to_int32` over the unsigned range, and `equal`.

## Not tested

`pp`; values on 32-bit platforms, where `Optint.t` is boxed.

## History

- 2026-10-09: created at fef8888d (v0.5.3+), hegel-ocaml 0.26.1; checkseum/1.
