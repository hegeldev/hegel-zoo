# typescript/superjson — flightcontrolhq/superjson (against JavaScript itself and structuredClone)

superjson "safely serializes JavaScript expressions to a superset of JSON, which includes Dates,
BigInts, and more" (~7M weekly downloads; the serialiser behind tRPC's and Blitz's data layers
and the Next.js `superjson` plugins). `serialize` splits a value into a JSON `json` part and a
`meta` part (type annotations by path, referential equalities by path); `deserialize` puts them
back together, `stringify`/`parse` wrap the pair in JSON, and a `dedupe` mode writes repeated
references once. Classes, symbols and custom transformers can be registered. The patch checks
all of it against the language itself — `JSON.parse`/`JSON.stringify` of the output,
`structuredClone` as a second implementation of the same value space — through a canonical
rendering that compares identity structure and Map/Set order as well as contents, and against
the README; it pins 12 bugs.

## How it is built

`src/` is TypeScript (ES modules) with one runtime dependency, `copy-anything`. The setup
installs Hegel, `copy-anything`, `typescript@5` and `@types/node` under `.hegel/` in one
`npm install --prefix .hegel` and compiles `src/` into `.hegel/dist` with `hegel/tsconfig.json`
(upstream's tsconfig plus `moduleResolution: bundler` and a `paths` entry for `copy-anything`'s
declaration file); the tests import `.hegel/dist/index.js`. The upstream tree and its lock file
stay untouched.

## How it is tested

`hegel/hegel.test.mjs` runs under `node --test`; `hegel/hegel-zoo.mjs` is the zoo's shared
harness, `hegel/canon.mjs` the canonical rendering (objects labelled in depth-first order, later
references written as back-references, so shared references and cycles compare; -0, NaN,
bigints, invalid Dates, Map and Set order, typed arrays by type and elements, Errors by name,
message, cause and own properties, class instances by constructor name, symbols by
description), `hegel/gen.mjs` the generators (the README's value kinds plus typed arrays,
registered classes and symbols and a custom transformer; object keys with dots and backslashes,
empty, numeric and reserved-word keys — the three superjson refuses by design excepted; Errors
with causes; with `share` repeated references and cycles).

| Property | What it checks |
|---|---|
| `TestHegelParseStringifyRoundTrips` | `parse(stringify(v))` and `deserialize(serialize(v))` equal `v` for every supported kind without sharing; `stringify` does not mutate its input |
| `TestHegelSharedReferencesAreRestored` | repeated references and cycles through plain objects and arrays |
| `TestHegelSharedValuesInSetsAndMapKeysAreRestored` | the same with Sets and Maps in the graph |
| `TestHegelSharedValuesInsideErrorsAndClassInstancesAreRestored` | the same with Errors and registered class instances |
| `TestHegelDedupeModeRoundTrips` | `dedupe: true` on plain graphs; the default instance reads a deduped payload |
| `TestHegelDedupeModeWithSetsAndMapsRoundTrips` | `dedupe: true` with Sets and Maps |
| `TestHegelDeserializeAgreesWithStructuredClone` | the round trip equals `structuredClone(v)` on the value space they share |
| `TestHegelSerializeOutputIsJsonAndMetaOnlyForSpecialValues` | `stringify` is `JSON.stringify(serialize)`; the output holds nothing JSON would change; a JSON-only value gets no `meta` and `json` equal to itself; `meta.v` is 1 |
| `TestHegelDeserializeInPlaceMatchesTheCopyingDefault` | `deserialize(payload)` leaves the payload untouched and equals `deserialize(payload, {inPlace: true})` |
| `TestHegelRegisteredClassesRoundTrip` | classes registered by name and by identifier, a custom transformer, instances with fields of every kind |
| `TestHegelAllowPropsKeepsOnlyTheListedFields` | `registerClass(C, {allowProps})` keeps exactly those fields |
| `TestHegelRegisteredSymbolsRoundTrip` | registered symbols (by description and by identifier) come back as the same symbols |
| `TestHegelErrorsRoundTripWithAllowedProps` | Errors (subclasses, causes, `allowErrorProps`) keep name, message, cause and the allowed props |
| `TestHegelTypedArraysRoundTrip` | all eleven typed-array kinds, subarrays, NaN/±Infinity/-0 elements |
| `TestHegelNodeBuffersRoundTrip` | a Node `Buffer` comes back with its bytes |
| `TestHegelDatesRoundTrip` | Dates over the whole range, invalid ones included, as values and Map keys |
| `TestHegelNestingAsDeepAsJsonStringify` | every depth `JSON.stringify` and `structuredClone` handle, superjson handles |
| `TestHegelHostilePayloadsNeverPollutePrototypes` | random payloads with `__proto__`/`constructor`/`prototype` paths, bogus annotations and bad references: `deserialize` returns or throws an Error and no built-in prototype changes |

`TestHegelPin…` are plain tests, one per bug in `bugs.toml`. The properties that are not about
superjson/6 skip (and count) inputs with two NaNs one of which is a Set element or a Map key.

## Bugs

See `bugs.toml`: restoring two shared values in one Set or two shared Map keys works by
position after the first restore has moved elements — elements lost, values on the wrong keys
(1, high); `dedupe` turns repeated references in Sets and Map keys into nulls that collapse (2,
high); restoring a shared Set element or Map key moves it to the end (3); shared references and
cycles inside Errors and registered class instances are not restored, cycles come back `null`
(4, high); referential equalities are applied in an order that loses the relinks recorded under
a first occurrence when the representative is a later, shorter path — `user.posts[0].author`
comes back `null` (5, high); NaN is tracked as a shared reference, which deletes a NaN-keyed Map
entry when another NaN exists (6); an invalid Date becomes `null` (7); `-0` in float typed
arrays becomes `0` (8); a Node `Buffer` serialises but cannot be deserialised (9); an anonymous
class or a description-less symbol is registered and ignored (10); depth 2000 overflows where
`JSON.stringify` handles 3000 (11); deserialized Errors gain own enumerable `name` and
allowed-prop properties (12).

## Notes

- Accepted as design and not recorded: keys `__proto__`, `constructor` and `prototype` are
  refused with an error on serialize and on deserialize; unregistered class instances, boxed
  primitives, DataViews and ArrayBuffers pass through `JSON.stringify` as they are (an
  unregistered instance's Date fields become strings and its Maps `{}`); unregistered symbols and
  functions vanish as in JSON; array holes become `null`; a null-prototype object comes back with
  `Object.prototype`; an Error subclass comes back as an `Error` whose `name` is the subclass name
  and whose `stack` is the payload's; a RegExp loses `lastIndex`; `registerClass` of two classes
  with the same name maps both to the last (the error message points to an upstream issue);
  bigints are tracked as identities too (harmless, since `1n === 1n`, but every repeated bigint
  gets a `referentialEqualities` entry); `deserialize` without `inPlace` deep-copies through
  `copy-anything`, which does not pollute on a `__proto__` key.
- `structuredClone` is the oracle for everything but URL, symbols and class instances; Errors are
  compared by name (structuredClone keeps the subclass, superjson only the name).
