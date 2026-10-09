# base64

`Base64` (RFC 4648) and `Base64_rfc2045` against Python's `base64` and `binascii`, run as a
coprocess.

## What is tested

- `encode_agrees_with_python`, `custom_alphabet_encode_agrees_with_python`: the default, URI-safe
  and random alphabets, with and without padding, on sub-ranges.
- `decode_agrees_with_python`: valid and mutated encodings (padding removed or added, characters
  inserted, truncated) accepted and decoded as `a2b_base64(strict_mode=True)` does.
- `final_quantum_agrees_with_python`: every pattern of data and `=` in the last quantum.
- `decode_inverts_encode`, `unpadded_decode_inverts_encode`: round trips; `~pad:false` is
  documented as best effort, so it is held only to inverting its own output.
- `rfc2045_decode_in_chunks`: MIME text of any line width fed to the decoder in small pieces.
- `rfc2045_encode_agrees_with_python`: the encoder through small `Manual` buffers against
  `encodebytes` (CRLF, no final line break).

## Not tested

`~pad:false` acceptance beyond round trips, the decoder's recovery after `Malformed`, the
`Channel` source and destination.

## History

- 2026-10-09: created at 08f34452 (v3.5.2+), hegel-ocaml 0.26.1; base64/1-3.
