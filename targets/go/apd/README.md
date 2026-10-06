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
  on the result's exact representation (form, sign, coefficient, exponent, the sign of a NaN
  included) and on the condition flags; the transcendental functions are allowed 1 ulp, as in
  apd's own GDA harness. **Not compared:** the `Rounded` flag (apd's harness strips it too —
  apd raises it on exact zero results and misses it elsewhere), `Clamped` on zero results, the
  `Inexact` flag of `Log10` (apd/10), zero exponents beyond the range (Python clamps them, apd
  does not), `Neg(0)` under `RoundFloor` (GDA's `-0`), and Python's `Clamped` on subnormal
  `power` results. apd prints small zeros as `0.000…` for
  PostgreSQL's sake, so strings are never compared directly.
- **math/big** for `BigInt`: apd's 63 `quick.CheckEqual` properties ported to one table of 48
  methods, widened to aliased receivers (`z == x`, `z == y`, `x == y`), mixed inline/heap sizes
  (up to 60 digits), `SetString` in every base on arbitrary strings, formatting verbs and the
  gob/JSON/text encoders.
- **Models**: `Text`/`Append`/`Format` against a renderer of the coefficient and exponent;
  `Float64` against `strconv.ParseFloat`, `Int64` against `big.Rat`, `SetFloat64` against the
  exact value of the float (`big.Rat`); `Modf`, `Reduce`, `Abs`/`Neg`/`Sign`/`IsZero`,
  `Compose(Decompose)`, `Scan`/`Value`, `MarshalText` round trips; `ErrDecimal` against the
  `Context` calls it wraps.

Properties (17 general): `TestHegelBigIntAgreesWithMathBig`, `TestHegelBigIntSetStringAgreesWithMathBig`,
`TestHegelNumDigitsCountsDigits`, `TestHegelArithmeticAgreesWithPythonDecimal` (Add, Sub, Mul,
Abs, Neg, Cmp, Round, Reduce, RoundToIntegral*, Floor, Ceil), `TestHegelDivisionAgreesWithPythonDecimal`
(Quo, QuoInteger, Rem), `TestHegelQuantizeAgreesWithPythonDecimal`, `TestHegelFunctionsAgreeWithPythonDecimal`
(Sqrt, Exp, Ln, Log10, Pow), `TestHegelExponentLimitsAgreeWithPythonDecimal` (small `Emax`/`Emin`),
`TestHegelZeroPrecisionIsExact` (Precision 0 = no rounding), `TestHegelSetStringAgreesWithPythonDecimal`,
`TestHegelCmpTotalAgreesWithPythonDecimal`, `TestHegelTextFormatsAgreeWithTheModel`,
`TestHegelConversionsAgreeWithStrconv`, `TestHegelSetFloat64RoundTrips`,
`TestHegelDecimalHelpersAgreeWithTheModel`, `TestHegelErrDecimalMatchesContext`,
`TestHegelBigIntEncodingRoundTrips`. Drawn by default (STYLE.md rule 11, the whole target since
2026-10-06): the wide properties draw the shapes of all twenty recorded bugs, compare by exact
representation, and fail naming the bug whose shape the case has ("the shape of apd/N"), so nine of
them are expected failures mapped to the bug they most often shrink to — Arithmetic → apd/3 (also /4
at 1000 cases; it draws /1, /2, /8, /9, /15, /16, /19 too), Text → /13, SetFloat64 → /14, DecimalHelpers
→ /12 every run; Quantize → /1, ExponentLimits → /3, SetString → /3, Division → /3 (also /2, /7, /8, /9,
/11, /20), Functions → /9 (also /3, /5, /6, /10) in most 100-case runs (shape rates 2–7 %) and every
1000-case run, mapped intermittent. A shared fail helper is one shrink group, so the shrink goes to
the smallest shape the run hit (apd/3 at precision 1 mostly), not the most frequent. Beside them one
narrow property per bug (`TestHegelQuantizeRoundsTinyValuesInTheRoundingDirection` … `TestHegelSubnormalQuotientsFlagInexactAndUnderflow`),
each over its shape alone and failing every run, and the pins of apd/18, /19 and /20.
`TestHegelErrDecimalMatchesContext` probes the `Ln` step in a child process with a one-second deadline
when the context and operand are in apd/18's shape and is mapped to it as intermittent (about one
case in ten thousand; found by the weekly 1000-case run of 2026-10-05, where the hang ran into
`go test`'s ten-minute timeout). `HEGEL_NO_KNOWN=1` (read once; one `Known` switch per bug) leaves
the shapes out: the generators are shaped off them (operands and products within the exponent
range, Floor/Ceil operands truncated to the precision and without specials, Exp left out at
precision 1–3, impossible integer divisions unsigned, Quantize targets capped), the sub-checks that
meet them follow the library (the text model's exponent digits, SetFloat64's shortest value, the
sign of a reduced zero, the Ln step), and a mismatch that still has a recorded shape is skipped
(assume; 0–1.7 % of cases per property). `APD_COLLECT=1` records mismatches instead of failing and
prints a histogram of the shapes per property.

`[run] setup` checks `python3 -c 'import decimal'`; the test file passes `HEGEL_TEST_CASES`
through `hegel.WithTestCases` and wraps each property in a `recover` (the zoo's Go conventions,
see `HACKING.md`).

## Bugs (20)

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
  `Floor`/`Ceil`, which never round the integral part (nor check its exponent: apd/19).
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

- **apd/18** (abort, high): `Context.Ln` never returns when a trap fires inside its power-series
  branch (|x-1| <= 0.1, or a range-reduced operand with leading digit 9): `Ln(0.95)` at precision
  10 with `MinExponent` -5 and `DefaultTraps` spins for ever (Python: -0.05129329439). The
  `ErrDecimal` makes the later steps no-ops once Subnormal/Underflow/Inexact fires, but the exit
  test keeps reading a term that is never divided again.
- **apd/19** (wrong-result, medium): `Floor`/`Ceil` of an integral operand beyond `MaxExponent`
  return it unchanged with no `Overflow` (`Ceil(-74E25)` with `MaxExponent` 6 is `-7.4E+26`),
  where the same call on a value with a fractional part overflows: the integral part bypasses
  the context unless a step is added. Found 2026-10-06 by the unsteered Arithmetic property.
- **apd/20** (wrong-result, medium): `Quo` loses `Inexact` and `Underflow` for a subnormal
  quotient with a nonzero remainder whose digits at the precision end in zeros
  (`Quo(0.0201, 1)` at precision 2, `MinExponent` -1 is `0.02` with `Subnormal` and `Rounded`
  only): `Quo` skips its own rounding below `MinExponent` and the rounding to Etiny raises
  `Inexact` only for nonzero dropped digits. Found 2026-10-06 by the Division property under
  `HEGEL_NO_KNOWN=1`.

## Not bugs (oracle tolerances)

- Zeros with negative exponents print as `0.000…` (PostgreSQL compatibility, documented in
  apd's GDA harness) — compared by representation instead.
- apd rounds every `Context` result to the precision and clamps it to the exponent range,
  including `RoundToIntegral*` (GDA's to-integral leaves the operand unrounded and unchecked):
  `RoundToIntegral*` of a value with a fraction beyond `MaxExponent` is left out (an integral
  one is apd/9's shape, and `Floor`/`Ceil` beyond the range are apd/19's).
- The `Rounded` flag, `Clamped` on zero results and the clamping of a zero's exponent beyond
  `Emax` are not compared (see Oracles); `Neg(0)` under `RoundFloor` is `0` (GDA: `-0`);
  Python's `Clamped` on a subnormal `power` result is not compared.
- `Pow`/`Exp` with results beyond apd's system limit of 10^±100000 return an error (documented)
  where Python overflows or underflows within its range: left out.
- `Compose(Decompose(sNaN))` is `NaN`: the decomposer's form byte has no signaling NaN.
- Upstream's own tests all pass at this commit.

## History

- 2026-09-14: written at 6d9c587326e7 (v3.2.3, 2026-03-23), hegel.dev/go/hegel v0.6.33.
- 2026-10-06: apd/18 (`Ln` spinning when a trap fires in its series) found by the weekly run's 1000-case budget; the wide property probes `Ln` in a child process and is mapped intermittent, narrow property and pin added, `HEGEL_NO_KNOWN=1` gate.
- 2026-10-06: unsteered (STYLE.md rule 11): the wide properties draw every recorded shape and fail naming it, one `Known` switch per bug off by default; apd/19 and apd/20 found on the way.
