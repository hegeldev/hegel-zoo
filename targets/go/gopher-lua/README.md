# gopher-lua

[yuin/gopher-lua](https://github.com/yuin/gopher-lua) (MIT), pinned at `75f4976` (2026-04-01, one
commit past v1.1.2): a Lua 5.1 virtual machine and compiler in Go - lexer, parser, code generator,
VM, coroutines, and the base, string, table, math and coroutine libraries. Its readme calls it "a
Lua5.1 (+ goto statement in Lua5.2) VM and compiler".

The patch adds the `hegel.dev/go/hegel` requirement to `go.mod` and five test files at the module
root (package `lua_test`): `hegel_test.go` (plumbing, the `Known` gates), `hegel_gen_test.go` (the
program generator and a list of fixed probe programs), `hegel_oracle_test.go` (the reference
interpreter as a child process, the value serialiser), `hegel_props_test.go` (the properties) and
`hegel_pins_test.go` (seventy-two pins). **Needs `lua5.1` (the reference Lua 5.1 interpreter,
5.1.5) on PATH**: one process per `go test`, fed a small driver that runs each program under
`pcall` with an instruction budget and prints its results in a canonical form. Run with
`go test -vet=off -count=1 -v .` - Go 1.27's vet rejects upstream's non-constant format strings in
`RaiseError` calls. The whole run takes about half a minute.

## Properties

| Test | Checks |
|---|---|
| `TestHegelRunAgreesWithLua` | A generated Lua 5.1 chunk - numerals in every form, strings with escapes and long brackets, table constructors, arithmetic, concatenation, comparison and logical operators with the 5.1 precedences, locals and multiple assignment, `if`/`elseif`, numeric and generic `for`, `while`, `repeat`, local functions with bounded recursion, closures over loop variables, varargs, `select`, `unpack`, `pcall`/`error`/`assert`, metatables with every metamethod, the string library (`find`, `match`, `gmatch`, `gsub` with patterns, captures, `%b`, `%f`, anchors; `format` with every conversion; `rep`, `sub`, `byte`, `char`, `upper`, `lower`, `reverse`, `len`), the table library (`insert`, `remove`, `sort`, `concat`, `maxn`), the math library, `tonumber` with and without a base, `tostring`, coroutines (`create`, `resume`, `yield`, `wrap`, `status`), plus a syntax-mangling step and a list of fixed probe programs over the corners of the language - compiles and runs in GopherLua (`LState.Load` + `PCall` under a ten-second context) to exactly the values the reference interpreter returns, or fails on both sides at the same stage (compile or run). Error messages are not compared; error values that are not strings are. |
| `TestHegelConstantFoldingAgrees` | A literal expression returned directly (folded by the compiler) evaluates in GopherLua to the same value as the same expression built at run time through an identity function. |
| `TestHegelOracleVersion` | The oracle is Lua 5.1 and its serialiser agrees with the Go one on a sample value. |
| `TestHegelPin...` | One plain test per recorded bug. |

Not judged: GopherLua's documented Lua 5.2 extension (`goto` and `::labels::`), and the
reference's own C quirks: `strtod` accepting hexadecimal floats
and `inf`/`nan` in numeric strings and stopping at an embedded NUL, `tonumber` with base 16 taking a
`0x` prefix, an unfinished capture going unnoticed when no capture is pushed (`gsub("(", "x")`),
`%5%` in a format, `%s` of a string with an embedded NUL (`sprintf` stops there) and `%c` of 0
(an empty string, for the same reason), `%` of an infinite, non-integral or huge operand (the
5.1 formula `a - floor(a/b)*b` gives nan for an infinity, differs from `fmod` in the last bits
for `5 % 1.25e-3`, and loses the low digits beyond 2^53: the generator keeps both operands
integers below 2^31), a `-0` folded into a constant and then shared with every later `0` of the
same function (`-0x0 * f() + 0` is -0 in the reference: constants are looked up by value), what a
weak table (`__mode`) still holds when it is read back (the reference's collector may have run),
which spelling of a `-0`/`0` key a table keeps (one key, chosen by insertion history),
`table.sort` with an order function that is not a strict order (undefined by the manual; the
reference sometimes reports "invalid order function"), the platform spelling of nan, the order of `next`, the border chosen by `#` for a table with holes, `table.insert` at a
position outside the sequence, 2^53 as a `for` bound (`i + 1 == i`), and the last ulp of `^`
(Go's `math.Pow` rounds more than once for an integer exponent above 2 where glibc's `pow` is
correctly rounded: `1.7^10` differs in the seventeenth digit, so the generator keeps such powers
exactly representable).

Seventy-two bugs are recorded in `bugs.toml`. The gravest is not a crash: an error caught by
`pcall` closes every open upvalue on the stack, not only those above the `pcall`, so closures made
before it stop sharing their variables with the enclosing function (68: `local sh = 0 local f =
function() sh = sh + 1 return sh end pcall(error, "x") return f(), sh` gives 1, 0 instead of
1, 1). Ten are crashes or hangs: an error after many
tail calls builds a stack trace with one line per tail call and dies of memory (22); `a, b = b, a`
assigns `b` to both (23); a constant-false `if` with locals in its branches miscompiles what
follows it inside a generic `for` (36, 37) or a `repeat` (58: the loop stops after one iteration,
or never); a sparse integer key below 67108864 allocates an array up to it (38); resuming a
coroutine suspended in `return coroutine.yield()`, or a wrapped one with no arguments,
dereferences a nil pointer (46, 51), as does a yield inside pcall (55) and a generic `for` over
`(f() .. s):gmatch(p)` (64); a plain `find` with init past the end slices out of range (65). The
rest are divergences
from the reference in the libraries and the coercions: `string.format` is Go's `Sprintf` (8, 52, 59; `%c` of 255 is two bytes, 61),
`tostring` formats numbers Go's way (13, 44), `tonumber("1e2")` is nil (24) and `tonumber("-0")` is 0 (60), `{1, a = f()}` leaks
the value into the array part (27), `math.huge + 1` is the largest finite double (28), `gsub` with
a limit of 0 replaces everything (39), a frontier never matches at the ends (40), `table.concat`
clamps a start index past the end down to the last element (57), a failed `match` returns no
value rather than nil (62), an init past the end finds nothing where 5.1 clamps it (67), `gmatch` returns two values and its iterator cannot be called by hand
(63), the parser takes `{1,, 2}`, `;;`, `[[a[[b]]` and the ambiguous call syntax the reference
rejects (50, 66, 72, 35), weak tables are not weak (69: `__mode` is never read), `collectgarbage` returns
nothing for any option (70), `table.sort` of `{3, 1, 2, nil}` sorts the nil slot too and fails
(71), and so on.
