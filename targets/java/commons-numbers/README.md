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

## What was found (25 bugs, `bugs.toml`)

- **Overflow and scaling**: `Complex.log`/`sqrt` return infinity for a huge real with a subnormal imaginary part (2),
  `Complex.exp` loses a finite part past e^709 (3), `CosAngle` computes the dot product unscaled (0 or ∞ for tiny or
  huge vectors, 12), `BigFraction.from(double, …)` keeps Fraction's 2^31 limit (15), `Precision.round` throws for extreme
  scales (14), `Combinations.comparator()` overflows a long norm (8); `Complex.log` with a subnormal part rescales by
  2^54 and keeps the rounding of 54 ln 2 (76 ulps in `log(1.5 + i MIN_VALUE)`, 21); `Complex.divide` forms the quotient
  at the dividend's magnitude before scaling it back, so a subnormal-sized dividend over a divisor below 1 loses bits
  that a normal result still shows (3% for 3·MIN_VALUE / 6.7e-19, 24); `RegularizedBeta.derivative` forms x^a before
  dividing by x(1 − x), so at small x it is infinite (at or below 2^-1024, whatever a and b), 0 or inaccurate (where x^a
  underflows), or NaN (23).
- **Special functions**: `Digamma` has no poles (6); `Digamma`/`Trigamma` evaluate tan/sin(πx) from the rounded product,
  breaking the 1e-8 promise for large negative arguments and near the poles (7); the arcsine shortcut for a = b = 1/2
  leaves `RegularizedBeta`/`IncompleteBeta` up to 1e-10 off near the ends, the complement exactly 1 below x = 2^-53 (19);
  `RegularizedBeta` loses accuracy for a subnormal x, its Lanczos power terms rounding in the subnormal range (1e4 ulps at
  2^-1050, 1e-5 relative at 2^-1070), while `IncompleteBeta` stays exact (25).
- **Angles**: `Reduce` returns the period itself or negative values (10) and the normalizers go below their lower bound
  (11) for large arguments — the naive `x − p·floor(x/p)` reduction — and for an argument a subnormal step below the
  lower bound, which comes back unchanged (11, second shape).
- **Contracts**: `intValue`/`longValue` truncate where the Javadoc says floor (1), `nthRoot(Integer.MIN_VALUE)` is
  empty (4), representable `Fraction` results throw (`gcd(MIN, MIN)`, sign in the denominator, 5), `LogFactorial`
  depends on its cache (9), `Sum` never returns −0.0 (13), `from(value, 0.0, n)` accepted and a wrong message (16),
  `from(value, ε, n)` ignores an ε below ulp(value) (17), `ArithmeticUtils.pow(-2, 31)`/`pow(-2L, 63)` throw for
  `MIN_VALUE` (18), `DD.multiply(DD)` promises 4 eps and reaches Dekker's 5 (20), `DD.longValue()` returns −1 for
  −1 + lo with a positive low part, where the documented truncation towards zero gives 0 (22).

Drawn by default (STYLE.md rule 11, the whole target since 2026-10-06): every switch in `Known` is off by default, so the
wide properties draw the shapes of all 25 bugs and are expected failures mapped to the bug they shrink to —
`fractionsAgreeWithBigIntegerRationals` (1), `fractionsFromDoublesMeetTheirBounds` (16), `combinatoricsAgreeWithBigInteger`
(9) and `gammaAndErrorFunctionsAgreeWithMpmath` (6) every run; `textPolarRootsAndPowersAreConsistent` (4),
`combinationsAreEnumeratedInOrder` (8), `anglesReduceIntoTheirIntervals` (10), `sumsAndNormsAreAccurate` (13),
`precisionComparisonsFollowTheirDefinitions` (14), `arithmeticUtilsAgreeWithBigInteger` (18),
`elementaryFunctionsAgreeWithMpmath` (21), `doubleDoubleArithmeticStaysWithinItsBounds` (22, also 20),
`incompleteGammaAndBetaAgreeWithMpmath` (23, also 19 and 25) and `arithmeticAndModulusAreAccurate` (24) at their natural
rates, mapped intermittent. Bugs 2, 3, 5, 7, 11, 12, 15 and 17
live in regions the wide generators reach rarely or never (a huge real beside a subnormal imaginary, `MIN_VALUE` parts,
the reflected digamma band, 2^30 periods out), so one narrow property per bug carries the deterministic failure beside
each wide one (`intValueAndLongValueOfANegativeFractionAreTheFloor`, `logAndSqrtWithAHugeAndASubnormalPartAgreeWithMpmath`,
`expOfARealPartPastTheOverflowKeepsItsFiniteImaginaryPart`, `nthRootRejectsIntegerMinValueForAnyBase`,
`fractionArithmeticWithMinValuePartsStaysRepresentable`, `digammaHasNoFiniteValueAtTheNegativeIntegers`,
`digammaAndTrigammaReflectionKeepsTheDocumentedAccuracy`, `comparatorOfALargeUniverseOrdersSubsets`,
`logFactorialWithACacheAgreesWithTheUncachedValue`, `reduceOfAHairBelowTheOffsetStaysBelowThePeriod`,
`normalizersStayAboveTheLowerBoundForLargeArguments`, `cosAngleOfTinyOrHugeVectorsIsTheirCosine`,
`sumOfNegativeZerosIsNegativeZero`, `roundWithAnExtremeScaleGivesTheDecimalRounding`,
`bigFractionApproximationsOfValuesBeyondTheIntRangeAreConvergents`, `fromWithANonPositiveEpsilonIsRejectedNamingTheEpsilon`,
`fromWithAnEpsilonBelowTheUlpOfTheValueStaysWithinIt`, for 18–21 and the second shape of 11 the five of 2026-10-06, and for
22–25 `conversionsOfAValueJustAboveMinusOneTruncateToZero`, `betaDerivativeOfASubnormalXStaysFinite`,
`divideOfATinyDividendBySmallDivisorIsAccurate` and `regularizedBetaOfASubnormalXAgreesWithMpmath`), with
the pins in `CommonsNumbersPinsTest` as regression examples. `HEGEL_NO_KNOWN=1` (`Zoo.NO_KNOWN`, read once into `Known`)
turns the switches on: the wide properties then check beside the shapes instead of skipping cases (the floor on the
negated fraction, digamma's accuracy at 1/2 − x and −x, a value folded into the int range, a period exponent capped at
2^29), the narrow properties draw the neighbouring region, and every property passes. The `DOUBLE_EQUIVALENCE_NAN_ORDER`
switch is not a bug gate and stays on.

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
- `Complex.nthRoot` is documented on the modulus `abs()`, which sits on the subnormal grid when |z| is subnormal:
  `nthRoot(2)` of 1.5e-314 + 6e-320 i is 4e-12 from the exact root that `sqrt` and `pow(1/2)` give. The principal-root
  check scales such a z by 2^600 first. (`Complex.log` of two subnormal parts is right: it scales before taking the
  magnitude, where `Math.log(Math.hypot(x, y))` is not, hypot's subnormal result being rounded to the grid.)
- mpmath's own `betainc(a, b, x, 1)` cancels catastrophically near x = 1: the oracle computes complements as
  I_(1−x)(b, a), which the library matches to 15 digits.
- 2026-09-17: base bumped a2e57b960e2a → ce344cbafdd8 (2026-09-17, "Update commons-parent 104 to 105"; 1.4-SNAPSHOT); 17 bug(s) still reproduce. 17 tests pass.
- 2026-09-17: base bumped ce344cbafdd8 → 21fa3accb0e4 (2026-09-17, "Checkstyle: Remove unnecessary parentheses"; 1.4-SNAPSHOT); 17 bug(s) still reproduce. 17 tests pass.
- 2026-09-20: base bumped 21fa3accb0e4 → 811a3b1c34fa (2026-09-19, "Bump github/codeql-action/* from 4.37.9 to 4.38.1"; 1.4-SNAPSHOT); 17 bug(s) still reproduce. 17 tests pass. Three harness corrections found by the bump runs: near() rounds an exact value between MAX_VALUE and MAX_VALUE + ulp/2 to MAX_VALUE rather than demanding infinity; a fraction representable only as -n / MIN_VALUE (denominator 2^31) may overflow or come out right; the mpmath oracle gives the x = 0 limits of the P and I_x derivatives instead of nan.
- 2026-09-20: base bumped 811a3b1c34fa → 30078a2322ce (2026-09-20, "Correct private javadoc errors"; 1.4-SNAPSHOT); 17 bug(s) still reproduce. 17 tests pass.
- 2026-10-06: the weekly 1000-case run (37296133806) failed five wide properties at 30078a2322ce: four new bugs (18–21) and a second shape of 11, each given a narrow property and a pin and drawn by default; two harness corrections (`Beta`'s tolerance grows with a + b, as its Lanczos product does — 825 ulps at a + b = 583; `G.in` clamps a value that rounds past its bound, which had sent `BrentSolver` an initial outside the bracket at 3000 cases) and an `ExactTest` oracle fix (`of(1, MIN_VALUE).negate()` is representable as -1 / MIN_VALUE, so the model no longer demands an overflow).
- 2026-10-06: unsteered (STYLE.md rule 11) for bugs 1–17: the 17 `Known` switches are off by default, each bug has a narrow property, the wide properties are mapped to the bugs they shrink to (see above); `anglesReduceIntoTheirIntervals` moves from 11 to 10, which is what it shrinks to. Harness corrections: the oracle's `polygamma(1, x)` is reflected for negative x (mpmath's series is linear in |x| there, 28 s at −1e7 and unbounded at −1e14 — the bug-7 gate had hidden it); the exact `binom(n, k)` model takes `min(k, n − k)` and, above 1100, checks overflow and the log against mpmath instead of multiplying 2^31 times (one likely cause of the earlier runs past ten minutes); `Fraction.pow(Integer.MIN_VALUE)` (bug 18 through `Fraction`) is a check failure instead of a test error; `BigDecimal.setScale` takes minutes for scales in about 5.4e8–7.16e8, so the round property draws from 7.2e8.
- 2026-10-07: `G.in(lo, hi)` draws `Generators.doubles().min(lo).max(hi)` instead of scaling a long: hegel-java's long draw is magnitude-biased (96% of `longs().min(0).max(2^53)` fall in the first percent of the range), so every linear draw had sat at its lower bound and every `logUniform` in its lowest decade; the double draw spreads evenly, with a quarter of the draws within 1e-6 of zero when the interval spans it, and `logUniform` draws its exponent as an offset from `lo` so that cluster falls on the lowest decade. The intermittent wide properties now fail most runs instead of a third (e.g. `incompleteGammaAndBetaAgreeWithMpmath`, `sumsAndNormsAreAccurate`, `precisionComparisonsFollowTheirDefinitions`, `doubleDoubleArithmeticStaysWithinItsBounds` at 100 cases), and the freed regions near zero found four bugs, each reproduced with jshell and mpmath: `DD.longValue()` of −1 + lo (22), `RegularizedBeta.derivative` losing its range at small x (23), `Complex.divide` of a subnormal-sized dividend (24) and `RegularizedBeta` at a subnormal x (25), each with a narrow property, a pin and a `Known` switch. Harness corrections the same draws exposed: a 0/0 relative error when `pow(2)` and `multiply` both underflow to zero (`relErr`), `DD.scalb`/`frexp` judged by the documented `Math.scalb` of each part once the low part is subnormal, a root whose modulus overflows (`nthRoot(−1)` of a subnormal w) not judged, the principal-root check scaled up when |w| is subnormal (above), the integer-power checks from |w| = 2^-500 up (a subnormal square sits on the grid), the I_x(a, b) + I_(1−x)(b, a) identity at the gross 4096-ulp bound of the mpmath checks (Boost's incomplete beta is 2e-13 off for a ≈ 59 at the mean), and the reflection model's sin(πx) computed from the reduced argument (the rounding of πx cost 1e-12 at x = 7.9994). Mappings: `doubleDoubleArithmeticStaysWithinItsBounds` 20 → 22 and `incompleteGammaAndBetaAgreeWithMpmath` 19 → 23 (their usual basins now), `arithmeticAndModulusAreAccurate` new, 24.
