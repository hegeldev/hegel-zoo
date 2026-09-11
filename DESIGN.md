# Design of the zoo

**Status: proposed, not yet settled.** Open questions are collected at the end.

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
hegel.toml                     # pinned Hegel library version per language (single source of truth)
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
version = "0.44.1"                      # must equal hegel.toml's pin for this language (zoo check enforces)

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
`target.toml [expected_failures]`. The runner treats their failure as expected and their
*passing* as a signal ("bug roaring/1 no longer reproduces at 0.12.0 — fixed?") that the record
needs updating. This keeps the patch clean enough to send upstream and keeps CI green without
`#[ignore]` littering. Process-aborting bugs (crash/hang/OOM) are the exception: per the skill,
those keep a skipped minimal reproducer in the patch, since an abort takes the whole suite down.

`TROPHIES.md` at the root is generated from all `bugs.toml` files by `zoo report`.

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
zoo bump   <target> <commit|tag>
                         rebase the patch onto a new upstream commit (3-way; stops on conflict),
                         run, append [[bug.observed]] rows, update [base]
zoo bump-hegel <lang> <version>
                         update hegel.toml and every patch's dependency line for that language
zoo report               regenerate TROPHIES.md
zoo new    <lang> <name> <upstream>
                         scaffold a target directory
```

Backends (`rust`, `go`, `typescript`, `java`, `cpp`, `ocaml`) know: how the Hegel dependency
appears in a manifest (so `bump-hegel` can rewrite it), the default test command, how to parse
per-test pass/fail from the runner's output, and how to filter to Hegel tests only (a zoo run
should not fail because upstream's own suite has a flaky network test).

## Pinning Hegel

`hegel.toml` at the root holds one version per language library:

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

## Open questions

1. **Patch vs standalone package**, and the "prefer new files" deviation from the skill.
2. **Seeding by wholesale import** of the predecessor's patches and trophies, or a curated
   subset (say the ~90 crates with bugs), or fresh?
3. **Known-bug tests as `expected_failures`** in `target.toml` (proposed) versus marking them
   ignored/skipped inside the patch.
4. **CI on GitHub Actions** with a weekly full run — acceptable in minutes and in noise? The
   alternative is running the full matrix on the project's own VM (2 CPUs; slow but free).
5. **Reporting upstream**: is filing the bugs with maintainers part of this project's remit
   (it would go as Andon work items with GitHub access), or does the zoo only record them?
