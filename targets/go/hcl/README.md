# hcl

[hashicorp/hcl](https://github.com/hashicorp/hcl) (`github.com/hashicorp/hcl/v2`) is the HCL
configuration language behind Terraform, Vault, Nomad and Packer: the native syntax parser and
evaluator (`hclsyntax`: expressions, templates, `for`, splats, functions, heredocs), the JSON
syntax (`json`), the schema-driven structure API (`Content`, `PartialContent`, `JustAttributes`,
`MergeFiles`), static analysis (`ExprList`, `ExprMap`, `ExprCall`, `AbsTraversalForExpr`), source
ranges and the `hclwrite` surgical editor and formatter. MPL-2.0, pinned at `4932c14` (main
2026-09-17, "Merge pull request #824"; v2.25.0 is the last tag, 27 commits behind). The repository
has no CONTRIBUTING file and no AI policy; the zoo only records bugs.

## Build

`go test -count=1 -run TestHegel -v .` in the module root (package `hcl_test`). The patch adds
`hegel_test.go` (value model, generators, the `Known` gates), `hegel_expr_test.go` (the expression
model and evaluator, rendering, the expression properties), `hegel_config_test.go` (bodies, the
native and JSON spellings, the structure properties), `hegel_more_test.go` (static analysis,
PartialContent/MergeFiles, edits, positions) and `hegel_pins_test.go` (one plain test per bug),
and requires `hegel.dev/go/hegel v0.6.33` in go.mod. `HEGEL_TEST_CASES` sets the case count
(default 100; the properties run clean at 1000 in about 40 s).

## Oracles

- **An expression model**: a typed value model (null, bool, number as `big.Float`, NFC strings,
  tuples, lists, objects) and a generator of expressions — literals, variables, arithmetic and
  logic with the operators' argument conversions (`"5" + 1`, `"true" && x`), `%` with the dividend's
  sign, comparisons, conditionals (differing primitive types unify to string), indexing and legacy
  `x.0`, attribute access, `[*]`/`.*` splats, `for` tuple and object expressions (grouping `...`,
  filters, sorted object keys), tuple and object constructors, function calls (`upper`, `lower`,
  `strlen`, `length`, `max`, `min`, `abs`, `concat`, `join`, `keys`, `contains`, `element`, `range`
  with cty's list/tuple result types) and quoted templates with `%{ if }`/`%{ for }` directives and
  `~` strip markers. Each expression is evaluated by the model and spelled in native syntax with
  random spacing and parentheses, and as a JSON `"${…}"` string.
- **Expressions evaluate as the spec says**: `hclsyntax.ParseExpression(...).Value(ctx)` and
  `json.ParseExpression` agree with the model (cty type and value).
- **Variables are the free references**: `Expression.Variables()` root names are exactly the
  model's free variables, in both syntaxes.
- **Static analysis sees the syntax**: `ExprList`, `ExprMap`, `ExprCall` and `AbsTraversalForExpr`
  return the spelled elements, pairs, call and traversal steps (natively and in the JSON forms:
  arrays, objects, and native text in a string); `ParseTraversalAbs`, `TraverseAbs` and
  `hclwrite.TokensForTraversal` agree; computed indexes are not static traversals.
- **Native and JSON bodies agree**: generated configurations (attributes with comments, nested
  blocks with quoted and identifier labels, one-line blocks, `<<`/`<<-` heredocs with directives)
  are spelled both ways and `Content` with the model's schema gives the same attributes (values),
  blocks and labels.
- **PartialContent leaves the rest**: with a schema for part of the body, the content is that part
  and the remaining body holds exactly the rest (`Content`, `JustAttributes`); `hcl.MergeFiles` of
  a native half and a JSON half offers the whole.
- **Format changes only whitespace**: `hclwrite.Format` output has the same token sequence and
  parses to the same content; formatting is idempotent.
- **The writer agrees with Format**: `hclwrite.ParseConfig(src).Bytes()` equals
  `hclwrite.Format(src)` (Bytes formats by design), the writer's `Blocks()`/`Labels()`/
  `Attributes()` match the parsed structure and each attribute's tokens evaluate to its value.
- **Generated files read back**: files built with `hclwrite` (`NewEmptyFile`, `AppendNewBlock`,
  `SetAttributeValue`, `SetAttributeRaw`, `RemoveAttribute`, `RemoveBlock`, random edits) parse to
  the model's content; **edits on parsed files keep the rest**: the same edits applied to a parsed
  generated file, the result parsing to the edited model and staying in Format's form.
- **TokensForValue round-trips** every model value through `hclwrite.TokensForValue` and back.
- **Ranges point at the source**: attribute, expression, block, label and body ranges slice the
  source to the text they describe, and nest; **structure at position**: `AttributeAtPos`,
  `BlocksAtPos`, `OutermostBlockAtPos`, `InnermostBlockAtPos` and `OutermostExprAtPos` return the
  items whose ranges hold a random position.
- **Broken inputs never panic**: mutated files (deleted, duplicated, swapped and injected pieces)
  give diagnostics or parse, in `hclsyntax`, `json` and `hclwrite`.

## Bugs (5; details in bugs.toml)

| id | summary | severity |
|----|---------|----------|
| hcl/1 | `<<-` heredocs strip the common indentation from every line except whitespace-only lines, which keep theirs (`<<-END\n  x\n \nEND` is `"x\n \n"`) | low |
| hcl/2 | hclwrite `Labels()` omits a quoted label spelled with a template escape or with `$`/`%` beside other characters (`resource "a$" "b" {}` → `["b"]`) | medium |
| hcl/3 | hclwrite drops a comment between a block's type and its first label (`resource /* c */ "a" {}`) | low |
| hcl/4 | `JustAttributes` on the body `PartialContent` leaves reports the extracted blocks as "Unexpected block" (`Content` on the same body does not) | low |
| hcl/5 | hclwrite edits inside a one-line block write invalid HCL (`resource {}` + `SetAttributeValue` → `resource { b = true\n}`); upstream #687 | medium |

How they were found: hcl/1 by the native/JSON property (the model's dedent disagreed on a heredoc
with a whitespace-only line), hcl/2 and hcl/3 by the writer property (`Labels()` against the
parsed labels; `Bytes()` against `Format`), hcl/4 by the PartialContent property and hcl/5 by the
edits property on the first one-line block it met; all at 300 to 1000 cases, each reduced to a
one-line probe. hcl/5 is upstream issue #687 (2024-07-25, `AppendNewBlock` on `atlas {}`; a fix in
pull request #828 is open); the attribute case is new there.

Not bugs, noted: `hclwrite.File.Bytes()` formats its output ("a simple formatting pass") so the
writer is compared with `Format`, not the source; `"${x}"` with any spacing inside the braces is a
single interpolation and unwraps to the value, in native and JSON; identifiers may contain `-`
(`true_-"0"` is one identifier minus a string; the renderer keeps a space); a nested splat `x.*.*`
is rejected on purpose (v2.24), `(x.*).*` and `x[*][*]` are fine, and after `[*]` or `.*` further
`[i]`/`.attr` steps apply per element, so indexing the splat result needs parentheses; chained
legacy indexes `t.0.0` are rejected on purpose; a comment after a heredoc's opening marker is a
parse error (the grammar wants `Identifier Newline`); JSON block types, labels and attribute names
are literal (no template escapes) while JSON string values are templates; cty normalises every
string to NFC, so labels and strings compare under NFC; `range()` gives a list where `[…]` gives a
tuple and `keys()` a tuple, `concat` gives a list only when all arguments are lists; `x % 0` is `x`
in cty; a `~` strip marker that removes the only literal beside an interpolation leaves a single
interpolation, which unwraps; a literal `$` right before `${` spells the escape `$${`.

Gates while the bugs are open (`Known` in hegel_test.go): heredocs have no whitespace-only lines
(/1); quoted labels containing `$` or `%` are not generated for the writer property (/2); no
comment between a block's type and its first label (/3); `JustAttributes` is asked of a native
remainder only when no block was extracted (/4); the edits property spells every block multi-line
(/5). The properties run clean at 1000 cases.

## History

- 2026-09-17: created at `4932c14` with 5 bugs.
