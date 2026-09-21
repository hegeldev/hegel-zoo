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
`go test -count=1 -run TestHegel -v ./hegel`. No oracle outside Go is needed.

## Oracle

Random expression trees over the grammar of `gval.Full` are rendered to text with random
spacing, either with minimal parentheses (from gval's precedence table, left associativity,
prefixes binding to the next primary, the ternary and `??` at the bottom) or with every
operand parenthesized, and evaluated by a model of the documented semantics: Go `float64`
arithmetic (`math.Mod`, `math.Pow`, `int64` conversions for the bit operations), the
operator resolution order read off `operator.go` (strict number, bool and text operands
first, then the same with the documented conversions — numeric strings, `"true"`/`"false"`,
nil as false —, then the arbitrary fallback `reflect.DeepEqual`/`in`/`??`), short circuits
for `&&`, `||` and `??`, `fmt %v` for `EvalString`, the variable selector on maps and
arrays, regex matching. Leaves are numbers, strings (numeric, boolean-looking, plain),
booleans and parameters of every kind (numbers, strings, nil, an array, nested maps). Cases
whose outcome Go leaves implementation-defined (float to integer conversions out of range)
are skipped. The decimal language is modelled with exact rationals (`math/big`) for `+ - * %`
and integer powers; its division is not modelled beyond the zero divisor.

## Properties

- `TestHegelEvaluate`: the minimal and the fully parenthesized rendering of a tree evaluate to
  the model's value, or fail exactly when the model fails (the documented `Evaluate` error).
- `TestHegelReuse`: an `Evaluable` built once answers for two parameter sets as the model
  does, and `IsConst` is true exactly for constant expressions.
- `TestHegelConversions`: `EvalBool`, `EvalFloat64`, `EvalInt` and `EvalString` apply the
  documented conversions to the expression's value.
- `TestHegelDecimal`: `DecimalArithmetic` computes `+ - * %` and integer powers exactly,
  compares exactly, and a zero divisor is an error.

## Bugs

Eight, see `bugs.toml`: the decimal language cannot negate a decimal (1) and panics on
division by zero (8); `??` drops zero values, not only nil and false as documented (2); the
ternary tests the zero value instead of the bool conversion, so `"false" ? 1 : 2` is 1 (3); a
bad index on an array returns the array (4); constant folding at parse time makes
`true || "a" - 1` a parse error while the variable form evaluates (5); base-prefixed integer
literals are rejected (6); the precedence of shifts and `&` is not Go's although the README
claims Go's order (7).

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
  behaviour of shopspring/decimal v1.3.1's `Pow`; division rounds to 16 places.
- `date(...)` is not exercised.
