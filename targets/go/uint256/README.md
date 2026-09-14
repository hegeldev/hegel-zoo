# uint256

[holiman/uint256](https://github.com/holiman/uint256) is the fixed-size 256-bit integer library
used by go-ethereum and erigon: `type Int [4]uint64` with EVM-style arithmetic (wrapping
add/sub/mul, division by zero giving zero, signed operations on two's complement values,
`AddMod`/`MulMod`/`Exp`/`ExtendSign`/`Byte`/`SRsh`), conversions to and from `math/big`,
bytes, hex, decimal, `fmt`, JSON, text, SSZ, RLP and `database/sql`. Pinned at 3b6e9cd
(v1.3.2+, 2026-08-23), BSD-3-Clause, no AI policy.

## Oracle

`math/big`, in-process: every operation is compared with the exact big.Int result reduced
modulo 2^256 (two's complement for the signed operations, truncated division and
dividend-signed remainder as the EVM defines them, `Exp` as `big.Int.Exp(x, y, 2^256)`), and
every encoding with big.Int's own bytes/text/`fmt` output or a few-line model (RLP, SSZ,
thousands separators). Upstream already differential-tests the arithmetic against big.Int
(10 000 random binary operations per run, fuzz functions for binary/ternary/unary operations,
decimal, `Float64` and `Log10` — the fuzz functions have no seed corpus, so `go test` runs them
on nothing); the zoo adds Hegel's shrinking and shaped generators, the encodings, the parsers,
and the aliasing forms upstream does not cover.

Generated values cover the shapes that matter for a four-word integer: 0, 1, small, one word,
four random words, 2^k and its neighbours for every k, 2^256 - small, two's complement
negatives of small numbers, 2^255 ± small, single non-zero words, byte strings of any length,
and values with a non-zero top word (the fast paths of `AddMod`/`MulMod`).

## Properties

- `TestHegelBinaryOperationsMatchBigInt` — Add, Sub, Mul, Div, Mod, SDiv, SMod, And, Or, Xor,
  Exp, ExtendSign, DivMod and their `I*` in-place forms agree with big.Int, leave their
  operands alone and work with the result aliasing either or both operands; AddOverflow,
  SubOverflow, MulOverflow flags match the exact result; Add/SubUint64; Lsh/Rsh/SRsh for shift
  amounts 0–512.
- `TestHegelModularOperationsMatchBigInt` — AddMod, MulMod, MulModWithReciprocal (with the
  reciprocal of the same modulus), MulDivOverflow, MulDivOverflowRem and DivMod, including
  operands already reduced modulo m and every supported aliasing form.
- `TestHegelUnaryOperationsAndComparisonsMatchBigInt` — Not, Neg, Abs, Sign, Sqrt, Log10,
  BitLen, ByteLen, Byte(n) for any n, ReverseBytes, the uint64 views and Cmp/Eq/Lt/Gt/Slt/Sgt/
  CmpUint64/LtUint64/GtUint64/CmpBig (against negative and over-wide big.Ints).
- `TestHegelEncodingsRoundTripAndMatchBigInt` — Bytes/Bytes32/Bytes20/WriteToArray*/
  WriteToSlice/PutUint256/PaddedBytes/SetBytes/SetBytes1–32, Hex/Dec/PrettyDec/String, `fmt`
  with every verb, flag, width and precision against big.Int's Formatter, MarshalText/JSON and
  their decoders (quoted decimal, quoted hex, bare number, struct/slice/pointer fields),
  Value/Scan (including scientific notation `<mantissa>e<exp>` and nil), SSZ (Marshal, Append,
  Into, Unmarshal, HashTreeRoot, SizeSSZ), EncodeRLP against the RLP rules, ToBig/IntoBig/
  FromBig/SetFromBig/MustFromBig for negative and over-wide big.Ints.
- `TestHegelParsersAgreeWithBigInt` — SetFromDecimal, SetFromHex, FromDecimal, FromHex,
  MustFrom*, UnmarshalText, UnmarshalJSON and Scan accept exactly the documented grammar
  (decimal digits with an optional `+` and any leading zeros up to 2^256-1; `0x`/`0X` hex
  without leading zeros, at most 64 digits), reject everything else (signs, underscores,
  spaces, letters, non-ASCII digits, corrupted strings, values at and beyond 2^256) and read
  the same value as big.Int.

All general properties pass at 1000 cases × 3 and at 10 000 cases. Five pinned expected
failures.

## Bugs (5)

| id | title | severity |
|----|-------|----------|
| uint256/1 | Float64 truncates the mantissa instead of returning the nearest float64 | medium |
| uint256/2 | UnmarshalJSON rejects the JSON null that encoding/json hands to Unmarshalers | low |
| uint256/3 | String, Dec, Hex, MarshalText, MarshalJSON and Value panic on a nil *Int | low |
| uint256/4 | MulDivOverflowRem mishandles aliasing: m == d panics, m == z loses the remainder | medium |
| uint256/5 | PaddedBytes drops the high bytes when n is shorter than the value | low |

Four of the five were visible from reading the 3 000 lines of source before any property ran
(Float64's `fraction>>12`, `m.Clear()` before `udivrem` reads `d`, `make([]byte, n)`, the
missing null check); the probe confirmed them all at once.

## Not bugs (documented or by design)

- Division, modulus, AddMod and MulMod by zero give zero (documented "OBS: differs from the
  big.Int"); `Log10(0)` is 0; `Exp(0, 0)` is 1 as in big.Int.
- `SetFromBig`/`FromBig` of a negative or over-wide big.Int take the low 256 bits of the two's
  complement and report overflow only for widths above 256 bits (`FromBig(-5)` is 2^256-5 with
  overflow false; `FromBig(-2^300)` is 0 with overflow true).
- `SetBytes` of more than 32 bytes uses the last 32 (documented); `WriteToSlice` into fewer
  than 32 bytes writes the low bytes (documented, "useful for filling an Address").
- `Scan("")` is zero (an explicit branch); `Scan("0e100")` fails with `hex number > 256 bits`
  because the exponent is range-checked before the mantissa is looked at (the value is 0);
  `Scan` only knows a lowercase `e`. Left unrecorded.
- `Format` delegates unsupported verbs to big.Int, so `%q` prints `%!q(big.Int=5)` rather than
  `%!q(uint256.Int=5)`; a plain `Int` value (not a pointer) is a `[4]uint64` to `fmt` and
  `encoding/json` unless it is addressable, exactly as for `big.Int`.
- The hex parser's error kinds (`ErrLeadingZero`, `ErrBig256Range` for a too-long decimal
  string, `io.EOF` for an empty decimal string) are not compared, only accept/reject.

## Conventions

External test package with a dot import; `HEGEL_TEST_CASES` via `hegelOpts`; `property()`
turns panics into test-case failures. A run of all five general properties takes under half a
second at the default budget.
