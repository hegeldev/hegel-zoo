# apd

[cockroachdb/apd](https://github.com/cockroachdb/apd) is CockroachDB's arbitrary-precision
decimal package for Go (v3; 1.3k importing modules): `Decimal` (coefficient `BigInt` +
exponent), `Context` (precision, exponent range, rounding, traps) with `Add`, `Sub`, `Mul`,
`Quo`, `QuoInteger`, `Rem`, `Sqrt`, `Cbrt`, `Exp`, `Ln`, `Log10`, `Pow`, `Quantize`, `Reduce`,
`Round`, `RoundToIntegral{Exact,Value}`, `Floor`, `Ceil`, `Cmp`, condition flags, `ErrDecimal`,
and `BigInt`, an inline-small-value wrapper around `math/big.Int` with the same API. It
implements the General Decimal Arithmetic (GDA) specification and ships GDA's `.decTest`
suites plus 63 `testing/quick` properties comparing `BigInt` with `big.Int`. Tests in
`hegel_test.go`, external package `apd_test` (dot import).

## Oracles

- **Python's `decimal` module** — the reference implementation of the same specification —
  as a child process (`python3 -c`, JSON lines, one process per test binary), given the same
  precision, rounding mode, `Emin`/`Emax` and no traps; every `Context` operation is compared
  on the result's representation (form, sign, coefficient, exponent) and on the condition
  flags. Pinned representation divergences (apd/9, apd/10) make `Quo`, `Sqrt`, `Exp`, `Ln`,
  `Log10` and `Pow` compare by value; the transcendental functions are allowed 1 ulp, as in
  apd's own GDA harness. **Not compared:** the `Rounded` flag (apd's harness strips it too —
  apd raises it on exact zero results and misses it elsewhere), `Clamped` on zero results, the
  sign of a NaN result (apd/11), the `Inexact` flag of `Log10` (apd/10), zero exponents beyond
  the range (Python clamps them, apd does not), `Neg(0)` under `RoundFloor` (GDA's `-0`), and
  Python's `Clamped` on subnormal `power` results. apd prints small zeros as `0.000…` for
  PostgreSQL's sake, so strings are never compared directly.
- **math/big** for `BigInt`: apd's 63 `quick.CheckEqual` properties ported to one table of 48
  methods, widened to aliased receivers (`z == x`, `z == y`, `x == y`), mixed inline/heap sizes
  (up to 60 digits), `SetString` in every base on arbitrary strings, formatting verbs and the
  gob/JSON/text encoders.
- **Models**: `Text`/`Append`/`Format` against a renderer of the coefficient and exponent;
  `Float64` against `strconv.ParseFloat`, `Int64` against `big.Rat`, `SetFloat64` against the
  shortest float representation; `Modf`, `Reduce`, `Abs`/`Neg`/`Sign`/`IsZero`,
  `Compose(Decompose)`, `Scan`/`Value`, `MarshalText` round trips; `ErrDecimal` against the
  `Context` calls it wraps.

Properties (17 general): `TestHegelBigIntAgreesWithMathBig`, `TestHegelBigIntSetStringAgreesWithMathBig`,
`TestHegelNumDigitsCountsDigits`, `TestHegelArithmeticAgreesWithPythonDecimal` (Add, Sub, Mul,
Abs, Neg, Cmp, Round, Reduce, RoundToIntegral*, Floor, Ceil), `TestHegelDivisionAgreesWithPythonDecimal`
(Quo, QuoInteger, Rem), `TestHegelQuantizeAgreesWithPythonDecimal`, `TestHegelFunctionsAgreeWithPythonDecimal`
(Sqrt, Ln, Log10, Pow — Exp is pinned), `TestHegelExponentLimitsAgreeWithPythonDecimal` (small `Emax`/`Emin`),
`TestHegelZeroPrecisionIsExact` (Precision 0 = no rounding), `TestHegelSetStringAgreesWithPythonDecimal`,
`TestHegelCmpTotalAgreesWithPythonDecimal`, `TestHegelTextFormatsAgreeWithTheModel`,
`TestHegelConversionsAgreeWithStrconv`, `TestHegelSetFloat64RoundTrips`,
`TestHegelDecimalHelpersAgreeWithTheModel`, `TestHegelErrDecimalMatchesContext`,
`TestHegelBigIntEncodingRoundTrips`; 17 pinned expected failures below. All general properties
pass at 1000 cases × 3.

`[run] setup` checks `python3 -c 'import decimal'`; the test file passes `HEGEL_TEST_CASES`
through `hegel.WithTestCases` and wraps each property in a `recover` (the zoo's Go conventions,
see `HACKING.md`).

## Bugs (17)

- **apd/1** (wrong-result, high): `Quantize`/`RoundToIntegral*` of a value below one unit give
  `0` under every rounding mode — `Quantize(0.001, -2)` with `RoundUp` is `0.00`, not `0.01`.
- **apd/2** (wrong-result, medium): in the subnormal range `RoundCeiling`/`RoundFloor` treat
  negative numbers as positive.
- **apd/3** (wrong-result, medium): overflow is always `Infinity`; GDA gives the largest finite
  number under `RoundDown`, `Round05Up`, `RoundCeiling` (negative) and `RoundFloor` (positive).
- **apd/4** (wrong-result, medium): `Ceil`/`Floor` of `+Infinity` are `0`, of `NaN` are
  `Infinity`, `sNaN` raises nothing.
- **apd/5** (wrong-result, high): `Exp` is not correctly rounded — off by up to 40% at
  precision 1–3 (`Exp(20.5)` at precision 2 is `4.9E+8`, want `8.0E+8`), 1.5 ulp at precision 5.
- **apd/6** (wrong-result, medium): `Exp` over/underflows beyond about ±23 000 although the
  result is within range (`Exp(60000)` with `MaxExponent` 99999 is `Infinity`).
- **apd/7** (contract, medium): `QuoInteger` ignores `MaxExponent`.
- **apd/8** (wrong-result, medium): results with more digits than the precision — a quotient
  whose rounding carries (`Quo(9.6, 1)` at precision 1 is `10`), `Rem` by an infinity, and
  `Floor`/`Ceil`, which never round the integral part.
- **apd/9** (contract, low): exponents differ from GDA's ideal exponent (`4.6000E+11`, `Sqrt(1)`
  = `1.0`, `RoundToIntegralValue(1E+2)` = `100`, `Exp(1E-5)` = `1` at precision 4).
- **apd/10** (contract, low): `Log10` of an exact power of ten is flagged `Inexact` and padded.
- **apd/11** (contract, low): the NaN of an impossible integer division is signed.
- **apd/12** (contract, low): `Decimal.Reduce` drops the sign of `-0`.
- **apd/13** (contract, low): `Text('e')` writes `1e+5`, documented as `-d.dddde±dd`.
- **apd/14** (contract, low): `SetFloat64` holds the shortest representation, documented as the
  exact value.
- **apd/15** (wrong-result, high): `c.Floor(x, x)` of `-0.01` is `-0` (`c.Floor(&d, x)` is `-1`):
  the documented aliasing of result and operand loses the step when the integral part is zero.
- **apd/16** (wrong-result, low): `Reduce` strips zeros before rounding, so `Reduce(1001)` at
  precision 2 is `1.0E+3`.
- **apd/17** (wrong-result, medium): `Quantize` returns `NaN` whenever it discards digits and
  the result has more than `MaxExponent+1` digits, however small the result (`Quantize(1.2345,
  -3)` with `MaxExponent` 2 is `NaN`, not `1.235`): the intermediate rounding runs at exponent
  0 and trips the exponent check.

## Not bugs (and what the general generators avoid)

- Zeros with negative exponents print as `0.000…` (PostgreSQL compatibility, documented in
  apd's GDA harness) — compared by representation instead.
- apd rounds every `Context` result to the precision and clamps it to the exponent range,
  including `Floor`, `Ceil` and `RoundToIntegral*` (GDA leaves those unrounded and unchecked):
  the Python model rounds `floor`/`ceil` results to the precision, and integral operands
  beyond `MaxExponent` are left out.
- The `Rounded` flag, `Clamped` on zero results and the clamping of a zero's exponent beyond
  `Emax` are not compared (see Oracles); `Neg(0)` under `RoundFloor` is `0` (GDA: `-0`).
- `Pow`/`Exp` with results beyond apd's system limit of 10^±100000 return an error (documented);
  such cases, and results Python flags `Overflow` (apd/3) or `Subnormal` (apd/2), are left out
  of the general properties, as are: `Quantize`/`RoundToIntegral*` of values below one unit
  (apd/1), `Floor`/`Ceil` of special values (apd/4), `Exp` altogether (apd/5, /6), quotients whose rounding carries and `Rem` by infinity (apd/8), `Reduce` with an
  inexact result (apd/16), `Quantize` discarding digits when the result has more than
  `MaxExponent+1` digits (apd/17); `Floor`/`Ceil` run with a separate result (apd/15).
- `Compose(Decompose(sNaN))` is `NaN`: the decomposer's form byte has no signaling NaN.
- Upstream's own tests all pass at this commit.

## History

- 2026-09-14: written at 6d9c587326e7 (v3.2.3, 2026-03-23), hegel.dev/go/hegel v0.6.33.
