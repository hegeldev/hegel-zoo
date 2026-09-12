# toml

[toml-rs/toml](https://github.com/toml-rs/toml).

## What is tested

**`tests/testsuite/value.rs`**
- `value_serialization_roundtrips_and_is_fixpoint`: Round-trip: `toml::to_string` then `toml::from_str` recovers an equal `Value` for arbitrary documents (nested tables, arrays, strings, i64 boundaries, floats including inf/nan/-0.0, bools, datetimes, keys that need quoting) — and re-serializing the reparsed value is a fixpoint.
- `from_str_value_never_panics`: Parse robustness: `toml::from_str::<Value>` must return `Err` rather than panic, on arbitrary text and on TOML-shaped soup.
- `deeply_nested_documents_error_gracefully`: Deeply nested input must never crash the deserializer: the recursion guard (`LIMIT = 80` in `src/de/parser/mod.rs`) turns it into a clean error. Sweeps depth well past the guard, pinning the exact boundary.

## Oracles

## Not tested

## History

- 2026-07-16: predecessor base commit `a0c14f4b6a46` (chore(deps): Update Prek to v0.4.10 (#1190)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/toml.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
