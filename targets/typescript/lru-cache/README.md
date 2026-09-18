# typescript/lru-cache — isaacs/node-lru-cache (against a model of its documentation)

lru-cache is "a cache object that deletes the least-recently-used items": `max` entries, or a
`maxSize` of calculated sizes, optionally a `ttl` with stale-item rules, `dispose`/`onInsert`
callbacks, `dump`/`load`, an async `fetch` with request coalescing and a sync `memo`. It is one
of the most depended-on npm packages. The patch checks it against a model of the typedoc
comments in `src/index.ts` (the README defers to them) and pins 4 bugs.

## How it is built

`src/index.ts` is TypeScript and `dist/` is not committed (upstream builds with tshy, then
minifies with esbuild). Hegel and esbuild go under `.hegel/`; `hegel/build.mjs` runs the
esbuild *binary* to bundle `src/index.ts` to `.hegel/dist/index.mjs`, which the tests import.
lru-cache has no runtime dependencies.

## How it is tested

`hegel/hegel.test.mjs` runs under `node --test`; `hegel/hegel-zoo.mjs` is the zoo's shared
harness (with a `propertyAsync` for Hegel's `testAsync`). The clock is mocked through the
`perf: { now }` option the README's testing section recommends, and `ttlResolution` is 0 so
that a burst of synchronous operations is not served a cached time.

| Property | What it checks |
|---|---|
| `TestHegelModelLikeMap` | random option sets (`max`, `maxSize`, `maxEntrySize`, `ttl`, `sizeCalculation`, `allowStale`, `noDeleteOnStaleGet`, `updateAgeOnGet/Has`, `noUpdateTTL`, `noDisposeOnSet`, `dispose`/`disposeAfter`/`onInsert`; one cache in five is built with the copy-constructor form `new LRUCache(cache)`) and sequences of `set` (with `size`, `sizeCalculation`, `ttl`, `start`, `noUpdateTTL`, `noDisposeOnSet` overrides), `get`, `has`, `peek`, `delete`, `clear`, `pop`, `purgeStale`, `find`, `load(dump())` and clock advances against an insertion-ordered Map model; after every step: return values, the `status` object, `size`, `calculatedSize`, the six iterators and `forEach`/`rforEach`, `info`, `getRemainingTTL`, `dump` (order, stale entries, sizes, TTLs) and the exact sequence of callback calls with their reasons |
| `TestHegelMemo` | `memo` is get-or-compute: `memoMethod` is called exactly on a miss or `forceRefresh`, with the key, the stale value and the context; the result is stored with the `ttl`/`size` options; `status.memo` |
| `TestHegelOptions` | constructor validation (`max`, `ttl`, `maxSize`, `maxEntrySize`, `sizeCalculation`, `fetchMethod`, `memoMethod`, `perf`, the "at least one bound" rule) and `set` size validation; every option reads back; a cache built from a cache copies all of them; `ttlResolution` fallback; the `toStringTag` |
| `TestHegelFetch` | (async) `fetch` against a scripted model with a controllable `fetchMethod`: one call per key in flight (coalescing), `status.fetch` (`miss`/`hit`/`stale`/`refresh`/`inflight`), the stale value and context passed to `fetchMethod`, stale-while-revalidate with `allowStale`, `has`/`get` during a fetch, resolution (value cached, `undefined` deletes or restores the stale value), rejection (deleted unless `noDeleteOnFetchRejection`; suppressed by `allowStaleOnFetchRejection`), `set`/`delete` over an in-flight fetch aborting it, `fetch` without a `fetchMethod`, `forceFetch` |

`ZOO_COLLECT=1` turns mismatches into `# COLLECT` counts instead of failures; `HEGEL_TEST_CASES`
(default 100) widens the sweep. Known bugs are skipped through the `Known` switches at the top
of the file (generator-level: the clock never reads 0, `maxEntrySize` never exceeds `maxSize`,
`noDisposeOnSet` is not combined with `disposeAfter`, a same-value `set` passes the stored size).

## Bugs

4 open, all pinned (see `bugs.toml`):

- TTL: an entry whose start time is 0 never expires — the README's own `perf` recipe starts its
  clock at 0, and `set(k, v, { start: 0 })` is affected too (1, medium).
- Sizes: an entry larger than `maxSize` but within an explicitly larger `maxEntrySize` evicts
  everything, is dropped, and leaves `calculatedSize` negative (2, medium); `set(k, sameValue,
  { size })` keeps the old size while resetting the TTL (4).
- Callbacks: `noDisposeOnSet` postpones the `disposeAfter` calls of the evictions made by that
  `set()` until a later operation (3).

## Accepted differences and notes (not counted as bugs)

- `ttl: NaN` and `maxEntrySize: NaN` are read as 0 (`NaN || 0`) and silently disable the
  feature, while every other non-positive-integer throws.
- With the default `ttlResolution` of 1 ms the cache caches the clock reading for a millisecond
  of real time, so staleness observed within a synchronous burst lags; the tests use 0.
- `forEach` is documented as not iterating stale values, but with the cache's `allowStale` set
  it (like `keys`/`values`/`entries`) does; the model follows the code, since `allowStale`
  is the user's request to see stale entries.
- `info().start` is `Date.now()` and `dump().start` a `Date.now()`-relative stamp even under a
  mocked `perf`; round trips are checked to within 2 ms.
- The unbounded-cache warning (`ttl` without `max`/`maxSize`/`ttlAutopurge`) is emitted once
  per process and appears on stderr during the run.

## Not tested

`ttlAutopurge` (real timers), `ignoreFetchAbort`/`allowStaleOnFetchAbort` with an external
`AbortSignal`, `backgroundFetchSize`, the `node:diagnostics_channel` metrics and tracing,
`unsafeExposeInternals`, the browser entry points, very large `max` values (Uint16/Uint32 index
arrays), the TypeScript types.

## History

- 2026-09-17: created at 16b3a91 (v11.5.2), 4 properties, 4 bugs.
- 2026-09-18: base bumped 16b3a916662a → 7e71a1f3babd (2026-09-18, "11.5.3"; 11.5.3); 4 bug(s) still reproduce. 4 tests pass.
