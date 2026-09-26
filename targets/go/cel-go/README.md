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
- Eleven narrow properties in `hegel_zoo_shapes_test.go`, one per recorded bug, each a
  generator over the bug's shape region with random contents judged by the same oracle
  (`TestHegelPrattLexesLiteralBeforeIn`, `TestHegelMapLiteralRepeatedKeyIsAnError`,
  `TestHegelFoldingKeepsLiteralPredicateMacros`, ...): the deterministic expected failure of
  each bug.
- `TestHegelPin…`: one pin per recorded bug (expected failures).

A case is data: the variables' values, a typed expression tree drawn from a grammar built once
per depth bound (`weighted` choices with the plainest alternative first, a forward-declared
table of expression generators, a leaf at the bound), and a tape of spelling choices
(whitespace, parentheses, literal spellings) recycled modulo its length, the empty tape being
the plainest text; a pure model evaluates the tree and a pure renderer writes it. Keys,
needles and substrings are positions resolved modulo the live size; macro cases are templates
over the loop variable.

## Bugs

Eleven, recorded in `bugs.toml`. The Pratt parser rejects a numeric literal glued to `in`
(cel-go/1) and records different offsets for negative literals, leading-dot identifiers and
message literals (2); the ANTLR parser ends a string or bytes literal's range after its byte
length, so a literal with a non-ASCII character is recorded too long (10); the Pratt parser
rejects an empty list, map or message literal written with a lone comma, `[,]`, which the
grammar and the ANTLR parser accept (11). The checker binds the type variable of an empty literal's element to the
first overload tried, so `-({}['a']) + 1` fails to check (3). Errors dropped: `OptOptimize`
and constant folding make `e in []` false, folding makes `x in [x, e]` true (4). A map literal
with a repeated key evaluates to a map instead of an error (5). `OptOptimize` fails Program()
on a constant unary call that errors in an untaken branch (6). Constant folding fails on a
pruned conditional whose ids collide with later nodes (7), unparses NaN and the infinities
as `NaN.0`, `+Inf.0`, `-Inf.0` (8), and gives a stray value for a macro whose literal
predicate leaves the accumulator unchanged (9).

## Known shapes

The shapes of the recorded bugs are drawn by default (STYLE.md rule 11): numeric literals
glued to `in`, negative literals, elements of empty literals as operands, `in` over an erroring
operand, repeated map keys, erroring constant unaries in untaken branches, pruned conditional
branches under folding, non-finite folded doubles, literal predicates, non-ASCII text literals
and lone commas in the parser comparison. A mismatch names the bug whose shape it has (the
`Known` switches keep the shape tests) and the property fails: the three wide properties in
most runs (their shapes are a few percent of cases and hegel's size ramp reaches repeated-key
maps rarely at 100 cases, so they are intermittent; `TestHegelEval` lands on cel-go/5, /8 or
/3, `TestHegelMacros` on /5, `TestHegelParsers` on /2 or /1), and each narrow property on its
own bug. `HEGEL_NO_KNOWN=1`, read once, switches the known shapes off: the generators draw the
neighbouring regions instead (a space before `in`, positive literals, one-entry literals,
distinct keys, ASCII text, no lone comma), a mismatch with a known shape is skipped or, for one
check among several, tolerated and counted (under one percent of cases), and every property
passes.

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
- 2026-09-26: generators rewritten in combinator style (a case is data: tree, tape, values);
  the known shapes are drawn by default and eleven narrow properties, one per bug, are the
  expected failures beside the pins. Two more parser discrepancies the freed comparison met,
  recorded as cel-go/10 (the ANTLR parser's literal ranges end in bytes; it had been tolerated
  as cel-go/2) and cel-go/11 (the Pratt parser rejects a lone comma).
