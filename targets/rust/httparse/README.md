# httparse

[seanmonstar/httparse](https://github.com/seanmonstar/httparse).

## What is tested

**`src/lib.rs`**
- `request_parse_never_panics_on_arbitrary_bytes`: `Request::parse` returns Ok/Partial/Err — never panics — on arbitrary bytes, and any `Complete(n)` satisfies the parser's self-evident invariants (n <= len, slices in range, tokens valid).
- `response_parse_never_panics_on_arbitrary_bytes`: As above, for `Response::parse`.
- `http_shaped_bytes_never_panic_and_invariants_hold`: HTTP-shaped bytes (a valid drawn message with 0..=4 drawn corruptions) never panic either parser, and any `Complete` result still satisfies all grammar/offset invariants. This reaches much deeper parser states than raw arbitrary bytes.
- `parse_headers_never_panics_and_offsets_valid`: `parse_headers` never panics, and a `Complete((pos, headers))` result has pos <= len and in-range, token-valid headers.
- `request_roundtrip`: A well-formed request built from drawn tokens parses back to exactly those tokens (header values modulo the documented OWS trim).
- `response_roundtrip`: A well-formed response built from drawn tokens parses back to exactly those tokens (reason becomes "" if absent or obs-text).
- `request_every_prefix_is_partial_and_agrees`: Incremental vs whole: every strict prefix of a valid request parses as `Ok(Partial)` (never `Err`, never an early `Complete`), and any request-line fields already parsed agree with the whole-buffer parse. This is the streaming contract from the README.
- `response_every_prefix_is_partial_and_agrees`: As above, for responses.
- `complete_result_unchanged_by_trailing_bytes`: Completeness monotonicity: once a buffer parses as `Complete(n)`, appending arbitrary bytes must yield the identical `Complete(n)` and identical parsed fields (the parser never reads past the head).
- `header_capacity_honored`: Header capacity is honored: a message with k headers parses completely with exactly k headers given >= k slots, and returns `Err(TooManyHeaders)` given fewer.
- `nul_byte_is_always_rejected`: Validation: a NUL byte replacing any single byte of a valid message makes the parse fail. NUL is forbidden in every position of an HTTP/1.x message head.
- `forbidden_header_byte_is_rejected`: Validation at the token-set boundary: inserting any byte that is outside the allowed set for a header name or header value (and is not a structural byte `:`/CR/LF, which would merely re-delimit the message) makes the parse fail. The classic parser bug is accepting a forbidden byte.
- `only_empty_lines_is_partial`: An input consisting only of empty lines (the parser skips leading empty lines) never completes: both parsers report `Partial`.
- `chunk_size_roundtrip`: Round-trip for `parse_chunk_size`: any u64 rendered as hex (either case, with leading zeros up to the 16-digit limit), optionally followed by LWS and a chunk extension, then CRLF, parses back to exactly that size with the position just past the CRLF — independent of trailing bytes.
- `chunk_size_never_panics_on_arbitrary_bytes`: `parse_chunk_size` never panics on arbitrary bytes, and a `Complete((pos, _))` result has pos <= len.

## Oracles

## Not tested

## History

- 2026-06-30: predecessor base commit `a0fa552e4e0f` (refactor: share invalid header handling (#221)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/httparse.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
