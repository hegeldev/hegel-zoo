# go/gval

[PaesslerAG/gval](https://github.com/PaesslerAG/gval) ("Go eVALuate") is an expression
evaluator with a composable grammar: arithmetic, bitwise, text and logical operators with
type conversions, regex matching, `in`, `??`, the ternary, JSON array and object literals,
parameter paths (`foo.bar`, `foo[expr]`), and a decimal variant of the arithmetic. Pinned at
`c622ea2` (seven commits after v1.2.4, 2026-09-13, BSD-3-Clause; no AI policy in README or
`.github`, no CONTRIBUTING).

## Build

The tests live in a new package directory `hegel/` of the upstream module and use the library
as a black box; `go.mod` gains `hegel.dev/go/hegel`. The run command is
`go test -count=1 -run TestHegel -v ./hegel`. No oracle outside Go is needed. The patch adds
`hegel_zoo_idioms_test.go` (the generator idioms shared with the other rewritten Go targets:
weighted choices, fair-bit dice, halving helpers), `hegel_zoo_test.go` (the harness, the
collector, the `known` switch set, the judge and the classifier), `hegel_zoo_model_test.go`
(the expression and decimal models with the switch set threaded, the pure renderer),
`hegel_zoo_cases_test.go` (the case records, the pools and their generators),
`hegel_zoo_props_test.go` (the four wide properties), `hegel_zoo_shapes_test.go` (one narrow
property per bug) and `hegel_pins_test.go` (one plain test per bug). `HEGEL_TEST_CASES`,
`HEGEL_SEED` and `HEGEL_VERBOSE` are passed through to the engine; `HEGEL_COLLECT=1` records
mismatches instead of failing and prints the counts per class; `HEGEL_NO_KNOWN=1` switches
the known shapes off (below).

## Oracle

Random expression trees over the grammar of `gval.Full` are rendered to text by a pure
function of the tree and a drawn spacing record, either with minimal parentheses by Go's
precedence table (the README's promise: "the normal Go-standard order of operators";
left associativity, prefixes binding to the next primary, the ternary and `??` at the bottom)
or with every operand parenthesized, and evaluated by a model of the documented semantics:
Go `float64` arithmetic (`math.Mod`, `math.Pow`, `int64` conversions for the bit operations),
the operator resolution order read off `operator.go` (strict number, bool and text operands
first, then the same with the documented conversions - numeric strings, `"true"`/`"false"`,
nil as false -, then the arbitrary fallback `reflect.DeepEqual`/`in`/`??`), short circuits for
`&&`, `||` and `??`, `fmt %v` for `EvalString`, the variable selector on maps and arrays, regex
matching. Leaves are numbers (spelled plainly, with a `.0` or a trailing `.`, a stripped
leading zero, or - integral values - with a base prefix: `0x10`, `0b101`, `0o17`, legacy
`017`, `1_000`, `0x1p4`), strings (numeric, boolean-looking, plain, in quotes or backticks),
booleans and parameters of every kind (numbers, strings, nil, an array, nested maps). Parse
errors are compared by kind (the library's message carries positions); evaluation errors by
their text, which the model predicts. Cases whose outcome Go leaves implementation-defined
(float to integer conversions out of range, a shift by a negative count) are filtered out by
name (`unspecifiedConversion`, under two percent). The decimal language is modelled with exact
rationals (`math/big`) for `+ - * %` and integer powers, and its division as
shopspring/decimal's `DivRound` to sixteen places, half away from zero (checked exact against
the library on five thousand quotients and two thousand chained ones), the result exact
thereafter.

Cases are records drawn from package-level generators built bottom-up by depth (`exprGen`,
`operandGen`, `varGen` up to depth four): a leaf at depth zero or at 20 % (a literal at 60,
else a variable), otherwise an infix at 50 (the operator even over the 23, arithmetic and
bitwise ones retargeted to numeric-looking operands at 60 then 50/50, the right operand a
regex literal at 25 or an array at 20), a prefix at 12, a ternary at 10 (elseless at 20 at
the top), an array at 8 and an object at 6 (zero to three elements, object keys literal at
70), else a parameter path (the scalar names bare at 80; zero to two keys, a dot key at 50,
an index literal, string or expression at 1:1:2). Every leaf record holds its value and its
spelling (plain 70, `.0` 20, `.` 10; the base-prefixed forms at one in 125 each, off under
`HEGEL_NO_KNOWN=1`); the spacing of a rendering is a coin at 63 (realising 70) and a list of
64 gap kinds (a space 40, two spaces, a tab, a newline 20 each) the renderer cycles through.
The decimal trees as before: a leaf at depth zero or 25 % (the variable `x` at 20, else one of
the fifteen literals), a negation at 15, else an operator over `+ - * % ** / < <= > >= == !=`
with `**`'s exponent from 0..3. Every weight is drawn through the fair-bit dice of the idioms
and the realised rate measured over 3000 cases in context stands beside it. A case of the
evaluate property costs about 740 draws, under two thousand at most; a decimal case about 90.

## Method

| Property | Checks |
|---|---|
| TestHegelEvaluate | the minimal (Go-table) and the fully parenthesized rendering of a tree evaluate in `gval.Full` to the model's value, or fail with the model's error |
| TestHegelReuse | an `Evaluable` built once answers for two parameter sets (three evaluations) as the model does, and `IsConst` is true exactly for constant expressions |
| TestHegelConversions | `EvalBool`, `EvalFloat64`, `EvalInt` and `EvalString` apply the documented conversions to the expression's value |
| TestHegelDecimal | `DecimalArithmetic` computes `+ - * %`, integer powers and the sixteen-place division exactly, compares exactly, and a zero divisor is an error |
| eight narrow properties | one per bug (below): the bug's shape forced, the rest of the case drawn as in the wide property, judged by the same model |

## Modelled as recorded, not counted

- The conversions make `nil == 0`, `true == 1`, `"1" == "1.0"` and `true == "true"` true
  (both operands convert to bool or to number), `"10" < "9"` true (two strings compare
  lexically) but `"10" < 9` false; `true + 1` is the string `"true1"`; `1 < 2 < 3` is false
  (`true < 3` compares the texts). All follow the documented conversion order.
- `**` and every other operator are left-associative (`2 ** 3 ** 2` is 64); a prefix binds
  to the next primary (`-2 ** 2` is 4).
- An elseless ternary (`a ? b`) gives nil when false and is only accepted at the end of the
  expression (`(a ? b) + 1` is a parse error).
- `[1 2]` and `[,1]` parse (commas optional), `{a: 1}` with an undefined `a` gives the key
  `"<nil>"`.
- `DecimalArithmetic` `**` truncates the exponent to an integer (`2 ** 0.5` is 1), a
  behaviour of shopspring/decimal v1.3.1's `Pow`; division rounds to 16 places; `??` does not
  exist in the decimal language.
- `date(...)` is not exercised.

## Bugs

Eight, see `bugs.toml`: the decimal language cannot negate a decimal (1) and panics on
division by zero (8); `??` drops zero values, not only nil and false as documented (2); the
ternary tests the zero value instead of the bool conversion, so `"false" ? 1 : 2` is 1 (3); a
bad index on an array returns the array (4); constant folding at parse time makes
`true || "a" - 1` a parse error while the variable form evaluates (5); base-prefixed integer
literals are rejected (6); the precedence of shifts and `&` is not Go's although the README
claims Go's order (7).

## Properties and the recorded bugs

The model states the documented behaviour; the `known` switch set (`type known [8]bool`, one
index per bug id, all off by default) turns a replica of the library's rule on in its place,
each transcribed from the lines of `gval.go`, `parse.go`, `operator.go`, `language.go`,
`evaluable.go` and shopspring/decimal it follows: the decimal prefix minus converting with
`convertToFloat` (1), `??` and the ternary testing `IsZero` (2, 3), the array case of
`variable` falling through with the value unchanged (4), every constant infix, prefix and
regex pattern evaluated when the parser reduces it (5), `parseNumber` handing the token to
`strconv.ParseFloat` (6), the minimal rendering re-read by gval's own table - the chains
flattened and rebuilt (7) -, `Div` and `Mod` panicking (8). The classifier runs the model per
switch on the case before the library is called and names the first bug in id order whose
switch alone changes the expected checks (sufficiency), else the first whose switch is needed
(necessity), else a hole; every mismatch by default is a named shape and no named shape passes.

Over 3000 default cases the evaluate property names 539 shapes (18 %), every one by
sufficiency with the library agreeing with the replica in all of them: gval/3 in 85, 4 in 56,
5 in 341, 6 in 56, 7 in 1 (gval/2 under one in a thousand: a `??` whose left side is a zero
value and whose right side differs); the reuse property 493 (2: 14, 3: 63, 4: 82, 5: 313, 6:
19, 7: 2), the conversions property 506 (2: 1, 3: 57, 4: 73, 5: 340, 6: 35); the decimal
property 1118 (1: 690, 5: 421, 8: 7), 34 of them by necessity - a run-time error on the left
masks a constant negation on the right that folds only with both switches on - and the
constant zero divisor is a folding error first, so gval/8 alone names the run-time divisors.
A fold whose value Go leaves implementation-defined (`~1e21 + "["` as a constant pattern)
makes the case unspecified under the folding switch, so the filter takes it whatever the
run-time walk would have reached first. Over forty rounds at a hundred cases every wide
property fails every round: the evaluate property shrinks to gval/5 in 29 (`-false`, a prefix
of a constant bool), to gval/6 in 5, 4 in 4 and 3 in 2; the reuse property to gval/5 in 32 (4
seven, 6 one), the conversions property to gval/5 in 27 (4 seven, 6 five, 2 one), the decimal
property to gval/1 in 39 (`-0`; gval/5 once). The narrow properties force the shape with the rest
of the case drawn as in the wide property, each named as its bug in every case (the right
operand of `??` equal to the zero left operand, 5 %, and equal ternary branches, 1 %,
rejected; the precedence property rejects the chains the two tables order alike, 18 % with
the engine's retries) on strict pools: the numbers spelled plainly where gval/6 would be named
first, no erroring constant where gval/5 would, no other negation and no constant divisor in
the decimal trees.
A default run takes a few seconds (most of it the twelve failing properties shrinking), a
thousand cases under `HEGEL_NO_KNOWN=1` under a minute on this machine.

Under `HEGEL_NO_KNOWN=1` the shapes are off: the base-prefixed spellings (6) and the negation
of a decimal value (1) are at weight zero; the cases the classifier names as 2, 3, 4, 5 or 7
(19 % of the evaluate property's, 25 % of the reuse property's: mostly folding errors) and
as 5 or 8 in the decimal language (16 %) are filtered out. The narrow properties draw the
region past their shape and pass. The pins alone fail there.

## Shrinking

The simplest alternative comes first in every choice: a literal zero spelled plainly, the
empty spacing, the first operator; the harness bounds a shrink by a budget of failing
judgements, since the engine keeps every attempt in memory.

## History

- 2026-09-21 (turn 341): target added at c622ea2 with four properties, 8 pins.
- 2026-10-14: rewritten to the standard: the eight `Known` switches on by default - three read
  by the model so that it reproduced the bugs, three gates skipping a shape, two read by
  nothing (the base-prefixed spellings were never drawn and the renderer parenthesized by
  gval's own table, so the Go-order shape never arose) - turned into eight switches off by
  default with the classifier naming the shape; the renderer a pure function of the record,
  the minimal rendering by Go's table; the decimal division modelled; the folding errors and
  the zero divisors judged instead of skipped; eight narrow properties.
