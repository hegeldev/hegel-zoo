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

## Bugs

Eight, in `bugs.toml`: a double-quoted value spelling a JSON pointer is read as a selector and
loses its slash (1, high); a collection expression cannot be an operand of `and`, `not` or the
left of `or` without parentheses (2, medium); `in` over an interface slice holding a nil panics
(3, high, crash); `\"` cannot appear in a double-quoted string (4, low); a number right before
`}` is an invalid number literal (5, low); `is nil` on a Go array panics (6, low, crash); `in`
errors at a nested slice or map element unless an earlier element matched (7, low); the
same-name binding check runs only when the collection has elements (8, low).

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
