# go/stats

[montanaflynn/stats](https://github.com/montanaflynn/stats) (v0.12.7): a statistics library
of about a hundred functions over `[]float64`, with no dependencies: descriptive statistics,
percentiles and quartiles, moments, correlations and distances, regressions, t- and z-tests,
moving windows, the normal distribution, and `LoadRawData` to convert mixed input. Many of
the newer functions document the NumPy, SciPy or pandas behaviour they match.

## Build

The patch adds `hegel.dev/go/hegel` to `go.mod` (and moves its `go` directive from 1.13, so
the module graph is pruned) and a `hegel/` package of test files that drive the public API:
`go test -count=1 -run TestHegel -v ./hegel`. `TestHegelSingle`, `TestHegelPair` and
`TestHegelNorm` need `python3` with `numpy` and `scipy` on PATH (the zoo's venv in CI).

## Oracles

NumPy and SciPy over a JSON-lines subprocess, floats travelling as their shortest round-trip
text: `np.percentile` (`linear` and `inverted_cdf`), `np.var`/`np.std` with the ddof each
function documents, `scipy.stats` for skewness, kurtosis, `sem`, `variation`, `zscore`,
`rankdata`, `gmean`/`hmean`, `entropy`, `percentileofscore(kind="mean")`, `trim_mean`,
`mstats.winsorize`, `spearmanr`, `kendalltau`, `ttest_1samp`/`ttest_ind`, `norm`;
`np.histogram`, `np.interp`, `np.polyfit` for the regressions (the exponential one weighted by
y, as the library and Excel do), `np.average` for the weighted mean, `scipy.spatial.distance`
for the distances; the quartiles as the library documents them (medians of the lower and upper
halves, the middle value excluded), the mode as every value of the greatest count (none when
all are unique or every distinct value has the same count, the library's convention), the
weighted percentile as the smallest value whose cumulative weight reaches the target, the
EWMA and the moving windows by their definitions. `math/big` for `Ncr`, a term-by-term sum
for `ProbGeom`. And the library against itself: permutation invariance of the order-based
functions, `Describe` against its parts, `Round` idempotent and within half a unit.

## Generator

Series of 1 to 200 values (mostly under 10) of one profile: small integers, tenths, quarters,
millions, 10^12 multiples, millionths, positive tenths, or magnitudes spread over twelve
decades; a third of the series drawn from a pool of one to three values, so ties and constant
series are common. Percents round and arbitrary, 0 and 100 included; windows, lags, trim
fractions, clip bounds, bin counts, EWMA factors. Pairs: an independent second series, a
noisy linear image of the first, or positive values for the exponential regression; weights
with zeros. Normal parameters: location 0, small or in the millions; scale 1, small or a power
of ten between 10^-6 and 10^6; standard scores to ±40, probabilities down to 1e-300 and up to
1 - 1e-16, moment orders to 30. Series holding NaN and infinities, with their permutations.
Typed slices, maps, mixed `[]interface{}`, whitespace-separated text and readers for
`LoadRawData`.

## Properties

- `TestHegelSingle`: sixty-odd one-series functions agree with the oracle (or return the
  documented error: `ErrZero` for a constant series in skewness, kurtosis and z-scores,
  `ErrEmptyInput` in `Quartile` for one value, `ErrBounds` for a window of one in
  `MovingStdDev`); `Describe` matches its parts; `Sample` and `StableSample` return the
  requested count of values of the series, in order for `StableSample`, or `ErrBounds`.
- `TestHegelPair`: covariances, correlations, distances, weighted mean and percentile, the
  three regressions' fitted values, t- and z-tests, `Interp`.
- `TestHegelNorm`: the normal distribution functions against `scipy.stats.norm` (density,
  distribution and survival functions and their logarithms into the far tails, quantiles,
  intervals, moments, entropy, fit), `Ncr`, the geometric distribution.
- `TestHegelLoad`: `LoadRawData` converts every element in order.
- `TestHegelSpecial`: NaN and infinities never panic; the order-based and arithmetic
  functions are permutation-invariant; a NaN in the data gives NaN or an error; `Round` and
  `Interp` follow their NaN documentation.
- `TestHegelPin…`: one pin per recorded bug (expected failures).

## Bugs

Thirteen, recorded in `bugs.toml`. `TTest`'s p-value is wrong for a small statistic, the
incomplete-beta continued fraction not converging near x = 1: t = 0.001 with one degree of
freedom gives p = 0.38 instead of 0.9994, t = 1e-6 gives 0.0004 (stats/3). A constant series
whose value is not the exact mean of its copies (ten 0.1s) gets a skewness of 1, a kurtosis
of -2, z-scores of -0.93 and an autocorrelation of 0.9 from rounding noise (2). `Percentile`
rejects percent 0 against its NumPy/Excel compatibility claim (1). `NormMoment` overflows its
int factorials from order 21 (4). `Sample` and `StableSample` panic on a negative count (5).
`LoadRawData` reads maps at the keys 0..len-1 (6) and drops sized numbers in a
`[]interface{}` and every `[]float32` (7). `ProbGeom` accepts probabilities outside [0, 1]
(8). `Min`/`Max` depend on the position of a NaN (9); the sort-based functions rank NaN below
every number, inconsistently with themselves (10). The sample statistics of one value are NaN
with no error (11). Two equal constant samples give a NaN t-test with no error where the
one-sample case gives t = 0, p = 1 (12). `PercentileWeighted` sums the weights in two orders
and, when the sums differ by an ulp, returns the largest value even with a weight of 0 (13).

## Modelled as recorded

Every bug reached by generated cases has an `HZKnown` switch. While a switch is on the
generator keeps away from the shape or the check is skipped: percent 0 not sent to
`Percentile`; constant series with an inexact mean skipped; the p-value not judged when
t² / (df + t²) < 3e-3; moment orders above 20 not drawn; no negative sample count; maps with
contiguous keys only and no sized numbers in mixed slices; `Min`/`Max` and the NaN
propagation of the order-based functions not judged when a NaN is present; the sample
statistics of one value not demanded to fail; probabilities in [0, 1] for `ProbGeom`; the
weighted percentile not judged when a cumulative weight is within rounding of the target. The
collector counts the avoidances; `ZOO_KNOWN_OFF=name,name` turns switches off and the
properties then fail. stats/12 is pinned only (SciPy gives NaN too).

## Not judged

`Percentile([1 2 Inf], 50)` is NaN (0 × Inf at an exact rank), as in NumPy; `Correlation`,
`Spearman` and `KendallTau` of a constant series return 0 where SciPy gives NaN (modelled as
the library's convention); a series varying only in its last bits (a linear image of a
constant series) is skipped, its statistics being rounding noise on both sides; `Round`'s tie
direction (half away from zero via `math.Round`, and the `x·10^p` artefacts); `Mode`'s
convention of no mode for a uniform distribution; `Entropy` of a zero or negative series;
`Minkowski` with λ < 1 (accepted by the library, rejected by SciPy); `NormInterval`'s upper
end, which the library keeps finite where SciPy's `(1+p)/2` rounds to 1; SciPy flushing the
subnormal tail of the density and survival functions to 0; `Sigmoid`'s comment promising a
range of -1 to 1 (it is (0, 1)); `Sample`'s randomness (global `math/rand` reseeded from the
clock).

## Not tested

`NormSample`, `NormPpfRvs`, `NormBoxMullerRvs` (random), `Description.String`, the legacy
aliases (`VarP`, `LinReg`, …, thin wrappers), `LoadRawData` with unparsable strings beyond
"dropped", the `Float64Data` methods (wrappers of the functions), `Ncr` beyond n = 40.

## History

- 2026-09-22: new target, five properties, 13 bugs.
