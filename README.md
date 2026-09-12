# Hegel zoo

A collection of high-quality property-based tests for open-source projects, in every language
[Hegel](https://github.com/hegeldev) supports.

The zoo grows out of [`DRMacIver/hegel-rust-oss-bug-finding`](https://github.com/DRMacIver/hegel-rust-oss-bug-finding),
which did this for Rust alone: a set of open-source crates at pinned base commits, a patch adding
Hegel tests to each, and a record of the bugs those tests found. The zoo extends that to all of
Hegel's languages and treats the tests themselves, rather than the bugs, as the thing being built.

It is worked on continuously by an agent, which adds tests for new repositories, records the bugs
they find (tracked across versions of each repository), updates to new versions of Hegel and
refactors, landing finished chunks on `main` as pull requests.

## Layout

Each **target** — one upstream project in one language — lives at `targets/<lang>/<name>/`:

- `target.toml`: upstream URL, pinned base commit, Hegel version, how to run, and the tests
  that are expected to fail because of a known, still-open bug;
- `hegel.patch`: the tests, as a `git apply`-able diff against the base commit, plus the
  one-line dev-dependency on Hegel;
- `README.md`: what is tested, with which oracles, and what deliberately is not;
- `bugs.toml`: every bug the tests found, with its status and a per-version history.

`zoo.toml` pins the Hegel library version per language. `TROPHIES.md` is generated from all
the `bugs.toml` files. `DESIGN.md` explains the choices.

## Running

`tools/zoo` (Python 3.11+, standard library only) does everything:

```sh
tools/zoo test rust/humantime      # clone upstream at the base commit, apply, run, judge
tools/zoo test rust                # every Rust target
tools/zoo check                    # static consistency of all targets
tools/zoo apply rust/foo           # materialise work/rust/foo to edit tests in place …
tools/zoo save rust/foo            # … and write the result back to hegel.patch
tools/zoo bump-hegel rust 0.45.0   # move a language to a new Hegel release
tools/zoo report                   # regenerate TROPHIES.md
```

Upstream checkouts go under `work/` (gitignored). You need the language's toolchain
(`cargo` for Rust, and so on) and network access for the first fetch of each target.

## Status

Layout settled (see `DESIGN.md`). Importing the predecessor's 162 Rust targets and porting
them to the current hegeltest is in progress; other languages follow.
