# Running and extending the zoo

`tools/zoo` (Python 3.11+, standard library only) does everything:

```sh
tools/zoo test rust/humantime      # clone upstream at the base commit, apply, run, judge
tools/zoo test rust                # every Rust target
tools/zoo check                    # static consistency of all targets
tools/zoo apply rust/foo           # materialise work/rust/foo to edit tests in place …
tools/zoo save rust/foo            # … and write the result back to hegel.patch
tools/zoo new go foo <url>         # scaffold targets/go/foo
tools/zoo drift rust               # which targets' base commit is behind upstream (ls-remote only)
tools/zoo bump rust/foo            # rebase the patch onto upstream HEAD, run, record the outcome
tools/zoo bump-hegel rust 0.45.0   # move a language to a new Hegel release
tools/zoo report                   # regenerate TROPHIES.md
```

`zoo bump` is the zoo's long-running loop: it advances `[base]`, regenerates `hegel.patch`, appends
a `[[bug.observed]]` row per bug (`reproduces` / `fixed` / `not-reproduced`) and a dated line to the
target's README. It lands nothing when the patch conflicts, a test fails unexpectedly or a known
bug stops reproducing — those need a look (`--accept-fixed` records a fix once confirmed).

Upstream checkouts go under `work/` (gitignored). You need the language's toolchain
(`cargo` for Rust, `go` ≥ 1.26 for Go, and so on) and network access for the first fetch of
each target. Some targets compare the library against a system tool or another language's
implementation (Python's `configparser`, `dpkg`, `bash`/`dash`/busybox `ash`, R, …); their
`target.toml` lists what they need under `[run] setup`, and `.github/workflows/check.yml`
installs it on CI.

## Judging

`zoo test` applies the patch, runs `[run] command` and judges the test results against
`[expected_failures]`: every test the patch adds must run and pass, except those pinned to a bug
in `bugs.toml`, which must fail (a pinned test that passes is reported — the bug may be fixed
upstream, `zoo bump --accept-fixed` records that). Upstream's own tests failing are reported as
`UPSTREAM` and not judged. `--test-cases N` sets Hegel's budget (the weekly `full.yml` run uses
1000, ten times the default).

## Per language

- **Rust**: the patch adds `hegeltest` to `[dev-dependencies]` and tests under `tests/` or in
  the crate; `cargo test` is the runner and `Cargo.lock` stays out of the patch. Tests are
  `#[hegel::test]` functions; `HEGEL_TEST_CASES` is read by hegeltest itself.
- **Go**: the patch adds `hegel.dev/go/hegel` to `go.mod` (`go.sum` stays out; `zoo test` runs
  with `GOFLAGS=-mod=mod`) and a `hegel_test.go` in an external test package (`<pkg>_test`, so
  nothing collides with upstream's test helpers); `go test -v` is the runner and the
  `--- PASS/FAIL` lines are judged (subtests are not). hegel-go reads no environment variable,
  so the test file passes `HEGEL_TEST_CASES` through `hegel.WithTestCases` itself, and wraps
  each property in a `recover` that turns a panic in the code under test into a test-case
  failure — hegel-go re-raises panics after shrinking, which would abort the test binary and
  hide every later test. See `targets/go/jsonparser` for the harness.
