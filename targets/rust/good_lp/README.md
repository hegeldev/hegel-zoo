# good_lp

[rust-or/good_lp](https://github.com/rust-or/good_lp).

## What is tested

**`src/solvers/microlp.rs`**
- `solved_lp_solution_is_feasible`: The solution returned for a feasible, bounded problem satisfies every constraint (within tolerance), respects the declared variable bounds, and gives integral values to integer variables.
- `solved_lp_objective_dominates_feasible_witness`: The optimal objective value is at least as good as the objective value at the known feasible witness point.
- `redundant_constraint_preserves_optimal_value`: Adding a constraint that is redundant (implied by the variable bounds) must not change the optimal objective value.
- `positive_scaling_of_objective_scales_optimal_value`: Scaling the objective by a positive constant k scales the optimal objective value by k (the optimal set is unchanged).
- `impossible_constraint_reports_infeasible`: A constraint that requires a linear expression to exceed its maximum over the variables' bounding box makes the problem infeasible, and the solver must report exactly that.
- `unbounded_objective_reports_unbounded`: Maximising a positive-coefficient objective over a continuous variable with no upper bound (or minimising with no lower bound) must report ResolutionError::Unbounded, not a wrong solution.

**`tests/variables.rs`**
- `expression_ops_match_coefficient_model`: Building an Expression through an arbitrary sequence of the public mutation operators (`+= c*v`, `-= c*v`, `+= k`, `*= k`, unary `-`) must agree with an independently tracked coefficient map + constant, as observed through `eval_with` at a random point.
- `expression_addition_commutes`: Addition of expressions is commutative. Per-variable coefficient addition of two floats is exactly commutative, so this holds with exact structural equality (`PartialEq` on the coefficient maps).
- `scalar_multiplication_distributes_over_addition`: Multiplying by a scalar distributes over addition: (e1 + e2) * k evaluates to e1 * k + e2 * k (up to fp rounding).

## Oracles

## Not tested

## History

- 2026-07-18: predecessor base commit `e4a73e22ee00` (bump microlp add mip gap and initial solution (#129)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/good_lp.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1.
- 2026-09-13: base bumped e4a73e22ee00 → 83d030b103d5 (2026-08-31, "docs: clarify determinism guarantees (#137)"; 1.15.3); 1 bug(s) still reproduce. 94 tests pass.
