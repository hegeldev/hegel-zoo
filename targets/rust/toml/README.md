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
- 2026-09-13: base bumped a0c14f4b6a46 → 8e1d5a85c361 (2026-09-10, "chore: Release"; 1.1.6+spec-1.1.0); 1 bug(s) still reproduce; 2 ignored reproducer(s) not run. 1366 tests pass. The run command must name the crate as `toml@<version>` because the workspace also carries toml 0.5.11 (a compatibility test fixture), so each bump has to move that pin (1.1.3 → 1.1.6).
- 2026-09-13: base bumped 8e1d5a85c361 → cd2ca7c3b88e (2026-09-13, "chore(deps): Update Prek to v0.5.3 (#1218)"; 1.1.6+spec-1.1.0); 1 bug(s) still reproduce; 2 ignored reproducer(s) not run. 1366 tests pass.
- 2026-09-15: base bumped cd2ca7c3b88e → 3b81b06418e1 (2026-09-15, "chore: Update from _rust template (#1220)"; 1.1.6+spec-1.1.0); 1 bug(s) still reproduce; 2 ignored reproducer(s) not run. 1366 tests pass.
- 2026-09-17: base bumped 3b81b06418e1 → 3d1ef7d5866a (2026-09-17, "chore: Update toml-test (#1221)"; 1.1.6+spec-1.1.0); 1 bug(s) still reproduce; 2 ignored reproducer(s) not run. 1362 tests pass.
- 2026-09-18: base bumped 3d1ef7d5866a → e4b8bda51c45 (2026-09-18, "chore: Rename master to main"; 1.1.6+spec-1.1.0); 1 bug(s) still reproduce; 2 ignored reproducer(s) not run. 1362 tests pass.
