# typescript/msgpackr — kriszyp/msgpackr (against the MessagePack spec and @msgpack/msgpack)

msgpackr is "a fast MessagePack NodeJS/JavaScript implementation" (~24M weekly downloads; the
codec behind cbor-x's sibling, lmdb-js and Harper): `Packr`/`Unpackr` with record structures,
shared and persisted structures, streams, structured cloning, custom extensions and a dozen
encoding options. The patch checks it against an independent model of the MessagePack
specification, against @msgpack/msgpack 3.1.3 as a second implementation, and against its own
README, and pins 9 bugs.

## How it is built

No build: `node-index.js` (the Node entry, streams included) re-exports plain ES modules. The
library has no runtime dependencies; `msgpackr-extract`, the optional native addon, is not
installed, so the pure JavaScript string decoder runs (as in browsers and Deno). Hegel and
@msgpack/msgpack are installed under `.hegel/` in one `npm install --prefix .hegel` so the
target's package.json and lock file stay untouched.

## How it is tested

`hegel/hegel.test.mjs` runs under `node --test`; `hegel/hegel-zoo.mjs` is the zoo's shared
harness, `hegel/msgpack-model.mjs` the spec model (canonical smallest encoder, strict decoder
with every length checked, a `canonical()` rendering that distinguishes -0, NaN, bigints, Dates,
binary, Maps and objects), `hegel/gen.mjs` the value generators (boundary integers, doubles with
few significant digits, the whole Date range, strings at the str8/16/32 boundaries and with lone
surrogates, binary views into larger buffers, typed arrays, Sets, Errors, RegExps).

| Property | What it checks |
|---|---|
| `TestHegelCompatibilityModeWritesSpecMessagePack` | `useRecords: false` output decodes, with the spec model, to the value; never shorter than the smallest encoding (longer is counted, not failed: the spec only says SHOULD) |
| `TestHegelAgreesWithMsgpackJavaScript` | both implementations read @msgpack/msgpack's bytes to the same value; @msgpack/msgpack reads msgpackr's compatibility-mode bytes to the value |
| `TestHegelUnpackReadsSpecMessagePack` | the model's bytes (including float 32 and 64-bit integers) unpack to the value in records mode (maps as `Map`), compatibility mode (maps as objects) and `int64AsType: "auto"` |
| `TestHegelPackrRoundTripsValues` | 1–5 messages through one `Packr` under each option set (defaults, `structures`, `bundleStrings`, `variableMapSize`, `moreTypes`, `structuredClone`, `useRecords: false`, a `useRecords` predicate with `mapsAsObjects`) come back equal from the same `Packr` and from a fresh `Unpackr` |
| `TestHegelStructuredCloneKeepsIdentity` | shared references and cycles survive `structuredClone` |
| `TestHegelFloat32OptionsFollowTheirDocumentation` | `ALWAYS` gives `Math.fround`, `DECIMAL_ROUND` gives `roundFloat32`, `DECIMAL_FIT` is lossless, for non-integers below 2^31 in absolute value as the README says |
| `TestHegelRoundFloat32RoundsToTheFloat32Digits` | idempotent, within a float 32 digit of its argument, at most 8 significant digits |
| `TestHegelInt64AsTypeDecodesSixtyFourBitIntegers` | `bigint`/`number`/`string`/`auto` on the model's uint64/int64 |
| `TestHegelLargeBigIntOptions` | `largeBigIntToFloat`/`largeBigIntToString`/`useBigIntExtension`, and a `RangeError` without them, beyond 64 bits |
| `TestHegelUndefinedOptions` | `encodeUndefinedAsNil`, `skipValues: [undefined]`, and the default fixext 0 round trip |
| `TestHegelDatesRoundTrip` | the whole Date range with and without `useTimestamp32`; the model reads msgpackr's timestamps and msgpackr reads the model's; the smallest format is used |
| `TestHegelCopyBuffersDetachesBinaryFromTheInput` | `copyBuffers` |
| `TestHegelStringsAreUtf8AndRoundTrip` | str payloads are UTF-8; strings (with lone surrogates) come back well-formed |
| `TestHegelTypedArraysAreTheirBytesOrTheirType` | with `moreTypes` a view keeps its type and contents; without, it can only be the bin of its bytes |
| `TestHegelUnpackMultipleFindsEveryValueAndOffset` | `unpackMultiple` values, callback offsets and early stop, `unpack` with `start`/`end` |
| `TestHegelTruncatedOrExtendedInputIsRejected` | every strict prefix and one trailing byte throw |
| `TestHegelArbitraryBytesDecodeLikeTheSpec` | random bytes the model accepts (no extensions) unpack to the same value |
| `TestHegelSharedStructuresDecodeEveryEarlierMessage` | up to 45 shapes under `maxSharedStructures` 1–100: the final `structures` array decodes every message in a fresh `Unpackr` |
| `TestHegelPersistedStructuresSurviveARestart` | the README's `getStructures`/`saveStructures` protocol: a restarted `Unpackr`/`Packr` reads everything |
| `TestHegelSequentialMessagesDecodeInOrder` | `sequential` with `unpackMultiple` and one `Unpackr` |
| `TestHegelUseRecordsPredicateAndMapsAsObjects` | a `useRecords` function plus `mapsAsObjects`; a compatibility `Unpackr` reads the bytes |
| `TestHegelCustomExtensionsRoundTrip` | `addExtension` in the `pack`/`unpack` (a real ext, visible to the model) and `read`/`write` forms |
| `TestHegelStreamsDeliverEveryValue` | `PackrStream` → random re-chunking → `UnpackrStream` |
| `TestHegelBundledStringsRoundTrip` | `bundleStrings` with 1–60 strings of 1-, 2-, 3- and 4-byte characters |
| `TestHegelCoercibleKeysKeepTheirNames` | `coercibleKeyAsNumber` round trips numeric-looking keys |
| `TestHegelStreamsReportATruncatedTail` | an `UnpackrStream` whose input ends inside a message errors |

`TestHegelPin…` are plain tests, one per bug in `bugs.toml`.

## Bugs

See `bugs.toml`: typed arrays other than Uint8Array packed without `moreTypes` become bin of
garbage (1, high); `bundleStrings` corrupts bundles of multi-byte strings past 64 KiB (2, high);
lone surrogates written as WTF-8 (3); an invalid Date becomes a 1-byte timestamp no other decoder
reads (4); `UnpackrStream` ends quietly on a truncated message (5); `coercibleKeyAsNumber`
rewrites `01`, `1.0`, `1e2`, `' 1'`, `''` (6); the `useFloat32` bound is 2^32, not 2^31 as
documented (7); dates with seconds in [2^32, 2^34) use the 96-bit timestamp although the 64-bit
one holds them (8); `roundFloat32` returns float artefacts above 2^31 (9).

## Notes

- Design choices the properties accept: `-0` is written as the integer 0; integers from 2^32 up
  (and below -2^31) are written as float 64 rather than uint64/int64, and every bigint in the
  int64 range as a 9-byte int64; objects in compatibility mode are always map 16 (`de`) unless
  `variableMapSize`; the default `Packr` writes 64–127 as uint 8 because the fixint range 0x40–0x7f
  is reserved for record ids; a bare `Unpackr` decodes every map as a `Map`; the key `__proto__`
  is renamed `__proto_` on decode; `0xc1` decodes to the exported `C1` marker instead of an error;
  Sets, Errors, RegExps and record definitions use msgpackr's own framing (a fixext 1 followed by
  a separately encoded value), readable only by msgpackr; `moreTypes` also turns on the bigint
  extension; `toJSON` is honoured for class instances but not for plain objects; a `Map` with
  object keys cannot be written in compatibility mode ("Invalid property type for record");
  `UnpackrStream` delivers `Symbol.for(null)` for a nil message (Node object streams cannot carry
  `null`); `int64AsType: "auto"` works but is missing from `index.d.ts`. None of these is in the
  README; the last five would be worth a sentence there.
- `DECIMAL_ROUND` decodes a float 32 to at most 7 significant digits, which can differ from the
  float 32 actually stored (the option presumes the source had few digits); `roundFloat32` is
  checked for idempotence and closeness rather than for float 32 identity.
- The mutated/random-bytes property skips inputs containing extensions (the record extension
  0x72 changes how later bytes are read) and the key `__proto__`.
