# bson

[mongodb/bson-rust](https://github.com/mongodb/bson-rust).

## What is tested

**`src/raw/test.rs`**
- `hegel_extjson_canonical_roundtrip`: (no doc comment)
- `hegel_document_roundtrip`: Round-trip: an arbitrary `Document` (all Bson variants, nested containers) serialized with `to_vec`/`to_writer` and parsed back via both `RawDocumentBuf::from_bytes` and `Document::from_reader` is bitwise-identical to the original.
- `hegel_decode_arbitrary_bytes_never_panics`: Untrusted input: decoding fully arbitrary bytes (raw or length-prefixed garbage) returns Err or Ok but never panics, and every lazily-parsed element can be visited without panicking.
- `hegel_length_prefix_corruption_rejected`: Untrusted input: corrupting the length prefix of a valid document is always detected by `RawDocument::from_bytes` (which documents that the prefix must match the slice length), and never causes a panic or a huge allocation in `Document::from_reader`.
- `hegel_single_byte_mutation_never_panics`: Untrusted input: flipping a single byte of a valid document never causes a panic in either the raw (lazy) or parsed (eager) pipeline, and (with serde) the serde deserializer agrees with the eager parser on accept/reject and on the parsed value.
- `hegel_raw_append_iterate_roundtrip`: Duplicate keys and insertion order are preserved exactly by the raw append/iterate cycle (the raw layer, unlike `Document`, is not a map).
- `hegel_invalid_utf8_string_rejected`: Untrusted input: a string value containing invalid UTF-8 is rejected by the strict parsed API (never a panic, never silent acceptance), while the documented lossy API accepts it.
- `hegel_nul_key_rejected`: A document key containing an interior NUL cannot be encoded: `to_vec` must return Err (keys are cstrings on the wire), never panic and never silently truncate.
- `hegel_deep_nesting_no_crash`: Moderately nested documents/arrays round-trip through the eager parser and re-serialization without crashing. NOTE: the depth here is deliberately capped at 30, well below the levels at which the decoders overflow the stack — ~282 for `Document::try_from`, and even shallower (~60-80 in a debug build) for the serde path exercised below. See the `hegel_deep_nesting_stack_overflow` reproducer for that KNOWN FAILURE. This sibling stays in the safe region so it keeps testing the no-crash property on inputs the crate actually handles.

## Oracles

## Not tested

## History

- 2026-07-21: predecessor base commit `27166baaee68` (minor: add .zed to gitignore (#679)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/bson.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped 27166baaee68 → 4b677e343d55 (2026-09-04, "RUST-2471 Fix Eq implementation for Bson; extend Eq/Hash to raw types (#686)"; 3.1.0); 0 bug(s) still reproduce; 1 ignored reproducer(s) not run. 433 tests pass.
- 2026-09-14: base bumped 4b677e343d55 → 43b8f4c57542 (2026-09-14, "Bump the rust-dependencies group across 1 directory with 13 updates (#693)"; 3.1.0); 0 bug(s) still reproduce; 1 ignored reproducer(s) not run. 433 tests pass.
