# roaringbitmap

[RoaringBitmap/RoaringBitmap](https://github.com/RoaringBitmap/RoaringBitmap): compressed bitmaps
of 32-bit integers (`RoaringBitmap`, its buffer-backed `ImmutableRoaringBitmap`/
`MutableRoaringBitmap`, `FastRankRoaringBitmap`, `RoaringBitmapWriter`, the `FastAggregation`/
`ParallelAggregation`/`BufferFastAggregation` statics), the 64-bit `Roaring64Bitmap` and
`Roaring64NavigableMap`, the `RangeBitmap` range index and `RoaringBitSet`, a `java.util.BitSet`
drop-in. Pinned at 1.6.23 (f2289086, 2026-09-10). Apache-2.0; the repository's AGENTS.md asks that
"bugs" about deserializing malformed bytes without `validate()` not be reported — the tests feed
`deserialize` only bytes the library wrote — and forbids nothing else (the zoo only records). The
fifth Java target and the first Gradle project: upstream builds with Gradle (Kotlin DSL, toolchain
downloads), so the patch's Maven module `hegel/` compiles the library's own sources
(`roaringbitmap/src/main/java`, minus `module-info.java`) as its main sources via
`<sourceDirectory>` instead of depending on a published artifact, and `[run] setup = []`. The
harness `Zoo.java`, the judge's `ZooListener` and three test classes live in
`hegel/src/test/java/zoo/`. See HACKING.md for the Java mechanics.

## What is tested

The models are `java.util.NavigableSet`s in unsigned order (`Integer::compareUnsigned` for the
32-bit classes, signed or unsigned `Long` comparators mirroring the 64-bit map's mode), a plain
`java.util.BitSet` for `RoaringBitSet`, and a linear scan for `RangeBitmap`. Generated bitmaps
have 0–4 containers of chosen shapes (sparse points, dense blocks, short runs, runs with holes,
container extremes, sometimes a full container) at keys that favour 0, 1, 2, 0x7FFF, 0x8000,
0xFFFE and 0xFFFF, randomly `runOptimize()`d or `removeRunCompression()`ed, so array, bitmap and
run containers all appear on both sides of 2^31.

`RoaringBitmapTest`:

- **mutationsAndQueriesMatchAnUnsignedSetModel** — a generated bitmap under sixteen kinds of
  mutation (`add`/`remove`/`flip`/`checkedAdd`/`checkedRemove` of values, `add`/`remove`/`flip`
  of ranges, `and`/`or`/`xor`/`andNot` with a second generated bitmap, `runOptimize`,
  `removeRunCompression`, `trim`, `clear`), then every reader against the model: the int, reverse,
  signed, boxed and batch iterators, `stream`, `forEach` (skipped for the shapes of bugs /2 and
  /27), `cardinalityExceeds`, `first`/`last`/`firstSigned`/`lastSigned`, `getContainerCount`,
  twelve point queries (`contains`, `rank`/`rankLong`, `nextValue`/`previousValue`,
  `nextAbsentValue`/`previousAbsentValue` — bugs /1 and /23 skipped), `advanceIfNeeded` forwards
  and backwards, `select` (and the `IllegalArgumentException` at the cardinality), the range
  queries `rangeCardinality`, `contains(min, sup)` (bug /7 skipped), `intersects`, `selectRange`,
  `forEachInRange` (bug /3 skipped), `limit`, `addOffset` (bug /4 skipped), `contains(subset)`
  and `isHammingSimilar`, `toString` (below the 0x80000-character cap), `equals`/`hashCode`
  against `bitmapOf(toArray())` after the same `runOptimize`/`removeRunCompression` (bug /8
  skipped) and `validate()`.
- **serializationConstructionAndBufferViewsRoundTrip** — `serialize` to a `DataOutput` and to
  `ByteBuffer`s of several sizes, `serializedSizeInBytes`, the `maximumSerializedSize` bound,
  `deserialize` from both (the copy agrees with the model and with the original's `validate()`),
  an `ImmutableRoaringBitmap` mapped over the bytes answering the same queries, a
  `MutableRoaringBitmap` copy, Java serialization, `bitmapOf`/`bitmapOfUnordered`/
  `bitmapOfRange`/`add(long, long)`, nine `RoaringBitmapWriter` configurations (bug /9 skipped),
  the buffer writer, `FastRankRoaringBitmap` (`rank`/`select` after adds and removes) and, for
  small bitmaps, the `BitSetUtil` bridges to `java.util.BitSet` (bug /20 skipped).
- **setAlgebraMatchesTheModel** — two to four generated bitmaps: the static and in-place
  `and`/`or`/`xor`/`andNot`, `andCardinality`/`orCardinality`/`xorCardinality`/`andNotCardinality`,
  the ranged `and`/`or`/`xor`/`andNot`, `orNot` (bugs /5 and /24 skipped), `FastAggregation`
  (`and`, `or`, `xor`, `naive_*`, `horizontal_*` — bug /6 skipped — `priorityqueue_*`,
  `workShyAnd`, `workAndMemoryShyAnd`), `ParallelAggregation.or`/`xor`, `BufferFastAggregation`
  and the `ImmutableRoaringBitmap` statics on buffer copies, and that operands are unmodified.
- **roaringBitSetIsADropInForBitSet** — `RoaringBitSet` against `java.util.BitSet` under `set`,
  `clear`, `flip` (single bits and ranges), `and`/`or`/`xor`/`andNot` with a second set (copied
  into a plain `BitSet` for the model, bug /19), `get`, `get(from, to)`, `nextSetBit`,
  `nextClearBit`, `previousSetBit`/`previousClearBit` (bug /22 skipped), `cardinality`,
  `length`, `size`, `isEmpty`, `intersects`, `stream`, `clone`/`equals`/`hashCode`.

`RoaringMoreTest`:

- **sixtyFourBitBitmapsTrackATreeSetOfLongs** — `Roaring64Bitmap`, and `Roaring64NavigableMap`
  unsigned, signed and without cached cardinalities, under `addLong`/`removeLong`/`flip`/
  `addRange` (signed maps skip ranges across the sign boundary, which `addRange` rejects by
  design)/`add(long...)`/`runOptimize`, then the forward and reverse iterators, `forEach`
  (skipped where the low 32 bits hit bugs /2 and /27), `select`, `contains`, `rankLong` (bug /14
  skipped), `getLongIteratorFrom`/`advanceIfNeeded` (bug /10 skipped), `first`/`last`/`clone`/
  equality (skipped after an in-place operation emptied a bucket, bug /12), `serialize`/
  `deserialize`, `serializePortable`/`deserializePortable` (cross-checked between the two
  classes; bug /15 skipped), the legacy format, the static and in-place `and`/`or`/`xor`/
  `andNot`, `andCardinality`, `intersects` (statics only for unsigned maps, bug /13),
  `naivelazyor`/`repairAfterLazy`, and `toString`.
- **rangeBitmapQueriesMatchAScan** — `RangeBitmap.appender(max)` for maxima of 0–63 bits with
  0–400 rows (zeros, the maximum, values near either end, random), built directly, via
  `serialize`+`map`, or via `build(ByteBuffer)`; `lte`/`lt`/`gte`/`gt`/`eq`/`neq` and their
  `*Cardinality` forms, with and without a context bitmap, `between`/`betweenCardinality` (bug
  /16 skipped), the appender's rejection of the next power of two (bug /17), `clear()` and reuse
  (bug /25 skipped).

`RoaringPinsTest` holds one pin per bug in bugs.toml, each asserting the documented behaviour;
all fail while the bugs exist (`[expected_failures]`).

## Not covered

The `bsi` module (bit-sliced indexes), `ImmutableRoaringBitmap`'s memory-mapped file paths and
`MutableRoaringBitmap`'s own mutation surface (only copies of `RoaringBitmap`s are checked), the
`art`/`insights` packages, `ParallelAggregation.and`, `FastRankRoaringBitmap`'s cache internals,
the `RangeBitmap` statistics helpers, `RoaringBitmapWriter`'s partial-flush semantics, and the
`Roaring64NavigableMap` bucket-supplier variants beyond the three constructors above.

## Bugs

1. `nextAbsentValue`/`previousAbsentValue` below a container with key >= 0x8000 jump into that
   container (signed comparison of `containerKey << 16`).
2. `RunContainer.forEach` emits nothing for a run at key 0x8000 whose start is below its length.
3. `forEachInRange`/`forAllInRange` stop at 2^31.
4. `addOffset` by a multiple of 65536 wraps containers that fall outside the range, or throws.
5. `orNot` includes the other bitmap's values beyond `rangeEnd` in the last container.
6. `FastAggregation.horizontal_xor` leaves an empty container.
7. `contains(min, sup)` is false for `sup = 2^32` and true when the supremum's container is absent.
8. Equal run-optimised bitmaps can have different `hashCode`s (run/array ties).
9. `RoaringBitmapWriter.initialCapacity` refuses 65535 and 65536 (`expectedRange` over the range).
10. `Roaring64Bitmap`'s `advanceIfNeeded` past the last container leaves the iterator unmoved.
11. `Roaring64Bitmap.limit`/`Roaring64NavigableMap.limit` throw `UnsupportedOperationException`.
12. `Roaring64NavigableMap`'s in-place `and`/`andNot`/`xor` leave empty buckets (`last` throws).
13. `Roaring64NavigableMap`'s static `or`/`and`/`andNot`/`andCardinality` ignore signed order.
14. `Roaring64NavigableMap` without cached cardinalities ranks with a signed high comparison.
15. `deserializePortable` silently switches a signed map to unsigned order (undocumented).
16. `RangeBitmap.between` with a minimum above the range returns every row.
17. `RangeBitmap.Appender.add` accepts values above `maxValue` up to the next power of two.
18. `RangeBitmap.Appender.build(ByteBuffer)` ignores the buffer's position.
19. `RoaringBitSet` does not interoperate with `java.util.BitSet` (`equals`, `or`, `and`, …).
20. `RoaringBitSet.toByteArray` is 64 bytes per word; `toLongArray` has an extra word below bit 64.
21. `RoaringBitSet.toString` does not use `BitSet`'s documented format.
22. `RoaringBitSet.previousSetBit(-1)` returns the last set bit.
23. `previousAbsentValue` fails its own assertion when it returns -1 and 0xFFFFFFFF is present.
24. `orNot` drops the range's last containers when the other bitmap has a full container beyond it.
25. `RangeBitmap` queries throw `IndexOutOfBoundsException` when every row has all bits set and
    the masks are 3 or 5–7 bytes wide.
26. `validate()` rejects a run container the library produced by removing a value from a run.
27. `forEach` runs away past 2^31 when a run container at key 0x7FFF ends with 0x7FFFFFFF alone.

## Observed and not recorded

- `deserialize(DataInput, byte[] buffer)` requires the buffer's length to be a multiple of 8 and
  says so only in its exception message; the tests use 8, 16 and 8192.
- `Roaring64Bitmap.toString` prints the values as signed longs while `Roaring64NavigableMap`
  prints per its order; neither Javadoc specifies the rendering.
- `toString` truncates after 0x80000 characters with "..." (the tests skip larger bitmaps).
- `RangeBitmap` accepts context bitmaps with rows beyond the appended ones and ignores them.
- The 64-bit `addRange` methods throw for an empty range and for a signed map's range across the
  sign boundary, while `RoaringBitmap.add(long, long)` ignores an empty range.
- `runOptimize()` keeps whichever of two equally small encodings a container already has, so two
  equal bitmaps can differ in `hasRunCompression()` after it (the root of bug /8).

## History

- 2026-09-16: target created at f2289086 (1.6.23); 27 bugs.
