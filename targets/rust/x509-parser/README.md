# x509-parser

[rusticata/x509-parser.git](https://github.com/rusticata/x509-parser.git).

## What is tested

**`tests/pem.rs`**
- `prop_pem_arbitrary_input_never_panics`: Property: PEM parsing of arbitrary bytes — raw, and wrapped in BEGIN/END markers around arbitrary body bytes (so the base64 decoder and the inner DER parser are reached) — never panics, and `Pem::iter_from_buffer` always terminates.
- `prop_pem_corrupted_seed_never_panics`: Property (valid-then-corrupt): a real PEM certificate with a few mutated bytes parses to Ok or Err, never panics — including the inner DER parse of the (possibly corrupted) base64 payload.

**`tests/readcert.rs`**
- `prop_cert_arbitrary_bytes_never_panic`: Property: parsing arbitrary bytes never panics (Err is fine, panic is not). Also exercised with a DER SEQUENCE magic prefix (0x30 0x82) so generated inputs get past the first tag check more often.
- `prop_cert_crafted_length_header_errs`: Property: a crafted long-form DER length header claiming more content than the input holds must return Err — quickly, and without pre-allocating attacker-controlled amounts of memory (a huge claimed length that triggered an allocation would OOM-abort this test).
- `prop_cert_corrupted_seed_never_panics`: Property (valid-then-corrupt): take a real certificate and corrupt a few bytes — anywhere, with a bias towards the leading tag/length bytes. Parsing must return Ok or Err, never panic; on Ok, all zero-copy field slices must still point inside the input.
- `prop_cert_strict_prefix_errs`: Property (truncation): every strict prefix of a valid certificate fails to parse — the outer SEQUENCE length always covers the whole certificate, so a prefix can never be a complete object — and it must fail with Err, not a panic or an out-of-bounds read.
- `prop_parsed_cert_slices_within_input`: Property (parsed-field bounds, oracle-independent): every zero-copy slice exposed by a successfully parsed certificate (serial, issuer, subject, extension values, remainder) lies within the input buffer.
- `prop_cert_reparse_equal`: Property (re-parse): re-parsing exactly the bytes consumed by a successful parse yields an equal structure with no remainder.
- `prop_deeply_nested_der_no_stack_overflow`: Property (deeply nested DER): SEQUENCEs/SETs nested thousands deep must be rejected gracefully — no stack overflow, no hang. DER length fields are attacker-controlled, so this is the classic "decompression bomb" shape for recursive-descent parsers.

**`tests/readcrl.rs`**
- `prop_crl_arbitrary_and_corrupted_never_panic`: Property: CRL parsing of arbitrary bytes, and of real CRLs with a few corrupted bytes, never panics. On success, the revoked-certificates iterator and its accessors must not panic either.
- `prop_crl_strict_prefix_errs`: Property (truncation): every strict prefix of a valid CRL returns Err, never panics.

**`tests/readcsr.rs`**
- `prop_csr_arbitrary_and_corrupted_never_panic`: Property: CSR parsing of arbitrary bytes, and of real CSRs with a few corrupted bytes, never panics. On success, the attribute and requested-extensions accessors must not panic either.
- `prop_csr_strict_prefix_errs`: Property (truncation): every strict prefix of a valid CSR returns Err, never panics.

## Oracles

## Not tested

## History

- 2026-07-23: predecessor base commit `303b80f44685` (fix(validate): reject unsupported critical extensions per RFC 5280).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/x509-parser.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
