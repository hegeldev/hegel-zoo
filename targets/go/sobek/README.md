# sobek

[grafana/sobek](https://github.com/grafana/sobek) (MIT), pinned at `8a431c4` (2026-09-15, main, untagged):
k6's JavaScript engine, a fork of dop251/goja (the zoo's `go/goja`) that merges goja regularly and
adds experimental ES modules, source maps and the changes k6 needs - an ECMAScript 5.1+ engine in
pure Go with most of ES2015-ES2023. Its readme documents the same caveats as goja's (JSON.parse of
invalid UTF-8, Date on an int overflow); its CLAUDE.md is architecture notes, not a policy.

The patch is goja's harness with the module and package renamed: `hegel.dev/go/hegel` in `go.mod`
and six test files at the module root (package `sobek_test`): `hegel_test.go` (plumbing, the `Known`
gates), `hegel_gen_test.go` (the program generator, the early-error list), `hegel_probes_test.go`
(fixed probe programs), `hegel_oracle_test.go` (the reference engine as a child process, the shared
value serialiser), `hegel_props_test.go` (the properties) and `hegel_pins_test.go` (thirty-eight
pins). **Needs `node` (the reference JavaScript engine; Node 22 was used) on PATH**: one process per
`go test`, fed a small driver that compiles each program as a function body in a fresh `vm` context
with a five-second timeout and prints its result, or the kind of error, in a canonical form; the
serialiser is one piece of ES5 JavaScript run in both engines. Run with
`go test -vet=off -count=1 -v .` (Go 1.27's vet rejects format strings in upstream's own
`modules_test.go`); the whole run takes about a minute.

## Properties

| Test | Checks |
|---|---|
| `TestHegelRunAgreesWithNode` | A generated program (one to three per case) - numeric, string, boolean, array, object and function expressions over the operators with their precedences, template literals, regexp literals with every flag, `Math`, `JSON`, `Number`/`String`/`Array`/`Object` methods, `Date.UTC` and the UTC getters, `parseInt`/`parseFloat`, `typeof`/`instanceof`/`in`/`delete`, spread, compound and logical assignment, IIFEs and arrows, `let`/`const`/`var` with block scoping, `if`, bounded `for`/`while`/`do`, `for-in`/`for-of`, labelled `break`/`continue`, `switch`, `try`/`catch`/`finally`, functions and generators with destructured parameters, classes with fields and methods, destructuring assignment; one program in five is mangled (a character dropped, a token inserted, two characters swapped, a line duplicated, a keyword replaced) or taken from a list of about four hundred programs around the early errors of the specification - compiles and runs in sobek (`sobek.Compile` + `RunProgram` under a ten-second interrupt) to exactly the value node returns, or fails on both sides at the same stage (compile or run) with the same error name. A Go panic or a hang is a failure outright. |
| `TestHegelProbesAgreeWithNode` | Forty-four fixed programs over the corners of the language - number formatting, `parseInt`/`parseFloat`, the coercions, comparisons, array methods, property order, `JSON`, the string methods, case mapping, `trim`/`pad`/`split`/`replace`, regexp `exec`/`test`/flags/lookbehind/named groups/backreferences, `Date`, Map/Set/WeakMap, Symbol, BigInt, ToPrimitive, `normalize`, `String.raw`, `%`, `**`, bitwise operators - agree in the same way. |
| `TestHegelOracleVersion` | The oracle is node and the shared serialiser prints a sample value the same way in both engines; a syntax error and a thrown error are reported at the right stage. |
| `TestHegelPin...` | One plain test per recorded bug. |

Not judged: the same as for `go/goja` - features the engine does not implement (the regexp `d` and
`v` flags, async iteration, `WeakRef`/`FinalizationRegistry`, the Iterator helpers, `groupBy`,
`Array.fromAsync`, `isWellFormed`/`toWellFormed`, `Promise.withResolvers`, symbols as WeakMap keys,
the JSON.parse reviver context, `Intl`, the Annex B leftovers), the reference being behind or off
the specification, and what the specification leaves to the implementation (Date strings off the
Date Time String Format, transcendental `Math` and `**` with fractional operands, `toString(radix)`
of a fraction, the time-zone name, error messages and `stack`, the escaping of `/` in
`RegExp.prototype.source`, the JSON.parse surrogate caveat).

Thirty-seven bugs are recorded in `bugs.toml`, every one of them shared with goja at 793a2a6
(the twenty-eight pins ported from `go/goja` all fail at this commit; the two engines are two days
apart and the fork merges upstream regularly): eight crashes of the Go process (`Array.from({length:
2}, String)` dereferencing a nil pointer, 35; `replaceAll` with an
empty search string on a string holding a non-ASCII character eating memory until the runtime
dies, 28 - found in the fork's rounds first, once in 20000 cases, and present in goja too; a `break`
in the never-taken branch of a constant `if` inside a `try` inside a `for-in`, popping an empty
iterator stack when the `try` catches, 33;
`arguments` inside an arrow inside a function, 1; a constant-false `continue` in a `for-of`, 19;
`Object.fromEntries([[]])`, 20; the `\u{10FFFF}` escape, 23; an unterminated regexp class
swallowing the source, 18), right-associative relational operators (21), `delete (v++)` not
evaluating its operand (26), `delete new Set()` throwing (13), property escapes never matching with
the `u` flag (15), dropped empty global matches (16), `-5 * 0` being +0 (14), and the rest as in
goja's `bugs.toml`; and seven more found the same day in the fork's rounds and goja's alike: `\b`/`\B`
without the `u` flag counting é or Σ as word characters (29), `let` at the end of a line before
`return` being a SyntaxError instead of the identifier `let` (30), `setUTCMilliseconds` on a Date
before the epoch (31), JSON indentation after an empty `[]`/`{}` (32), an invalid regexp literal
being a SyntaxError only when evaluated (34), `String.fromCodePoint(-0)` throwing (36),
`BigInt.prototype` carrying a function's `name` and `length` (37). Rounds of 1500, 3000, 3000,
20000 and six of 10000 generated cases plus thirty-five
probes of the fork's own code (`Object.freeze`/`seal` on accessors, arrays, typed arrays and
proxies, `hasOwnProperty` on indices, symbols and proxies, `arguments` in constructors,
`new.target`, `import.meta`) found nothing else that is the fork's own: sobek at this commit
behaves as goja does on everything the harness reaches.
