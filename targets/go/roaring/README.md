# roaring

[RoaringBitmap/roaring](https://github.com/RoaringBitmap/roaring) is the Go implementation of
Roaring bitmaps: compressed sets of uint32 (and, in `roaring64`, uint64) values stored as
array, bitmap or run containers keyed by the high 16 bits, with set algebra, rank/select,
neighbour queries, iterators, copy-on-write, and a portable serialization format shared with
the C and Java implementations. About 30 000 lines, Apache-2.0, pinned at `7d3e4c8`
(2026-09-15, after v2.28.0). The repository's `AGENTS.md` states that deserializing untrusted
bytes and using the result without `Validate()` is documented misuse, not a bug; the zoo
respects that (only validated bitmaps are compared) and nothing else in the project documents
speaks about AI-written code.

## Build

`go test -count=1 -run TestHegel -v .` in the module root. The patch adds the test files and
requires `hegel.dev/go/hegel v0.6.33` in go.mod: `hegel_zoo_idioms_test.go` (the generator
idioms: weighted choices, fair-bit dice, halving helpers), `hegel_zoo_test.go` (the harness,
the collector, the `known` switch set, the judge and the classifier),
`hegel_zoo_model_test.go` (the interval-set model, the container-kind reader and the replicas
of the recorded bugs), `hegel_zoo_bitmaps_test.go` (the key, point, range, op and bitmap
records and the pure build of a bitmap from a record), `hegel_zoo_construction_test.go`,
`hegel_zoo_algebra_test.go`, `hegel_zoo_queries_test.go`, `hegel_zoo_iterators_test.go`,
`hegel_zoo_serialization_test.go`, `hegel_zoo_specbytes_test.go`,
`hegel_zoo_corrupt_test.go`, `hegel_zoo_dense_test.go`, `hegel_zoo_cow_test.go` and
`hegel_zoo_roaring64_test.go` with `hegel_zoo_roaring64_records_test.go` (the ten wide
properties), `hegel_zoo_spec_test.go` (the format-specification parser and writer, the
64-bit portable parser, and a replica of the library reader's walk over a stream),
`hegel_zoo_shapes_test.go` (one narrow property per bug a wide property reaches) and
`hegel_pins_test.go` (one pin per bug).

## Oracles

- **An interval-set model** (`set`: sorted, disjoint, half-open `[lo, hi)` intervals over
  `[0, 2^32)` or `[0, 2^63)`) with union, intersection, difference, symmetric difference,
  complement, range add/remove/flip, rank, select, neighbours, cardinality in range and
  shifting. Every library bitmap is read back through `Ranges()`, cross-checked with
  `GetCardinality` and `ToArray`, and compared with the model as a set; `Minimum`, `Maximum`,
  `IsEmpty`, `Stats` and `HasRunCompression` are checked against it too.
- **The Roaring format specification** (RoaringFormatSpec): an independent parser that checks
  every structural rule (cookies, run bitmap, descriptive and offset headers, strictly
  increasing keys, sorted array containers, run lengths inside the container, bitmap containers
  only above 4096 values, exact length) and yields the set, and an independent writer that
  emits any container mix (array, bitmap, run) for a set. The 64-bit portable format (bucket
  count, per-bucket key and 32-bit stream) is parsed the same way.
- **The documented contracts**: functional operations leave their operands alone and return
  independent bitmaps; in-place operations change only the receiver; clones and copy-on-write
  clones are isolated; `Validate` accepts what the library builds and what the spec allows;
  `Checksum` is a function of the set; `Equals` on equal sets; `Contains` agrees with the
  iterators; `MustReadFrom` errors or panics with a validation error, never crashes; `Clear`
  empties the set and nothing else.
- **bits-and-blooms/bitset** and the dense (`[]uint64`) representation for `ToDense`,
  `FromDense`, `WriteDenseTo`, `ToBitSet`, `FromBitSet`.
- **The container kinds**, read from the library's frozen form of a built bitmap before the
  operation under test (`kindsOf`), and a dry replica of the library's kind rules carried
  through the ops (`dryReplay`, checked against the read kinds on every case): the shapes of
  roaring/3, 6, 9, 10, 12 and 13 are properties of the kind of container at a key or of the
  copy-on-write flag; the 64-bit bitmap's kinds are read per bucket from its portable stream.
- **The library reader's layout of a stream** (`libLayout`): a replica of `readFrom`'s walk
  (the fields it reads in order, the container slots it allocates at the announced count and
  fills as each container's read ends) that says, for a truncated or mutated stream, where the
  read fails and what the receiver is left holding; with scratch reads of corrupt bytes into
  throwaway bitmaps before the judged read, it is the predictor set of the corrupt-bytes
  property (the shapes of roaring/7 and 11 are computed from it, not from the judged read).

## Properties

A case is a record drawn from package-level generators (the keys, the points and ranges over
them, the ops of a bitmap at the shares the old generators had, measured and written beside
every weight) and the library bitmap is built from the record in the property; the model
states every value the property checks (`expected(c, k)` for the case and the switch set
`known`, every switch off by default) and the library's values are judged against it as text.

| Property | Checks |
|---|---|
| ConstructionMatchesTheModel | random sequences of Add/Remove/CheckedAdd/CheckedRemove/AddInt/AddRange/RemoveRange/Flip/FlipInt/AddMany/RunOptimize/Clear/Clone (ranges up to and across container boundaries, 4095–4097 and 65535–65537 long, the full universe) against the model after every step; Contains, ContainsInt, GetCardinality, String, Equals (including against nil and non-bitmaps); Validate on every state (roaring/6 when a range op leaves a loose run) |
| SetAlgebraMatchesTheModel | Or/And/Xor/AndNot/Flip/AddOffset/AddOffset64 and the aggregates FastOr/FastAnd/HeapOr/HeapXor/ParOr/ParAnd/ParHeapOr with 0–3 inputs against the model; results independent of their inputs (a bit flipped in the result, operands re-checked: roaring/4 for ParHeapOr at a key one input holds, roaring/5 for HeapOr/HeapXor of one bitmap); cardinality shortcuts OrCardinality/AndCardinality/Intersects; AndAny; in-place Or/And/Xor/AndNot on clones (operands and clone source re-checked: roaring/12 for Xor with a bitmap-container argument), and on themselves |
| RankSelectAndNeighboursFollowTheModel | Rank, Select (including past the end), CardinalityInRange, IntersectsWithInterval, NextValue/PreviousValue and NextAbsentValue/PreviousAbsentValue at drawn and boundary points (roaring/1 outside container 0, roaring/2 across containers, roaring/3 in bitmap containers); AddOffset/AddOffset64 results (roaring/6 and 9) |
| IteratorsWalkTheSet | Iterator (HasNext/Next/PeekNext/AdvanceIfNeeded), ReverseIterator, ManyIterator (NextMany/NextMany64 in odd-sized buffers), UnsetIterator and Unset (roaring/3 over a bitmap container), Values/Backward/Ranges against the model |
| SerializationFollowsTheFormatSpec | ToBytes/WriteTo/MarshalBinary/ToBase64 parse under the spec to the set with the container kinds of the built bitmap, agree with GetSerializedSizeInBytes and BoundSerializedSizeInBytes; ReadFrom/FromBuffer/FromUnsafeBytes/UnmarshalBinary/FromBase64/MustReadFrom read them back (also through one-byte and half readers, into receivers that already hold a value, with trailing data) and the results validate (roaring/6 on a loose run), equal the source, hash like it, and take a Flip; a prefix never gives the whole set back and Validate after the failed read does not crash (roaring/7 when the cut falls inside the last container); Checksum equality of equal sets built differently (roaring/10 when the kinds differ) |
| SpecConformantBytesAreAccepted | streams written by the independent writer with every container mix, run containers drawn freely (roaring/6 where a run is not the smallest form), are read by every reader, validate, equal the set, keep their kinds when written again |
| CorruptBytesNeverPanicAndValidateGuards | serialized streams with bytes flipped, set, inserted, deleted, truncated or appended: no reader panics, Validate never panics (roaring/7 after a read that fails inside the last container); bytes the spec accepts must be accepted and validate (roaring/6 on a loose run); bytes the library accepts and validates must behave (iteration, Contains, re-serialization), and Validate rejects a run past its container (roaring/11) |
| DenseConversionsRoundTrip | ToDense/DenseSize/FromDense/WriteDenseTo/ToBitSet/FromBitSet against a bitset built from the model, with and without copying, a zero-word tail; no recorded bug, passes |
| CopyOnWriteIsolatesBitmaps | clones with and without copy-on-write, seven derived bitmaps mutated in turn with every other re-checked, the copy-on-write receiver, CloneCopyOnWriteContainers, and GetCopyOnWrite after every step (roaring/13 when a step is Clear) |
| Roaring64MirrorsTheModel | the roaring64 API (construction, algebra, rank/select/neighbours, iterators, portable and native serialization, hand-written portable streams with every container mix, Roaring32AsRoaring64) with keys spread across the low 2^63 (roaring/8 when the embedded low part is empty, roaring/6 on loose runs) |

The properties keep drawing the shapes of the recorded bugs they reach and fail by them: the
model with a switch on reproduces the library's rule for that bug as a replica of its code
(roaring/1's double shift, roaring/2's container walk, roaring/3's shifted word, roaring/4's
shared container and what a flip does to it, roaring/5's returned input, roaring/6's size
rule, roaring/7's container slots left empty by a read that fails inside the last container,
roaring/8's unconditional bucket, roaring/9's split pieces, roaring/10's hash per container
kind, roaring/11's validate without a bound on the run's end, roaring/12's in-place xor into
the argument, roaring/13's flag cleared by Clear), and the classifier names the shape of a
case before the library is judged by running the model per switch (the first switch that
alone moves the model, in bug order; at 3000 cases per property every shaped case is named
so, with the replica agreeing with the library on all of them). Each is mapped to the shape
it fails by most often over forty rounds at a hundred cases; a mismatch names the shape "(the
shape of roaring/N)". Under `HEGEL_NO_KNOWN=1` a shape is not drawn where the generator can
avoid it (a run container at a key where it would not be the smallest form, a Clear on a
bitmap with copy-on-write set) and otherwise the checks it covers are dropped from the case
(the absent-value queries outside container 0 or into a bitmap container, the independence of
a ParHeapOr result at a key one input holds, the HeapOr/HeapXor of one bitmap, the argument
after an in-place Xor with a bitmap-container argument, the Validate of a result predicted
loose or small, the Validate after a read that fails inside the last container, the behaviour
of a bitmap holding a run past its container, the checksum of a set rebuilt with other
container kinds, the embedding of an empty low part), counted, and the rest judged, so a run
looks past the known bugs; every property must then pass. Nine narrow properties, one per bug
a wide property reaches by a shape its generator can force, draw the bug's region with random
contents and fail every run: `TestHegelAbsentValuesKeepTheHighBits` (1),
`TestHegelAbsentValuesCrossContainers` (2), `TestHegelAbsentValuesInBitmapContainers` (3),
`TestHegelParHeapOrResultsAreIndependent` (4), `TestHegelHeapAggregatesOfOneBitmapAreCopies`
(5), `TestHegelLibraryBuiltRunContainersValidate` (6), `TestHegelAddOffsetResultsAreValid`
(9), `TestHegelInPlaceXorLeavesTheArgumentAlone` (12), `TestHegelClearKeepsCopyOnWrite` (13);
under `HEGEL_NO_KNOWN=1` they draw the region past the shape and pass. `ROARING_COLLECT=1`
(or `ZOO_COLLECT=1`) records mismatches instead of failing and prints the counts (the shapes,
the classifier's rule, the replica agreement, the dropped checks); `HEGEL_VERBOSE=1` turns on
the engine's log. The byte properties write a full-universe set as bitmap containers (a
270 MB stream read by up to nine readers) in about one case in a hundred, so the test sets a
soft memory limit of 1.75 GB for the runtime's collector, writes streams into reusable
buffers and collects after each reader of a large stream; the old test never ran those
cases (its per-key coin overran the engine's draw budget and the case was dropped). A run
takes four to six minutes on two CPUs (eighteen properties shrink a failure each; the
properties run two at a time), about 1.5 GB of address space at its peak.

## Bugs (13; details in bugs.toml)

| id | summary | severity |
|----|---------|----------|
| roaring/1 | `NextAbsentValue`/`PreviousAbsentValue` return only the low 16 bits when the target's container key is not 0 (`combineLoHi32` shifts the already shifted keyspace) | high |
| roaring/2 | `NextAbsentValue`/`PreviousAbsentValue` answer wrongly when the answer is outside the target's container: adjacent containers taken as gaps, −1 for a full first/last container, 65536 for the full bitmap | medium |
| roaring/3 | `NextAbsentValue`, `PreviousAbsentValue` and `UnsetIterator` return present values inside a bitmap container (bits vacated by `w >> target%64` counted as absent; the previous absent value can lie above the target) | high |
| roaring/4 | `ParHeapOr`'s result shares containers with its inputs without copy-on-write; mutating either changes the other, and can leave the input with a 4097-value array container | high |
| roaring/5 | `HeapOr` and `HeapXor` of a single bitmap return that bitmap itself | medium |
| roaring/6 | `Validate` rejects run containers that are not the smallest representation, including ones the library builds itself (`AddOffset64`, `Flip`, `RemoveRange`, `AddRange` onto a run) and spec-conformant foreign streams, adjacent runs among them | medium |
| roaring/7 | `MustReadFrom` and `Validate` crash with a nil dereference after a `ReadFrom`/`FromBuffer` that fails inside the last container (MustReadFrom ignores the read error; a failure in an earlier container is caught by the key-order check instead) | medium |
| roaring/8 | `Roaring32AsRoaring64` of an empty bitmap is invalid, not empty, not equal to the empty 64-bit bitmap, its iterator crashes on `Next`, and it serializes with an empty bucket the reader drops | low |
| roaring/9 | `AddOffset`/`AddOffset64` can build bitmap containers of 4096 values or fewer (every piece of a split bitmap container stays a bitmap container); the result fails `Validate` and `ToBytes` refuses to write it after `GetSerializedSizeInBytes` promised a size | high |
| roaring/10 | `Checksum` depends on the container types, not only on the set: equal bitmaps hash differently | medium |
| roaring/11 | `Validate` accepts a run container whose run extends past the container; the bitmap then has Maximum below Minimum and iterates values `Contains` denies | medium |
| roaring/12 | in-place `Xor` mutates its argument (and shares the container with it) when the argument holds a bitmap container and the receiver an array or run container | high |
| roaring/13 | `Clear` turns copy-on-write off: `GetCopyOnWrite` is false afterwards and clones are full copies | low |

How they were found: roaring/1 and roaring/2 by hand probes while writing the neighbour
property (every case with values above 65535 hit roaring/1); roaring/3 by the neighbour and
iterator properties at 200 cases (first at a word-aligned answer); roaring/4, 5 and 12 by the
algebra property's independence checks (a bit flipped in each result, each operand re-checked
after each in-place operation); roaring/6 and 9 by the `Validate` call the model comparison
makes on every result, the serialization consequence of roaring/9 by probes; roaring/7 and 11
by the corrupt-bytes property (a truncation; a single mutated run-length byte that the spec
parser rejected and `Validate` accepted); roaring/8 by the 64-bit property on the empty
bitmap; roaring/10 by the serialization property rebuilding each set from its intervals;
roaring/13 by the rewritten algebra property, whose replica of roaring/4's sharing disagreed
with the library on bitmaps cleared after `SetCopyOnWrite(true)`; the iterator crash of
roaring/8 and the last-container rule of roaring/7 by the rewritten 64-bit and byte
properties, whose replicas were checked against the library's code; the adjacent-runs
instance of roaring/6 by the corrupt-bytes property under `HEGEL_NO_KNOWN=1` (a mutated
run start made two runs adjacent, which the spec allows and `Validate` rejects). Four
collect rounds of the
first version otherwise caught harness mistakes only (`DenseSize` counts uint64 words, an
interval end of 2^32 combined with a key by `|` instead of `+`, 64-bit keys outside the
model's universe).

## Accepted differences (not bugs)

- Using a deserialized bitmap without `Validate` is documented misuse (`AGENTS.md`): the
  corrupt-bytes property only inspects bitmaps that both read and validated.
- `Iterate` visits containers in key order but its order inside a container is not specified;
  the properties collect and sort.
- `AddOffset` wraps in uint32 arithmetic by documentation; `AddOffset64` drops values that
  leave the range.
- `Minimum` and `Maximum` on an empty bitmap panic, as documented.
- `ReadPortableFrom` (roaring64) drops empty buckets silently; the format never stores one
  except through roaring/8.
- `AddOffset`/`AddOffset64` shift run containers value by value (`runContainer16.inplaceUnion`
  calls `Add` for each value of the shifted run, about 5 ns each): a non-aligned shift of the
  full universe takes some 20 s where an aligned one takes microseconds. Linear, not a hang,
  so not recorded; the generator keeps sets above 2^26 values on aligned offsets.
- `Validate` requiring bitmap containers to hold more than 4096 values is the library's own
  invariant (the spec allows any cardinality); the spec writer emits bitmap containers only
  above 4096 and this is not counted against the library.
- `RunOptimize` does not always shrink the serialized size (a loose run of two values grows
  from 19 to 20 bytes; a bitmap container of more than 2048 runs grows by a few bytes): the
  construction property checks the exact size of the chosen representation before and after,
  not that it never grows.

## Not tested

`BitSliceIndexing`, the frozen format (`Freeze`/`FrozenView`) beyond reading the container
kinds, the `smat` and fuzz harnesses, `roaring64`'s `Roaring64Map`-specific statistics, and
performance.

## History

- 2026-09-17: first version, twelve bugs recorded.
- 2026-10-12: part 1 of the rewrite: the harness, the model, the bitmap records and the four
  properties Construction, SetAlgebra, RankSelectAndNeighbours and Iterators with the
  switches of the eight bugs they reach off by default, the container kinds read from the
  live state and replicated dryly, eight narrow properties; roaring/13 recorded; the notes of
  roaring/3, 4, 6 and 9 widened.
- 2026-10-12: part 2: the six byte, dense, copy-on-write and 64-bit properties under the
  same standard (the shapes of roaring/6, 7, 8, 10, 11 and 13 drawn by default and named,
  the corrupt-bytes property a differential property over a predictor set), the older
  harness removed, a ninth narrow property for roaring/13; the notes of roaring/7 and 8
  widened.
