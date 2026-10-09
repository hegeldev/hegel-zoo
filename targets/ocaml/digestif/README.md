# digestif

Both implementations of the virtual library, `digestif.c` and `digestif.ocaml`, each in its own
test executable (results `c::…` and `ocaml::…`).

## What is tested

- `digest_matches_hashlib`, `feed_matches_hashlib`, `digest_lists_match_hashlib`: MD5, SHA-1,
  SHA-2, SHA-3 and BLAKE2 against Python's `hashlib`, through every input shape (string, bytes,
  bigstring, `?off`/`?len`, incremental, `digestv`/`digesti`).
- `hmac_matches_python`, `hmac_feed_matches_python`, `hmac_lists_match_python`: the same
  against Python's `hmac`, keys around the block size.
- `blake2_sizes_match_hashlib`, `blake2_keyed_matches_hashlib`: `Make_BLAKE2B/S` digest sizes
  and the keyed modes.
- `backends_agree`: every algorithm, and BLAKE3's keyed, derive-key and XOF modes, against the
  other implementation.
- `of_hex_opt_matches_docs`, `consistent_of_hex_opt_matches_docs`, `to_hex_is_hex_of_raw`,
  `raw_string_roundtrip`, `compare_and_equal_are_string_order`, `get_into_bytes_matches_get`,
  `blake3_xof_seeks_into_one_stream`: the conversions and helpers against their documentation.

## Not tested

The polymorphic `'k hash` interface, Keccak-256, RIPEMD-160, Whirlpool and BLAKE3 beyond the two
implementations agreeing.

## History

- 2026-10-09: created at 171cd7f6 (v1.3.1+), hegel-ocaml 0.26.1; digestif/1.
