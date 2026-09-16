# java/caffeine

Hegel property tests for [Caffeine](https://github.com/ben-manes/caffeine) (3.3.0-SNAPSHOT at the pinned commit),
the W-TinyLFU in-memory cache for Java: the `Caffeine` builder and `CaffeineSpec`, the bounded and unbounded caches
behind `Cache`/`LoadingCache`, their `asMap()` views, the `Policy` inspection API, `CacheStats`, and the data
structures underneath (hierarchical timer wheel, count-min frequency sketch, intrusive linked deques).

## How it is built

Upstream builds with Gradle and generates the 144 `Node` and 50-odd `LocalCache` specialisations at build time
(`caffeine/src/javaPoet`), so `hegel.patch` adds a two-module Maven reactor: `hegel/codegen` compiles the JavaPoet
generators against their declared dependencies (guava, palantir javapoet, commons-lang3, jspecify, error-prone and
spotbugs annotations, versions from `gradle/libs.versions.toml`) and runs `NodeFactoryGenerator` and
`LocalCacheFactoryGenerator`; `hegel/tests` copies `caffeine/src/main/java` minus `module-info.java` into its build
directory (javac would otherwise find the descriptor on the source path and compile in module mode) and compiles
it together with the generated sources as its own main sources. Nothing is installed; `[run] setup` is empty. The
tests live in `com.github.benmanes.caffeine.cache` so they can reach the package-private internals.

## How it is tested

Everything runs single-threaded with a fake `Ticker`, `executor(Runnable::run)` so maintenance runs inline, and
`cleanUp()` at every checkpoint — the instrument the maintainers' own docs describe as deterministic.

- **`CacheModelTest`** drives a random configuration (unbounded / `maximumSize` / `maximumWeight` with a weigher;
  no expiry / `expireAfterWrite` / `expireAfterAccess` / both / `expireAfter(Expiry)`; manual or loading) against a
  `LinkedHashMap` model that carries each entry's value, weight, stored write/access times (with the 1 s
  `EXPIRE_TOLERANCE` rule) and variable deadline: presence and values of every read, `getAllPresent`, `asMap`
  `putIfAbsent`/`remove(k, v)`/`replace`/`compute`, the loader being called exactly on misses, the size and weight
  bound after `cleanUp()`, `weightOf`/`weightedSize`, every removal notification (EXPLICIT, REPLACED, EXPIRED; SIZE
  evictions are the policy's choice but must name a live entry with its current value), hit/miss/load statistics,
  and the `Policy` views (`coldest`/`hottest`/`oldest`/`youngest` key sets and prefixes, `ageOf`,
  `getExpiresAfter`, `getIfPresentQuietly`).
- **`AsMapTest`** runs every `ConcurrentMap` operation and collection view (`keySet`/`values`/`entrySet` removal,
  `removeIf`, `retainAll`, write-through entries, iterator removal, `replaceAll`, `merge`, `compute*`) against a
  `HashMap` on a bounded and an unbounded cache, checking `equals`/`hashCode`/`containsValue`/`getAllPresent` and
  the exact multiset of removal notifications after each step.
- **`InternalsTest`**: the `TimerWheel` with a Mockito-stubbed cache (timers never fire early; after `advance` every
  due timer has fired unless it sits in the current finest bucket — the wheel expires by bucket, so a timer may be
  up to one 1.07 s tick late — including past-scheduled and negative clocks; iterators visit each timer once);
  the `FrequencySketch` count-min guarantee (never under-counts before a reset, saturates at 15, halves on reset);
  `AccessOrderDeque`/`WriteOrderDeque` against `ArrayDeque` with the intrusive extras (`moveToFront/Back`,
  `isFirst/isLast`, link hygiene after removal).
- **`SpecAndStatsTest`**: `CaffeineSpec` strings generated from the documented grammar (whitespace, ISO-8601 and
  `NdNhNmNs` durations, `_` digit separators, order) parse to builders carrying the values and are stable under
  `toParsableString`; malformed strings are rejected by `parse` or by the builder; builder validation
  (negatives, repeats, incompatible pairs, `Duration` saturation, the `MAXIMUM_CAPACITY` clamp); `CacheStats`
  saturating `plus`, floored `minus` and rate conventions against `BigInteger`; `Interner` canonicality.

## What was found (1 bug, `bugs.toml`)

`Scheduler.forScheduledExecutorService` documents that a rejected submission is ignored but lets the
`RejectedExecutionException` through (only `isShutdown()` is handled); inside a cache `GuardedScheduler` masks it.

That is all — the cache itself agreed with the models everywhere. The project audits its own code continuously
(`.claude/docs/audit-*.md`, `ruled-out.md`) and fuzzes with Jazzer; the properties here re-derive the same
territory from the Javadoc and found it sound.

## Design choices respected (not recorded)

Read `.claude/docs/design-decisions.md` and `ruled-out.md` before reporting anything here; these are the rulings and
documented behaviours the models replicate:

- Access and write times move only when they differ from the stored time by more than `EXPIRE_TOLERANCE` (1 s), or
  the expiry itself is ≤ 1 s; so entries may expire up to 1 s "early" against a naive clock, `ageOf` reflects the
  stored time, and `oldest()` (write order) is only ordered within that tolerance. The write time is stored even
  (its low bit marks a refresh in flight).
- The access-order `oldest()/youngest()` and eviction-order `coldest()/hottest()` traversals merge several deques
  (window, probation, protected) by frequency or time; `hottest` is not the reverse of `coldest`, and read events
  may be dropped by the lossy read buffer, so only key sets and prefixes are checked.
- `coldestWeighted(limit)` returns the prefix of the traversal whose cumulative weight stays within the limit
  (stops at the first entry that would exceed it).
- Variable expiration is enforced exactly on reads (`getIfPresent`) but the timer wheel removes expired entries by
  bucket, so `asMap().size()`, `estimatedSize()`, `weightedSize()` and the EXPIRED notifications may lag by up to
  one tick; fixed expiration is exact after `cleanUp()`. A negative or zero `Expiry` duration means "already
  expired" (the entry is written but never readable); durations clamp at `MAXIMUM_EXPIRY` (2^62 ns).
- Weight 0 pins an entry; an entry heavier than `maximumWeight` is evicted at once with cause SIZE. `getMaximum()`
  reports `min(maximum, Long.MAX_VALUE - Integer.MAX_VALUE)`.
- Removing or overwriting an expired-but-still-mapped entry notifies EXPIRED (and counts an eviction), not
  EXPLICIT/REPLACED; `put` of the same value instance sends no notification; `remove(k, null)` is `false`.
- `asMap().compute*`/`merge` count loads (and `computeIfAbsent` hits/misses) although the `CacheStats` Javadoc
  describes them as loads only; statistics are best-effort by the maintainers' ruling.
- `CaffeineSpec.parse` checks only the grammar and the sign of durations, as Guava's `CacheBuilderSpec` does:
  `maximumSize=-1`, `refreshAfterWrite=0s` or `maximumWeight=…` without a weigher fail later in `Caffeine.from`
  or `build()` (IllegalArgumentException/IllegalStateException). Duplicate keys are IllegalArgumentException in a
  spec but IllegalStateException on the builder. `1.5h` is invalid but `PT1.5S` is valid; simple durations
  saturate through `TimeUnit.toNanos`. `Caffeine.from(spec)` disables strict parsing, so `.weigher(w)` on a
  `maximumSize` spec is accepted with a warning and disables eviction (documented footgun).
- `Caffeine.toString()` omits several settings (documented as unspecified); `Caffeine.getMaximum()` on a builder
  with `maximumWeight` but no weigher is the unset marker.
- `getAll` stores every entry a bulk loader returns, requested or not, and silently omits requested keys the loader
  left out; `getAllPresent` applies read side effects (access time, refresh).
- `CacheEntry.expiresAt()/refreshableAt()` are `snapshotAt() + Long.MAX_VALUE` when the policy is absent (wraps).
- A plain `maximumSize` cache (strong keys and values, no `expireAfterAccess`) takes the fast path: its read buffer
  does not exist until the frequency sketch is initialised at about half the maximum, so reads before that point
  neither reorder nor count; the sketch's sample size is `10 × max(maximum, 256)`, i.e. 2560 for small caches
  although the design notes say `10 × maximum`; an entry heavier than the window is queued at the cold end; and
  admission between two candidates of frequency ≥ 6 has a 1/128 random tie-break, so eviction *identity* is never
  asserted. Every `Policy` snapshot (`coldest`, `oldest`, …) runs a maintenance cycle and may reorder the regions.
- `getAllPresent` records a read on an in-flight async entry where `getIfPresent` deliberately does not (an
  asymmetry that heals when the future completes; not pinned, no observable effect was found).
