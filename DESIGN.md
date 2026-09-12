# Design of the zoo

**Status: settled 2026-09-11** (decisions at the end). Amend as the zoo teaches us better.

## What the zoo is

A curated, runnable, versioned collection of Hegel property-based tests for open-source
projects, in every language Hegel supports. The unit is a **target**: one upstream repository
(or one package inside a monorepo/workspace) in one language, with its Hegel tests, the exact
upstream version they were written against, a record of the bugs they found and what became of
those bugs, and enough metadata that a tool can fetch upstream, apply the tests and run them
without anyone remembering how.

The tests are the product. Bugs are the evidence that the tests are good, and are tracked so
that a test which found a bug at version *n* is re-run at version *n+1* and the record updated.

## Layout

```
README.md
DESIGN.md
zoo.toml                     # pinned Hegel library version per language (single source of truth)
TROPHIES.md                    # generated: every bug across all targets, by status
targets/
  rust/<name>/
  go/<name>/
  typescript/<name>/
  java/<name>/
  cpp/<name>/
  ocaml/<name>/
tools/
  zoo                          # the runner (Python, `uv run` script; see below)
  zoo_lib/...
.github/workflows/
  check.yml                    # on PR: zoo check (all) + zoo test (changed targets)
  full.yml                     # weekly: zoo test on every target, sharded by language
work/                          # gitignored: upstream checkouts materialised by the tool
```

Each `targets/<lang>/<name>/` contains exactly:

| File | Purpose |
|---|---|
| `target.toml` | metadata (below) |
| `hegel.patch` | the tests, as a `git apply`-able diff against the pinned upstream commit: test files plus the minimal build-manifest change that adds the Hegel dev-dependency. Nothing else (no reports, no `.gitignore`). |
| `README.md` | what is tested and why: the properties, the oracles used, what was deliberately not tested, notable design choices; a dated history of version bumps |
| `bugs.toml` | bug records (below); absent if none found |

`target.toml`:

```toml
name = "roaring"
language = "rust"
upstream = "https://github.com/RoaringBitmap/roaring-rs"
subdir = "roaring"                      # package within the repo, if not the root
license = "MIT OR Apache-2.0"
ai_policy_checked = "2026-07-22"        # date the maintainers' AI-contribution policy was checked; must be absent of opt-out

[base]                                  # what hegel.patch applies to
commit = "83caaca2ec5ea29e27dc19f930b9450b9a246b5b"
date = "2026-07-20"
version = "0.11.2"                      # nearest upstream release tag, if any

[hegel]
version = "0.44.1"                      # must equal zoo.toml's pin for this language (zoo check enforces)

[run]
# language backends supply defaults (cargo test -p roaring, go test ./..., …); override here
command = "cargo test -p roaring --tests hegel"
setup = []                              # extra steps, e.g. ["npm ci"]

[expected_failures]                     # tests that fail because of a known, still-open bug
"ops::hegel_remove_smallest_run_container" = "roaring/1"   # test name -> bug id
```

## Form of a target: patches, not standalone packages

Two ways to keep tests for someone else's code:

1. **Patch against a pinned upstream commit** (what the Rust predecessor did). Tests live where
   upstream's own tests live, can reach crate/package internals, and are exactly what one would
   send upstream as a PR. Cost: the patch has to be rebased when upstream moves.
2. **Standalone package** depending on upstream at a published version. Always runnable from the
   zoo alone, version bump is a one-liner. Cost: public API only; awkward for C++ and OCaml
   (no universal registry); the tests are not in a form upstream can take.

**Proposal: patches**, for three reasons. The hegel-skill and its accumulated lessons are built
around adding tests inside the target project; internals are often where the interesting
properties are; and "tracking bugs across versions" *is* rebase-and-rerun, so the rebase cost is
paid for something we want anyway. The runner (`zoo`) removes the usability gap: `zoo test
rust/roaring` clones, checks out, applies and runs.

One deliberate deviation from the skill's "add to existing test files" rule: **prefer new files**
(`tests/hegel_*.rs`, `*_hegel_test.go`, `*.hegel.test.ts`, `HegelXxxTest.java`, …) and touch
existing files only when the tests need module-private access. New-file patches survive
upstream churn far better, which matters more for a maintained zoo than for a one-shot bug hunt.

## Bugs

`bugs.toml`, one `[[bug]]` per finding:

```toml
[[bug]]
id = "roaring/1"
title = "remove_smallest/remove_biggest corrupt run containers when amount exactly consumes an interval"
kind = "silent-corruption"               # panic | abort | hang | silent-corruption | contract | roundtrip | differential | docs
severity = "high"
test = "ops::hegel_remove_smallest_run_container"
found = { commit = "83caaca2ec5", version = "0.11.2", hegel = "0.28.2", date = "2026-07-22" }
status = "open"                          # open | reported | fixed | duplicate | disputed | wontfix | retired
upstream_issue = ""                      # URL once reported
fixed_in = ""                            # upstream commit/version once fixed
reproducer = """
minimal standalone reproduction, or a pointer to the test
"""

[[bug.observed]]                         # appended by `zoo bump` at every upstream version tried
version = "0.11.2"
commit = "83caaca2ec5"
hegel = "0.44.1"
date = "2026-09-12"
result = "reproduces"                    # reproduces | fixed | not-run
```

Tests that expose a still-open bug stay in the patch, unmodified, and are listed in
`target.toml [expected_failures]`. A test that reaches a known bug only on some runs (a
model-based test whose random walk sometimes hits the buggy sequence, say) is listed as
`"name" = { bug = "id", intermittent = true }`: its failure is expected and its passing is
not taken as a sign the bug is fixed. The runner treats their failure as expected and their
*passing* as a signal ("bug roaring/1 no longer reproduces at 0.12.0 — fixed?") that the record
needs updating. This keeps the patch clean enough to send upstream and keeps CI green without
`#[ignore]` littering. Process-aborting bugs (crash/hang/OOM) are the exception: per the skill,
those keep a skipped minimal reproducer in the patch, since an abort takes the whole suite down.

`TROPHIES.md` at the root is generated from all `bugs.toml` files by `zoo report`.

Only the tests the patch adds are judged. Upstream's own suite runs alongside (the patch sits
in its test files) and can fail for reasons that are not the zoo's: patches exclude lockfiles,
so dependencies float, and toolchains drift. Such failures are reported as `UPSTREAM` and do not
make the run BAD; a failing test that *is* ours is either an expected failure or a problem.

## The runner: `tools/zoo`

A single Python script run with `uv run` (this machine and CI have python3 + uv; no other
toolchain is universal). Language backends encapsulate the per-language mechanics.

```
zoo fetch  <target>…     clone upstream into work/<lang>/<name>/ at base.commit (cached)
zoo apply  <target>…     fetch + git apply hegel.patch (fails loudly if it does not apply)
zoo test   <target>…     apply + run; honours expected_failures; prints a per-test verdict
zoo check  [<target>…]   static: target.toml valid, patch applies cleanly, hegel.version == pin,
                         every expected_failures entry names an open bug, every open bug has
                         a test, README present
zoo drift  [<target>…]   ls-remote upstream's default branch and say which targets' base.commit
                         is behind it (no clone; ~10 s for 158 targets)
zoo bump   <target>… [--to <commit>] [--accept-fixed] [--finish] [--keep]
                         rebase the patch onto upstream HEAD (3-way), run, and land the result:
                         hegel.patch regenerated, [base] advanced, one [[bug.observed]] row per
                         bug whose test ran, a README history line. Stops without landing on a
                         conflict (resolve in work/, `zoo test --no-apply`, `zoo bump --finish`),
                         on unexpected failures / unrun tests (investigate there), or when an
                         expected failure passes (rerun with --accept-fixed: status = fixed,
                         fixed_in set, the test leaves expected_failures). Intermittent expected
                         failures that pass are recorded as not-reproduced and do not block.
zoo bump-hegel <lang> <version>
                         update zoo.toml and every patch's dependency line for that language
zoo report               regenerate TROPHIES.md
zoo new    <lang> <name> <upstream>
                         scaffold a target directory
```

Backends (`rust`, `go`, `typescript`, `java`, `cpp`, `ocaml`) know: how the Hegel dependency
appears in a manifest (so `bump-hegel` can rewrite it), the default test command, how to parse
per-test pass/fail from the runner's output, and how to filter to Hegel tests only (a zoo run
should not fail because upstream's own suite has a flaky network test).

## Pinning Hegel

`zoo.toml` at the root holds one version per language library:

```toml
[rust]       hegeltest = "0.44.1"
[go]         module = "hegel.dev/go/hegel"  version = "v0.6.33"
[typescript] package = "@hegeldev/hegel"    version = "0.4.5"
[java]       artifact = "dev.hegel:hegel"   version = "0.1.0"
[cpp]        repo = "hegeldev/hegel-cpp"    tag = "v0.12.1"
[ocaml]      package = "hegel"              version = "…"
```

Every patch pins that exact version in the manifest it edits; `zoo check` refuses drift. A
Hegel upgrade is one PR per language: `zoo bump-hegel`, fix API breaks, `zoo test` everything.
Hegel releases several times a day; the zoo does not chase every release but bumps on a
schedule (say monthly) or when a release matters.

## CI

GitHub Actions.

- **PR (`check.yml`)**: `zoo check` on all targets (cheap, no builds), then `zoo test` on the
  targets whose directories the PR touches, one job per language that has changes, with the
  standard setup actions (`dtolnay/rust-toolchain`, `actions/setup-go`, `setup-node`,
  `setup-java`, `ocaml/setup-ocaml`, cmake preinstalled).
- **Weekly (`full.yml`)**: `zoo test` on every target, sharded per language, results as a job
  summary; unexpected failures and unexpectedly-passing expected failures are collected into
  one report that comes back to this project as work to triage.
- **Drift (`full.yml`, same run)**: for each target, note whether upstream has a newer release
  than `base.version`; list candidates for `zoo bump`.

Upstream clones are cached per target keyed on `base.commit`. The full run over ~160 Rust
targets is heavy (each is a cold `cargo test` build); sharding into ~8 parallel jobs keeps it to
tens of minutes.

## Seeding

Import the predecessor's 162 Rust patches as targets: strip `HEGEL_REPORT.md` and `.gitignore`
hunks, take `[base]` from `PATCHES.md`, take `[hegel] version = "0.28.2"` initially, and turn
the relevant `TROPHIES.md` rows into `bugs.toml` records (`status = "open"`, unreported). The
six opted-out crates are already excluded there. Then `zoo bump-hegel rust 0.44.x` as the
first real maintenance task, which will exercise the tooling and reveal how much the
0.28→0.44 API drift costs. Then one pilot target per other language, chosen from domains the
Rust experiment found richest (interpreters, parsers of untrusted input, codecs, anything with
a reference implementation to diff against), before scaling out.

### Evidence from a spike (2026-09-11, humantime)

The predecessor's `humantime.patch` (base `76c8929`, hegeltest 0.28.2) was applied to a fresh
clone on the project's 2-CPU VM: applied cleanly, built and ran in 17 s, 46 tests passed and
exactly the two known-bug tests failed deterministically (trophy #20 and the weak-parser
duplicate of upstream #67). Bumping to hegeltest **0.44.1** produced five compile errors, all
the 0.29 change (`#[hegel::composite]` now takes `&TestCase`), each with a compiler message
saying exactly what to change; after that mechanical edit the result was identical. `cargo
test` at 0.41+ builds `libhegel_c` via hegeltest's build script, so patches need no
`static-engine` feature. Across 162 patches the API drift will vary (0.30 `one_of!` arity,
0.33 `PrintableGenerator` for hand-written generators, 0.42 stateful `Machine`), but this
sample says the import is cheap and largely mechanical.

A static survey of all 162 patches (same day) bears that out. Median patch adds 817 lines;
all pin 0.28.2. Of the constructs that changed: 96 patches use `#[hegel::composite]` (the
mechanical fix above), 129 use `one_of!` of which about 8 exceed the new 12-arm limit
(calamine, edn-rs, jj, jsonc-parser, ron, sqlparser, vte — switch to vec-based `one_of()`),
38 use stateful testing (`#[hegel::state_machine]`/`#[rule]`/`#[invariant]`/`stateful::run`,
which the 0.35 and 0.42 changes touch), and 3 have hand-written `Generator` impls (0.33
`PrintableGenerator`). 19 use nothing that changed. So roughly 120 port mechanically and 40
need patterned manual edits. Only 25 new test files were created across all patches against
549 edits to existing files — the predecessor followed the skill's "add to existing files"
rule, so the new-file preference above would govern new targets, not the import. 84 patches
note an MSRV below hegeltest's 1.86, which the runner must handle.

## Decisions (David, 2026-09-11)

1. **Patches** against pinned upstream commits, as above; new files preferred for new targets.
2. **Seed by importing the predecessor** wholesale, updating each patch to the pinned Hegel.
3. **Known-bug tests stay as written and are listed as `expected_failures`.** The zoo's tests
   never work around a known bug.
4. **CI on GitHub Actions** as above; `tools/zoo` must equally run everything locally, since
   porting to new Hegel versions is done locally.
5. **The zoo only records bugs.** Most predecessor bugs have already been filed upstream;
   upstreaming what the zoo finds will be a separate downstream project later. Bug records
   therefore carry `upstream_issue` when known but the zoo does not chase it.
