# decimal

[shopspring/decimal](https://github.com/shopspring/decimal) is the most used arbitrary-precision
fixed-point decimal for Go (7.5k stars, 38k importing modules): an immutable `Decimal` of
`big.Int` coefficient and int32 exponent with constructors from ints, floats, strings and
`big.Rat`; `Add`/`Sub`/`Mul`/`Div`/`DivRound`/`QuoRem`/`Mod`/`Shift`; the rounding family
(`Round`, `RoundBank`, `RoundCeil`/`Floor`/`Up`/`Down`, `RoundCash`, `Truncate`, `Floor`,
`Ceil`); `Pow`/`PowWithPrecision`/`PowInt32`/`PowBigInt`, `ExpTaylor`, `ExpHullAbrham`, `Ln`,
`Sin`/`Cos`/`Tan`/`Atan`; `String`/`StringFixed*`/`ScientificNotationString`; JSON, text, binary,
gob, `sql` and Spanner encodings and `NullDecimal`. Upstream has two `testing/quick`
properties (`NewFromFloat`/`NewFromFloat32` against `strconv`, ported). Tests in
`hegel_test.go`, external package `decimal_test` (dot import).

## Oracles

- **`math/big.Rat`** for everything exact: a `Decimal`'s value is `Coefficient() × 10^Exponent()`,
  and every constructor, arithmetic operation, comparison, `QuoRem` contract (identity, quotient
  scale, remainder bounds and sign), `DivRound`/`Div`/`Mod`/`Avg`, rounding mode (`Round` halves
  away from zero, `RoundBank` half-even, the directed modes, `RoundCash` on 5/10/25/50/100 cent
  intervals, `Truncate`, `Floor`, `Ceil`), integer power (exact, or the reciprocal rounded to
  `PowPrecisionNegativeExponent` places) and `NewFromFloatWithExponent` (the exact float rounded
  half away from zero) is checked against the rational model; formatting is checked against a
  renderer of coefficient and exponent under both `TrimTrailingZeros` and `UseScientificNotation`,
  `StringFixed*` against the rounded value printed with exactly that many places.
- **Python's `decimal` module at 200 digits** (child process, JSON lines) for `ExpTaylor` (within
  2 units of the requested places — e²³⁰ is 1.6 units off), `ExpHullAbrham` (within 1 ulp of the
  requested significant digits), `Ln` (1 unit) and `PowWithPrecision` (1 unit, positive exponents,
  results between 10⁻⁶ and 10⁶); `Pow` with a fractional exponent only to a relative 10⁻⁶
  (decimal/3).
- **`math`** for `Sin`/`Cos`/`Tan`/`Atan` up to |x| ≤ 100 (10⁻¹² absolute; `Tan` away from its
  poles), plus odd/even symmetry and sin² + cos² = 1 in the decimal domain.
- **`strconv`** for `NewFromFloat`/`NewFromFloat32` (the shortest round-tripping decimal);
  `big.Rat.Float64` for `Float64`.
- **The grammar** `[+-]? digits [. digits] [e [+-] digits]` (at least one mantissa digit, the
  exponent within int32 and the final exponent too) as the model of `NewFromString`,
  `RequireFromString`, `NewFromFormattedString`, `UnmarshalJSON` and `UnmarshalText`, on
  well-formed strings with mutations and on random pieces (`+`, `.`, `e`, `_`, `٣`, spaces…).

Properties (12 general): `TestHegelConstructorsAgreeWithTheModel`, `TestHegelArithmeticAgreesWithBigRat`,
`TestHegelDivisionAgreesWithBigRat`, `TestHegelRoundingAgreesWithTheModel`, `TestHegelStringsAgreeWithTheModel`,
`TestHegelEncodingsRoundTrip`, `TestHegelNewFromStringAgreesWithTheGrammar`,
`TestHegelFloatConversionsAgreeWithStrconv`, `TestHegelIntegerPowersAreExact`,
`TestHegelExpAndLnAgreeWithPythonDecimal`, `TestHegelFractionalPowersAgreeWithPythonDecimal`,
`TestHegelTrigAgreesWithMath`; 10 pinned expected failures below. All general properties pass at
1000 cases × 3.

`[run] setup` checks `python3 -c 'import decimal'`; the test file passes `HEGEL_TEST_CASES`
through `hegel.WithTestCases` and wraps each property in a `recover` (the zoo's Go conventions,
see `HACKING.md`). Package-level switches (`DivisionPrecision`, `TrimTrailingZeros`,
`UseScientificNotation`, `MarshalJSONWithoutQuotes`) are set per test case and restored.

## Bugs (10)

- **decimal/1** (wrong-result, high): `ExpHullAbrham` of a small argument returns `10^exponent(d)`
  instead of 1 — `NewFromString("0.001").ExpHullAbrham(2)` is `0.001`.
- **decimal/2** (wrong-result, medium): `ExpHullAbrham` rounds results below one to *decimal
  places* instead of significant digits — `NewFromInt(-50).ExpHullAbrham(10)` is `0`.
- **decimal/3** (wrong-result, medium): `Pow` with a fractional exponent carries only about
  `NumDigits(base)+6` significant digits — `Pow(16, 0.5)` is `3.99999999`, `Pow(2, 0.5)` is
  `1.4142136`; the doc comment's own `5^5.73` example is wrong from the ninth digit.
- **decimal/4** (wrong-result, medium): `PowWithPrecision` misses its documented precision once the
  integer-part power is large — `2^60.5` at precision 0 is off by 5.7·10³, `1000^100.5` by 10²⁸⁶.
- **decimal/5** (wrong-result, medium): `Sin`/`Cos`/`Tan` of large arguments are unbounded —
  `Sin(1E17)` is −2102.65, `Sin(1E20)` has 250 integer digits (`float64(j)` loses the octant).
- **decimal/6** (wrong-result, low): `PowInt32(math.MinInt32)` is 1 for every base (`abs` overflow).
- **decimal/7** (contract, low): `IntPart` wraps silently beyond int64 (`1E19` → −8446744073709551616).
- **decimal/8** (contract, low): `Shift` wraps the exponent silently where `Mul` panics on the
  same overflow.
- **decimal/9** (crash, medium): `PowInt32`/`PowBigInt` of zero with a negative exponent panic
  ("decimal division by 0"); the doc promises an error only for 0⁰.
- **decimal/10** (wrong-result, medium): `PowWithPrecision` with a negative non-integer exponent
  rounds the integer-part reciprocal to the requested places first —
  `0.03^-1.4` at precision 0 is 134.17, the true value 135.53.

## Not bugs (and what the general generators avoid)

- `ExpTaylor` is within 2 units of the requested places rather than 1 for large arguments
  (e²³⁰ is 1.6 units off at 2 and 5 places): the property allows 2 units and stays below |x| ≤ 100
  (beyond a few thousand the Taylor series needs tens of thousands of terms and minutes).
- The trigonometric functions carry float64-level coefficients (ported from the Go runtime), so a
  50-digit π/2 gives `Tan` = −1.4·10¹⁶: no precision is documented, the property compares with
  `math` to 10⁻¹² below |x| ≤ 100 and the unbounded results above 10¹⁶ are decimal/5.
- `NewFromFloatWithExponent(0.5, -5)` has exponent −1, not −5: it never keeps more digits than the
  exact float needs (the value is still the model's).
- `BigFloat()` goes through a 64-bit-mantissa `big.Float` and loses digits — documented.
- The value of `String()` is always exact; the *representation* survives a round trip only when
  no trailing zeros were trimmed (`TrimTrailingZeros = false`) and positive exponents are printed
  in scientific notation; zero prints as `0` whatever its exponent.
- `UnmarshalJSON` of `""` (an empty quoted string) is an error, `null` leaves the value alone.
- `QuoRem`/`Mod` remainders take the dividend's sign (documented), `Div` by zero panics (documented).
- Generators avoid each pinned shape: arguments below `9·10^-(p+1)` and negative ones for
  `ExpHullAbrham` (decimal/1, /2), `PowWithPrecision` with results above 10⁶ or negative exponents
  (decimal/4, /10), trigonometry above |x| = 100 (decimal/5), `PowInt32`/`PowBigInt` of zero with
  a negative exponent (decimal/9), `IntPart` beyond int64 (decimal/7), `Shift` beyond int32
  (decimal/8); `Pow` with fractional exponents is compared loosely (decimal/3).
- Upstream's own tests all pass at this commit.

## History

- 2026-09-14: written at ca4740823783 (after v1.4.0, 2026-08-19), hegel.dev/go/hegel v0.6.33.
