# microlp

[Specy/microlp](https://github.com/Specy/microlp) (crates.io `microlp`): a small pure-Rust
linear and mixed-integer programming solver (revised simplex with LU, branch and bound). Pinned
at 0.6.0 (f9a3ecdd, 2026-08-02). The tests are David R. MacIver's, pulled in at his request from
the `hegel-tests` branch of his fork ([DRMacIver/microlp](https://github.com/DRMacIver/microlp),
5996cb0): that branch carries eight commits of solver fixes for upstream issue #44 and the tests
that drove them; the zoo takes the tests (`src/tests/general.rs`, `src/tests/regressions.rs`, the
new `src/tests/feasibility.rs`, `.gitignore`) and runs them against upstream master without the
fixes, so what the branch fixed is recorded here as bugs. The fork's master is upstream's master,
so the tests apply cleanly. One change of the zoo's own: `free_zero_cost_variable_is_dual_feasible`
hangs at the pinned commit (that is microlp/2), so its solves run on a thread under a 20 s
limit and a hang fails the test instead of stalling the suite.

## What is tested

- **an_origin_feasible_bounded_model_solves** (`feasibility.rs`, `#[hegel::test]`, 1,000,000
  cases) — one to three real variables bounded by small integers either side of zero, an
  optional integer variable fixed at zero (so the solve takes the MIP path where #44 failed),
  up to two rows with coefficients from 1e-8 to 2e4 (a quarter of them exact small values, so
  a row can pair `-1` with `1.19e-8` as the issue's does) whose right-hand sides the origin
  satisfies. Every bound is finite and the origin is feasible, so `Ok` is the only correct
  answer: no tolerance, no reference solver. A counterexample prints as the Rust that rebuilds
  the model (`PrettyPrintable`). The models are tiny: the million cases take about 23 s in the
  optimized test profile. At the pinned commit it fails on most seeds (four of six runs, after
  0.4–23 s; the derandomized CI profile fails in 12 s) and passes on the rest, so it is listed
  as an intermittent expected failure.
- **regressions.rs** — the reported issue-#44 model and the same shape through the pure-LP
  path (`issue_44_reported_model_solves_to_the_only_feasible_point`); a deterministic sweep of
  200 full-mantissa coefficients over the failing band
  (`issue_44_coefficient_band_solves_to_the_only_feasible_point`); the issue's second model at
  five row scales on both paths (`issue_44_scaled_row_solves_for_every_scale`); a row with
  coefficients around 1e8 with a brute-force enumeration of its two integer variables as oracle
  (`huge_coefficient_row_validates_within_round_off`); `Tolerances::feasibility` = 1e-9
  yielding the exact vertex (`feasibility_tolerance_drives_the_engine`). Upstream's own
  regressions for issues #3 and #42 pass.
- **general.rs** — `free_zero_cost_variable_is_dual_feasible` (four small models with a free
  zero-cost variable), `large_activity_rows_terminate_and_solve` and
  `large_activity_rows_are_feasible_in_any_units` (rows with activities near 1e5 that a
  constant tolerance floor hung or declared infeasible on the branch; they pass at the pinned
  commit and stay as guards).

## Oracles

Feasibility by construction (the origin), brute-force enumeration of integer variables, the
only feasible point of a model known analytically; no reference solver.

## Not tested

Anything beyond the branch's tests: the TSP and resume suites upstream ships are `#[ignore]`d
in debug builds; no property compares against another solver. The branch's engine-level tests
(planted drift, tolerance derivations, `check_constraints` floors) test code that exists only
on the branch and are not included.

## Bugs

Six, microlp/1–6 in `bugs.toml`, all recorded at upstream master: the reported issue-#44
`InternalError` after a pivot on a tiny element (/1); a free zero-cost variable making the
solve return `Unbounded` or loop forever on a NaN objective (/2); the effective feasibility
tolerance growing with a row's largest coefficient (/3); `Tolerances::feasibility` never
reaching the engine (/4); rows around 1e8 that no double-precision point can validate (/5);
and the origin-feasible property itself (/6), which per the branch's own commit message still
fails with all of its fixes in place (`InternalError` and, on pure LPs, `Infeasible`), so it
is wider than the other five. Upstream issue: <https://github.com/Specy/microlp/issues/44>.

## History

- 2026-09-15: created at f9a3ecdd (0.6.0) from DRMacIver/microlp `hegel-tests` 5996cb0; 6 bugs.
