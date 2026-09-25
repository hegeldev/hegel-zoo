# typescript/structured-clone — ungap/structured-clone (against the native algorithm)

`@ungap/structured-clone` is a `structuredClone` polyfill (~60M weekly downloads: pulled in by
`jsdom`, `@sveltejs/kit` and many others): `serialize(value)` turns a value graph into an array
of records that JSON can carry, `deserialize(records)` rebuilds it, the default export composes
the two (or defers to the native function where there is one), and the `json` entry point adds
`stringify`/`parse` with the `json`/`lossy` options that drop functions and symbols and honour
`toJSON`. The patch checks it against the implementation it polyfills — Node's own
`structuredClone`, V8's serializer — through a canonical rendering that compares identity
structure as well as contents, against the README's claims about JSON text and the lossy modes,
and against `JSON.stringify` for the json mode's `toJSON` contract; it pins 17 bugs.

## How it is built

No build: `esm/index.js` and `esm/json.js` are plain ES modules with no runtime dependencies
(the `cjs/` copy is generated). Hegel is installed under `.hegel/` with `npm install --prefix
.hegel` so the target's package.json and lock file stay untouched. Node 22 supplies the oracle.

## How it is tested

`hegel/hegel.test.mjs` runs under `node --test`; `hegel/hegel-zoo.mjs` is the zoo's shared
harness, `hegel/canon.mjs` the canonical rendering (objects labelled in depth-first order, later
references written as back-references, so shared references and cycles compare; -0, NaN,
bigints, boxed primitives, invalid Dates, holes and own array properties, buffer identity and
offsets of views, Errors by prototype/name/message/cause/errors, DOMExceptions — optionally views
by their elements alone), `hegel/gen.mjs` the generators (the value kinds the algorithm covers,
strings with controls and lone surrogates, keys that are reserved words, numeric, empty or
`__proto__`, Errors of every built-in kind with causes and odd names, DOMExceptions, views over
shared buffers, SharedArrayBuffers, objects with internal slots, plain objects with misleading
`Symbol.toStringTag`s, and with `share` repeated references and cycles), and `hegel/known.mjs`
the predicates that attribute a mismatch to a recorded bug from the shape of the value.

Two value spaces: `FULL`, the default space of every property, draws the shapes of every
recorded bug like any other value, so every property fails on them and the failure names the bug
(`shapesOf(v)`); anything without a recorded shape is a new bug. Under `HEGEL_NO_KNOWN=1` the
properties draw `CLEAN` (`JSON_CLEAN` for the json module), which leaves those shapes out, and
skip the rare value that still has one (a -0 after a +0, bug 17, about 2% of cases).

| Property | What it checks |
|---|---|
| `TestHegelCloneMatchesNative` | `deserialize(serialize(v))` equals `structuredClone(v)` (views by elements) — or both throw |
| `TestHegelCloneMatchesNativeEverywhere` | the same with the strict rendering (views by buffer, offset and length) |
| `TestHegelJsonRoundTripMatchesNative` | `parse(stringify(v))` of the json module equals `structuredClone(v)` |
| `TestHegelRecordsSurviveJsonText` | README: `deserialize(JSON.parse(JSON.stringify(serialize(v))))` equals `deserialize(serialize(v))` |
| `TestHegelLossyDropsFunctionsAndSymbolsLikeJson` | with functions and symbols inserted, `{ lossy: true }` equals `structuredClone` of the value with them removed as the README describes (properties dropped, array elements `null`, Map entries and Set elements dropped) |
| `TestHegelStrictRefusesFunctionsAndSymbols` | without options, a function or symbol anywhere makes `serialize` throw `TypeError: unable to serialize function|symbol`, and native `structuredClone` refuses the value too; without one nothing throws |
| `TestHegelJsonModeAppliesToJSONLikeJsonStringify` | with `toJSON` members inserted (returning a fresh value, a primitive, `this`, or not callable), `{ json: true }` equals `structuredClone` of what `JSON.stringify` would see |
| `TestHegelDeserializeReturnsOrThrowsAndNeverPollutes` | random records with bad indices, `__proto__`/`constructor` keys, error and regexp payloads: `deserialize` returns or throws an Error and no built-in prototype changes |

Seventeen narrow properties, one per bug in `bugs.toml`, draw that bug's shape region with random
contents (the shape bare or placed in an array, object, Map or Set among plain siblings) through the
same oracle and fail every run: `TestHegelSparseArraysKeepTheirHoles` (1),
`TestHegelArrayOwnPropertiesClone` (2), `TestHegelErrorCausesClone` (3),
`TestHegelAggregateErrorsCloneAsErrors` (4), `TestHegelErrorsNamedAfterGlobalsCloneAsErrors` (5),
`TestHegelDOMExceptionsCloneAsDOMExceptions` (6), `TestHegelUncloneableObjectsAreRefusedLikeNative` (7),
`TestHegelSharedArrayBuffersClone` (8), `TestHegelDataViewsOverPartOfABufferKeepTheirRange` (9),
`TestHegelRepeatedBufferReferencesCloneAsOneObject` (10), `TestHegelViewsOverOneBufferKeepSharingIt` (11),
`TestHegelTaggedPlainObjectsCloneAsPlainObjects` (12),
`TestHegelJsonModeNonCallableOrSelfToJSONLikeJsonStringify` (13), `TestHegelNullOptionsCloneLikeNative` (14),
`TestHegelJsonModuleKeepsNonFiniteNumbersAndBoxedNegativeZero` (15), `TestHegelBigIntArraysSurviveJsonText` (16),
`TestHegelNegativeZeroAfterZeroStaysNegative` (17); under `HEGEL_NO_KNOWN=1` they are registered skipped.
The wide properties fail every run too, each mapped to the bug it most often shrinks to.
`TestHegelPin…` are plain tests, one per bug in `bugs.toml`, kept as regression examples. `ZOO_TRACE=<file>` appends every
value the full-space property is about to clone, to find one that hangs.

Accepted differences, not recorded: `stack` is never compared (the polyfill's Errors get the
deserializer's stack); an Error's extra own properties (`code`) are dropped by both; Node's
`Buffer` clones as a `Uint8Array` in both; a `Proxy` cannot be told from its target in
JavaScript, so it is not generated; under `HEGEL_NO_KNOWN=1` the properties skip a value in which
a -0 follows a +0 (bug 17), the only recorded shape the clean generator cannot avoid without changing
the numbers it draws.

## Bugs

See `bugs.toml`. The one with teeth: **`deserialize` resolves record types and error names
against the global object** and constructs whatever it finds (5, medium, security): 26 bytes of
records allocate a gigabyte (`["Uint8Array", 2**30]`), `["WebSocket", url]` opens a connection
in Node 22+ and every browser, `["BroadcastChannel", "x"]` keeps a Node process alive, and no
crafted input is needed on the serialize side — an Error whose `name` is `"Array"` clones as
`["3"]`, `"Date"` as a Date, `"Uint8Array"` as an empty typed array. The deny-list of six names
(Function, Worker, eval, setTimeout, …) shows the intent; an allow-list is what the algorithm
specifies.

Silent wrong results against the native algorithm: a DataView over part of a buffer comes back
over the whole buffer, so it reads the wrong bytes (9, medium); holes become `undefined` (1);
arrays lose own properties such as a regex match's `index` and `groups` (2); Errors lose their
`cause` (3); an AggregateError loses its message and gains an `errors` list made of its
characters (4); a DOMException becomes a plain Error named Error, so `AbortError` checks fail
(6); a `-0` that follows a `0` anywhere in the value clones as `0` — the identity map is a
SameValueZero Map, so 1.4.0's negative-zero fix only covers a -0 seen first (17); two references
to one ArrayBuffer or DataView become two objects, a memoization typo (10); views over one
buffer stop sharing it (11). Refusals that should happen and do not: Promise, WeakMap, WeakSet,
WeakRef, boxed Symbol and `arguments` clone as `{}` (7). Crashes: SharedArrayBuffer (8), plain
objects whose `Symbol.toStringTag` says Array/Map/Set/Date/Int8Array (12), json mode's `toJSON`
handling (a non-callable `toJSON` throws, `toJSON() { return this }` overflows the stack) (13),
`serialize(v, null)` despite the nullable signature (14). The json module: NaN and the
infinities become null and the -0 of boxed Numbers and float arrays is lost (15); BigInt64Array
cannot be stringified (16, a documented limitation of the integer-array support, recorded as a
throw).

## History

- 2026-09-20: created against df3b152 (1.4.0); 17 bugs.
