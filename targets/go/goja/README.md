# goja

[dop251/goja](https://github.com/dop251/goja) (MIT), pinned at `793a2a6` (2026-09-17, master, untagged):
an ECMAScript 5.1+ engine in pure Go - lexer, parser, compiler to its own bytecode, VM, and the
standard library up to most of ES2023 (classes, generators, destructuring, template literals,
Map/Set/WeakMap, Symbol, BigInt, Promise, Proxy/Reflect, typed arrays, the ES2018 regexp features).
Its readme says "Some of the AnnexB functionality is missing" and documents two caveats (JSON.parse
of invalid UTF-8, Date.UTC on an int overflow).

The patch adds the `hegel.dev/go/hegel` requirement to `go.mod` and six test files at the module
root (package `goja_test`): `hegel_test.go` (plumbing, the `Known` gates), `hegel_gen_test.go` (the
program generator, the early-error list), `hegel_probes_test.go` (fixed probe programs),
`hegel_oracle_test.go` (the reference engine as a child process, the shared value serialiser),
`hegel_props_test.go` (the properties) and `hegel_pins_test.go` (twenty-eight pins). **Needs `node`
(the reference JavaScript engine; Node 22 was used) on PATH**: one process per `go test`, fed a
small driver that compiles each program as a function body in a fresh `vm` context with a
five-second timeout and prints its result, or the kind of error, in a canonical form. The
serialiser is one piece of ES5 JavaScript run in both engines, so the two sides print values
identically: numbers via `Number.prototype.toString` with `-0` kept, strings escaped outside
printable ASCII, arrays with holes and extra keys, objects in own-key order, errors by name only,
dates by time value, regexps by source/flags/lastIndex, Map, Set, wrapper objects, functions by
arity, symbols, bigints, cycles. Run with `go test -count=1 -v .`; the whole run takes about a
minute.

## Properties

| Test | Checks |
|---|---|
| `TestHegelRunAgreesWithNode` | A generated program (one to three per case) - numeric, string, boolean, array, object and function expressions over the operators with their precedences, template literals, regexp literals with every flag, `Math`, `JSON`, `Number`/`String`/`Array`/`Object` methods, `Date.UTC` and the UTC getters, `parseInt`/`parseFloat`, `typeof`/`instanceof`/`in`/`delete`, spread, compound and logical assignment, IIFEs and arrows, `let`/`const`/`var` with block scoping, `if`, bounded `for`/`while`/`do`, `for-in`/`for-of`, labelled `break`/`continue`, `switch`, `try`/`catch`/`finally`, functions and generators with destructured parameters, classes with fields and methods, destructuring assignment; one program in five is mangled (a character dropped, a token inserted, two characters swapped, a line duplicated, a keyword replaced) or taken from a list of about four hundred programs around the early errors of the specification - compiles and runs in goja (`goja.Compile` + `RunProgram` under a ten-second interrupt) to exactly the value node returns, or fails on both sides at the same stage (compile or run) with the same error name. A Go panic or a hang is a failure outright. |
| `TestHegelProbesAgreeWithNode` | Forty fixed programs over the corners of the language - number formatting (`toString` with a radix, `toFixed`, `toPrecision`, `toExponential`), `parseInt`/`parseFloat`, the coercions, comparisons, array methods, property order, `JSON`, the string methods, case mapping, `trim`/`pad`/`split`/`replace`, regexp `exec`/`test`/flags/lookbehind/named groups/backreferences, `Date`, Map/Set/WeakMap, Symbol, BigInt, ToPrimitive, `normalize`, `String.raw`, `%`, `**`, bitwise operators - agree in the same way. |
| `TestHegelOracleVersion` | The oracle is node and the shared serialiser prints a sample value the same way in both engines; a syntax error and a thrown error are reported at the right stage. |
| `TestHegelPin...` | One plain test per recorded bug. |

Not judged: features goja does not implement (the regexp `d` and `v` flags, `Symbol.asyncIterator`
and async iteration, `WeakRef`/`FinalizationRegistry`, the Iterator helpers, `Map.groupBy`/`Object.groupBy`,
`Array.fromAsync`, `String.prototype.isWellFormed`/`toWellFormed`, `Promise.withResolvers`, symbols as
WeakMap keys, the JSON.parse reviver context, `Intl`, and the Annex B leftovers: `getYear`/`toGMTString`,
the String HTML methods, `__defineGetter__`, `08`/`08.5` numerals, `for (var i = 0 in {})`, HTML
comments, block-level function hoisting to the function scope); the reference being behind the
specification (a repeated group name across alternatives, `Error.isError`, `Uint8Array.fromBase64`) or
off it (V8 lists the accessor properties of an object literal that also has a spread after its data
properties: `Object.keys({...{}, get g() {}, x: 1})` is `x, g` in node; the generator does not mix the two);
and what the specification leaves to the implementation: Date strings not in the Date Time String
Format, `Math` transcendental functions and `**` with fractional operands (the generator keeps `**` to
small integer exponents), `toString(radix)` of a non-integer or of a number beyond 2^53, the
time-zone name in `Date.prototype.toString` (the generator returns no valid Date objects), V8's own
`arguments`/`caller` properties on sloppy functions, error messages and `stack`, the way `/` is
escaped in `RegExp.prototype.source`, and the documented JSON.parse surrogate caveat.

Twenty-seven bugs are recorded in `bugs.toml`. Five are crashes of the Go process: `arguments`
inside an arrow function inside a function is undefined, or an index out of range (1); `continue`
or `break` under a constant-false condition in a `for` loop with a `let`/`const` binding panics the
compiler, or makes it loop forever with a `while` in between (19: `for (const a of 'x') { if (false)
continue; }` at the top level of a script); `Object.fromEntries([[]])` dereferences a nil pointer
(20); the escape `\u{10FFFF}` in a string literal panics the parser (23); and a regexp literal
whose character class is not closed swallows the rest of the source (18, a SyntaxError in node).
Three are the parser or compiler getting the language wrong: relational operators associate to the
right, so `3 > 2 > 1` is true and `1 in {} in {}` throws (21); `delete` of anything that is not a
reference skips evaluating it, so `delete (v++)` leaves `v` unchanged (26); and `delete new Set()`
throws a TypeError (13). The regexp engine accounts for most of the rest: a Unicode property escape with the
`u` flag never matches anything (15: `/\p{L}/u.test('a')` is false), `match`/`replace` with a
global regexp drop an empty match after a non-empty one (16), `.` and `^`/`$` do not know `\r`,
U+2028 and U+2029 as line terminators (5), the `i` flag without `u` uses Unicode case folding so
the Kelvin sign matches `k` (22), invalid patterns are accepted with the `u` flag (9), duplicate
group names and quantified lookbehinds are accepted (10, 11), and a match result's keys come as
input, index instead of index, input (17), as a function's own keys come as prototype, length, name
(27). Numbers: `-5 * 0` is +0 (14), `parseInt('-0')` is +0
(3), `ToInt32` of 2^63 or more is 0 (7), `'\u00A0' == 0` is false and `Math.trunc('\u00A0')` NaN
while `Number('\u00A0')` is 0 (24), `JSON.parse('1e400')` throws (12), extended ISO years are
printed short (4). Strings: a lone surrogate becomes U+FFFD in `toUpperCase`/`toLowerCase`/`normalize`
(6). Syntax: legacy octal escapes pass in strict mode (2), a labelled function declaration is
rejected (8), a `'use strict'` directive after a rest parameter is accepted (25).
