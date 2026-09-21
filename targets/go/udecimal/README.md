# go/udecimal

[quagmt/udecimal](https://github.com/quagmt/udecimal) is a fixed-point decimal type for Go
with up to 19 fraction digits: the coefficient is a 128-bit unsigned integer that falls back
to a `big.Int` when it overflows, so most operations allocate nothing. It offers the
arithmetic (Add, Sub, Mul, Div, QuoRem, Mod, the uint64 variants), four rounding methods plus
Trunc/Floor/Ceil, integer powers and Sqrt, parsing and printing, and JSON, text, binary and
SQL codecs. Pinned at `c9f302d` (v1.10.1, 2026-06-12, BSD-3-Clause; no CONTRIBUTING file and
no AI policy).

## Build

The tests live in a new package directory `hegel/` of the upstream module and import the
library as a black box; `go.mod` gains `hegel.dev/go/hegel`. The run command is
`go test -count=1 -run TestHegel -v ./hegel`. The oracle is `math/big`, so nothing outside
the Go toolchain is needed.

## Oracle

Every generated decimal carries its exact value as a `big.Rat`. The documented rules are
applied to the exact result: Add and Sub are exact; Mul, Div, Div64, the powers and Sqrt are
truncated toward zero to 19 fraction digits; QuoRem is C's fmod (an integer quotient toward
zero, a remainder with the dividend's sign); the rounding methods are half-to-even, half away
from zero, half toward zero, away from zero and truncation at the asked precision, Floor and
Ceil at zero. Generated coefficients cover the three representations (uint64, 128-bit, big)
and sit on and beside the word and power-of-ten boundaries (2^63, 2^64, 10^19, 2^128, 10^38,
10^39); precisions favour 0 and 19; values are built either by `Parse` of their plain text
or by `NewFromHiLo`, so the two constructors are checked against each other too.

## Properties

- `TestHegelText`: `String` prints the canonical text; `Parse` reads it and its variants (a
  `+`, leading zeros, trailing fraction zeros, padding to the 200-character limit), rejects
  malformed text, more than 19 fraction digits and longer strings with the documented
  errors; `StringFixed`; `ToHiLo`; the sign predicates, `Neg`, `Abs`; `Int64` and
  `InexactFloat64`.
- `TestHegelConstructors`: `NewFromInt64`/`NewFromUint64`/`NewFromHiLo` and the `Must`
  variants, precision range errors, `NewFromFloat64` through the shortest float text, `Scan`
  from every documented source type, `Value`, `EncodeValues`, `NullDecimal`.
- `TestHegelArithmetic`: Add, Sub, Mul, Div, QuoRem, Mod, the uint64 variants and the `Must`
  variants against the exact model; division by zero; a value held as a `big.Int` compares
  equal to the same value held in 128 bits; Cmp and the predicates, Max, Min.
- `TestHegelRounding`: the five rounding methods at every precision (including above 19,
  a no-op) against the exact rules; Floor and Ceil; idempotence; symmetry under negation.
- `TestHegelPow`: `PowInt32`, `PowToIntPart` (with a fractional exponent and the
  too-large error), the deprecated `PowInt`, and `Sqrt`, against exact powers and roots
  truncated to 19 digits, with the documented zero cases.
- `TestHegelCodec`: JSON (quoted out, quoted or bare or null in), text and binary round
  trips; the documented binary layout; corrupt binary data (prefixes, a wrong length byte,
  random bytes) rejected without a panic.

## Bugs

Five recorded (bugs.toml), each with a pin: the constructors do not trim trailing zeros as
documented; `Int64` rejects `math.MinInt64`; `PowToIntPart` of zero with an exponent in
(-1, 0) errors instead of returning 1; the MarshalBinary doc example has the flag byte
wrong; and `PowInt32(math.MinInt32)` / `PowInt(math.MinInt)` negate the exponent in its own
width, returning 1 for bases of magnitude 2 or more and panicking for smaller ones.

## Modelled as recorded, not counted

- `StringFixed(p)` trims trailing zeros of the coefficient down to p fraction digits, not
  below; the comment's "Trailing zeros will not be removed" describes the padding case.
- `Div` and `Div64` return results at precision 19 (or the operand's, on the 128-bit path):
  the precision of a quotient is not documented, so only values are compared.
- `UnmarshalJSON` accepts bare numbers and leaves the value unchanged on `null`.
- `SetDefaultPrecision` and `SetDefaultParseMode` are package globals and are not exercised
  (the properties run concurrently).
- Powers with exponents of astronomical magnitude (`0.5.PowInt32(2^31 - 1)`) are not
  attempted: the exact result has 6e8 digits.
