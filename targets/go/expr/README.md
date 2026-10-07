# expr

[expr-lang/expr](https://github.com/expr-lang/expr) is an expression language for Go: a
lexer, parser, type checker (`checker`), optimizer (constant folding, `in` on arrays and
ranges, `filter`/`map` fusions, `sum`/`count` specialisations) and a bytecode VM, with about
sixty builtins (string, number, array, map, conversion and date functions) and a small
grammar of literals, arithmetic, comparisons, `?:`/`??`/`if`, membership, slices, ranges,
pipes, predicates (`filter(arr, # > 1)`), `let` and `;` sequences. About 20 000 lines,
MIT, pinned at `4b31df3` (master 2026-07-07; v1.17.8 of 2026-02-14 is the last release).
README.md, SECURITY.md and LICENSE are the project documents and say nothing about
AI-written code. The package's own tests are example tables plus a Go fuzz test
(`test/fuzz`) with a 19 546-line corpus and a list of runtime errors it accepts.

## Build

`go test -count=1 -run TestHegel -v .` in the module root. The patch adds `hegel_test.go`
(the harness, the generators, the model and the ten wide properties), `hegel_shapes_test.go`
(one narrow property per bug) and `hegel_pins_test.go` (one plain test per bug) and
requires `hegel.dev/go/hegel v0.6.33` in go.mod (the `go` directive moves from 1.18 to
1.26). The upstream fuzz corpus and environment (`test/fuzz/fuzz_corpus.txt`,
`fuzz.NewEnv()`, `fuzz.Func()`) seed and host the self-consistency properties.

## Oracles

- **A Go model of the documented semantics** (`docs/language-definition.md`, the
  `vm/runtime` helpers' types): a typed generator builds int, float, string and bool
  expressions over variables (`i`, `k`, `f`, `s`, `t`, `arr`) with `+ - * % **`, unary
  minus, `abs/min/max/ceil/floor/round`, `int/float/string`, `len`, `count`, comparisons
  across int and float, `and/or/not`, `contains/startsWith/endsWith`, `in` on arrays and
  ranges, `?:`, `let`, and expects the model's value *of the model's Go type*: ints stay
  `int` (wrapping), `/` and `**` are always `float64`, `%` by zero is a runtime error.
- **The Go standard library** behind the builtins: `strings` for trim/trimPrefix/trimSuffix/
  upper/lower/split/splitAfter/replace/repeat/indexOf/lastIndexOf/hasPrefix/hasSuffix and the
  string operators (`len` counts runes), `encoding/json` for toJSON/fromJSON, `encoding/base64`,
  `strconv` for the conversions, `sort` for sort/sortBy.
- **The documentation's array functions** modelled over an int array with `# > k` and
  `# % m == r` predicates: all/any/one/none/map/filter/find*/count/sum/reduce/sort/sortBy/
  reverse/uniq/take/concat/flatten/first/last/min/max/mean/median/join, and the indexing
  rules (negative indices, `[a:b]` with either bound from the end, `a..b`, `in` on maps,
  `?.`, `??`, `get`, pipes).
- **Expr against itself**: the optimizer on vs off must compile alike and give the same
  value or fail alike; the checker's static type must be the kind of the value the program
  produces; `parser.Parse` → `Node.String()` → `parser.Parse` must give the same AST
  (`ast.Dump`); `AsInt/AsInt64/AsFloat64/AsBool/AsKind` accept exactly the documented
  kinds (numbers cast, others refused), `MaxNodes` counts what `ast.Walk` counts,
  `DisableBuiltin` removes a builtin, `AllowUndefinedVariables` makes unknown names nil;
  and upstream's own fuzz criterion — a mutated corpus line never panics in Compile,
  Disassemble, Dump or Run, and a program that compiled fails only with an error the fuzz
  test accepts.

## Known shapes drawn by default

A `Known` struct in `hegel_test.go` has one switch per bug shape, every one off by default:
the generators draw the shapes (`shaped(Known.x, on, off)` at the generator, `let` nodes
nested anywhere, integral float literals, finders and nil conditionals, the predicate builtins
in the DisableBuiltin loop) and `mismatch` names the bug whose shape the failing case has.
The wide properties reach the shapes at natural rates and are mapped intermittent:
PrintedAstReparses to expr/2 (fails about 15 rounds in 17 at the default case count),
StaticTypeMatchesRuntime to expr/1 (about 12 in 17), OptionsAreHonoured to expr/4 (about 1 in
17 at the default count, 4 in 5 at 1000 cases). `HEGEL_NO_KNOWN=1`, read once, turns every
switch on: the shapes are left out at the generators or assumed away where they are
recognised, the narrow properties draw the neighbouring region, and every property passes.
Four narrow properties in `hegel_shapes_test.go`, one per bug and named after what it tests
(`TestHegelNilResultsMatchTheirStaticType`, `TestHegelIntegralFloatLiteralsReparse`,
`TestHegelNestedLetsReparse`, `TestHegelDisableBuiltinCoversThePredicates`), each draw the
bug's shape region with random contents and are the deterministic expected failures beside
the pins.

Candidates, gated by `Assume` and reproduced standalone, to be judged and recorded: the
printer never parenthesises the operands of `..` (`(true ? 1 : 2)..3` prints as a different
AST, `(1 ?? 2)..3` as text that does not parse); a seedless `reduce` is typed as its
predicate but a one-element array returns the element; `min`/`max` are typed as their first
argument (`min(1, 0.5)` static int, runtime float64); `sum` of an empty array is int 0
whatever the element type; the optimizer folds `x and false` and `x or true` whatever x,
hiding a run-time error of x.

## Bugs (4; details in bugs.toml)

| id | summary | severity |
|----|---------|----------|
| expr/1 | static types never admit nil: `find`/`findIndex`/`first`/`last`/`get` are typed as the element type and `c ? nil : x` as x's type, but return nil — the documented-safe `output.(int)` panics | medium |
| expr/2 | `FloatNode.String()` prints `1.0` as `1`: the printed AST re-parses as an integer | low |
| expr/3 | a nested `let` or `;` sequence prints without parentheses: `1 + (let x = 1; x)` prints as `1 + let x = 1; x`, which does not parse | low |
| expr/4 | `DisableBuiltin`/`DisableAllBuiltins` leave the fifteen predicate builtins (filter, map, count, sum, sortBy, reduce, find, …) enabled | medium |

How they were found: the first 300-case round of the ten properties. The static-type
property tripped on `find(array, !ok)` (static int, runtime nil) and the array property on
`findIndex` of an empty array, which the probe generalised to every finder, `first`/`last`/
`get` and conditionals with a nil branch (expr/1); the print → parse property on `0.0`
(expr/2) and on a generated `(i + (let x = i; x + i))`, then a mutated corpus line with a
`;` sequence under `!` (expr/3); the options property on `count(arr, # > 0)` compiling under
`DisableBuiltin("count")` (expr/4; the parser consults its `predicates` table before
`config.Disabled`). Not bugs, noted: the lexer reads a literal's magnitude first, so
`-9223372036854775808` has no literal form (the generator uses `MinInt+1`); `len` of a
string counts runes while `s[a:b]` slices bytes (undocumented either way); `mean`/`median`
of an empty array are `0.0`; `fromPairs` builds a `map[any]any`; the `As*` numeric casts are
documented in `docs/configuration.md` (AsFloat64 casts ints too, beyond the "float32" the
docs mention). Under `HEGEL_NO_KNOWN=1` the properties run clean at 3000 cases.

## History

- 2026-10-07: generators rewritten in combinator style (the environment as a record, the
  typed expression grammar as depth-memoised weighted choices of node kinds realised and
  rendered by pure functions, corpus mutations as edit records applied modulo the live
  length, an evenly distributed corpus index composed from digits — `Integers` over 19 546
  lines put seven draws in ten into the first tenth, which is why the old test never left
  it); the known shapes drawn by default with four narrow properties. Three latent model
  faults fixed: a predicate over an empty array never runs its (erroring) bound; the optimizer
  folds a constant `% 0` into a compile error even in an untaken branch; `keys`/`values`/
  `toPairs` results were compared in map order (tolerated as multisets now). Five library
  bug candidates surfaced (above).
