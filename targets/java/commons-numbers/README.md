# java/commons-numbers

Hegel property tests for [Apache Commons Numbers](https://github.com/apache/commons-numbers) (1.4-SNAPSHOT at the
pinned commit), the small numeric library behind Commons Math's successors: fractions, integer utilities, double-double
arithmetic, compensated sums and norms, combinatorics, primes, angles, complex numbers, the gamma/beta/error functions,
quaternions and a Brent root finder.

## How it is tested

`hegel.patch` adds a `hegel/` Maven module whose tests run against the modules that `[run] setup` installs from the
pinned tree into the local repository (`commons-numbers-docs` and `-bom` are left out; `commons-numbers-complex-streams`
is in the tree but not in the root pom's module list, so it is not tested). The oracles:

- **Exact arithmetic** (`ExactTest`): `BigInteger` rationals for `Fraction`/`BigFraction` (representation, order,
  equality, conversions, text, arithmetic with the overflow contract, powers, `from(double, ...)` bounds), `BigInteger`
  for `ArithmeticUtils` (gcd/lcm/pow/unsigned), the binomial/factorial/Stirling recurrences, `Combinations` (count,
  sorted subsets, the documented right-to-left lexicographic order, the comparator against an exact norm), and
  `BigInteger.isProbablePrime` for `Primes`.
- **mpmath** (`GammaTest`, `ComplexTest`, and the log-factorial/log-binomial checks): `hegel/oracle.py` runs in a
  virtual environment that `[run] setup` creates (`python3 -m venv hegel/.venv`, `mpmath==1.4.1`); surefire passes the
  interpreter as `ZOO_PYTHON`. Arguments travel as hex floats, results as 40-digit decimals at 80 digits of working
  precision. It covers Gamma, LogGamma (+sign), Digamma, Trigamma, Erf, Erfc, Erfcx, InverseErf, InverseErfc,
  regularized/incomplete gamma and beta (values, complements, derivatives), Beta, LogBeta, GammaRatio, and the fifteen
  complex elementary functions.
- **Documented bounds and identities** (`CoreTest`, `GammaTest.specialFunctionIdentitiesHold`): `Precision`'s
  ulp/epsilon definitions and `round` on the decimal string, `Sum`/`Norm` within 1 ulp of exact `BigDecimal` values,
  `DD` within its documented multiples of 2^-106 (with the exact factories exact), the angle normalizers' intervals and
  congruence, exact unit conversions, `CosAngle` against an exact cosine, `BrentSolver`'s tolerance, and the gamma
  family's recurrence/reflection/complement identities.

Complex numbers are compared normwise (|got − exact| ≤ 16·2^-53·|exact|) and componentwise (64 ulps unless a part is
tiny next to the other); the gamma family uses a gross-error bound of 512 ulps because only Digamma/Trigamma document an
accuracy (1e-8), which is checked as written. Observed accuracy is far better than the bounds except where recorded.

## What was found (17 bugs, `bugs.toml`)

- **Overflow and scaling**: `Complex.log`/`sqrt` return infinity for a huge real with a subnormal imaginary part (2),
  `Complex.exp` loses a finite part past e^709 (3), `CosAngle` computes the dot product unscaled (0 or ∞ for tiny or
  huge vectors, 12), `BigFraction.from(double, …)` keeps Fraction's 2^31 limit (15), `Precision.round` throws for extreme
  scales (14), `Combinations.comparator()` overflows a long norm (8).
- **Special functions**: `Digamma` has no poles (6); `Digamma`/`Trigamma` evaluate tan/sin(πx) from the rounded product,
  breaking the 1e-8 promise for large negative arguments and near the poles (7).
- **Angles**: `Reduce` returns the period itself or negative values (10) and the normalizers go below their lower bound
  (11) for large arguments — the naive `x − p·floor(x/p)` reduction.
- **Contracts**: `intValue`/`longValue` truncate where the Javadoc says floor (1), `nthRoot(Integer.MIN_VALUE)` is
  empty (4), representable `Fraction` results throw (`gcd(MIN, MIN)`, sign in the denominator, 5), `LogFactorial`
  depends on its cache (9), `Sum` never returns −0.0 (13), `from(value, 0.0, n)` accepted and a wrong message (16),
  `from(value, ε, n)` ignores an ε below ulp(value) (17).

## Design choices respected (not recorded)

- `Fraction` keeps the sign wherever the reduction left it: `Fraction.of(219, -75)` is `73 / -25`, `of(-3, -6)` prints
  `-1 / -2`, `of(7, -2).abs()` is `-7 / -2`; equals/hashCode/compareTo are value-based, so this is cosmetic (and the
  cause of one shape of bug 5). `parse` strips commas (`"1,000/3"` = 1000/3).
- `Fraction.from(x, maxDenominator)` stops early when the next numerator would overflow an int, so the result is a
  convergent but not necessarily the best one under `maxDenominator`; the property checks the convergent bound |x − p/q| < 1/q².
- `BinomialCoefficientDouble` is not correctly rounded (up to ~40 ulps observed); `LogBinomialCoefficient`,
  `GammaRatio.delta` for tiny deltas (~700 ulps) and the incomplete functions are within a few thousand ulps at most.
  No accuracy is documented for them.
- `Complex.log10`'s imaginary part is `arg(z)`, not `arg(z)/ln 10` — documented that way, so the oracle compares
  `log10` only through `log`. `Complex.multiply` leaves ∞·0 as NaN deliberately; `ZERO.pow(0)` is NaN+iNaN as documented;
  `parse` is more permissive than `toString` (spaces, `1d`, hex floats). mpmath has no signed zeros, so the axis and
  branch-cut cases (covered by upstream's C99 tables) are left to those tables.
- `Digamma(-0.0)` is +∞ and `Digamma(0.0)` is −∞ (directional limits). `Gamma` treats every |x| ≥ 2^52 as an integer
  (`Gamma(-1e300)` is NaN). `RegularizedBeta` accepts a = 0 or b = 0 (1 and 0) while `IncompleteBeta` returns NaN;
  the epsilon/maxIterations overloads are ignored by the closed-form branches (integer a, a = 1 or b = 1).
- `Slerp` throws `IllegalStateException` for zero/NaN endpoints and for `apply(NaN)`; `Turn.WITHIN_0_AND_1` returns
  −0.0 for −0.0; `Precision.equals(x, x, -1)` is false (negative maxUlps is undefined); `DoubleEquivalence.compare`
  orders NaN with `Double.compare` semantics as `Precision.compareTo` documents, contradicting the interface's own
  Javadoc ("+1 if either value is NaN") — a documentation defect, not pinned.
- `GeneralizedContinuedFraction` silently clamps an epsilon outside (2^-53, 0.5] to its defaults and reports
  `maxIterations <= 0` as `ArithmeticException`; `BrentSolver` returns the initial midpoint when
  `functionValueAccuracy` is large (undocumented parameter of `findRoot`).
- mpmath's own `betainc(a, b, x, 1)` cancels catastrophically near x = 1: the oracle computes complements as
  I_(1−x)(b, a), which the library matches to 15 digits.
- 2026-09-17: base bumped a2e57b960e2a → ce344cbafdd8 (2026-09-17, "Update commons-parent 104 to 105"; 1.4-SNAPSHOT); 17 bug(s) still reproduce. 17 tests pass.
- 2026-09-17: base bumped ce344cbafdd8 → 21fa3accb0e4 (2026-09-17, "Checkstyle: Remove unnecessary parentheses"; 1.4-SNAPSHOT); 17 bug(s) still reproduce. 17 tests pass.
- 2026-09-20: base bumped 21fa3accb0e4 → 811a3b1c34fa (2026-09-19, "Bump github/codeql-action/* from 4.37.9 to 4.38.1"; 1.4-SNAPSHOT); 17 bug(s) still reproduce. 17 tests pass. Three harness corrections found by the bump runs: near() rounds an exact value between MAX_VALUE and MAX_VALUE + ulp/2 to MAX_VALUE rather than demanding infinity; a fraction representable only as -n / MIN_VALUE (denominator 2^31) may overflow or come out right; the mpmath oracle gives the x = 0 limits of the P and I_x derivatives instead of nan.
- 2026-09-20: base bumped 811a3b1c34fa → 30078a2322ce (2026-09-20, "Correct private javadoc errors"; 1.4-SNAPSHOT); 17 bug(s) still reproduce. 17 tests pass.
