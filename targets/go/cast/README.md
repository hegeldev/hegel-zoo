# cast

[spf13/cast](https://github.com/spf13/cast) is the "easy and safe casting" library behind Hugo,
Viper and much configuration-handling Go code: `ToInt`, `ToString`, `ToBool`, `ToTime`,
`ToDuration`, the `E` variants that return an error, generic `To[T]`/`ToE[T]`/`ToNumberE[T]`,
and the slice and `map[string]…` conversions. About 1 500 lines without tests. The pinned commit
is the September 2026 head, just past v1.9.2. MIT; no CONTRIBUTING.md and no AI policy at the
pin (the `.github` directory holds workflows only).

## Oracle

There is no second implementation, so the oracle is cast's own contract — the README ("If input
is provided that will not convert to that type, the 0 or nil value for that type will be
returned"; the E methods "tell you if it successfully converted"; a string converts to an int
only "when it is a string representation of an int such as 8"; `ToInt(8.31)` is 8) and the doc
comments — made concrete by small models: the exact value of a number (`math/big`) against each
Go type's range, `strconv` and `time.Parse` for text, element-wise conversion for slices and
maps, and the round trip `ToX(ToString(v)) == v`. Where the contract is silent the properties
require consistency between the paths that should agree (typed function, `ToE[T]`,
`ToNumberE[T]`, plain variant; the same map in different Go map types).

## Properties

- `TestHegelNumbersConvertByValue` — integers with the type boundaries over-represented, in
  every Go width, named types, pointers, floats with fractions, NaN/±Inf, decimal strings and
  `json.Number`s with an optional `+` and `.0…` tail: every `ToXxxE` gives the integer part
  (truncated toward zero) when it fits the target, an error for negative values into unsigned
  types, the plain variant the same value or zero, and `ToE[T]`/`ToNumberE[T]` agree; floats
  follow `strconv.ParseFloat` for text and Go conversion otherwise. Out-of-range values are
  drawn too, so the property lands on cast/1 (the text ones are cast/2's region).
- `TestHegelMalformedTextIsRefused` — words, doubled signs, exponents, blanks, units, hex
  floats, non-ASCII digits, random ASCII: every integer conversion errors with a zero result;
  the float conversions follow `strconv`'s verdict; decimals such as `"1."` and `".5"` get
  cast's documented reading (the integer part). The `.` family (cast/4), base prefixes
  (cast/3) and doubled signs (cast/10) are in the pool, so the property lands on cast/4 in
  most runs (about 3 % of cases; intermittent).
- `TestHegelToStringRoundTrips` — `ToString` of every integer width, floats (no exponent
  notation, shortest repr), bools, durations and times (UTC and named fixed zones) reads back
  with the matching conversion; bare-number strings are nanoseconds for `ToDuration`.
- `TestHegelOwnLayoutsRoundTrip` — a time formatted with each of cast's 24 layouts
  (`internal.TimeFormats`) is parsed back by `ToTimeInDefaultLocationE` with the documented
  meaning: numeric-offset layouts give the same instant and offset; layouts without a zone (and
  the zone-name-only layouts, by design) give the wall clock in the default location; time-only
  layouts give year 0 in UTC; two-digit years follow Go's 69/68 rule; fractional seconds appended
  to a seconds field are accepted; `ToTimeE`, `ToE[time.Time]` and `StringToDate` agree.
  RubyDate texts with an offset under an hour are drawn, so the property lands on cast/5
  (about 1 % of cases; intermittent).
- `TestHegelIntegersAreUnixSeconds` — every integer kind, named integer types, floats and
  `json.Number` inputs are Unix seconds; `time.Time` is returned as is; `nil` is the zero time.
  Lands on cast/9 (the narrow kinds).
- `TestHegelSlicesConvertElementWise` — `[]any`, typed slices and arrays of convertible scalars
  through every `ToXxxSliceE`; an unconvertible element is an error and a nil plain result; a
  string splits on white space; a scalar is a one-element string slice.
- `TestHegelMapsConvertValueWise` — the same data as `map[string]any`, `map[any]any`,
  `map[any]string`, `map[string]int64`, `map[string]string` and JSON text through
  `ToStringMapIntE`/`Int64E`/`StringE`/`BoolE`/`ToStringMapE`, with keys stringified; the
  reflect path reports an unconvertible value. Lands on cast/12 (cast/7 and cast/11 are in
  its region too).
- `TestHegelStringSliceMapsKeepValuesWhole` — `ToStringMapStringSliceE` stringifies slice values
  element-wise and wraps scalars, for `map[string]any`, `map[any]any` and `map[string][]any`.
  Lands on cast/8.

## Known bugs

The generators draw the shape of every recorded bug (STYLE.md rule 11): the properties above
are the expected failures mapped to the bugs they land on, and each bug also has a narrow
property over its own shape region, the deterministic expected failure beside the pin:
`TestHegelNumbersBeyondTheTargetAreErrors` (cast/1), `TestHegelTextsBeyondTheTargetAreErrors`
(/2), `TestHegelZeroPaddedTextsAreDecimal` (/3), `TestHegelBareDotIsRefused` (/4),
`TestHegelRubyDateTextsKeepTheirOffset` (/5), `TestHegelJSONNumberBoolsFollowTheValue` (/6),
`TestHegelAnyValuedMapsReportValueErrors` (/7), `TestHegelAnyKeyedMapsKeepStringValuesWhole`
(/8), `TestHegelNarrowIntegerKindsAreUnixSeconds` (/9), `TestHegelDoubledPlusIsRefused` (/10),
`TestHegelIntegerMapsFromAnyKeyedMapsDoNotPanic` (/11, the panic is caught and named) and
`TestHegelStringMapsAcceptOtherValueTypes` (/12). `HEGEL_NO_KNOWN=1` (read once) switches the
known shapes off: out-of-range values, leading zeros and base prefixes, the `.` family, doubled
signs and the narrow RubyDate offsets leave the generators, and the sub-checks that only a
recorded bug can fail (out-of-range integers, `json.Number` bools, the `map[any]…` and
other-value-type map paths) are skipped by name; every property then passes at 3000 cases.
`CAST_COLLECT=1` makes the properties record mismatches instead of failing and print them
shortest-first.

## Bugs (12; details in bugs.toml)

| id | summary | severity |
|----|---------|----------|
| cast/1 | Numeric inputs out of range wrap or turn into garbage: `ToInt8(300)` = 44, `ToInt(NaN)` = MinInt64, `ToFloat32(1e40)` = +Inf | medium |
| cast/2 | Strings parsed at 64 bits then truncated: `ToInt8E("300")` = 44, `ToUint8E("256")` = 0 | medium |
| cast/3 | Base-0 parsing: `"010"` is 8, `"08"` is an error, `"0x1f"`/`"1_000"` accepted | medium |
| cast/4 | `"."`, `"-."`, `"+."` convert to 0 without error | low |
| cast/5 | RubyDate strings with an offset under an hour are claimed by UnixDate and re-read in the default location | medium |
| cast/6 | `ToBool(json.Number("0.5"))` is false, `json.Number("1e3")` an error | low |
| cast/7 | `map[string]any`/`map[any]any` conversions swallow value errors (`{"a": "x"}` → `{a: 0}`, nil) | low |
| cast/8 | `ToStringMapStringSliceE` splits string values on white space for `map[any]…` but not `map[string]…` | low |
| cast/9 | `ToTimeE` rejects int8/int16/uint8/uint16, floats and named integer types as Unix seconds | low |
| cast/10 | `ToUintE("++5")` = 5 | low |
| cast/11 | `ToStringMapIntE`/`Int64E` panic on `map[any]string`, `map[int]int` (reflect path uses the raw key) | medium |
| cast/12 | `ToStringMapE(map[string]string)`, `ToStringMapStringE(map[string]int)` are "unable to cast" | low |

How they were found: /1, /2, /3, /6, /7, /8, /9, /10 and /12 from reading `number.go`,
`time.go` and `map.go` while writing the models (each confirmed by its pin; the properties
draw the shapes since 2026-09-25); /4 by the malformed-text property's first run (`"."` → 0); /5 by the
layout round-trip property (`"Mon Feb 08 19:19:01 +0000 1971"` came back with the default
location's offset), then narrowed with a probe of which layout claims each layout's output and
a look at Go's `parseSignedOffset`; /11 by the map property's first run (a panic on
`map[any]string{"a": "0"}`).

## Not bugs (documented, Go's, or design)

- Decimal strings lose their fraction (`ToInt("12.75")` = 12): the README's `ToInt(8.31)` = 8
  applied to text. Asserted as such.
- `""` is 0 for every number conversion (documented in the code) but an error for `ToBoolE`,
  `ToDurationE` (it becomes `"ns"`) and `ToTimeE`. Not compared.
- Bare-number strings are nanoseconds for `ToDurationE` (`"123"` = 123ns); a string containing
  any of `nsuµmh` goes to `time.ParseDuration` unchanged. Asserted as such.
- `"inf"`, `"NaN"`, hex floats and exponents are what `strconv.ParseFloat` says; `ToIntE("1e3")`
  is an error although 1e3 is integral. Not recorded.
- Layouts with a zone name only (RFC1123, RFC822, RFC850, UnixDate, ANSIC) are re-read in the
  default location, discarding the name — the code says so, citing golang/go#19694 — and this
  applies to `UTC`/`GMT` too. Only UTC-named strings are generated; the rest is design.
- `Time.String()` of a nameless fixed zone (`… -0700 -0700`) cannot be parsed back by Go's own
  `time.Parse` (the zone-name slot accepts numeric offsets only up to `+23`); named zones other
  than three letters, or four/five ending in T, are rejected by Go as well. Go's limits, not
  cast's; the generators use UTC and such names.
- The Stamp layouts with fractions and `2006-01-02 15:04:05Z07:00` are claimed by earlier
  layouts in the list; the results are identical, so it does not matter.
- `ToSliceE` accepts only `[]any` and `[]map[string]any`; `ToStringSliceE` of a string is
  `strings.Fields`. Established behaviour, asserted as such.
- JSON text into a map goes through `json.Unmarshal` into the target type, so values must
  already be numbers for the int maps and strings for the string map. Not compared.
- Error messages and types are not compared.
- Not covered: `Must`, the `float64Provider`/`float64EProvider` interfaces, `template.HTML`
  and friends into `ToString`, `fmt.Stringer`/`error` inputs beyond `time.Duration`/`time.Time`.
