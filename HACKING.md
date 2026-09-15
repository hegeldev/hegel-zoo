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
- **TypeScript / JavaScript**: the patch adds ESM test files under the package's test directory
  (`test/hegel.test.mjs` plus the small harness `test/hegel-zoo.mjs`: `property`, `pin`,
  `fail`/`count` with a collect mode under `ZOO_COLLECT=1`, and a load-time check that the
  installed `@hegeldev/hegel` is the pinned version, `HEGEL_PIN` — the line `zoo check` reads);
  package.json is not touched. `node --test --test-reporter=tap <files>` is the runner and the
  top-level TAP lines are judged (`ok N - TestHegel…`, `not ok`, `# SKIP`); test names are
  `TestHegel…` without spaces. `zoo test` installs the package's runtime dependencies and
  Hegel with `npm install --no-save --no-package-lock --omit=dev @hegeldev/hegel@<pin>`
  (override with `[run] setup` when a build step is needed); lockfiles and node_modules stay
  out of the patch. `@hegeldev/hegel` reads no environment variable: the harness passes
  `HEGEL_TEST_CASES` as `testCases` and `HEGEL_DATABASE` as the database path. Node 22+.
  See `targets/typescript/ini` for the harness.
- **Java**: the patch adds a self-contained Maven module `hegel/` at the repository root:
  `hegel/pom.xml` depends on the library's own artifact at the version its pom declares (the
  `[run] setup` step installs it into the local Maven repository with `mvn -DskipTests install`,
  or Gradle's `publishToMavenLocal`), on `dev.hegel:hegel` (the FFM binding, JDK 22+; the version
  is the module's `<hegel.version>` property — the line `zoo check` reads) and on JUnit 5, and
  runs surefire with `--enable-native-access=ALL-UNNAMED` and `testFailureIgnore`. Under
  `hegel/src/test/java/zoo/` sit the harness `Zoo.java` (`settings(name)` reads `HEGEL_TEST_CASES`
  and `HEGEL_DATABASE`, which hegel-java itself does not; `fail`/`count` with a collect mode under
  `ZOO_COLLECT=1`), `ZooListener.java` — a JUnit platform `TestExecutionListener`, registered in
  `hegel/src/test/resources/META-INF/services/`, that prints one `ZOO ok|FAILED|ignored <method>`
  line per test method, the lines the judge reads — and the tests: plain `@Test` methods, each
  property calling `Hegel.test(body, Zoo.settings("<method>"))` (the `@HegelTest` annotation takes
  only compile-time settings). `mvn -q -B -ntp -f hegel/pom.xml test` is the runner; the
  annotation must sit on the line before `void name(`. JDK 25 and Maven on the machine. See
  `targets/java/gson` for the harness.
