# period

[rickb777/period](https://github.com/rickb777/period) (module `github.com/rickb777/period`)
represents ISO-8601 periods ("P3Y11M4W1DT12H30M5.5S") as seven decimal fields on
`govalues/decimal`: `Parse`/`MustParse`, `String`/`Period`, the constructors `New*`,
`NewDecimal`, `NewOf`, `Between`, the getters and `GetField`/`SetField`, `Normalise`,
`NormaliseDaysToYears`, `Simplify`, `SimplifyWeeks*`, `Add`/`Subtract`/`Mul`/`Negate`/`Abs`,
`Duration`/`AddTo`/`TotalDaysApprox`/`TotalMonthsApprox`, `Format`/`FormatLocalised`, and the
text, JSON, sql and flag interfaces. The pin is `0b049b5` (2026-09-07, v1.1.0).

The repository is BSD-3-Clause; there is no CONTRIBUTING file, the README says nothing about
AI-written code, and there are no agent instructions. The zoo keeps its tests in its own patch
and files nothing upstream.

## Build

`go test -count=1 -run TestHegel -v .` in the module root (Go 1.25). The patch adds, in the
external test package, `hegel_test.go` (harness, the `Known` switch), `hegel_model_test.go`
(the rational value model, the grammar, the generators), `hegel_props_test.go` (properties),
`hegel_ref_test.go` (the isodate reference test) and `hegel_pins_test.go`, and requires
`hegel.dev/go/hegel v0.6.33` in go.mod. `TestHegelIsodateAgrees` runs `python3` with the
`isodate` module when it is on PATH (the CI's venv installs it) and is skipped otherwise.

## Oracle

The package's own documentation read as a specification, with the values of the seven fields
held as exact rationals (`math/big`):

- the grammar: `[+|-]P` then Y M W D in that order, optionally `T` then H M S in that order,
  each field a number (a leading `-` is a documented extension, comma or point) with its
  designator, each at most once, only the last non-zero field with a non-zero fraction, the
  documented zero forms; weeks may be mixed with other fields (documented). The model tags the
  leniencies the library shows (order, trailing T, bare decimal mark, "P0", a zero fraction,
  more than 19 digits) so that the property can require the recorded behaviour for each.
- the canonical string: `P0D` for zero, else the sign of the most significant field in front,
  fields in order without trailing zeros, `T` before the time fields.
- value preservation: `Normalise(true)`, `Simplify(true)` and `NormaliseDaysToYears` keep the
  calendar part (years at 365.2425 days, months at a twelfth of that, weeks at 7 days) and the
  time part separately; the approximate modes keep the total with 24-hour days; `Add`,
  `Subtract` and `Mul` act on the values field-wise (Add normalises, so per part); all results
  obey the fraction rule and parse back to themselves.
- `Duration` is the total under the documented approximation, exact where the fixed-point
  factors divide (the model knows which scales those are), precise iff the calendar part is
  zero; `AddTo` is `time.AddDate` plus the time part for whole calendar periods and `t.Add` of
  the duration otherwise; the totals are the truncated day count (whole days of the time part
  included) and its twelfth-of-a-year quotient; `NewOf` and `Between` invert them.
- `Format`: each non-zero field as number and unit (singular up to one), "minus" for a
  negative field, joined by ", ".
- the Python isodate library on a batch of 400 strictly ISO strings (years, months and the
  total of the rest must agree, within a millisecond for isodate's floats).

Generators draw period strings of the grammar with fields present at random, fractions with up
to 12 digits, numbers of 1 to 18 digits, negative fields, zero-valued fields ("0", "0.0"),
signs and zero forms, and mutate them (insert / delete / replace / swap / duplicate over the
period alphabet) for the grammar property; periods come from `Parse` of such strings, from
`New`, `NewDecimal` and `NewOf`.

## Method

| Property | Checks |
|---|---|
| ParseFollowsTheGrammar | accept/reject as the grammar with the recorded leniencies, the fields, the canonical `String`, `MustParse` panics, text/JSON/Scan/Value/flag round trips, the sign predicates |
| NormalisePreservesTheValue | `Normalise`, `Simplify`, `SimplifyWeeks*`, `NormaliseDaysToYears`: value kept, idempotent, fraction rule, sign convention, parse back |
| ArithmeticIsExact | `Add`/`Subtract` (per part, commutative, inverse), `Mul`, `Negate`, `Abs`, `Sign`, `OnlyYMWD`/`OnlyHMS` against the rationals; results parse back |
| DurationIsTheSum | `Duration`, `DurationApprox`, precise flag, `AddTo` (AddDate or duration), `TotalDaysApprox`, `TotalMonthsApprox`, `NewOf`, `Between` |
| FormatListsTheFields | `Format` and `FormatLocalised` against the model text |
| AccessorsAreTheFields | the getters, `GetField`/`GetInt`, `SetInt`/`SetField` with the fraction rule, `New*` |
| IsodateAgrees | the Python isodate library parses a batch of 400 strict strings alike (plain test) |

`ZOO_COLLECT=1` records mismatches instead of failing and prints the agreement classes.

## Accepted differences

- `Format` drops the overall sign of a negative period ("-P1Y" is "1 year"); the upstream
  tests assert this, so the model does the same.
- `Normalise` does not move a whole part when the remainder is a pure fraction ("PT60.5S"
  stays); the totals' consequence is bug 10, the normalisation itself is modelled as value
  preservation only.
- `NormaliseDaysToYears` acts on the stored (sign-normalised) fields, so a mixed-sign period
  with a negative days field is left alone; the model checks the year threshold for same-sign
  periods only.
- `Duration` truncates each field's fixed-point factor by its scale (a months field with more
  than 3 decimals, hours with more than 11) and the totals truncate a mixed-sign time part
  stage by stage; both are counted and not compared.
- isodate rejects negative fields and canonicalises differently; only strict strings are sent
  and only values compared.

## Bugs found

Fifteen, in bugs.toml: `SetInt`/`SetField` on a negative period drop the sign of the other
fields (high); a zero fraction ("P1.0Y") is kept as a fraction, so `AddTo` approximates it and
"P1.0Y1D" is rejected; `NormaliseDaysToYears` writes a fractional days field in front of time
fields, which `Parse` rejects; `Duration` wraps on overflow and calls the result precise;
`Parse` rounds beyond 19 digits instead of rejecting; `Add`/`Mul`/`Simplify` round silently and
`Simplify` keeps the rounded value; the whole-number getters round; `Normalise`/`Simplify` can
leave a negative leading field with `Sign()` +1 (medium); and the lenient grammar ("P0"
rejected, designators in any order, trailing T, bare decimal mark), `Add`/`Mul` spreading
fractions, `Format` in float notation, and the totals ignoring whole days of a fractional time
field (low). The rest agreed: the exact values of every accepted string, the canonical string,
value preservation of all normalisations within 19 digits, `Duration`/`AddTo`/`NewOf`/`Between`
to the nanosecond, the totals, `Format`, and isodate on every strict string.

## History

- 2026-09-21 (turn 345): target added at 0b049b5 (v1.1.0) with six properties, the isodate
  reference test and 15 pins.
