# java/agrona — Agrona

[aeron-io/agrona](https://github.com/aeron-io/agrona) is the data-structure and off-heap-buffer library under
Aeron and SBE: primitive-specialised open-addressing collections, `DirectBuffer` implementations over byte arrays,
`ByteBuffer`s and raw addresses with hand-rolled ASCII number codecs, inter-thread ring buffers, and assorted
concurrency utilities. Upstream has thorough example-based JUnit 5 tests and Guava conformance suites for the
collections, but no property-based tests.

Upstream builds with Gradle, and two things are generated at build time: `org.agrona.UnsafeApi` is a stub whose
method bodies (delegating to `jdk.internal.misc.Unsafe`) are injected with ByteBuddy, and the `Long*`/`Object2Long*`
collections are produced from the `Int*` sources by `SpecialisationGenerator`. The patch adds a Maven module `hegel/`
that compiles `agrona/src/main/java` as its own main sources with upstream's `UnsafeApi.java` excluded and a
delegating `UnsafeApi` (generated from the stub's signatures, `hegel/src/main/shim`) in its place; it compiles with
`--add-exports java.base/jdk.internal.misc=ALL-UNNAMED` (hence `source`/`target` rather than `--release`) and runs
with `--add-opens`. The generated `Long*` collections are not built.

## The oracles

- **java.util**: `HashMap`, `HashSet`, `ArrayList`, `ArrayDeque` driven by the same random operation sequences as
  `Int2ObjectHashMap`, `Int2IntHashMap`, `Object2IntHashMap`, `IntHashSet`, `IntArrayList`, `IntArrayQueue`, with the
  documented missing-value and null rules (a value equal to `missingValue` is rejected by `put` and means "absent"
  when returned; a mapping function returning it removes the entry).
- **The JDK's number formatting and parsing**: `Integer.toString`/`Long.toString` for what `put*Ascii` writes,
  `Integer.parseInt`/`BigInteger` for what `parse*Ascii` must accept or reject.
- **A `byte[]` model driven through `ByteBuffer`** for the three buffer implementations (every primitive with every
  byte order, array/`ByteBuffer`/`DirectBuffer` copies including overlapping self copies, `setMemory`, string codecs,
  bounds checks; expandable buffers grow where fixed ones throw).
- **A sequential record model** of the many-to-one and one-to-one ring buffers replicating the documented layout
  (8-byte aligned records, padding at the wrap, one header of slack in the one-to-one variant): write/tryClaim/commit/
  abort results, producer and consumer positions, `size()`, and everything `read`/`controlledRead` hand back.
- **A FIFO of payloads** for `ExpandableRingBuffer`.

## Properties

`CollectionsTest` (6): each collection against its java.util twin for up to 60 random operations (put/remove/
compute/merge/replace/iterator removal/view removal/compact/copy/putAll…), comparing every return value and, after
each step, size, `equals` in both directions, `hashCode`, key sets, values, entry sets, `forEach`, `toString` where
the order is fixed.

`CodecsTest` (4): `intAndLongAsciiRoundTrip` (put*Ascii writes `toString`, parse*Ascii reads it back, natural and
padded variants, `digitCount`), `asciiParsersMatchTheJdk` (random digit strings with signs, leading zeros and stray
characters: the value when the JDK accepts it, `AsciiNumberFormatException` otherwise), `fourAndEightDigitHelpers`
(the SWAR digit helpers against `Integer.parseInt`), `stringCodecsRoundTrip` (length-prefixed and plain ASCII/UTF-8
strings with every byte order, the `Appendable` and `maxEncodedLength` variants).

`BuffersTest` (2): `buffersMatchAByteArrayModel` over `UnsafeBuffer` (byte array, offset view, heap and direct
`ByteBuffer`), `ExpandableArrayBuffer` and `ExpandableDirectByteBuffer`, plus `equals`/`hashCode`/`compareTo` against
twins (antisymmetry, transitivity, prefixes sort first); `wrappingReportsTheAdjustment` for views of arrays,
`ByteBuffer`s and other buffers.

`RingBufferTest` (2): `ringBuffersMatchTheRecordModel` (ManyToOne/OneToOne, capacities 16–1024, messages up to
`maxMsgLength`, scripted `controlledRead` actions, misuse of `commit`/`abort`), `expandableRingBufferIsAFifo`
(append/consume/forEach/reset).

`AgronaPinsTest` holds one pin per recorded bug; each asserts the correct behaviour on a minimal input and is listed
in `[expected_failures]`.

## What the generators avoid

- `putNaturalIntAsciiFromEnd` is not exercised with 0 (agrona/1).
- Well-formed decimal strings longer than 10 characters (int) or 19 (long) are not expected to parse (agrona/2).
- An `ExpandableRingBuffer.append` whose record fits in total but neither before the end nor at the front while the
  ring cannot grow is skipped (agrona/3; the shape is computed from `head()`, `tail()`, `capacity()`, `maxCapacity()`).
- Self copies on an expandable buffer whose source range lies beyond the capacity are skipped (agrona/4).
- `values().remove(v)` is only used when `v` occurs once (which of several equal values goes is the iteration
  order's choice); `IntHashSet.copy` is only called with a set of equal capacity (an undocumented precondition);
  `IntArrayQueue` is created with at least `MIN_CAPACITY`; stale claim indices are only re-committed while the
  record is still in the ring (afterwards the slot may hold another message's payload bytes, and `commit` cannot
  tell); ASCII strings stay within 7 bits (chars above 127 are documented to become `?`).

## Not tested

The generated `Long*` collections, `Object2ObjectHashMap`, `ObjectHashSet`, `BiInt2ObjectMap`, the `*Nullable*`
maps, counter maps, `IntLruCache`, `Int2ObjectCache`; `nullValue` handling of `IntArrayList`/`IntArrayQueue`
through the boxed API; iterator reuse with `shouldAvoidAllocation`; atomic/ordered/volatile buffer operations and
anything multi-threaded (`unblock`, broadcast buffers, concurrent array queues, `CountersManager`,
`DistinctErrorLog`); `DeadlineTimerWheel`, `SnowflakeIdGenerator`, `SystemUtil` parsing, `BitUtil` hex, `SemanticVersion`,
`AsciiSequenceView`, `MarkFile`/`IoUtil`, checksums, the agent, `wrap(long address, int length)`; the Gradle build.

## Bugs found

| id | severity | what |
|---|---|---|
| agrona/1 | low | `putNaturalIntAsciiFromEnd(0, end)` writes nothing and returns `end` |
| agrona/2 | low | int (long) parsers reject any input longer than 10 (19) characters as overflow, so leading zeros fail (`00000000001`); the padded writer produces such strings |
| agrona/3 | medium | `ExpandableRingBuffer.append` writes past the end of the buffer when the free space is split and the ring cannot grow |
| agrona/4 | low | expandable buffers copying from themselves grow before checking the source range, reading beyond the capacity |

## Observed, not recorded

- `IntHashSet.copy(that)` throws `IllegalArgumentException("cannot copy object: masks not equal")` unless the two
  sets have the same capacity; the javadoc says only "copy values from another IntHashSet into this one".
- `checkLimit(-1)` passes on `UnsafeBuffer` (the check is `limit > capacity`) and throws on the expandable buffers
  (`ensureCapacity` rejects negatives); the interface documents "not greater than the capacity".
- `ManyToOneRingBuffer.write` returns false, after consuming the space to the end of the buffer as padding, when the
  free space is split and the record fits in total but not at the front; `size()` grows on a failed write.
- A `OneToOneRingBuffer` of `MIN_CAPACITY` (16) has `maxMsgLength() == 0`.
- `ExpandableRingBuffer.head()`/`tail()` are re-based to 0 on growth and `reset`, so they are not monotonic.
- `putNaturalPaddedIntAscii` with a negative value writes bytes below `'0'` without throwing (outside the documented
  natural-number domain).
- `DirectBuffer.compareTo` compares 8-byte words in native byte order, so on little-endian hosts the order is not
  lexicographic by byte; it is a consistent total order (antisymmetric, transitive, zero exactly for equal contents).

## History

- 2026-09-16: created (turn 178) at 6a57dd3df11c (2.7.0-SNAPSHOT of 2026-08-31); 4 bugs.
- 2026-09-17: base bumped 6a57dd3df11c → b4858542512f (2026-09-17, "ExpandableRingBuffer align bug (#370)"; 2.7.0-SNAPSHOT); 3 bug(s) still reproduce; fixed upstream: agrona/3. 15 tests pass.
