# gitoxide

[GitoxideLabs/gitoxide](https://github.com/GitoxideLabs/gitoxide).

## What is tested

**`tests/url/parse/mod.rs`**
- `parsed_urls_roundtrip_through_to_bstring`: Property: `Url::to_bstring()` is documented to serialize "losslessly, ready to be parsed again" (see `Url::write_to()`), so any successfully parsed URL must reparse from its own serialization to an equal `Url`. This is `assert_url_roundtrip()` generalized over generated inputs.
- `from_parts_preserves_components`: Property: the field docs on `Url` state that `user`, `password` and `path` are stored in decoded form and re-encoded during canonical serialization, and `Url::from_parts()` validates by parsing the serialized form back. Therefore constructing a URL from valid parts must preserve each component (modulo the documented `/~` path normalization for ssh/git).
- `users_with_colons_roundtrip_through_to_bstring`: KNOWN FAILURE: pins a real bug — `Url::to_bstring()` is not lossless for users containing `:`. `parse("http://a%3Ab@host/")` percent-decodes the user to `a:b` (as documented on `Url::user`), but `USERINFO_ENCODE_SET` in `write_canonical_form_to()` (src/lib.rs) does not include `:`, so `to_bstring()` yields `http://a:b@host/` which reparses as user `a` with password `b`. This violates the documented contract of `write_to()`: "Write this URL losslessly to `out`, ready to be parsed again". A colon inside the user component must be percent-encoded because the first unencoded `:` in userinfo delimits user from password.

## Oracles

## Not tested

## History

- 2026-07-22: predecessor base commit `2315ede714da` (Merge pull request #2737 from GitoxideLabs/encoding-fallback-pony).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/gitoxide.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped 2315ede714da → 19beb949b897 (2026-09-12, "Merge pull request #2988 from GitoxideLabs/error-conversion-review"; 0.58.0); 2 bug(s) still reproduce; fixed upstream: gitoxide/1. 655 tests pass. gitoxide/1 is fixed by the gix-url serializer rewrite in this range, which also introduced gitoxide/3 (hosts with both `:` and `%` are bracketed and `%`-escaped but not un-escaped when reparsed; zoo-original, pinned). Two of gix-config's own tests (`multi_line_value_starting_on_a_continuation_line_is_not_indented`, `source::git_config_no_system`) fail on this machine — they compare against the installed git and are not patch tests.
- 2026-09-13: base bumped 19beb949b897 → 4f29e0cd4c85 (2026-09-13, "Merge pull request #2992 from GitoxideLabs/fix-message-newline"; 0.58.0); 2 bug(s) still reproduce. 656 tests pass.
- 2026-09-14: base bumped 4f29e0cd4c85 → c609062db5e7 (2026-09-14, "Merge pull request #2990 from GitoxideLabs/various-improvements"; 0.58.0); 2 bug(s) still reproduce. 656 tests pass.
- 2026-09-14: base bumped c609062db5e7 → 65c5dfe8895a (2026-09-14, "Merge pull request #2993 from youdie006/fix-blank-space-character-classes"; 0.58.0); 2 bug(s) still reproduce. 656 tests pass.
- 2026-09-14: base bumped 65c5dfe8895a → 37149b894efa (2026-09-14, "Merge pull request #2994 from rawsun007/fix-date-offset-range"; 0.58.0); 2 bug(s) still reproduce. 656 tests pass.
- 2026-09-15: base bumped 37149b894efa → e96027477756 (2026-09-15, "Merge pull request #2998 from youdie006/test-reproduce-remaining-t3070-rows"; 0.58.0); 2 bug(s) still reproduce. 656 tests pass.
