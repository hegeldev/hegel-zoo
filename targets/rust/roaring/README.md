# roaring

Compressed bitmaps ([RoaringBitmap/roaring-rs](https://github.com/RoaringBitmap/roaring-rs)),
the `roaring` crate in the workspace. Tests are added to the crate's existing integration test
files under `roaring/tests/`; a shared `RoaringBitmap` generator in `tests/common/mod.rs`
covers array, bitmap and run containers.

## What is tested

- **Iteration** (`iter.rs`): `iter()` yields exactly the members, strictly increasing, `len()`
  of them; backward iteration is the reverse of forward.
- **Construction** (`lib.rs`, `push.rs`): `from_lsb0_bytes(offset, bytes)` contains exactly the
  set bits at their documented positions; `from_sorted_iter(iter())` rebuilds the same bitmap;
  `try_push` keeps exactly the strictly-increasing subsequence.
- **Removal** (`lib.rs`): `remove_smallest(n)` / `remove_biggest(n)` agree with plain iteration
  and leave the bitmap internally valid (**fails: roaring/1**, run-container corruption).
- **Ranges** (`range_checks.rs`): `range_cardinality`, `contains_range`, `insert_range`,
  `remove_range` agree with counting over plain iteration and with each other.
- **Rank/select** (`rank.rs`): `select(n)` returns a member `v` with `rank(v) == n + 1`.
- **Multi-way ops** (`ops.rs`): `MultiOps` union/intersection/difference/symmetric difference
  equal the naive left fold of the binary operator.
- **Serialisation** (`serialization.rs`, `treemap_serialization.rs`): `serialize_into` →
  `deserialize_from` round-trips for bitmaps and treemaps, `serialized_size` equals the bytes
  written; `deserialize_from` never panics on arbitrary or corrupted input.
- **Model-based** (`lib.rs`): a state machine drives a `RoaringBitmap` against a `BTreeSet<u32>`
  model through insert/remove/range ops/optimize/remove_run_compression, checking length,
  min, max, contents and `internal_validate` as invariants.

## Oracles

Plain iteration over the bitmap; a `BTreeSet<u32>` model; the crate's own `internal_validate`;
the rustdoc contracts quoted in each test's comment.

## Not tested

`RoaringTreemap` beyond serialisation; the `croaring` differential comparison (upstream has a
fuzz target for that); performance claims.

## History

- 2026-04-24: predecessor base commit `83caaca2` (v0.11.4).
- 2026-07-22: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding.
- 2026-09-11: imported; ported to hegeltest 0.44.1 — composites take `&TestCase`; draws of the
  foreign `RoaringBitmap` type need `.print_as_debug()` (with `use hegel::Generator`); the local
  `SetOp` enum derives `hegel::PrettyPrintable`; `stateful::run(m, tc)` became
  `stateful::machine(m).run(tc)`.
- 2026-09-13: base bumped 83caaca2ec5e → 0ce3fc8b55b1 (2026-08-12, "Merge pull request #364 from RoaringBitmap/upgrade-dependencies-bump-version"; 0.11.5); fixed upstream: roaring/1 (interval_store.rs boundary comparisons; both deterministic pins pass, and the model-based property is no longer an expected failure). 520 tests pass.
