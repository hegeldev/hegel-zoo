# go/excelize

[xuri/excelize](https://github.com/xuri/excelize) (v2.11.0 plus 38 commits): a library for
reading and writing Office Open XML spreadsheets, with a formula calculator (`CalcCellValue`)
of some 530 functions written to Excel's documentation. This target tests the calculator on
its mathematical, statistical and probability functions, about 220 of them: a formula is
written to a cell of a fresh workbook, its range arguments to columns A, B, ..., and the
computed value compared with what Excel documents.

## Build

The patch adds `hegel.dev/go/hegel` to `go.mod` and a `hegel/` package of test files:
`go test -count=1 -run TestHegel -v ./hegel`. `TestHegelMath`, `TestHegelStat` and
`TestHegelDist` need `python3` with `numpy` and `scipy` on PATH (the zoo's venv in CI).

## Oracles

Python over a JSON-lines subprocess, floats travelling as their shortest round-trip text.
`math` for the elementary functions; `decimal` for Excel's decimal semantics of ROUND,
ROUNDUP, ROUNDDOWN, TRUNC, MROUND, CEILING, FLOOR and their `.MATH`/`.PRECISE` forms (Excel
rounds the 15-digit decimal, not the binary value); exact integers for FACT, COMBIN, PERMUT,
MULTINOMIAL, GCD, LCM, BASE and DECIMAL; ROMAN in its classic form and ARABIC. NumPy for the
descriptive statistics (`ddof` as each function documents, PERCENTILE.INC as `linear`,
PERCENTILE.EXC as `weibull` within [1/(n+1), n/(n+1)]), the sums of products, the regression
functions (`polyfit`), TRIMMEAN (floor(n·percent/2) values off each end); SciPy for the
moments, RANK, the t-, z-, F- and chi-squared tests (T.TEST's p as two-sided·tails/2, Z.TEST
as 1 − Φ, F.TEST two-tailed, CHISQ.TEST with n − 1 degrees of freedom for one row), the
confidence intervals, and every distribution (`norm`, `lognorm`, `t`, `chi2`, `f`, `beta`,
`gamma`, `expon`, `poisson`, `binom`, `nbinom`, `hypergeom`, `weibull_min`, `erf`, `erfc`,
`jv`/`yv`/`iv`/`kv`), with Excel's documented domain rules (arguments truncated to integers,
the errors #NUM!, #DIV/0!, #VALUE!, #N/A by function). A range is "constant" when its minimum
equals its maximum (the numpy standard deviation of eleven copies of -0.17 is not 0). The
library against itself: SUBTOTAL and AGGREGATE against the functions they number,
ARABIC(ROMAN(n, form)) = n for every form, DECIMAL(BASE(n, radix), radix) = n.

## Generator

Numbers of one profile: integers to 1000, decimals of one to three places, multiples of
10^3..10^12, fractions down to 10^-9, quarters, decimals starting with zeros, small integers;
negative 40% of the time.
Series of 1 to 12 values (13 to 60 a tenth of the time) of one profile: small integers, tenths,
0..100, thousandths, thousands; a third drawn from a pool of one to three values, so ties and
constant ranges are common; pairs independent or a noisy linear image. Probabilities in
(0, 1) with the ends, tiny values and 1 − 10^-6 included; degrees of freedom, counts and
shapes from 0 to about 30 with fractional and negative values, and a count of 200; num_digits
from -6 to 8 and fractional; every ROMAN form; radixes 2 to 36 and out of range; the Bessel
orders 0 to 30, arguments to 75. Results are compared at 15 significant digits (Excel's
precision and the calculator's formatting), tighter for the exact functions.

## Properties

- `TestHegelMath`: 70 functions of one to six numbers (rounding, elementary, trigonometric
  and hyperbolic, combinatorial, number-theoretic, BASE/DECIMAL, ROMAN/ARABIC, sums and
  products) agree with the oracle to 1e-12, or return the documented error; the two round
  trips.
- `TestHegelStat`: 80 functions over ranges (descriptive statistics, percentiles, quartiles,
  ranks, sums of products, regressions, correlations, tests and confidence intervals, and the
  `A` forms and legacy names) agree with the oracle to 1e-9, or return the documented error;
  SUBTOTAL and AGGREGATE agree with the function they number.
- `TestHegelDist`: 70 distribution functions (densities, cumulatives, inverses, legacy
  names, GAMMA, GAMMALN, PHI, GAUSS, the error and Bessel functions) agree with SciPy to
  1e-8 (1e-6 for the Bessel functions), or return the documented error.
- `TestHegelPin…`: one per recorded bug, asserting the Excel behaviour; expected failures.

## Bugs

Thirty-four, recorded in `bugs.toml`. Four crash or destroy the result outright: PERCENTILE.EXC
and QUARTILE.EXC panic with an index out of range for k outside (1/(n+1), n/(n+1)) (excelize/1);
SEC returns the cosine (2); HARMEAN of a range is always #N/A (3); AVEDEV takes a range as one
value (4). Several lose most digits: the inverse searches of CHISQ.INV.RT, CHIINV and GAMMA.INV
return their bound 5·mean (every df ≥ 30 gives 5·df), and BETA.INV's runs to 0 or 1 for shapes of
0.1 (13); cumulative GAMMA.DIST is a 33-term series that collapses beyond twice the mean
(GAMMA.DIST(75,15,1,TRUE) = 0.00035) (27); BESSELJ diverges from x = 50 and BESSELY is 1% off from
x = 10 (28); the one-pass variance in VAR, VARP, STDEVP and friends (STDEVP of nine 31.2s is 4e-7,
of 48 0.005s #NUM!) (22); NORM.S.INV is Acklam's approximation unrefined, 1e-9 (12); the T.INV
family converges to an absolute tolerance (26); the cumulative normal 0.5(1 + erf) flushes below z
≈ -8.3 (11). Wrong formulas: CORREL and the SUMX functions drop every pair containing a 0 (5);
COMBIN rounds its floating product up, COMBIN(20,18) = 191 (6); cumulative HYPGEOM.DIST sums
impossible outcomes and exceeds 1 (14); CEILING.MATH and FLOOR.MATH misread the mode and the sign
of significance, and FLOOR(0,-1) is #NUM! (9); the zero-variance checks compare sums of rounding
noise with 0 or test the covariance, and T.TEST type 2 of two constant ranges is 0 (24); ODD(0.5)
= 3 (7); a fractional num_digits is used as a power of ten (8); ROUNDDOWN, TRUNC, MROUND and the
FLOOR family round the binary quotient, ROUNDDOWN(0.0031,5) = 0.00309, FLOOR(5460.2,0.2) = 5460,
MROUND(0.15,0.1) = 0.1 (29); TRUNC returns the number itself when its fractional digits are small,
TRUNC(3.0318,1) = 3.0318 (33); PERCENTRANK's significance is decimal places, not significant
digits (20); DEGREES(0) is #DIV/0! and ATAN2(0,0) is 0 (31). Overflows: the discrete distributions
from 171 trials and the F.DIST and GAMMA.DIST densities from 342 degrees of freedom or from x = 20
at df1 = 200 (32), GAMMALN from 172 (30), COTH at 710 and FISHERINV at 355 (17); GAMMA rejects
negative arguments (16). Contract: infinite results come back as the text +INF/-INF instead of
#NUM! (10); integer arguments are not truncated (15); ROMAN, BASE, DECIMAL, COMBIN, PERMUT and
MULTINOMIAL accept out-of-range arguments (18, 19, 23); a dozen domain ends are the wrong way
round (25); error codes differ from the documented ones in some 20 functions (21); a negative zero
is formatted as -0 (34).

## Modelled as recorded

Every bug reached by generated cases has an `HZKnown` switch (33 of them; excelize/34 is pinned
only). While a switch is on the generator keeps away from the shape or the check is relaxed: k
outside the safe range not sent to PERCENTILE.EXC; SEC, HARMEAN and AVEDEV of a range not judged;
pairs containing a 0 skipped for CORREL and the SUMX functions; COMBIN and COMBINA judged to ±1;
ODD in (0, 1), fractional num_digits, num_digits beyond the binary resolution, a quotient by the
significance within rounding of an integer (or a half for MROUND), TRUNC's shortcut shape,
significance 0, FLOOR of 0 by a negative significance and the three-argument or negative forms of
CEILING.MATH/FLOOR.MATH avoided; an infinite result accepted for a documented #NUM!; results below
1e-8 not judged; NORM.S.INV judged to 1e-8 and NORM.INV to 1e-6; CHISQ.INV.RT, CHIINV and
GAMMA.INV not judged, nor BETA.INV with both shapes below 0.5; cumulative HYPGEOM.DIST only with a
support starting at 0; fractional integer arguments replaced; GAMMA of a negative number, COTH
beyond 710 or below 0.01, FISHERINV beyond 355 avoided; ROMAN, BASE and DECIMAL within Excel's
ranges; PERCENTRANK results below 0.1 not judged; a different error code accepted; negative counts
avoided; ill-conditioned ranges (|mean| > 1000·sd) skipped for the one-pass variances; constant
ranges skipped for the regressions, SKEW, KURT, Z.TEST and T.TEST, and a zero covariance for the
regressions; the wrong domain ends avoided; T.INV judged to 1e-7 within [1e-3, 100] and
CONFIDENCE.T to 1e-7 for alpha below 0.99; cumulative GAMMA.DIST only within 1.2 α and for α < 20;
BESSELJ within |x| ≤ 20 and BESSELY within x ≤ 5; GAMMALN below 170; DEGREES(0) and ATAN2(0,0)
avoided; counts and gamma arguments above 170 avoided. The collector counts the avoidances;
`ZOO_KNOWN_OFF=name,name` turns switches off and the properties then fail.

## Not judged

ACOT to 1e-9 and within |x| ≤ 10^5 only (the calculator's π/2 − atan(x) cancels for large
x; the oracle uses atan(1/x)); SUM, AVERAGE and SUMSQ to 1e-12 of their largest term (binary
sums cancel); BETA.DIST's density at a bound A or B (always 0 here, SciPy's limit or inf;
Excel's answer unknown); BINOM.INV when a cumulative probability ties with alpha within
rounding; paired T.TEST whose differences are constant within rounding
(#DIV/0! on both sides once the oracle allows an ulp); COMBINA with n < k (Excel's
documentation is unclear); MODE with tied counts (either value); MROUND with multiple 0; SECH
and CSCH beyond |x| = 700 and Bessel values SciPy overflows or underflows; LARGE and SMALL
with a fractional k; PERCENTRANK of one value; T.TEST with fractional tails or type;
CONFIDENCE.T to 1e-8, F.INV to 1e-7 and F.TEST to 1e-6 only; 1 − exp(−x) cumulatives to an
absolute 1e-15; the legacy BETADIST/BETAINV with bounds only when A < B.

## Not tested

The text, date and time, lookup, logical, information, financial and engineering functions,
the operators (`0^0` = 1 where POWER(0,0) is #NUM!), array formulas, cell references across
sheets, the cell-name helpers and the file format itself: a second part. Probes in passing
found UNICODE("é") = 195 (the first UTF-8 byte), UNICHAR(128512) #VALUE!, TIME(25,0,0) =
1.0417 (no wrap at 24 hours) and a lowercase `1e-7` literal parsed as a name (#NAME?, the
efp parser's).

## History

- 2026-09-22: new target, three properties, 34 bugs.
