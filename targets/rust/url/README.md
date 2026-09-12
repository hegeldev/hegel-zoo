# url

[servo/rust-url](https://github.com/servo/rust-url).

## What is tested

**`tests/unit.rs`**
- `hegel_parse_never_panics`: Parsing arbitrary text must never panic (parse robustness).
- `hegel_parsed_url_upholds_check_invariants`: Any successfully parsed URL must satisfy the crate's own internal invariant checker (`Url::check_invariants`).
- `hegel_parse_serialize_parse_is_fixed_point`: The crown stability property: serializing a parsed URL and re-parsing it is a fixed point. (This mirrors the crate's own fuzz target `fuzz/fuzz_targets/parse.rs`.)
- `hegel_plausible_url_parse_serialize_parse_is_fixed_point`: Same fixed-point property, but on generated plausible URLs where the parse is required to succeed (no vacuous guard).
- `hegel_as_str_is_concatenation_of_components`: `as_str()` is exactly the concatenation of the component getters: scheme ":" ["//" authority] path ["?" query] ["#" fragment].
- `hegel_authority_is_concatenation_of_credentials_host_port`: `authority()` is exactly the concatenation of [username [":" password] "@"] host [":" port].
- `hegel_safe_setter_values_roundtrip_through_getters`: Setting fragment / query / path to values made only of characters that the parser neither encodes nor normalizes must round-trip exactly through the getters, and the URL must still re-parse to itself.
- `hegel_arbitrary_setter_values_keep_url_reparseable`: After hitting a parsed URL with setters fed *arbitrary* text, the URL must still satisfy the internal invariants and re-parse to itself (i.e. setters can never produce an invalid serialization).
- `hegel_set_port_default_port_normalization`: Setting a special scheme's default port normalizes to `port() == None`, and `port_or_known_default()` always reports the effective port.
- `hegel_join_absolute_url_is_that_url`: Joining an absolute URL's serialization against any base returns that URL again (the base is ignored).
- `hegel_join_empty_string_is_base_without_fragment`: Per the WHATWG spec, `base.join("")` returns the base URL without its fragment.
- `hegel_origin_ignores_path_query_fragment`: A tuple origin depends only on scheme, host and port: it is stable under re-parsing and unchanged by path/query/fragment mutation.
- `hegel_set_path_on_cannot_be_a_base_url_upholds_invariants`: KNOWN FAILURE — pins a real bug in `Url::set_path`. For cannot-be-a-base (opaque-path) URLs, `set_path` routes the value through `Parser::parse_cannot_be_a_base_path` in setter context (url/src/parser.rs, `Context::Setter`), where the `'?' | '#'` early-return guard only applies to `Context::UrlParser`. The characters are therefore written *raw* into the serialization (the CONTROLS percent-encode set does not cover them) without setting `query_start`/`fragment_start`. Result: the crate's own `Url::check_invariants()` fails, and the URL's getters disagree with a re-parse of its own serialization, e.g.:   Url::parse("a:").set_path("?")  =>  as_str() == "a:?" with   query() == None, while Url::parse("a:?").query() == Some(""). By contrast, non-opaque paths correctly encode to %3F / %23. Every generated case triggers the bug, so this test fails deterministically. Do not "fix" the test — fix `set_path`.
- `hegel_set_empty_host_with_credentials_or_port`: KNOWN FAILURE — pins a real bug in `Url::set_host`. The WHATWG hostname setter fails when the new host is the empty string and the URL includes credentials or a port ("host state" with state override: <https://url.spec.whatwg.org/#host-state>). `Url::set_host` only enforces the empty-host rejection for special schemes (url/src/lib.rs, `set_host`), so on a non-special URL with credentials or a port it returns Ok(()) and produces a serialization such as "a://user@" or "a://:1" that `Url::parse` itself rejects with `ParseError::EmptyHost` — `check_invariants()` panics with "Failed to parse myself?". The converse direction is guarded correctly: `set_username`/`set_port` on an empty-host URL return Err. Every generated case triggers the bug, so this test fails deterministically. Do not "fix" the test — fix `set_host`.

## Oracles

## Not tested

## History

- 2026-07-08: predecessor base commit `25137be1fc1d` (fix percent-encode of caret in path (#1140) (#1141)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/url.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
