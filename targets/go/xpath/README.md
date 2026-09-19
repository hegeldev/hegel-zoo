# xpath

[antchfx/xpath](https://github.com/antchfx/xpath) (MIT), pinned at `551dd37` (v1.3.8 plus twelve
commits, 2026-09-16): the XPath 1.0 engine behind htmlquery, xmlquery and jsonquery, evaluating
compiled expressions over any tree that implements its `NodeNavigator` interface - all thirteen
axes, node tests, predicates, the core function library, the `|`, comparison, arithmetic and
boolean operators, plus extensions (`lower-case`, `ends-with`, `matches`, `replace`, `reverse`,
`string-join`, sequences).

The patch adds the `hegel.dev/go/hegel` requirement to `go.mod` and six test files (package
`xpath_test`): `hegel_test.go` (plumbing, the `Known` gates), `hegel_doc_test.go` (generated XML
documents and a `NodeNavigator` over them with the data model's string-values), `hegel_gen_test.go`
(a typed expression generator: node-set, number, string and boolean grammars), `hegel_oracle_test.go`
(the lxml child process), `hegel_props_test.go` (the three properties) and `hegel_pins_test.go`
(eighteen pins). **Needs `python3` with the `lxml` package on PATH**: libxml2's XPath is the second
implementation. The whole run takes about a second; the library's own tests run in the same
`go test`. The pinned upstream fails `go vet` with the current toolchain (non-constant format
strings), so the command runs with `-vet=off`.

## Properties

| Test | Checks |
|---|---|
| `TestHegelEvaluateAgreesWithLxml` | Expressions of the shared XPath 1.0 subset (every axis, name/`*`/`node()`/`text()`/`comment()` tests, predicates with numbers, `position()`, `last()`, node-sets and booleans, filters `(expr)[pred]`, unions, the core functions, comparisons, arithmetic with `div`/`mod`, `and`/`or`) over generated documents (elements, attributes, text with numeric and non-ASCII values, comments) evaluate to the same typed value in the library and in libxml2, with the document element as the context node: node-sets as sets of nodes (the document node dropped, as lxml never returns it), numbers NaN-aware, strings and booleans exactly. Both parsers must also see the same tree. |
| `TestHegelSelectAgreesWithEvaluate` | For node-set expressions including the extensions: `Expr.Select`, a second `Select`, the deprecated `xpath.Select`, `MustCompile`, the iterator from `Evaluate` and a recompiled expression return the same nodes in the same order, `String()` is the source, and `count()` is the number of distinct nodes. |
| `TestHegelPositionalPredicates` | `(expr)[i]` is the i-th node of `expr` in document order (and, once the bugs are fixed, `[last()]`, `[position() > i]` and `[position() <= i]` the tail and head). |
| `TestHegelOracleVersion` | The oracle is lxml 5 or 6. |
| `TestHegelPin...` | One plain test per recorded bug. |

Not judged, because libxml2 and XPath 1.0 differ or the library's choice is legitimate: the
document node is never in lxml's results, so the generator uses the document element as the
context and drops the root from node-sets; number-to-string conversion (libxml2 prints 15
significant digits with exponents, so numbers reach `string()` only when integer-valued); libxml2
accepts `1e2` as a number where XPath 1.0 does not, and parses large exponents inexactly (so no
exponent text and nothing beyond 2^53 reaches `mod`); iteration order of node-sets is not compared
directly, only through `(expr)[n]`; `position()` and `last()` outside a predicate (lxml raises).
The rare shapes matter: CI hit `name(/b | /.)` at the default case count after three local rounds
of 3000 had passed, so the generator is now checked with a dozen rounds of 4000 before a commit.

## Bugs

Twenty-three, see `bugs.toml`: comparing a boolean with another type panics and boolean =
boolean is false (1); trailing tokens after an expression are silently dropped, so `3 div-1` is 3
(2); `sum()` skips non-numeric values instead of returning NaN (3); `substring` with a NaN start
panics (4); `string-length()` needs an argument (5); parent, ancestor, sibling and self steps
after `//` return duplicate nodes (6); `position()` and `last()` in a filter predicate count
siblings, not the filtered set (7); every attribute is at position 1 (8); `@k/@n` selects the
element's other attribute (9); `substring-after(s, '')` is empty (10); `(x)[p][q]` followed by an
operator or `)` fails to parse (11); `last()` is empty and `position()` counts document order on
non-child axes (12); unions keep operand order, so `(b | a)[1]` and `name(b | a)` are wrong (13);
`number()` accepts Go float syntax (14); a step predicate evaluated in one argument moves the
context node for the next (15); a descendant path with a predicate or a further step is out of
document order (16); `boolean(NaN)` is true (17); `descendant-or-self::x/y` ignores the node test
x (18); `x[2.5]` is `x[2]` (19); `last()` in a second predicate is empty and non-child steps
miscount their second predicate (20); `substring()` rounds halves away from zero (21); a filter
over a reverse axis keeps nearest-first order, so `(ancestor::*)[1]` is the nearest ancestor (22);
`position()` and `last()` after a path in the same predicate lose their context (23).
