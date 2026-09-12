# varisat

[jix/varisat](https://github.com/jix/varisat).

## What is tested

**`src/assumptions.rs`**
- `hegel_solve_under_assumptions_matches_brute_force`: Solving under assumptions must agree with a brute-force check of the formula extended by the assumptions as unit clauses (the documented semantics of `Solver::assume`).
- `hegel_failed_core_is_unsat_subset_of_assumptions`: When solving under assumptions is UNSAT, `failed_core` must return a subset of the assumptions that together with the formula is unsatisfiable (checked by brute force).

**`src/solver.rs`**
- `hegel_solve_matches_brute_force`: The crown property for a SAT solver: on small arbitrary formulas the solve result must match a brute-force check over all assignments, and any returned model must satisfy every clause.
- `hegel_sat_formula_has_valid_model`: Hegel port of the proptest `sat` test: a formula constructed to be satisfiable must be reported SAT and the model must satisfy every clause.
- `hegel_sgen_unsat`: Hegel port of the proptest `sgen_unsat` test: hard unsat instances must be reported UNSAT.
- `hegel_sgen_unsat_checked`: Hegel port of the proptest `sgen_unsat_checked` test: the same as `hegel_sgen_unsat` but with on-the-fly proof checking enabled, using the checker as an oracle for the generated proof.
- `hegel_self_checked_solve_matches_brute_force`: With self checking enabled, solving arbitrary small formulas must still agree with the brute-force oracle. A proof-checking failure surfaces as a solve error, so this also validates the generated proofs for SAT and UNSAT outcomes.
- `hegel_sat_via_dimacs`: Hegel port of the proptest `sat_via_dimacs` test: feeding a satisfiable formula through the DIMACS writer and incremental DIMACS parser must produce SAT and a model of the original formula.
- `hegel_dimacs_roundtrip`: Round-trip: writing a formula as DIMACS and parsing it back must reproduce the formula exactly, including the variable count from the header (hegel port of the `roundtrip` proptest in varisat-dimacs).
- `hegel_dimacs_parse_no_panic`: Parse robustness: the DIMACS parser must return an error, never panic, on arbitrary input bytes.
- `hegel_incremental_solves_match_brute_force`: Incremental solving: after each added clause the solve result must match the brute-force result for the clauses added so far (generalizes the proptest `sgen_unsat_incremental_clauses` test, which only checks the SAT -> UNSAT transition).
- `hegel_solver_model_machine`: (no doc comment)

**`tests/checker.rs`**
- `hegel_checked_unsat_via_dimacs`: Proof-checker oracle: a proof written while solving an unsat instance must be accepted by the standalone checker for the same DIMACS input (hegel port of the proptest `checked_unsat_via_dimacs` test).

## Oracles

## Not tested

## History

- 2022-11-02: predecessor base commit `33e876937c5d` (Merge pull request #165 from maugier/cnfformula-clone).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/varisat.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
