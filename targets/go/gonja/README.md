# gonja

[nikolalohinski/gonja](https://github.com/nikolalohinski/gonja) (MIT), pinned at `e3fe5ef` (v2.9.0
plus seven commits, 2026-09-12): a Jinja2 template engine for Go, aiming at Python Jinja2's syntax
and semantics - expressions, filters, tests, control structures, macros, whitespace control,
Python's str/int/float/list/dict methods and `str.format`.

The patch adds the `hegel.dev/go/hegel` requirement to `go.mod` and five test files at the module
root (package `gonja_test`; upstream's own tests are Ginkgo suites in `tests/`): `hegel_test.go`
(plumbing, the `Known` gates), `hegel_gen_test.go` (typed generator of contexts, expressions and
templates), `hegel_oracle_test.go` (the Jinja2 child process), `hegel_props_test.go` (the
properties) and `hegel_pins_test.go` (sixty-six pins). **Needs `python3` with the `jinja2`
package on PATH**: Jinja2 3.1 is the second implementation, one process per `go test`, batches of
templates as JSON lines. The whole run takes a few seconds.

## Properties

| Test | Checks |
|---|---|
| `TestHegelExpressionsAgreeWithJinja` | `{{ e }}` for typed expressions - int, float, string, boolean, list and dict literals and context variables; arithmetic with `//`, `%`, `**`; `~`; comparisons, `in`, `and`/`or`/`not`, conditional expressions; the built-in tests; filters (`abs`, `int`, `float`, `round`, `length`, `sum`, `min`, `max`, `first`, `last`, `join`, `sort`, `unique`, `select`/`reject` with tests, `map`, `list`, `string`, `tojson`, `upper`, `lower`, `capitalize`, `trim`, `replace`, `indent`, `truncate`, `reverse`, `format`, `filesizeformat`, `default`, `e`/`escape`/`forceescape`/`safe`); slices and indexes; Python str methods (`upper`, `lower`, `strip`, `zfill`, `ljust`, `rjust`, `replace`, `removeprefix`, `split`, `partition`, `splitlines`, `join`, `find`, `startswith`, `endswith`, the `is...` predicates, `format` with Python's spec mini-language) - renders the same text as Jinja2 over the same context. |
| `TestHegelTemplatesAgreeWithJinja` | Templates with text, prints, `if`/`elif`/`else`, `for` (over lists, ranges, strings, dicts and `.items()`, with `if` filters, `loop.*`, `break`/`continue`, `else`), `set` (incl. block set), `with`, `filter` blocks, `raw`, comments and `{%-`/`-%}`/`{{-`/`-}}` under random `trim_blocks`, `lstrip_blocks` and `keep_trailing_newline` settings render the same text. |
| `TestHegelMacrosAgreeWithJinja` | Templates defining macros (positional and default arguments, `caller()` with `{% call %}` blocks) and calling them render the same text. |
| `TestHegelOracleVersion` | The oracle is Jinja2 3.x. |
| `TestHegelPin...` | One plain test per recorded bug. |

A case where Jinja2 itself raises is skipped (the generator aims at valid templates; the
library's leniency - `3 / 0`, `'a' + 1`, `4 is divisibleby 0`, `none|length` - is not judged).
Also not judged, because the library documents the difference or the reference is a CPython
detail: the `format` filter takes Go's Sprintf syntax (`%s` of an integer prints `%!s(int=1)`),
so only `%s` of strings and `%d` of integers are generated; escaping is applied immediately with
no Markup type, so `e`/`escape`/`forceescape`/`safe` are only the last filter of a printed
expression (Jinja2's `"a<b"|e + "<"` escapes the other operand and a later `|e` leaves Markup
alone) and `tojson` output is never re-escaped; tuples print as lists (`(1, 2)`, `partition`,
`items`); `is sameas` on strings (interning); integers beyond 64 bits and `float ** n` beyond
squaring (Go's `Pow` rounds twice for `** 3`); `|first` of an empty string (Undefined in
Jinja2); Jinja2's own for-`else` quirk (the `else` block runs when the last iteration ended in
`break` or `continue`); a lone `{#` at the end of a template (text for Jinja2, an unclosed comment
here); non-standard methods (`capwords`) and methods the README lists as unsupported.

## Bugs

Sixty-six, see `bugs.toml`. Arithmetic and types: `//` and `%` truncate for negatives (1) and
return ints for floats (2); `int ** int` is a float (3); None prints as nothing (4); `not 0` is 1
(5); `[1] * 2` and `2 * 'x'` are 0 (6); booleans are not numbers (29); None and undefined are
conflated (30); `range()` is a one-shot channel (13). Precedence and parsing: tests apply to the
whole arithmetic expression (18); `in` with a filtered right operand (19) or a non-primary right
operand (20); conditionals inside parentheses or brackets (23); `- -6` (24); chained tests (25);
methods on parenthesised expressions (26); adjacent string literals (54); `not not x` (56);
`{% call %}` inside any block (55); extra macro arguments (51). Filters: `items`/`dictsort` empty
(7); `tojson` spacing (8), non-ASCII (9) and integral floats (63); dict iteration order (10);
`round` halves (11), ints (12) and `-0.0` (64); `|reverse|list` (16); `center` bias (36);
`wordwrap` (37); `wordcount` (38); `float` and whitespace (39); `title` (47); `urlencode` (48);
`striptags` (49); `pprint` (50); `sum(start=[])` (53); `truncate` at whitespace (66). Tests:
`upper`/`lower` on uncased strings (21); `odd`/`even` on negatives and floats (22); `escaped`,
`filter`, `test` erroring (27); `sequence` (28); `true`/`false` by truthiness (31); `gt` on strings
(32). Str methods: results compare unequal to their value (17); `split` maxsplit (14); `ß|upper`
(15); `count` (33); `find` with start (34) and on `''` (57); optional arguments rejected (35);
byte-based indexing, reverse, zfill and iteration (40); list repr escaping (41); `str.format`
conversions (42), grouping (43), brace escapes (44), floats (45) and None/lists (46); `zfill('')`
panics (58); `istitle` (61); `''.endswith` (62); index `-len` empty (60). Templates: `loop.depth`
(52); `-}}` after a newline (59); `lstrip_blocks` stripping blanks anywhere on the line (65).
