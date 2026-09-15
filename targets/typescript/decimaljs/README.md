# decimal.js

[MikeMcl/decimal.js](https://github.com/MikeMcl/decimal.js) (npm `decimal.js`): an arbitrary
precision decimal type with configurable precision and nine rounding modes, correctly rounded
transcendental functions, radix strings and fractions. Pinned at 10.6.0 (b1d1e311, 2026-08-30).
The library is a single ES module with no dependencies and no build step; the tests are
`test/hegel.test.mjs` with the zoo's harness `test/hegel-zoo.mjs` and the oracle
`test/hegel-decimal-oracle.py`, next to upstream's own `test/` suite and its
`test/hypothesis/error_hunt.py` (a hypothesis + mpmath hunt for errors in the trigonometric and
hyperbolic functions at precision 14 — the project already uses property-based testing there).

## The oracle

Python's `decimal` module (libmpdec) computes add/sub/mul/div at any precision in any of the
seven IEEE rounding modes; decimal.js's ROUND_HALF_CEIL and ROUND_HALF_FLOOR are obtained from
ROUND_HALF_UP and ROUND_HALF_DOWN (they only differ on ties, and then the one in the direction
is taken). Square roots (also inside `hypot`) and cube roots are computed exactly with integer
roots plus a sticky digit, then rounded once; `sum` is an exact rational sum rounded once; modulo
(all ten `modulo` modes), `toNearest`, `toFraction`, the radix conversions and the constructor's
syntaxes are exact rational arithmetic with `fractions`. For exp, ln, log2, log10, log(x, base)
and pow the oracle computes at 30 guard digits (correctly rounded by libmpdec), rounds to the
target precision and refuses to decide (the case is skipped, about 1% of them) when the guard
digits sit on a rounding boundary while the result is inexact; exact results (`log2(256)`,
`pow(2, -1)`) are recognised by the Inexact flag staying clear. The oracle runs as one Python
child process over two FIFOs, one JSON line per request. Formatting (`toString`, `toFixed`,
`toExponential`, `toPrecision`, radix notation) is checked against models of the documented
rules written in the test.

## What is tested

Every case draws a fresh constructor (`Decimal.clone`) with precision 1–40 (small ones often),
rounding 0–8 and modulo 0–9. Values are decimal strings of 1–45 significant digits with ties and
trailing 0/9 digits favoured, exponents mostly within ±40 and sometimes ±1000, plus NaN,
±Infinity, ±0 and a few small constants.

- **TestHegelArithmeticMatchesPythonDecimal** — plus/minus/times/div/sqrt/cmp/abs/neg, the
  static forms, `Decimal.sum`, `Decimal.hypot`, `mod` (every `modulo` mode) and `divToInt`
  against the oracle, including the specials and the signs of zeros; operands are not mutated;
  results are instances of the constructor with at most `precision` digits.
- **TestHegelTranscendentalsAreCorrectlyRounded** — exp, ln, log (log10), log2, log(x, base),
  pow (integer exponents up to ±40 for any base, real exponents for positive bases), cbrt and
  sqrt are the correctly rounded values in the constructor's rounding mode.
- **TestHegelRoundingAndFormattingMatchTheModels** — with random `toExpNeg`/`toExpPos`:
  `toString`/`valueOf`/`toJSON` follow the notation rule, `toFixed()` is plain, the string
  round-trips; `dp`, `sd`, `sd(true)`, `isInt`, `sign`, `toNumber`; `toDP`/`toFixed(dp)`,
  `toSD`/`toPrecision`, `toExponential` (values from the oracle, formats from the models);
  `round`/`floor`/`ceil`/`trunc`; `toNearest(n, rm)`.
- **TestHegelConstructorRadixAndFractionsAreExact** — the constructor is exact for decimal text
  (signs, bare points, underscores, upper-case E), numbers, BigInts and binary/octal/hex text with
  fractions and `p` exponents; `toBinary`/`toOctal`/`toHex` with and without `sd` are the
  correctly rounded values (read back exactly with BigInt) in the documented notation;
  `toFraction()` is the exact lowest-terms fraction and `toFraction(maxD)` is at least as close
  as Python's `limit_denominator`.
- **TestHegelExponentLimitsRandomAndMinMaxClamp** — construction and multiplication clamp to
  `minE`/`maxE` (±Infinity above, ±0 below); `max`/`min`/`clamp` are consistent with `cmp`;
  `random(dp)` (with and without `crypto`) is in [0, 1) with at most dp places.

Not covered: the trigonometric and hyperbolic functions (no exact oracle here; upstream's own
hypothesis hunt covers them), `Decimal.set` validation beyond what the properties exercise, and
`toSignificantDigits`/`toDecimalPlaces` above 40 digits. decimal.js has no subnormals (values
below `minE` are zero) and always overflows to Infinity, so the properties keep exponents inside
the oracle's ranges.

## Bugs

Six, all recorded in `bugs.toml` with a pin each:

- **decimaljs/1** (low) — `toNearest` with a negative n rounds the quotient, so ROUND_FLOOR
  rounds up (`9.499.toNearest(-0.5, ROUND_FLOOR)` is 9.5), and CEIL/HALF_CEIL/HALF_FLOOR flip too.
- **decimaljs/2** (high) — `toFraction` never returns when the rounding mode is ROUND_FLOOR:
  the exact remainder becomes -0 and the next quotient -Infinity/NaN, so the loop's exit test
  never holds.
- **decimaljs/3** (high) — `Decimal.sum('1e40', 1, '-1e40')` is 1e7 at the default precision:
  the unrounded intermediate additions collapse and misplace an addend more than about
  precision + 7 digits below the total.
- **decimaljs/4** (low) — `Decimal.random(0)` throws although the docs allow dp = 0.
- **decimaljs/5** (low) — `new Decimal(-6).mod(3)` is +0; the docs promise the dividend's sign
  (JavaScript's `%` gives -0).
- **decimaljs/6** (medium) — radix strings with a binary exponent are parsed inexactly
  (`new Decimal('0o1p+104')` has 20 digits, 2^-27 loses its last digits), whatever the
  precision, so `toBinary(sd)`/`toOctal(sd)`/`toHex(sd)` output does not read back.
