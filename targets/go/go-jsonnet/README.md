# go-jsonnet

[google/go-jsonnet](https://github.com/google/go-jsonnet) (Apache-2.0), pinned at `567b61a` (the
v0.22.0 release, 2026-03-24): the Go implementation of the Jsonnet data templating language -
parser, desugarer, interpreter, the `std` library (part native, part `std.jsonnet`), the
manifesters, and `jsonnetfmt` (`formatter.Format`). Its readme states the goal: a feature-complete
implementation that passes the C++ implementation's test suites.

The patch adds the `hegel.dev/go/hegel` requirement to `go.mod` and five test files at the module
root (package `jsonnet_test`): `hegel_test.go` (plumbing, the `Known` gates), `hegel_gen_test.go`
(the program generator), `hegel_oracle_test.go` (the C++ implementation as a child process),
`hegel_props_test.go` (the properties) and `hegel_pins_test.go` (eighteen pins). **Needs `python3` with
the `jsonnet` package on PATH**: jsonnet 0.22.0, the C++ implementation at the same version as the
pinned go-jsonnet, is the oracle - one process per `go test`, batches of programs as JSON lines.
The whole run takes about a minute.

## Properties

| Test | Checks |
|---|---|
| `TestHegelEvalAgreesWithJsonnet` | A generated program - number, string (quoted, verbatim, text block, escapes), boolean, null, array and object literals; `local`s and functions with defaults, named arguments and `tailstrict`; bounded recursion; objects with hidden and `+:` fields, computed names, `self`, `super`, `$`, object-level locals and asserts, methods; array and object comprehensions; slices; the arithmetic, string, comparison, logical and bitwise operators, `in`, `if`/`then`/`else`; `%` formatting with every conversion; some eighty `std` functions with plausible and with mistyped arguments; `error`, failing asserts, unknown variables; external variables (`std.extVar`, strings and code) and top-level arguments - evaluates in go-jsonnet (`EvaluateSnippet`, which like the C++ `evaluate_snippet` makes the file name `std.thisFile`) to exactly the JSON the C++ implementation produces, or fails in both with the same kind of error (static or runtime). Error messages are not compared. |
| `TestHegelFormatPreservesMeaning` | `formatter.Format` with the default options formats every generated program that evaluates (or fails at runtime), is idempotent, and its output evaluates like the original in go-jsonnet and like the original in the C++ implementation. |
| `TestHegelOracleVersion` | The oracle is jsonnet at the same version as go-jsonnet. |
| `TestHegelPin...` | One plain test per recorded bug. |

Not judged, because the C++ implementation is the one that is wrong or that crashes: `$` inside a
comprehension at top level (`[{a: 1, d: $.a}.d for e in [1]]` is Unknown variable: $ in C++), an
object literal inside the computed field name of a `+:` field (C++ loses `self` for the whole
object), an object `local` in an object without fields (dropped before C++'s static analysis, so an
unknown variable in it goes unnoticed), NUL bytes in strings (the C++ `std.codepoint` stops at
them), a `!!str` YAML tag (ignored by C++'s `std.parseYaml`), `.5` in YAML and `1e400` in JSON
(`std.parseYaml`/`std.parseJson` abort the C++ process), `std.parseJson("-0")` (0 in C++, -0 in Go), the YAML dialect of `std.parseYaml` (`yes`, `y`, `~`, `0x1f` are strings in C++, values in Go), large counts (`std.repeat("a", 1e16)` exhausts the C++ process' memory), the Go-only `std.sha1/sha256/sha512/sha3`,
transcendental functions on inexact arguments (libm and Go's math package differ in the last bit),
and error messages (go-jsonnet words its own).

## Bugs

Eighteen, see `bugs.toml`. `std.parseInt` takes a leading plus (1) and loses the sign of `-0` (2);
`std.makeArray` takes a negative size (3) and a function with optional extra parameters (4);
`std.xor`/`std.xnor` reject non-booleans the C++ implementation compares (5); the YAML manifesters
turn a function value into nothing (6); a field separator other than `:` glued to a following
operator character does not parse (`{a:::-1}`, `{a::$.x}`) (7); the JSON and YAML manifesters
format numbers in the shortest form instead of `%.17g` (8); `std.length` of a function counts only
the required parameters (9); `std.reverse`, `sort`, `set`, `removeAt`, `minArray`, `maxArray` and
`sum` reject a string the C++ implementation treats as an array of characters (10); `std.sort`/`set`
apply `keyF` to a single element (11); `std.member`/`contains`/`remove`/`removeAt` force the needle
for an empty array (12); a shift result outside the safe integer range wraps, `1 << 63` (13); and a
`tailstrict` call of a function whose default parameter refers to an outer variable crashes with an
INTERNAL ERROR (14). jsonnetfmt strips one layer of parentheses per run (15); `std.removeAt` with an
index beyond the length crashes (16); `std.minArray`/`maxArray` return a single non-comparable element
(17); `std.splitLimit` rejects an empty separator the C++ implementation accepts (18).
