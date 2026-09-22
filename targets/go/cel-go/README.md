# go/cel-go

[cel-expr/cel-go](https://github.com/cel-expr/cel-go) (v0.32.0, 77 commits after): the Go
implementation of the Common Expression Language: two parsers (the ANTLR grammar and the
hand-written Pratt parser), the type checker, the interpreter with its evaluation options, the
constant-folding optimizer and the unparser, behind `cel.Env`. Tested here: parse, check,
Program and Eval of generated expressions over the standard types and operators, the five
comprehension macros, the two parsers against each other, the evaluation options and the
optimizer against plain evaluation, and the unparser's round trip.

## Build

The patch adds `hegel.dev/go/hegel` to `go.mod` and a `hegel/` package of five
`hegel_zoo_*_test.go` files that drive the public API: `go test -count=1 -run TestHegel -v ./hegel`.
Upstream vendors its dependencies, so the zoo's `GOFLAGS=-mod=mod` is needed for the added
module.

## Oracles

A Go-side model of the specification's Standard Definitions (`doc/langdef.md`): checked
int and uint arithmetic with overflow errors, IEEE doubles, byte-wise string ordering,
code-point `size`, equality across the numeric types, conversions as cel-go performs them
(strconv rules), strict functions that pass errors through and `&&`, `||`, `?:` that absorb
them commutatively, and the Macros section's definitions of `all`, `exists`, `exists_one`,
`map` and `filter` as folds. The library against itself: the Pratt parser must accept what the
ANTLR parser accepts and build the same tree, macro-call records and offset ranges; the
checked program, every `EvalOption` (`OptOptimize`, `OptExhaustiveEval`, `OptPartialEval`,
`OptTrackState`), the constant-folded AST and the unparsed-and-recompiled text must evaluate
as the plain program does; the checker's output type must be the type the generator gave the
expression (`dyn` matching anything); `AstToString` must be a fixpoint whose text parses to
the same tree.

## Generator

Expressions of depth 1 to 4 over twelve variables (ints, a uint, a double, strings, bytes, a
bool, lists of int and string, maps string→int and int→string) with random values from pools
of edge cases (the int and uint bounds, -1, 0, ±0.0, subnormals, 1e-300, 1.8e308, strings
with escapes, code points above the BMP, invalid UTF-8 bytes): literals in every spelling
(hex, `u`, exponent, `.5`, quotes, triple quotes, raw and escaped strings and bytes),
arithmetic, negation, `!` and `!!`, comparisons, `&&`/`||`/`?:`, `in`, indexing, `size` in
both styles, conversions, string functions, list and map literals (empty ones too), with
random spacing and redundant parentheses. Macro cases: a list or map range, a predicate and a
transform from small templates over the loop variable, optionally a chained second macro
and a `!` or `size()` wrapper. For the parser comparison, generated expressions, generated
expressions with one character changed, deleted or inserted, and random token soup.

## Properties

- `TestHegelEval`: parse, check (output type as generated), evaluate against the model; the
  checked program, each evaluation option, the constant-folded AST, and the unparsed text
  (folded and unfolded) give the same result; the unparser is a fixpoint and its text parses
  to the same tree.
- `TestHegelParsers`: the Pratt and ANTLR parsers accept the same inputs and record the same
  tree, macro calls and offsets (reject messages and positions are counted, not judged).
- `TestHegelMacros`: the five macros over lists and maps against the specification's folds,
  with the same variants as `TestHegelEval`; map-derived results compared as multisets.
- `TestHegelPin…`: one pin per recorded bug (expected failures).

## Bugs

Nine, recorded in `bugs.toml`. The Pratt parser rejects a numeric literal glued to `in`
(cel-go/1) and records different offsets for negative literals, leading-dot identifiers and
message literals (2). The checker binds the type variable of an empty literal's element to the
first overload tried, so `-({}['a']) + 1` fails to check (3). Errors dropped: `OptOptimize`
and constant folding make `e in []` false, folding makes `x in [x, e]` true (4). A map literal
with a repeated key evaluates to a map instead of an error (5). `OptOptimize` fails Program()
on a constant unary call that errors in an untaken branch (6). Constant folding fails on a
pruned conditional whose ids collide with later nodes (7), unparses NaN and the infinities
as `NaN.0`, `+Inf.0`, `-Inf.0` (8), and gives a stray value for a macro whose literal
predicate leaves the accumulator unchanged (9).

## Modelled as recorded

Every bug has an `HZKnown` switch. While a switch is on the generator keeps away from the
shape or the checks skip it: a space before `in` after a numeric literal; offsets of
literals, identifiers and structs not compared; indexes and macro ranges regenerated when
the aggregate is an empty literal; the rewrite variants skipped when an erroring expression
contains `in`; repeated map keys not generated; Program() errors under `OptOptimize`
tolerated when the plain result is not an error; folding errors mentioning "already exists
for expression" skipped; folded texts containing `NaN.0` or `Inf.0` not recompiled; literal
`false` predicates for filter/map/exists and `true` for all replaced. The collector counts
the avoidances; `ZOO_KNOWN_OFF=name,name` turns switches off and the properties then fail.

## Not judged

`1e400` is rejected as a literal and `12.` is a select, so the generator writes `(1.0/0.0)`
and `12.0`; the parser folds `--5` to `5` and `-(5)` to `-5` and the unparser writes `-(0)`
as `-0` and re-associates `&&`/`||` chains, so trees are compared with negated literals and
chains normalized and the fixpoint is required only when the trees agree exactly; the
comparison operators return false for NaN rather than following the specification's
`e1 <= e2 == !(e1 > e2)` law; `string(double)` uses `%g`, `bool(string)` accepts the Go
spellings; `OptOptimize` may fail Program() on a bad regex pattern, as documented; the Pratt
parser's error messages and positions; map iteration order.

## Not tested

The extension libraries (strings, math, lists, sets, encoders, protos), protobuf message
types and enums, timestamps and durations, `has()` and the optional syntax beyond parsing,
cost estimation and tracking, partial evaluation with `PartialVars` and unknowns, the policy
compiler, the interpretable decorators and `Program.ContextEval`.

## History

- 2026-09-22: new target, three properties, 9 bugs.
