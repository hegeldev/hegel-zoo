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
below 1e-18), lgamma, digamma, the elliptic integrals, `hyp2f1`, Airy and the dilogarithm; the
Hurwitz zeta is an Euler–Maclaurin sum of the test's own (mpmath's `zeta(s, q)` loses digits for
large `s` and `q`). SciPy's `stats` gives the distributions, with mpmath taking over where SciPy
is known to fail: the Bernoulli and Binomial moments near P = 1, the Chi moments (a difference of
lgammas at 90 digits), the Pareto median, quantile, skewness and kurtosis, the Poisson pmf for
λ > 1e4, the Weibull log density, the LogNormal beyond |μ| = 300, and the noncentral t as a
validated quadrature of its definition for |μ| > 37 or wherever SciPy returns NaN or raises. NumPy
models `stat` from the documented formulas (weights dropped when they are 0 except in the
raw moments, which multiply 0 by an infinite power as gonum does).

## Generator

Numbers of ten magnitude profiles (small integers, quarters, three decimals, tiny 1e-3…1e-12,
large 10…1e9, huge to 1e100, binary fractions, near integers, integers) with a 40% sign;
probabilities with the ends, 1e-2…1e-15 and their complements. Shapes for the special functions
add half-integers and values near 1; distribution parameters are locations of moderate size,
scales, counts and probabilities, plus per-distribution edge points (support ends, the mode, the
mean, 1e20). Datasets of 0 to 40 values with weights that include zeros; the paired series for
the regressions share the x profile.

## Properties

- `TestHegelMathext`: 21 real functions of `mathext` (Beta, Lbeta, MvLgamma, Digamma, Zeta,
  the complete elliptic integrals K/E/B/D, EllipticF/E, EllipticRF/RD, GammaIncReg and its
  complement and both inverses, RegIncBeta and its inverse, Hypergeo, NormalQuantile) agree with
  mpmath to 1e-13 relative (1e-10 where recorded), or panic where documented.
- `TestHegelMathextComplex`: Li2, AiryAi and AiryAiDeriv of a complex argument to 1e-9.
- `TestHegelDistuv`: the 21 distributions' Prob, LogProb, CDF, Survival, Quantile, Mean, Median,
  Mode, Variance, StdDev, Skewness, ExKurtosis and Entropy agree with SciPy/mpmath to 1e-12
  relative (1e-9 for cumulatives and quantiles).
- `TestHegelDistuvOther`: the AlphaStable moments and the Categorical distribution.
- `TestHegelDistuvLaws`: a distribution against itself: CDF + Survival = 1 to 1e-10,
  Quantile(CDF(x)) = x wherever the density is positive, LogProb = log Prob, StdDev² = Variance,
  Mode inside the support, CDF monotone.
- `TestHegelStat`: 37 functions of `stat` (moments, means, correlation, covariance, Kendall,
  the entropies and divergences, histograms, quantiles and CDF, Kolmogorov–Smirnov, the linear
  regressions and R², Mode, StdErr, StdScore, Wasserstein) agree with the NumPy model to 1e-10
  of the data's magnitude.
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

Every bug has an `HZKnown` switch (39). While a switch is on the generator keeps away from the
shape or the check is relaxed: Hypergeo judged only for c > 0, −0.9 < z < 0.99 and parameters
below 10, and its NaN/panic inputs skipped; Lbeta/Beta judged to 1e-15 of their lgamma scale;
the inverse incomplete functions not judged where the answer is below 1e-18 (gamma) or within
1e-6 (1e-3 beyond parameter 1e4) of the ends (beta), and to 1e-7 for shapes beyond 1e4;
GammaIncRegCompInv to 1e-15/(a(1 − y)); RegIncBeta skipped for b < 1 within 1e-4 of 1; elliptic
amplitudes within π/2; Digamma to 1e-10 absolute and skipped within 1e-5|x| of a negative pole;
the trivial-argument inverses not asked to panic; Zeta skipped for x > 1e12 and q < 0; Logistic
LogProb not judged and Prob skipped beyond |z| = 354; Quantile(p ∉ [0, 1]) not asked of Logistic
and NoncentralT; NoncentralT judged for |Mu| ≤ 38, 1e-3 ≤ Nu ≤ 3000, x² ≤ 1e9 Nu, densities above
1e-3 and cumulatives above 1e-6 (variance to 3e-15 lgamma(Nu/2) Mu²); Exponential, Weibull and
Laplace quantiles for p ≥ 1e-6; Bernoulli/Binomial log(1 − P) to 1e-13 absolute; Triangle widths
above 1e-9|a| and CDF values above 1e-6; F cumulatives skipped when d2/(d1 x) < 1e-8; LogNormal
x ≤ 0 skipped; negative x not sent to ChiSquared, F, InverseGamma, Chi; support edges skipped
for Prob; Weibull{K: 1}.Prob(0) skipped; Survival not judged below 1e-4; Chi K ≤ 1e5 (moment
limits per method), Weibull K ≤ 170 (200 for the variance), LogNormal Sigma ≥ 1e-3 (0.05 for the
kurtosis); StudentsT cumulatives skipped within 1e-5 Sigma√Nu of Mu and Quantile for Nu >
1e6(2.5(p − 0.5))², and for Nu < 0.1; Poisson densities for λ ≤ 1e5; empty HarmonicMean,
constant weighted StdDev and Quantile(p ≥ 1 − 1e-12, Empirical, weighted) skipped. The collector
counts the avoidances; `ZOO_KNOWN_OFF=name,name` turns switches off and the properties then
fail.

## Not judged

Results in the denormal range (|want| < 1e-280, LogProb below −708); Zeta to 1e-16|x| extra (Go's
`math.Pow` by repeated squaring); InvRegIncBeta to 1e-8 within 1e-6 of the ends; moments of a
fractional order whose deviations are roundoff; RSquared, LinearRegression and the other
regressions to 1e-13 of their cancellation ratio (|α| + |β| max|x| + max|y|)/spread(y);
constant-data skewness and kurtosis (0/0); Kendall with ties (the model is τ-b, gonum's τ-a is
documented); Entropy to 1e-10 where it uses Digamma; NoncentralT beyond the bounds above (the
quadrature oracle is slow for a tiny Nu); Beta.Quantile and F.Quantile through InvRegIncBeta's
recorded limits; Mode of an empty or tied dataset (either value).

## Not tested

The multivariate distributions (`distmv`), `distmat`, sampling (`Rand`, `stat/sampleuv`), the
fitting methods (`Fit`) and `NumParameters`/`NumSuffStat`; `stat`'s `ROC`, `SortWeighted`,
`CovarianceMatrix` and the `combin`, `mds`, `spatial` and `card` subpackages; the `mat`,
`optimize`, `integrate`, `interp`, `graph`, `floats` and `dsp` packages: candidates for a
second part.

## History

- 2026-09-22: new target, seven properties, 39 bugs.
