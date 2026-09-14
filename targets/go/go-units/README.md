# go-units

[docker/go-units](https://github.com/docker/go-units) is Docker's 300-line library for human
sizes (`HumanSize`, `HumanSizeWithPrecision`, `BytesSize`, `CustomSize`, `FromHumanSize`,
`RAMInBytes`), human durations (`HumanDuration`) and `ulimit` strings (`ParseUlimit`,
`Ulimit.String`, `Ulimit.GetRlimit`); it parses `--memory 1.5g`, `--shm-size`, `--ulimit
nofile=1024:2048` and prints image sizes and "3 days ago" in the docker CLI. Pinned at 2bd057e
(v0.5.0+, 2026-04-15), Apache-2.0, no AI policy.

## Oracles

- Exact arithmetic: a size string's number is read as a `math/big.Rat`, multiplied by the unit
  and floored — the number of bytes the string denotes.
- The printers are checked against the unit tables and their own parsers: the mantissa must
  lie in [1, base), the unit must be the table entry whose power divides the size, the printed
  value must equal the size to the requested precision, and `FromHumanSize(HumanSize(x))` /
  `RAMInBytes(BytesSize(x))` must come back within that precision.
- HumanDuration is read back as a count of a unit and compared with the duration (within one
  unit, monotone).
- ParseUlimit against its grammar (name table with the RLIMIT numbers, `soft[:hard]`, the -1
  and soft ≤ hard rules) and String()/GetRlimit round trips.

## Properties

- `TestHegelSizeParsersReadTheGrammar` — `<number>[ ]<suffix>` with fractions, bare dots, `+`,
  a single space, suffixes `b`/`B`, `k m g t p` in any case with `b`/`ib` in any case, for both
  parsers, against the exact value (within the float64 rounding error, relative 2^-50, plus
  one byte: go-units/2).
- `TestHegelSizeParsersRejectJunk` — leading/double/tab blanks, trailing blanks after a suffix,
  negatives, unknown or over-long suffixes, two numbers, NaN/Inf, non-ASCII digits → error and
  -1.
- `TestHegelSizePrintersUseTheRightUnit` — HumanSize, HumanSizeWithPrecision (1–10),
  BytesSize, CustomSize with short tables, for sizes from 0 to 10^27 (exact integers,
  log-uniform reals), plus the parse-back round trips below the E units.
- `TestHegelHumanDurationIsWithinOneUnitAndMonotone` — for durations from 0 to centuries.
- `TestHegelUlimitGrammarAndRoundTrip` — every name × limits in {-1, 0, small, huge,
  MaxInt64}, `soft` and `soft:hard` forms, String() and GetRlimit round trips, twenty junk forms.

All general properties pass at 1000 cases × 3 (under a second). Six pinned expected failures.

## Bugs (6)

| id | title | severity |
|----|-------|----------|
| go-units/1 | FromHumanSize/RAMInBytes return -9223372036854775808 with a nil error for sizes at or beyond 2^63 | medium |
| go-units/2 | Decimal sizes are multiplied in float64 and truncated, so `1.007kB` is 1006 bytes and `16.1PB` is 16100000000000002 | medium |
| go-units/3 | The printers emit EB/ZB/YB and EiB/ZiB/YiB but the parsers know no unit above P | low |
| go-units/4 | Rounding the mantissa to the precision can reach the base: 999950 bytes print as `1000kB` | low |
| go-units/5 | ParseUlimit's "invalid ulimit argument" error prints an empty argument | low |
| go-units/6 | ParseUlimit accepts negative limits other than -1 and GetRlimit turns them into limits near 2^64 | low |

All six were visible from reading the 300 lines (the `int64(float64)` conversion, the float
product, the `kmgtp` map against the nine-entry print table, the unit chosen before rounding,
the `:=` over the parameter, the `-1`-only check); one probe confirmed them.

## Not bugs (documented, asserted upstream, or lenient by design)

- The number is read by strconv.ParseFloat, so `1e3kB`, `1E+3`, `0x1p4` and `5_000` are
  accepted (1000000, 1000, 16, 5000); `0x10` (no `p` exponent) and `1,5` are not. Lenient
  extras, kept out of the generators.
- `32.5 B` is 32 bytes (fractional bytes truncated; asserted upstream), `-0` is 0, `0.` and
  `.3kB` parse, `32 ` (trailing space, no suffix) parses while ` 32`, `32b ` and `32  b` do not
  (asserted upstream). `32KiB` through FromHumanSize is 32000 (the suffix grammar is shared,
  only the multipliers differ).
- HumanSize of a negative size prints it as bytes (`-5B`), of NaN `NaNB`, of +Inf `+InfYB`, of
  a fraction `0.5B` or `1e-05B`; sizes past 1000^8 print as `1000YB`, `1e+04YB` (asserted
  upstream).
- HumanDuration never says "1 year": 365–729 days are "12 months" to "24 months", 730 days
  "2 years"; 47 h 30 min is "2 days" (hours rounded to 48 first) and 1 h 29 min "About an hour";
  negative durations are "Less than a second". Month = 30 days, year = 365 days.
- ParseUlimit names are case-sensitive and `as` is deliberately absent (commented out
  upstream); `+5` is accepted (strconv.ParseInt), `nofile=1024:2048:4096` is rejected as a
  bad integer, not as a bad shape.

## Conventions

External test package with a dot import; `HEGEL_TEST_CASES` via `hegelOpts`; `property()`
turns panics into test-case failures. No child processes.
