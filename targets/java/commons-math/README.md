# commons-math

[Apache Commons Math](https://github.com/apache/commons-math) (Apache-2.0), pinned at `7bc81e97`
(4.0-SNAPSHOT, 2026-08-31): the `commons-math4-legacy` module (linear algebra, analysis,
statistics) and `commons-math4-transform` (FFT, DCT, DST, Walsh-Hadamard).

The patch adds a Maven module `hegel/` that depends on `commons-math4-legacy` and
`commons-math4-transform` at the reactor version (installed by the setup step, which builds those
two modules and what they need with `mvn -DskipTests install`), on `dev.hegel:hegel` 0.6.0 and JUnit
5. The properties are JUnit tests driven by `Hegel.test`; `Zoo.java` is the small harness shared by
the Java targets (case counts from `HEGEL_TEST_CASES`, a collect mode under `ZOO_COLLECT=1`) and
`ZooListener` prints one `ZOO ok|FAILED <method>` line per test for the judge. `Rational.java` is
the oracle's arithmetic: BigInteger rationals (every double is one exactly) with Gauss-Jordan rank,
determinant and inverse.

## What is tested

The inputs are small integer (and half-integer) matrices, polynomials and samples, so the oracle can
be exact; tolerances are scaled by the exactly computed 1-norm condition number where a linear
system is solved, and ill-conditioned cases (cond > 1e7) are skipped rather than judged.

- `LinearTest` — LU, QR, RRQR, Cholesky and SVD solvers, inverses and determinants against the exact
  rational solution (and singular detection against the exact rank) on `Array2DRowRealMatrix`,
  `BlockRealMatrix` and `OpenMapRealMatrix`; matrix algebra (multiply, transpose, operate, add,
  scalar operations, norms, trace, power, submatrices, `DiagonalMatrix`, equals/hashCode) exact on
  integers; `EigenDecomposition` (trace and product identities, `A V = V D`, orthonormal `V` for
  symmetric input, eigenvectors, square root of an SPD matrix, solver); SVD and QR factor
  reconstruction, orthonormality, rank, norm and condition number against exact values, least
  squares against the exact normal equations.
- `AnalysisTest` — `PolynomialFunction` arithmetic, values, coefficients, `PolynomialsUtils.shift`,
  the Lagrange and Newton forms and `DerivativeStructure` derivatives of every order against exact
  integer polynomial arithmetic; Simpson, Romberg, trapezoid, midpoint and iterative Legendre-Gauss
  integrators against the exact rational integral; the bracketing solvers (bisection, Brent, Ridders,
  Illinois, Pegasus, regula falsi, bracketing nth-order Brent, with `AllowedSolution` sides), the
  open methods (secant, Muller, Muller2, Newton-Raphson) and `LaguerreSolver.solveAllComplex` on
  polynomials with known integer roots; linear, cubic, Akima, Neville, divided-difference and Hermite
  interpolators reproducing their samples, derivatives and the spline conditions.
- `StatTest` — `StatUtils`, `DescriptiveStatistics` (including the windowed form as a queue model)
  and `SummaryStatistics` against exact sums, means, variances, extremes, the legacy percentile
  estimate and the mode; `Covariance`, Pearson, Spearman (average ranks) and Kendall tau-b
  correlations against their exact definitions; `SimpleRegression` (with and without intercept),
  `OLSMultipleLinearRegression` and `MillerUpdatingRegression` against the exact normal equations;
  `Frequency` against a map of counts.
- `TransformTest` — `FastFourierTransform` (both normalisations, real and complex input, the
  in-place and sampled-function entry points, inverse, Parseval), `FastCosineTransform`,
  `FastSineTransform` and `FastHadamardTransform` (double and int) against their O(n^2)
  definitions and inverses; rejection of unsupported lengths.
- `PinsTest` — one plain JUnit test per recorded bug.

## Bugs

See `bugs.toml`: `EigenDecomposition.getDeterminant` multiplies the real parts of the eigenvalues
only, so a matrix with complex eigenvalues gets the wrong determinant (1); `RRQRDecomposition.getRank`
reports rank 1 for the zero matrix (2); `SecantSolver` returns a point where the function is -362 as
a root when two successive iterates happen to fall within the accuracy (3).

## Notes

- Not covered yet: `ode`, `optim`, `fitting`, `ml`, `filter`, `genetics`, `random`, `distribution`
  and `special` (the last three largely delegate to Commons Numbers/RNG/Statistics, which the zoo
  already tests or could test directly). `stat.inference` and `stat.ranking` are empty in the legacy
  module (moved to Commons Statistics). `ResizableDoubleArray` is package-private here.
- The O(h^2) rules (trapezoid, midpoint, one-point Legendre-Gauss) are run with a relative accuracy
  of 1e-6 and at least three iterations: with a minimal iteration count of 1 two successive
  estimates can coincide by accident (the 1- and 3-point midpoint sums of a quartic over [-2, 1]
  are equal), which is the documented purpose of the minimum, not a bug.
- Where a polynomial evaluates to rounding noise around a root, the solvers cannot tell the sides
  of the root apart; the sided-solution check accepts an answer whose function value is within a
  Horner rounding bound.
- 2026-09-20: base bumped 7bc81e97e91d → 3c7e96cb47e2 (2026-09-19, "Bump github/codeql-action/* from 4.37.9 to 4.38.1"; 4.0-SNAPSHOT); 3 bug(s) still reproduce. 14 tests pass. The integrator property now counts, rather than fails, an O(h^2) rule (Trapezoid, MidPoint, one-point Legendre-Gauss) that exhausts its 100,000 evaluations on an integral cancelling to nearly zero (5x^4 - 3x^5 over [0, 2]): only the absolute tolerance is left to meet there.
