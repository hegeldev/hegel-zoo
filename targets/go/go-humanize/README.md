# go-humanize

[dustin/go-humanize](https://github.com/dustin/go-humanize) is the Go library most programs
reach for to print "83 MB", "1,234,567", "3rd", "2.2345 pF" and "3 weeks ago": byte sizes
(`Bytes`, `IBytes`, `BytesN`, `IBytesN`, `ParseBytes`, and `math/big` versions `BigBytes`,
`BigIBytes`, `ParseBigBytes`), thousands separators (`Comma`, `Commaf`, `CommafWithDigits`,
`BigComma`, `BigCommaf`), a template-friendly `FormatFloat`/`FormatInteger` with a format
string, `Ftoa`/`FtoaWithDigits`, SI prefixes (`ComputeSI`, `SI`, `SIWithDigits`, `ParseSI`),
`Ordinal`, and relative times (`RelTime`, `CustomRelTime`, `Time`). About 1100 lines of Go with
example-based tests and a fuzz test for `Comma`. Pinned at 4d1d908 (v1.0.1+, 2025-11-24), MIT,
no AI policy.

## Oracles

- Exact arithmetic: a size string's number is read as a `math/big.Rat`, multiplied by the
  suffix's power and floored — the number of bytes it denotes. The printers are checked against
  the exact mantissa `s / base^e` (unit index `e` computed in `big.Int`), with the rounding they
  are entitled to (the requested significant digits) and nothing more, and their output is
  parsed back by both parsers.
- String-insertion models for the comma family: `strconv`'s digits with a separator every three
  from the right; truncation for the `WithDigits` variants (documented as "limits").
- The documented reading of `FormatFloat` formats (thousands separator, decimal separator,
  precision, `+`) as a table, checked structurally: sign, grouping, digit count, and the value
  to the precision.
- Tables for SI prefixes and ordinal suffixes; an independent if-chain for the RelTime
  magnitudes (seconds, minutes, hours, days, weeks, 30-day months, 360-day years, singular
  below twice the unit, "now" under a second, "a long while" from 37 years).

## Properties

- `TestHegelBytePrintersFollowTheModel` — `Bytes`/`IBytes`/`BytesN`/`IBytesN` with 1–6 digits
  for uint64 sizes spread over the whole range and biased to unit boundaries: `"%d B"` below
  10, the right unit, the right number of decimals, the value within the rounding (the double
  rounding of go-humanize/2 is allowed for), and `ParseBigBytes`/`ParseBytes` of the output
  give the printed value back (ParseBytes within its float64 rounding, go-humanize/3; an
  output at or beyond 2^64 must be rejected). Mantissas within one unit of the base are skipped
  (go-humanize/1).
- `TestHegelBigBytePrintersFollowTheModel` — `BigBytes`/`BigIBytes` for integers up to 36
  digits: one decimal below a mantissa of 10, none above, the unit (the table ends at quetta;
  beyond it the mantissa grows), the value within the rounding plus the 1/base truncation of
  go-humanize/9, and the `ParseBigBytes` round trip.
- `TestHegelByteParsersAgreeWithExactArithmetic` — `<digits[,digits]*>[.digits][blank]<suffix>`
  with suffixes `""`, `b`, and `k m g t p e z y r q` bare or with `b`/`i`/`ib`, in any case, with
  trailing blanks: `ParseBigBytes` exact; `ParseBytes` within float64 rounding, rejecting the
  suffixes above exa it does not know and values that do not fit a uint64.
- `TestHegelByteParsersRejectJunk` — leading sign or blank, exponents, two points, no digits,
  unknown suffixes, blanks inside a suffix, `_`, `0x`, `bytes`, `kbps`.
- `TestHegelCommaFormattersFollowTheModel` — `Comma` over all of int64, `Commaf` over
  decimal/random-bit/huge floats, `CommafWithDigits`, `BigComma` up to 36 digits, `BigCommaf`
  (handed a copy: go-humanize/5), and `FormatInteger("#,###.", k)` = `Comma(k)` below 2^52
  (go-humanize/8).
- `TestHegelFormatFloatFollowsItsFormat` — thirteen formats from the documentation (`""`,
  `#,###.##`, `#,###.`, `#,###`, `# ###,##`, `#.###,######`, `#.##`, nine places, no directive,
  `+`), values up to 10^12; the documented-invalid formats panic with a `FormatFloat()` message.
- `TestHegelFtoaSIAndOrdinalFollowTheirModels` — `Ftoa` and `FtoaWithDigits` against
  `strconv` with six places and stripped zeros; `ComputeSI` for mantissas clear of the decade
  boundaries times every tabled power of ten (prefix and mantissa), `SI` → `ParseSI` round
  trips for units that do not start with a prefix letter, `ParseSI` on hand-built text;
  `Ordinal` for 0..10^9.
- `TestHegelRelTimeFollowsTheTable` — both argument orders for differences from a nanosecond
  to 40 years, biased to the table boundaries, against the if-chain model with both labels.

All general properties pass at 1000 cases × 3 (under a second). Nine pinned expected failures.

## Bugs (9)

| id | title | severity |
|----|-------|----------|
| go-humanize/1 | A mantissa that rounds up to the base is printed as `1000 kB`, `1024 KiB` or `1000 kF` instead of moving to the next unit | low |
| go-humanize/2 | Bytes/IBytes round twice (to two significant digits, then %.0f), so 82.549 MB prints as `82 MB` while BytesN(_, 1) and BigBytes say `83 MB` | low |
| go-humanize/3 | ParseBytes multiplies in float64 and truncates, so `1.007 kB` is 1006 bytes (ParseBigBytes: 1007), `16.1 PB` ends in ...002 and 18446744073709551615 is "too large" | medium |
| go-humanize/4 | Commaf(+Inf) is `+,Inf` and Commaf(-Inf) is `-+,Inf` | low |
| go-humanize/5 | BigCommaf calls v.Abs(v) and so turns a negative argument positive | low |
| go-humanize/6 | Outside the quecto..quetta table SI drops the prefix and prints the bare mantissa: SI(1e-31, "F") is `100 F`, SI(1e-33, "F") is `1 F` | low |
| go-humanize/7 | FormatFloat converts the integer part with int64(), so from 2^63 it prints -9,223,372,036,854,775,808 (and `--9,223,...` for negatives) | low |
| go-humanize/8 | FormatInteger adds a float64 rounder of 0.5, so from 2^52 odd integers print as the next even one | low |
| go-humanize/9 | BigBytes/BigIBytes round a mantissa truncated to 1/1000 (1/1024), so 1950000001 prints `1.9 GB` and 82500001 prints `82 MB` | low |

Seven were visible from reading the sources and confirmed by one probe (the unit chosen before
rounding, the `%.0f` after a first rounding, the float64 product and `uint64(f)`, the comma loop
over "+Inf", `v.Abs(v)`, the map lookup of an exponent outside the table, `int64(intf)`); the
properties found the other two (the 2^52 rounder in `FormatInteger` and oomm's discarded
remainders in `BigBytes`).

## Not bugs (documented, asserted upstream, or lenient by design)

- `CommafWithDigits`, `FtoaWithDigits` and `SIWithDigits` truncate rather than round ("limits
  the resulting string to the given number of decimal places"; the documented example
  834142.32, 1 → 834,142.3 is consistent with both). Modelled as truncation.
- `FormatFloat`'s doc comment says `#,###.##` of 12345.6789 gives "12,345.67" and `#,###.`
  gives "12,345"; the code rounds ("12,345.68", "12,346") and its tests assert the rounding.
  The comment is stale, the behaviour is the better one. Likewise the comment promises
  "+Infinity" and the code returns "Infinity".
- `FormatFloat` with more than nine digit specifiers after the decimal separator panics with an
  index-out-of-range ("The highest precision allowed is 9 digits"); a clearer panic would be
  nicer, but the input is documented as disallowed. Three or more separators in a format are
  silently ignored (undocumented; kept out of the generator).
- `FormatFloat("#,###.##", -0.001)` is "-0.00": the sign is decided against a 1e-9 threshold
  before rounding. Cosmetic; allowed by the property.
- `Ftoa(-1e-7)` is "-0" for the same reason (strconv's "-0.000000" stripped). Modelled.
- `ParseSI("5 m")` is 0.005 with an empty unit, `ParseSI("5 Pa")` is 5e15 "a": a unit that
  starts with a prefix letter is inherently ambiguous in the `<number> <prefix><unit>` grammar
  the function reads and `SI` writes. The round-trip property uses units that do not start with
  one (B, F, V, Hz, W, s, Ω, bit/s, h, cd).
- `ParseSI` is lenient: `"1e3 k"` is 1 with unit "e3 k", `"5  kV"` (two blanks) is 5 with unit
  " kV". Kept out of the generator.
- `ParseBytes("1,0,0 kB")` is 100000 and `"1,5 kB"` is 15000: commas are simply dropped, in
  any position. The generator uses arbitrary comma positions and expects that.
- `BytesN(s, 0)` and negative digit counts give nonsense ("0 kB", "80 MB" for 82.8 MB): the
  count of significant digits is a positive number by definition. Not generated.
- `Ordinal(-1)` is "-1th": ordinals of negative numbers are undefined; the property covers
  0..10^9.
- `RelTime` at exactly 18 months says "2 years", a month is 30 days and a year 360 days: the
  documented table.
