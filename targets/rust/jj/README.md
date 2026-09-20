# jj

[jj-vcs/jj](https://github.com/jj-vcs/jj).

## What is tested

**`src/dag_walk.rs`**
- `test_topo_order_forward_random_dags`: Property: `topo_order_forward()` returns exactly the nodes reachable from `start`, each node once, and (per its doc) every neighbor comes before the node itself.
- `test_heads_random_dags`: Property: `heads()` returns exactly the start nodes that are not reachable from any *other* node in the start set (per its doc).

**`src/diff.rs`**
- `test_diff_hunks_reconstruct_inputs`: Property: the hunks of a diff form a partition of the inputs, i.e. concatenating the hunk contents for input `i` reconstructs input `i` exactly. This holds for any number of inputs and any tokenizer.

**`src/fileset_parser.rs`**
- `test_parse_program_never_panics`: Property: fileset parsing returns `Err` on invalid input; neither entry point may panic, whatever the input.

**`src/merge.rs`**
- `test_simplify_idempotence`: Property: `simplify()` is a normal form, so simplifying twice gives the same result as simplifying once.
- `test_update_from_simplified_roundtrip`: Property: updating a merge from its own (unmodified) simplified form is a no-op. This is the round-trip that `conflicts::update_from_content()` relies on when it expands an edited simplified conflict back to the original number of sides.

**`src/revset.rs`**
- `test_format_symbol_parse_symbol_roundtrip`: Property: `format_symbol()` quotes and escapes any string such that `parse_symbol()` reads back exactly the original string. This is the round-trip used when emitting symbols (bookmark/tag names etc.) into revset expressions.

**`src/revset_parser.rs`**
- `test_parse_program_never_panics`: Property: `parse_program()` returns `Err` on invalid input; it must never panic, whatever the input.

**`tests/test_conflicts.rs`**
- `test_materialize_parse_roundtrip_generated`: Property: materializing a conflict and parsing the result back yields exactly the hunks that were materialized, for every marker style and merge option. `update_from_content()` relies on this round-trip to detect that a materialized file is unchanged, so a failure here means writing and re-snapshotting a conflicted file would corrupt it.
- `test_materialize_parse_roundtrip_lone_cr`: KNOWN FAILURE: pins a real bug in the materialize/parse round trip. If a conflict term's content ends with a lone CR (a `\r` not followed by `\n`), the term does not end with an EOL, so `materialize_conflict_hunks()` "spreads" the detected EOL (`\n`) to every side as a separator. When `parse_conflict()` removes the separator again, it pops the `\n` *and* a preceding `\r` (assuming a CRLF separator), which eats the `\r` that was real content. The parsed hunks then differ from the materialized ones, so `update_from_content()` considers an *unmodified* working-copy file changed and silently rewrites the conflict, dropping the `\r` from the base/side contents. Minimal counterexample: contents `["", "\r", ""]` with `SameChange::Keep` materialize to a conflict whose parse yields `["", "", ""]`. Code path: `conflicts::materialize_conflict_hunks()` (EOL spreading) + `conflicts::parse_conflict()` (`term.pop_if(.. b'\n')` followed by `term.pop_if(.. b'\r')`).
- `test_parse_conflict_never_panics`: Property: `parse_conflict()` returns `None`/`Some` but must never panic, whatever the input bytes and parameters. It is fed unvalidated working-copy file contents.

## Oracles

## Not tested

## History

- 2026-07-21: predecessor base commit `f296bc36b18d` (cli: show workspace roots in workspace list).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/jj.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped f296bc36b18d → f532eadfc228 (2026-09-13, "cli: diff: add utility command for comparing materialized files"; 0.45.1); 0 bug(s) still reproduce; fixed upstream: jj/1. 1957 tests pass. jj/1 is fixed (issue #9868, someone reported the same lone-CR loss): the generated round-trip property covers lone CRs again. Upstream split `dag_walk`, `diff` and `merge` into the new `jj-core` crate; the patch's properties for them moved along and `[run] command` now tests `-p jj-core` too.
- 2026-09-13: base bumped f532eadfc228 → bd3d537a6308 (2026-09-13, "windows: don't attach an invisible console to subprocesses"; 0.45.1); 0 bug(s) still reproduce. 1958 tests pass.
- 2026-09-13: base bumped bd3d537a6308 → 8504a124e3ca (2026-09-13, "docs: restore backend::Commit hyperlink"; 0.45.1); 0 bug(s) still reproduce. 1958 tests pass.
- 2026-09-13: base bumped 8504a124e3ca → d737b32faa01 (2026-09-13, "cli: diff: remove repo dependency from utility command"; 0.45.1); 0 bug(s) still reproduce. 1958 tests pass.
- 2026-09-14: base bumped d737b32faa01 → aa729d0f8b9d (2026-09-14, "rust: update MSRV to 1.97.1"; 0.45.1); 0 bug(s) still reproduce. 1958 tests pass.
- 2026-09-14: base bumped aa729d0f8b9d → 629be9ecdedc (2026-09-14, "cargo: bump the cargo-dependencies group with 5 updates"; 0.45.1); 0 bug(s) still reproduce. 1958 tests pass.
- 2026-09-15: base bumped 629be9ecdedc → 9b42f79e5d7b (2026-09-15, "templates: expose resolved tree values"; 0.45.1); 0 bug(s) still reproduce. 1958 tests pass.
- 2026-09-15: base bumped 9b42f79e5d7b → e6dd2c0d60f2 (2026-09-15, "git colocation: release the repo before moving the Git directory"; 0.45.1); 0 bug(s) still reproduce. 1958 tests pass.
- 2026-09-17: base bumped e6dd2c0d60f2 → f9588f37ec00 (2026-09-17, "revset: drop 'index lifetime from evaluate_revset()"; 0.45.1); 0 bug(s) still reproduce. 1958 tests pass.
- 2026-09-17: base bumped f9588f37ec00 → a497458e49e8 (2026-09-17, "workspace remove: remove workspace directory"; 0.45.1); 0 bug(s) still reproduce. 1958 tests pass.
- 2026-09-18: base bumped a497458e49e8 → bb9b8fac71fe (2026-09-18, "bisect: --trust-endpoints"; 0.45.1); 0 bug(s) still reproduce. 1958 tests pass.
- 2026-09-20: base bumped bb9b8fac71fe → aa8c087f7d2f (2026-09-20, "config: Support `aliases.<name>.enabled = false`"; 0.45.1); 0 bug(s) still reproduce. 1958 tests pass.
