# go/go-bexpr

Hegel property tests for [hashicorp/go-bexpr](https://github.com/hashicorp/go-bexpr), the
boolean expression evaluator behind Consul's and Nomad's API filters: a PEG grammar
(`grammar/grammar.peg`, compiled with pigeon) and an evaluator over Go data through
pointerstructure.

## Build

The patch adds a `hegel/` package; `go test -count=1 -run TestHegel -v ./hegel` needs nothing
beyond the module.

## Oracle

A model of the documented language: the grammar in `grammar/grammar.peg` for parsing, and for
evaluation the rules of `evaluate.go` (its comments), `grammar/ast.go`'s
`NotPresentDisposition` and the README. Generated expression trees are rendered to source with
random whitespace, grouping and spellings (dotted, indexed and JSON-pointer selectors; bare,
numeric, raw and quoted values; `x in s` and `s contains x`) and parsed back; generated
expressions over generated data (nested maps, slices, arrays, typed slices and maps, every
primitive kind, nils) are evaluated by the package and by the model evaluator, which computes
the set of outcomes an evaluation may have (a map is iterated in any order, so an element that
errors and one that decides may come in either order) and the package's outcome must be in it;
`Filter.Execute` over a few data must keep the elements that evaluate to true.

## Properties

- `TestHegelParse`: render, parse, compare trees.
- `TestHegelEvaluate`: `CreateEvaluator` + `Evaluate` against the model (value, error or panic);
  `CreateFilter` + `Execute` on a slice of data now and then.
- Nine narrow properties in `hegel_shapes_test.go`, one per bug, each over the bug's shape
  region with random contents and judged as `TestHegelEvaluate` judges:
  `QuotedPointerValueKeepsItsSlash` (1), `CollectionExpressionAsOperand` (2),
  `InSkipsNilElements` (3), `EscapedQuoteInDoubleQuotedString` (4),
  `NumberBeforeClosingBrace` (5), `IsNilOnArray` (6), `InSkipsNestedElements` (7),
  `SameNameBindingIsRejected` (8), `MatchesOnNilValueIsAnError` (9). Each fails on its bug;
  under `HEGEL_NO_KNOWN=1` it draws the neighbouring region (a raw-quoted pointer value, a
  parenthesised collection, a slice without nils, a string or a non-string value under
  `matches`, and so on) and passes.

## Bugs

Nine, in `bugs.toml`: a double-quoted value spelling a JSON pointer is read as a selector and
loses its slash (1, high); a collection expression cannot be an operand of `and`, `not` or the
left of `or` without parentheses (2, medium); `in` over an interface slice holding a nil panics
(3, high, crash); `\"` cannot appear in a double-quoted string (4, low); a number right before
`}` is an invalid number literal (5, low); `is nil` on a Go array panics (6, low, crash); `in`
errors at a nested slice or map element unless an earlier element matched (7, low); the
same-name binding check runs only when the collection has elements (8, low); `matches` and
`not matches` on a selector whose value is nil - an interface nil at any depth or a nil
pointer, as a map value or a struct field - panic where an int gives a clean "not convertible
to []byte" error (9, high, crash).

## Known shapes drawn by default

The nine `Known` switches are off by default (`HEGEL_NO_KNOWN=1`, read once, turns them
on): the generators draw every recorded shape as an explicit alternative at a modest rate (a
double-quoted value spelling a JSON pointer, a collection expression as an operand of `and`,
`not` or the left of `or`, `\"` in a double-quoted string, a number directly before `}`, a nil
in an interface slice under `in`, a Go array under `is nil`, nested elements under `in`, `as k,
k` over an empty collection, `matches` on a nil value - a nil scalar at any depth meets
`matches` from the operator table for a nil target or from the any-operator draw), the model
says what the documentation says, and a mismatch names the shapes the case has
(`mismatch(ht, shapes, ...)`; measured over 20000 cases, 14.5% of Parse cases and 13.6% of
Evaluate cases carry a shape, the collection-operand shape the largest at 7%). Over nine
default rounds `TestHegelParse` shrank to go-bexpr/1 seven times (4, 5 once each) and
`TestHegelEvaluate` to go-bexpr/3 five times (2 and 5 twice each); over the four rounds after
go-bexpr/9 was recorded Parse shrank to go-bexpr/1 twice (2, 5 once each) and Evaluate to
go-bexpr/9 twice (3, 4 once each), so the ninth shape shares Evaluate's basin and both
properties stay mapped plain to their plurality over all thirteen rounds (go-bexpr/1 nine of
thirteen, go-bexpr/3 six of thirteen); neither ever passed. Under `HEGEL_NO_KNOWN=1` the
switches steer the renderer off the shapes and make the model reproduce the behaviour as
before, and both wide properties pass (1000 cases; the only skips are the order-dependent
filter cases).

The generators are package-level values in combinator style (`hegel_model_test.go`): data as
depth-indexed towers (`scalars`, `intSlices`, `arrays`, `intMaps`, `valueTower(2)`,
`datums`), expressions as recipes (`targets`, `matchValues`, `matches`, `exprTower(3)`)
resolved against the datum by a pure `scope.resolve`, the source spelling as a `tape` of die
rolls read by a pure `render(n, tape)` that also reports the shapes it chose, and
`exprCases`/`evalCases` as Composites with `GoString()`. The old renderer parenthesised `and`
on the left of `or`; the grammar allows it bare, and it is now drawn bare too.

The model follows a pointer as `evaluateMatchExpression` does (`reflect.Indirect`, so a nil
pointer is the zero value like a nil interface) and reads an exported struct field by name as
pointerstructure does (a missing field is an error, the not-present disposition being for map
keys only); the wide generators draw no pointers or structs, the narrow property for
go-bexpr/9 does (a nil `*string` as a map value and as a struct field, beside the interface
nil at the top, under a map and in a slice).

## Modelled as recorded, not counted

- Coercion of a value to the target's kind uses the package's own rules (strconv with base 0:
  `n == "0x10"` and `n == "1_6"` are true for n = 16; `b == 1` and `b == T` are true for a true
  bool; `f32 == 1.50000001` is true for a float32 1.5); the model calls the same functions.
- Over a typed slice (`[]int`) a value that does not parse is an error, over a `[]interface{}` it
  is skipped: both are as the code is written, the model follows each.
- A missing key at the end of a path of two or more parts is "not present" and takes the
  operator's disposition; a missing top-level key, an out-of-range index and a path through a
  scalar are errors. The `_` placeholder and a binding name that is a keyword are grammar
  matters not exercised; identifiers that are keywords (`not == 1`) are avoided.
- Iteration over a map has no order: the model allows every outcome some order produces.

## History

- 2026-10-07: generators rewritten in combinator style; the eight known shapes drawn by default (both wide properties plain); eight narrow properties added; `matches` on a nil value counted as a candidate.
- 2026-10-07: the candidate recorded as go-bexpr/9 (`matches` on a nil value panics): a pin and a ninth narrow property, the model names the shape and reproduces the panic under `HEGEL_NO_KNOWN=1`, `matches` drawn for a nil target, the candidate counter and its assume removed.
