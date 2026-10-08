# go/gonum

[gonum/gonum](https://github.com/gonum/gonum) (v0.17.0 plus 1 commit): numerical libraries for
Go. This target tests three packages against exact references: `mathext` (the special
functions: incomplete gamma and beta and their inverses, the elliptic integrals, digamma, zeta,
the Gauss hypergeometric function, Airy and dilogarithm), `stat/distuv` (21 univariate
distributions and their densities, cumulatives, quantiles, moments and entropies) and `stat`
(37 descriptive statistics, weighted and unweighted).

## Build

The patch adds `hegel.dev/go/hegel` to `go.mod` and a `hegel/` package of test files:
`go test -count=1 -run TestHegel -v ./hegel`. The properties need `python3` with `numpy`,
`scipy` and `mpmath` on PATH (the zoo's venv in CI); the pins need nothing.

## Oracles

Python over a JSON-lines subprocess, floats travelling as their shortest round-trip text.
mpmath at 30 digits (40 to 90 where the moments cancel) is the reference for `mathext`: the
regularised incomplete beta and gamma and their inverses (the inverses refined by a root search
in log space against the 30-digit forward function, with the exact leading term when the root is
below 1e-18, and solving for the complement when the root is above 1/2: the secant's first log
step used to land beyond 1 and the oracle skipped every answer above 0.78), lgamma, digamma, the elliptic integrals, `hyp2f1`, Airy and the dilogarithm; the
Hurwitz zeta is an Euler–Maclaurin sum of the test's own (mpmath's `zeta(s, q)` loses digits for
large `s` and `q`). SciPy's `stats` gives the distributions, with mpmath taking over where SciPy
is known to fail: the Bernoulli and Binomial moments near P = 1, the Chi moments (a difference of
lgammas at 90 digits), the Pareto median, quantile, skewness and kurtosis, the Poisson pmf for
λ > 1e4, the Weibull log density and moments (80 digits: the kurtosis cancels to 1/K⁴), the
LogNormal beyond |μ| = 300 and its moments (SciPy's take exp(σ²) − 1 in doubles and cancel like
gonum's), the Student's t CDF and quantile within 1e-3 √ν of the centre (SciPy's CDF is exactly
0.5 there for ν = 1), the Triangle and Uniform survival (SciPy's is 1 − CDF), and the noncentral
t as a validated quadrature of its definition for |μ| > 37 or wherever SciPy returns NaN or raises. NumPy
models `stat` from the documented formulas (weights dropped when they are 0 except in the
raw moments, which multiply 0 by an infinite power as gonum does).

## Generator

Numbers of ten magnitude profiles (small integers, quarters, three decimals, tiny 1e-3…1e-12,
large 10…1e9, huge to 1e100, binary fractions, near integers, integers) with a 40% sign;
probabilities with the ends, 1e-2…1e-15 and their complements. For `mathext` (rewritten in
combinator style, part 1 of three) a number is a record of profile, mantissa, exponent and sign
rendered by a pure function, the plainest profile first; the argument list of a function is a
record of its function and arguments drawn from package-level generators, the function table a
`SampledFrom` with Digamma first; the shape region of every recorded `mathext` bug is drawn one
time in five beside the plain arguments (never under `HEGEL_NO_KNOWN=1`), and the narrow
properties draw the regions alone, with the region next to the shape under `HEGEL_NO_KNOWN=1`.
Shapes for the special functions add half-integers and values near 1. For `distuv` (part 2) a
case is a distribution of a `SampledFrom` table of 22 specs, a method it has, parameters from
the distribution's own package-level generators (locations of moderate size, scales, counts,
probabilities, Chi and Weibull shape parameters capped for the moments, NoncentralT's Nu and Mu
with their wild regions) and an argument - a point of the support (the ends, the mode, the mean,
1e20), a number, or for a discrete distribution a small integer; the shape regions of the
twenty-three `distuv` bugs and of the five `mathext` bugs the distributions inherit are drawn
beside the plain calls with the same `known` weight as in `mathext`, never under
`HEGEL_NO_KNOWN=1`, and where a region is a large share of a parameter's range (|Mu| above 38,
Nu beyond 3000 or below 1e-3, a negative argument of the cumulatives of ChiSquared, F,
InverseGamma and Chi, a Logistic density beyond 354 scales out, Chi K above 5 and Weibull K
above 20 for the moments) its weight is zero under `HEGEL_NO_KNOWN=1`. For `stat` (part 3) a
case is a function of a `SampledFrom` table of 37 specs (HarmonicMean first, its empty dataset
the simplest deterministic failure) and the inputs of that function's own generator: a dataset
record of a profile (small integers, tenths, counts, thousandths, thousands, the number records)
and 0 to 60 values drawn one by one or, one time in three, from a pool of one to three values
(ties, and constant data), the empty dataset a plain alternative; weights of 1, integers,
thousandths or tenths with a zero one time in twenty, absent half the time; a second series
independent or a noisy linear image of the first; the extras (a moment's order, a quantile's p
and kind, a histogram's dividers, a regression's line) as named values; the shape regions of the
three `stat` bugs drawn beside the plain inputs with the same `known` weight - the empty dataset
for HarmonicMean, constant data under weights whose sum makes the corrected variance negative
(kept by `hegel.Filter` on the library's own NaN, 88 % of the draws) for the deviations, the
quantile at p = 1 under weights of 1 and m 10⁻¹⁷ for Quantile - and never under
`HEGEL_NO_KNOWN=1`.

## Properties

- `TestHegelMathext`: 21 real functions of `mathext` (Beta, Lbeta, MvLgamma, Digamma, Zeta,
  the complete elliptic integrals K/E/B/D, EllipticF/E, EllipticRF/RD, GammaIncReg and its
  complement and both inverses, RegIncBeta and its inverse, Hypergeo, NormalQuantile) agree with
  mpmath to 1e-13 relative (1e-10 where recorded), or panic where documented.
- `TestHegelMathextComplex`: Li2, AiryAi and AiryAiDeriv of a complex argument to 1e-9.
- `TestHegelDistuv`: the 21 distributions' Prob, LogProb, CDF, Survival, Quantile, Mean, Median,
  Mode, Variance, StdDev, Skewness, ExKurtosis and Entropy agree with SciPy/mpmath to 1e-12
  relative (1e-9 for cumulatives and quantiles).
- `TestHegelDistuvOther`: the AlphaStable moments and the Categorical distribution (no
  recorded bug; passes).
- `TestHegelDistuvLaws`: a distribution against itself: CDF + Survival = 1 to 1e-10,
  Quantile(CDF(x)) = x wherever the density is positive, LogProb = log Prob, StdDev² = Variance,
  Mode inside the support, CDF monotone; it draws the same cases as `TestHegelDistuv`, so it
  reaches the recorded shapes too and fails nearly every run, mapped intermittent to gonum/15
  (Logistic's far-tail Prob is NaN while exp(LogProb) is 0), the plurality of its basins
  (twenty-nine of forty rounds at a hundred cases; gonum/27's panic ten; one round passed).
- `TestHegelStat`: 37 functions of `stat` (moments, means, correlation, covariance, Kendall,
  the entropies and divergences, histograms, quantiles and CDF, Kolmogorov–Smirnov, the linear
  regressions and R², Mode, StdErr, StdScore, Wasserstein) agree with the NumPy model to 1e-10
  of the data's magnitude; it fails every run and is mapped to gonum/37, the basin it shrinks
  to every time (forty of forty rounds at a hundred cases: HarmonicMean of the empty dataset,
  the first table entry and the simplest shape).
- Thirteen narrow properties, one per `mathext` bug, each a generator over the bug's shape
  region with random contents judged like `TestHegelMathext` and failing every run
  (`HypergeoIsDefinedAtItsSpecialPoints` 1, `HypergeoNearTheUnitPoint` 2,
  `LbetaWithALargeArgument` 3, `GammaIncRegInvTinyAnswers` 4, `GammaIncRegCompInvNearOne` 5,
  `InvRegIncBetaNearTheEnds` 6, `RegIncBetaSmallSecondParameterNearOne` 7,
  `EllipticAmplitudeBeyondAQuarterTurn` 8, `DigammaToFullPrecision` 9,
  `DigammaNextToANegativePole` 10, `InverseIncompleteArgumentChecks` 11, `ZetaHugeExponent` 12,
  `ZetaNegativeQ` 13); `TestHegelMathext` itself fails every run and is mapped to gonum/9, the
  plurality of its shrunk basins (thirty-six of forty rounds at a hundred cases; gonum/11 the
  other four).
- Twenty-three narrow properties, one per `distuv` bug gonum/14 to 36, each a region generator
  with random contents judged exactly like `TestHegelDistuv` and failing every run
  (`LogisticLogProbIgnoresItsParameters` 14, `LogisticProbInTheFarTails` 15,
  `QuantileSkipsItsArgumentChecks` 16, `NoncentralTQuantileHitsItsBracketBound` 17 - kept
  where the library's own CDF fails to invert its Quantile -, `NoncentralTWithALargeMu` 18,
  `NoncentralTDensityWithALargeNu` 19, `NoncentralTCDFFarOut` 20, `NoncentralTWithATinyNu` 21,
  `QuantileTakesLogOfOneMinusP` 22, `BinomialLogProbTakesLogOfOneMinusP` 23,
  `NarrowTriangleFarFromZero` 24, `FCDFArgumentRoundsToOne` 25, `LogNormalBelowItsSupport` 26,
  `CumulativesOfANegativeArgument` 27, `DensitiesAtTheEdgeOfTheSupport` 28,
  `WeibullWithUnitShapeAtZero` 29, `SurvivalAsTheComplementOfTheCDF` 30, `ChiMomentsForALargeK`
  31, `StudentsTNearItsCentre` 32, `WeibullMomentsForALargeK` 33, `WeibullMomentsForATinyK` 34,
  `LogNormalMomentsForASmallSigma` 35, `PoissonDensitiesForALargeLambda` 36; the regions of 27,
  28 and 30 cover several distributions, the simplest first, and every region's edge was
  measured against the oracle - the comments quote the measurements). `TestHegelDistuv` itself
  fails every run and is mapped to gonum/28, the basin it shrinks to every time (forty of forty
  rounds at a hundred cases: Chi{1}.LogProb(0), the lowest table entry whose minimal parameters
  are a shape - Logistic{0, 1} is outside gonum/14's).
- Three narrow properties, one per `stat` bug, judged exactly like `TestHegelStat` and failing
  every run: `HarmonicMeanOfAnEmptyDataset` 37 (a draw-free region of twelve cases),
  `WeightedStdDevOfConstantData` 38 (constant data under sixteen weight lists of tenths whose
  sum makes the corrected two-pass variance negative, kept by `hegel.Filter` on the library's
  own NaN since 1, 2 and 4 are powers of two whose weighted mean is exact; the region past the
  shape alternates v and v(1 + 10⁻ᵉ)) and `WeightedEmpiricalQuantileAtOne` 39 (four to sixteen
  points under weights of 1 and m 10⁻¹⁷, m in 6..10, whose vector sum exceeds the sequential
  running sum: every instance panics, measured; p below 1 never does).
- `TestHegelPin…`: one per recorded bug, asserting the exact behaviour; expected failures.

## Bugs

Thirty-nine, recorded in `bugs.toml`. In `mathext`: Hypergeo is NaN, Inf, garbage or a panic
where 2F1 is defined (Gauss's theorem at z = 1, b = 0, z = 0 with a negative c, terminating
series before the pole of c) (gonum/1) and loses up to five digits for parameters of 10 or more,
a negative c or negative z (2); Lbeta and Beta lose everything when one argument is large
(Lbeta(1e20, 8.75) = 0) (3); GammaIncRegInv returns 0 or three times the answer where it is tiny
(4) and GammaIncRegCompInv loses digits as y → 1 (5); InvRegIncBeta is 1e-8 to completely wrong
within 1e-6 of the ends and for parameters beyond 1e4 (6); RegIncBeta loses 1% for a second
parameter below 1 and x near 1 (7); EllipticF and EllipticE are wrong beyond |φ| = π/2 (8);
Digamma is accurate to 3e-11 only (9) and loses seven digits next to its negative poles (10);
InvRegIncBeta and GammaIncReg skip their documented argument checks (11); Zeta is NaN for
x > 1e13 (12) and cancels or overflows for a negative q (13). In `distuv`: Logistic.LogProb
ignores Mu and S (14) and Prob is NaN or 0 in the tails (15); Logistic and NoncentralT Quantile
accept any p (16); NoncentralT.Quantile returns NaN or its bracket bound ±2^24 (17); the
NoncentralT CDF is wrong for |Mu| > 38 (18), loses digits in the tails and for a large Nu (19),
collapses for |x| > 3e7√Nu (20) and for a tiny Nu (21); Laplace, Exponential and Weibull Quantile
take log(1 − p) (22), Bernoulli and Binomial LogProb log(1 − P) (23); the Triangle moments and
CDF cancel (24); F.CDF and Quantile lose their incomplete-beta argument when it rounds to 1 (25);
LogNormal is NaN at or below 0 (26); ChiSquared, F and InverseGamma CDF panic for a negative x
and Chi.CDF mirrors it (27); Prob is NaN at the edge of the support in seven distributions
(0 log 0) (28); Weibull{K: 1}.Prob(0) = 1 whatever Lambda (29); Survival is 1 − CDF in seven
distributions (30); the Chi (31), Weibull (33, 34) and LogNormal (35) moments cancel or overflow;
StudentsT.CDF is exactly 0.5 near the centre and Quantile loses digits there for large Nu (32);
Poisson.Prob cancels for a large Lambda (36). In `stat`: HarmonicMean panics on empty data (37),
the weighted StdDev of constant data is NaN (38), Quantile(1, Empirical) panics when the running
weight sum rounds short (39).

## Modelled as recorded

The `mathext` bugs (1 to 13) are found: the property draws every recorded shape by default
(one time in five beside the plain arguments), judges it at the strict tolerance and fails
naming the bug ("the shape of gonum/N"), the classifier `mathShape` holding the shape
predicates - Hypergeo at z = 1 with c − a − b > 0 or a nonpositive integer c (1), a parameter of
10 or more, a negative c, z ≤ −0.9 or z ≥ 0.99 (2), Lbeta/Beta with an argument beyond 1e6 (3),
an inverse incomplete gamma answer below 1e-18 (4), GammaIncRegCompInv within 1e-6 of 1 (5),
InvRegIncBeta within 1e-6 of the ends or a parameter beyond 1e4 (6), RegIncBeta with b < 1
within 1e-3 of 1 (7), an elliptic amplitude beyond π/2 (8), any Digamma at 1e-13 (9), Digamma
within 1e-5|x| of a negative pole (10), the trivial-argument inverses asked to panic (11), Zeta
beyond x = 1e12 (12) and with q < 0 (13). `HEGEL_NO_KNOWN=1` switches the shapes off: the wide
generator stops drawing the regions, the narrow properties draw the region next to the shape,
a case the classifier still names is skipped (2.5 % of three thousand cases) or judged at the
old relaxed tolerance, and every property passes. The `distuv` bugs (14 to 36) are found the
same way since part 2: the classifiers `distShape` (from the parameters and argument) and
`distShapeOf` (from the oracle's answer) hold the old steering's predicates exactly - Logistic
LogProb (14) and Prob beyond |z| = 354 (15); Quantile(p ∉ [0, 1]) of Logistic and NoncentralT
(16); a NoncentralT quantile NaN or at its bracket bound 2^24 (17); NoncentralT with |Mu| > 38
(18), with Nu > 3000, the densities for |x| < 1e-8 Nu, below 1e-3 and the CDF below 1e-5, the
quantile within 1e-4 of the ends (19), the cumulatives for x² > 1e9 Nu and a quantile out there
(20), Nu < 1e-3 (21); Exponential and Weibull quantiles for p < 1e-6 and Laplace's within 1e-5
of the ends (22); Bernoulli/Binomial LogProb and Entropy for P < 1e-6 (23); Triangle moments
for |a| > 300 (b − a) and a CDF below 1e-6 (24); F cumulatives for d2/(d1 x) < 1e-12 and a
quantile through an argument within 1e-8 of 1 (25); LogNormal densities and cumulatives at
x ≤ 0 (26); a negative x or −0 to the cumulatives of ChiSquared, F, InverseGamma and Chi (27);
the densities at the support edges where 0 log 0 occurs (28); Weibull{K: 1}.Prob(0) (29); a
Survival below 1e-4 in Normal, LogNormal, GumbelRight, Logistic, Poisson, Binomial, Triangle,
and F (30; Uniform's survival is (Max − x)/(Max − Min), exact, and left the list in part 3 when
the oracle's own 1 − CDF was replaced by the exact tail); Chi moments beyond K = 1e5 (300 for the variance, 30 for the skewness, 5 for
the kurtosis) (31); StudentsT cumulatives within 1e-5 Sigma√Nu of Mu and the quantile for Nu >
1e6(2.5(p − 0.5))² (32); Weibull moments beyond K = 200 (50 for the skewness, 20 for the
kurtosis) (33) and for order/K > 170 (34); LogNormal moments for Sigma < 1e-3 (0.05 for the
kurtosis) (35); Poisson densities for λ > 1e5 (36) - and the distributions inherit the `mathext`
regions through their quantiles, cumulatives and entropies (an inverse gamma answer below
1e-18 (4), InverseGamma's quantile within 1e-6 of 1 (5), the inverse beta within 1e-6 of the
ends or beyond 1e4 (6), RegIncBeta's second parameter below 1 within 1e-3 of 1 (7), every
Entropy that sums digammas (9), judged at 1e-10 of the parameters' scale under
`HEGEL_NO_KNOWN=1` only). Under `HEGEL_NO_KNOWN=1` a case the classifiers still name is skipped
(5 % of `TestHegelDistuv`'s cases and 8 % of the Laws', mostly Logistic's LogProb and the
support edges) and every property passes. Between a CDF of 1e-6 and 1e-5 the NoncentralT CDF is
still 1e-7 off one time in five, so the old steering's 1e-6 became 1e-5 in part 2. The `stat`
bugs (37 to 39) are found the same way since part 3: the classifier `statShape` holds the old
steering's predicates - HarmonicMean of an empty dataset (37), a standard deviation of a
nonempty dataset whose weighted points have no spread to 1e-7 of their magnitude (38), Quantile
with weights and p within 1e-12 of 1 (39) - the property draws the shapes beside the plain
inputs by default and fails naming the bug, and under `HEGEL_NO_KNOWN=1` a case the classifier
still names is skipped (1.3 % of three thousand cases, mostly constant weighted data from the
pool draw; the NaN of 38 also arises unweighted, one time in fifty, and is named and skipped
there too) and every property passes. The `HZKnown` switches, the avoidance counter and
`ZOO_KNOWN_OFF` are gone with part 3.

## Not judged

Results in the denormal range (|want| < 1e-280, LogProb below −708); Zeta to 1e-16|x| extra (Go's
`math.Pow` by repeated squaring); InvRegIncBeta to 1e-8 within 1e-6 of the ends; moments of a
fractional order whose deviations are roundoff; RSquared, LinearRegression and the other
regressions to 1e-13 of their cancellation ratio (|α| + |β| max|x| + max|y|)/spread(y);
constant-data skewness and kurtosis (0/0); Kendall with ties (the model is τ-b, gonum's τ-a is
documented); the NoncentralT variance to 3e-15 lgamma(Nu/2) Mu² extra and its quantile root at 0 to 1e-13 of
the parameters (rounding noise); Mode of an empty or tied dataset (either value).

## Not tested

The multivariate distributions (`distmv`), `distmat`, sampling (`Rand`, `stat/sampleuv`), the
fitting methods (`Fit`) and `NumParameters`/`NumSuffStat`; `stat`'s `ROC`, `SortWeighted`,
`CovarianceMatrix` and the `combin`, `mds`, `spatial` and `card` subpackages; the `mat`,
`optimize`, `integrate`, `interp`, `graph`, `floats` and `dsp` packages: candidates for a
second part.

## History

- 2026-09-22: new target, seven properties, 39 bugs.
- 2026-10-08: part 1 of the rewrite in combinator style: the harness and `mathext` - package-level
  number records, the function table and argument records, the thirteen `mathext` shapes drawn by
  default and named by the property, thirteen narrow properties, the inverse-beta oracle solving
  for the complement; `distuv` and `stat` to follow.
- 2026-10-08: part 2 (the complement solve of part 1 recursed forever at the symmetric point
  a = b, y = 1/2; once only now), `distuv`: the table of specs and their package-level parameter generators,
  the twenty-three `distuv` shapes and the five inherited `mathext` shapes drawn by default and
  named by the classifiers, twelve narrow properties (gonum/14 to 25), the NoncentralT CDF
  shape widened from 1e-6 to 1e-5; the eleven remaining narrow properties and `stat` in part 3.
- 2026-10-08: part 3, the eleven narrow properties of gonum/26 to 36 (every region's edge
  measured, the survival tails and the moment regions tightened to where every instance reaches
  the bug; four oracle faults found by the probing and fixed: SciPy's LogNormal moments, its t
  CDF and quantile near the centre, its Triangle and Uniform survival, the Weibull moments'
  precision), `stat` in combinator style with its three switches turned around through a
  classifier, three narrow properties, and the harness without `HZKnown`, `ZOO_KNOWN_OFF` and
  the old draw helpers.
