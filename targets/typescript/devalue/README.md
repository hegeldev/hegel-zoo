# typescript/devalue — Rich-Harris/devalue (against JavaScript itself and structuredClone)

devalue is "like `JSON.stringify`, but handles" cycles, repeated references, `undefined`,
`NaN`, `-0`, RegExps, Dates, Map, Set, BigInt, ArrayBuffers and views, URL, Temporal and custom
types (~10M weekly downloads; SvelteKit's serialiser for load data and hydration). It has two
forms: `uneval` returns JavaScript that recreates the value, `stringify`/`parse`/`unflatten`
a JSON encoding, plus `stringifyAsync` for promises and pluggable operations for both sides.
The patch checks all of them against the language itself — indirect `eval` of `uneval` output,
`JSON.parse` of `stringify` output, `structuredClone` as a second implementation of the same
value space — through a canonical rendering that compares identity structure as well as
contents, and against the README; it pins 10 bugs.

## How it is built

No build: `index.js` re-exports plain ES modules from `src/`; the library has no runtime
dependencies. Hegel and `@js-temporal/polyfill` (devalue's devDependency; Node 22 has no
`Temporal`) are installed under `.hegel/` in one `npm install --prefix .hegel` so the target's
package.json and lock file stay untouched; the test installs the polyfill on `globalThis`.

## How it is tested

`hegel/hegel.test.mjs` runs under `node --test`; `hegel/hegel-zoo.mjs` is the zoo's shared
harness, `hegel/canon.mjs` the canonical rendering (objects labelled in depth-first order,
later references written as back-references, so shared references and cycles compare; -0,
NaN, bigints, boxed primitives, invalid Dates, holes, buffer identity and offsets of views,
null prototypes and class names all distinguished; tags rather than `instanceof`, so values
from another realm compare), `hegel/gen.mjs` the generators (the value kinds above, strings
with `<`, U+2028, quotes, controls and lone surrogates, object keys that are reserved words,
numeric or empty, arrays with holes in both of devalue's encodings, views over shared buffers,
Temporal values in several calendars and zones, and with `share` repeated references and
cycles).

| Property | What it checks |
|---|---|
| `TestHegelParseStringifyRoundTrips` | `parse(stringify(v))` and `unflatten(JSON.parse(stringify(v)))` equal `v`, identity structure included |
| `TestHegelEvalUnevalRoundTrips` | indirect `eval` and `new Function` of `uneval(v)` give `v` |
| `TestHegelRoundTripsAgreeWithStructuredClone` | both round trips equal `structuredClone(v)` on the value space it shares |
| `TestHegelOutputIsJsonAndSafeToEmbed` | `stringify` output is JSON (an array or a negative sentinel); neither output contains `<`, U+2028/2029 or a raw control character (the README's XSS mitigation) |
| `TestHegelOutputIsWellFormedText` | neither output contains an unpaired surrogate |
| `TestHegelStringifyAsyncMatchesStringify` | with random positions replaced by promises of their values, `stringifyAsync` output is JSON and parses to `v`; `stringify` refuses the same value |
| `TestHegelViewsOverAnyBufferRoundTrip` | typed arrays and DataViews over buffers whose length is not a multiple of the element size round-trip through both forms |
| `TestHegelBuffersSerialiseOnlyTheirBytes` | a Node `Buffer` comes back over a buffer of its own size, in output proportional to it |
| `TestHegelUnserialisableValuesReportTheirPath` | a function, Symbol, class instance, symbol-keyed or `__proto__`-keyed object at a random addressable position makes both forms throw `DevalueError` with the documented message, `value`, `root`, and a `path` that evaluates to the offender |
| `TestHegelReducersAndReviversRoundTrip` | custom classes through reducers/revivers, shared instances included, with `parse` and `unflatten` |
| `TestHegelUnevalReplacerRoundTrip` | the same through an `uneval` replacer |
| `TestHegelCustomOperationsBuildInAnotherRealm` | a descriptor-based `get` operation gives the same output; parse operations built from a `node:vm` realm give an equal value whose every object has that realm's prototypes |
| `TestHegelSparseArraysKeepTheirHoles` | arrays up to 5000 long with holes, in the hole and the sparse encodings, keep length and populated indices |
| `TestHegelLargeGraphsRoundTrip` | graphs with up to 70 000 values referenced twice (across the 65 534 parameter cutoff) round-trip through both forms |
| `TestHegelTaggedObjectsAreObjectsOrRejected` | a plain object with a `Symbol.toStringTag` is written as a plain object or refused |
| `TestHegelParseNeverPollutesPrototypes` | random flattened input in devalue's own encoding with `__proto__`/`constructor` keys, self-references, bad indices and lengths: `parse`/`unflatten` return or throw an Error, and no built-in prototype changes |
| `TestHegelUrlsRoundTrip` | URL and URLSearchParams (href, entries) |
| `TestHegelTemporalValuesRoundTrip` | Temporal values (`equals` where defined) |

`TestHegelPin…` are plain tests, one per bug in `bugs.toml`.

## Bugs

See `bugs.toml`: `stringifyAsync` writes `[object Promise]` when a promise resolves to a value
already serialised, e.g. two promises of the same number or string (1, high); a nested promise
resolving to `undefined`/`NaN`/`Infinity`/`-0` parses back as -1/-3/-4/-6 (2, high); a root
promise of a negative number gives `-35` instead of `[-35]` (3); `uneval` throws for a typed
array over a buffer whose length is not a multiple of the element size (4); `uneval` output
with about 61 000 to 65 534 repeated values overflows the stack when evaluated (5); placeholder
names reach `Map`/`Set`/`URL`/`NaN` past 113 000 repeated values and shadow them in the body
(6); a plain object tagged `Array` through `Symbol.toStringTag` becomes `[]` (7); unpaired
surrogates are written raw (8); `error.path` for a Map keyed by `undefined` or a bigint is
`.get(-1)`/`.get(["BigInt","5"])` (9); a pooled Node `Buffer` is serialised with its whole
8 KiB pool, other Buffers' bytes included (10).

## Notes

- Accepted as design and not recorded: `stringify` writes 64-bit-safe integers and every other
  number with `String()` and dedupes primitives by value; a `Date` is written by `toISOString`
  (an invalid one as `""`), a RegExp without `lastIndex`, a Node `Buffer` as `Uint8Array`, an
  Array subclass as `Array` (all as `structuredClone` does); an object is "plain" when its
  prototype is `Object.prototype`, null, or an object whose own property names match
  `Object.prototype`'s (cross-realm objects), so `Object.create(Object.create(null))` loses its
  inherited properties; `__proto__` keys are refused in both directions and `Symbol` keys
  refused; `unflatten` appends to the array it is given when a custom reviver meets a built-in
  payload; a reducer's falsy return means "no match" (README); a value with a `then` method is
  a thenable in both `stringify` (refused) and `stringifyAsync` (awaited); paths inside a Set or
  under an object Map key have no expression and stop at the container / say `.get(...)`;
  20 000 levels of nesting overflow the stack (as in `JSON.stringify`).
- The Temporal generator skips the `chinese` calendar: the polyfill's `toPlainMonthDay` throws
  "Unexpected leap month suffix" there, which is the polyfill's problem, not devalue's.
- 2026-09-18: base bumped 8ade61d0e70d → 58ad7452142f (2026-09-18, "chore: enforce formatting with Prettier (#195)"; 5.9.4); 7 bug(s) still reproduce; fixed upstream: devalue/10, devalue/5, devalue/8. 11 tests pass.
- 2026-09-20: base bumped 58ad7452142f → 80e75e7c08f6 (2026-09-19, "Version Packages (#203)"; 6.0.0); 7 bug(s) still reproduce. 17 tests pass.
