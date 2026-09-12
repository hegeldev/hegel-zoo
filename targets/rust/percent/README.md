# percent

[servo/rust-url](https://github.com/servo/rust-url).

## What is tested

**`src/ascii_set.rs`**
- `prop_ascii_set_behaves_like_hashset_model`: (no doc comment)

**`src/lib.rs`**
- `prop_decode_inverts_encode_when_set_has_percent`: Round-trip: decoding inverts encoding for arbitrary bytes, as long as the set contains `%` (otherwise a literal `%XX` in the input is left unescaped and decodes to a different byte string — see the percent-free-input property below for that case). The set is either an arbitrary generated set with `%` forced in, or the public `NON_ALPHANUMERIC` (which contains `%`).
- `prop_decode_inverts_encode_for_percent_free_input`: Round-trip for *any* generated set (with or without `%`), for inputs containing no literal `%`. This includes inputs full of bytes that ARE in the set and non-ASCII bytes.
- `prop_decode_matches_reference_decoder`: The decoder agrees with a reference decoder written from its docs, on inputs biased toward malformed escapes (lone `%`, `%X`, `%` + non-hex). In particular it never panics on arbitrary input.
- `prop_decode_views_agree`: All documented views of `PercentDecode` agree with the iterator: `Cow::from` yields the same bytes (and borrows when nothing decodes, as documented), `decode_utf8` agrees with `str::from_utf8` on the decoded bytes, and `decode_utf8_lossy` agrees with `String::from_utf8_lossy`.
- `prop_encode_matches_per_byte_oracle`: The encoder agrees with a per-byte oracle built from the documented rule "Non-ASCII bytes and bytes in `ascii_set` are encoded" and from `percent_encode_byte` (itself pinned by an exhaustive unit test above).
- `prop_encode_views_agree`: All documented views of `PercentEncode` agree: `Display` and `Cow::from` match `collect::<String>()`, and the `Cow` borrows the input when none of its bytes are encoded, as documented.
- `prop_utf8_encode_decode_roundtrip`: `utf8_percent_encode` round-trips arbitrary Unicode strings through `percent_decode_str` + `decode_utf8`, for any generated set containing `%`, and the lossy decode agrees since the bytes are valid UTF-8.

## Oracles

## Not tested

## History

- 2026-07-08: predecessor base commit `25137be1fc1d` (fix percent-encode of caret in path (#1140) (#1141)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/percent.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
