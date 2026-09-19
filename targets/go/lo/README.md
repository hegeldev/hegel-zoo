# samber/lo

[lo](https://github.com/samber/lo) (MIT), pinned at `a94fb4b` (v1.53.0+, 2026-09-09): the lodash-style
helper library for Go - some 300 generic functions over slices, maps, strings, numbers, tuples, pointers,
conditions and errors, with iterator twins in `it` (over `iter.Seq`), in-place variants in `mutable` and
concurrent ones in `parallel`. The README advertises an "AI Agent Skill" for users of the library and
`docs/CLAUDE.md` guides agents writing helper documentation; nothing restricts AI-written contributions.

The patch adds `hegel/`, a test-only package inside the module: `hegel_test.go` (plumbing),
`hegel_gen_test.go` (generators: short int slices with many repeats and an occasional extreme value,
strings from a pool mixing ASCII, multi-byte runes, a combining mark and a NUL), one file per area, and
`hegel_pins_test.go` (one plain test per recorded bug). `go get hegel.dev/go/hegel@v0.6.33` moved the
module's `go` directive to 1.26 (the `it` package needs 1.23 anyway). The oracles are naive models
written from each helper's documentation and - for `it`,
`mutable` and `parallel` - the slice helpers they mirror.

## What is tested

- `hegel_slice_test.go` - *TestHegelSliceTransformsMatchNaiveModels*: Filter/Reject/FilterReject/
  FilterErr (the predicate's error is returned), Map/MapErr/FilterMap/FlatMap/UniqMap, Reduce/
  ReduceRight/ForEach/ForEachWhile (order and indexes), Times/RepeatBy/Repeat, Uniq/UniqBy/IsUniq/
  IsUniqBy, GroupBy/GroupByMap/PartitionBy (first-occurrence order), Flatten/Concat/Reverse/Fill/Clone
  (independent copy)/Compact/Shuffle (same multiset), KeyBy/Associate/SliceToMap (last wins)/
  FilterSliceToMap/Keyify, Count/CountBy/CountValues/CountValuesBy, IsSorted/IsSortedBy; the input is
  never modified. *TestHegelSliceWindowsAndCutsMatchNaiveModels*: Chunk (panics on size <= 0)/Window/
  Sliding, Interleave (round robin over uneven lists), Drop/DropRight/Take (panic on n < 0)/DropWhile/
  DropRightWhile/TakeWhile/TakeFilter, DropByIndex (negative from the end, duplicates and out-of-range
  ignored)/WithoutNth, Subset/Slice/Splice with offsets on both sides of the bounds, Replace (n
  occurrences, n = -1 all)/ReplaceAll, Cut/CutPrefix/CutSuffix/HasPrefix/HasSuffix with separators taken
  from the input, Trim/TrimLeft/TrimRight (cut sets) and TrimPrefix/TrimSuffix (every leading/trailing
  copy), Nth/NthOr/NthOrEmpty with indexes from -len-2 to len+1.
- `hegel_find_test.go` - *TestHegelFindAndSetHelpersMatchNaiveModels*: IndexOf/LastIndexOf/Contains/
  ContainsBy/Find/FindIndexOf/FindLastIndexOf/FindOrElse/FindKey/FindKeyBy, FindUniques/FindDuplicates
  and their By forms (first-occurrence order), Min/Max/MinIndex/MaxIndex (first extremum)/MinBy/MaxBy/
  MinIndexBy, First/Last and their Or/OrEmpty forms on empty and non-empty input, Sample/Samples (a
  sub-multiset of the right size), Every/Some/None and their By forms, Intersect (distinct elements of the
  first list present in the second, in order)/IntersectBy, Difference (both sides, repeats kept), Union/
  UnionBy (distinct, in order), Without/WithoutBy/WithoutEmpty, ElementsMatch/ElementsMatchBy.
- `hegel_map_test.go` - *TestHegelMapHelpersMatchNaiveModels*: Keys (repeats across maps)/UniqKeys/
  Values/UniqValues/HasKey/ValueOr, PickBy/OmitBy and the ByKeys/ByValues forms partition the map,
  FilterKeys/FilterValues, Entries/FromEntries and ToPairs/FromPairs round trips, Invert (one key per
  distinct value, each mapping back), Assign (right wins), ChunkEntries (sizes, disjoint, add up; panics
  on 0), MapKeys/MapValues/MapEntries/MapToSlice/FilterMapToSlice.
- `hegel_string_test.go` - *TestHegelStringHelpersMatchRuneModels*: RuneLength, Substring against a rune
  window (negative offsets from the end, NUL runes dropped; bug 2 gated), ChunkString in runes (the
  documented `[""]` for the empty string; panics on 0), Ellipsis (trimmed, length in runes including
  the dots), RandomString (size and charset), Words against the two documented regexps plus
  letter/digit fields, PascalCase/CamelCase/KebabCase/SnakeCase built from those words, Capitalize as
  documented (bug 1 gated) - on ASCII input, since the converters use x/text's full case mappings.
- `hegel_math_test.go` - *TestHegelMathHelpersMatchModels*: Range/RangeFrom (negative counts descend)/
  RangeWithSteps over ints and floats (empty on a zero or wrong-signed step), Clamp, Sum/SumBy/Product/
  ProductBy/Mean (integer division)/MeanBy/Mode (the most frequent values as a set), SumByErr/MeanByErr.
  *TestHegelTuplesZipAndUnzipRoundTrip*: Zip2/Zip3 pad with zero values, Unzip2/Unzip3 and UnzipBy2
  invert them, ZipBy2, T2/Unpack2, CrossJoin2/CrossJoinBy2/CrossJoin3 as the cartesian product in
  first-list-major order. *TestHegelTypeConditionAndErrorHelpersFollowTheirDocs*: ToPtr/FromPtr/
  FromPtrOr/Nil/EmptyableToPtr/ToSlicePtr/FromSlicePtr/FromSlicePtrOr/ToAnySlice/FromAnySlice (a
  foreign element fails), IsNil, IsEmpty/IsNotEmpty/Empty, Coalesce/CoalesceOrEmpty/CoalesceSlice/
  CoalesceMap, Ternary/TernaryF/If-ElseIf-Else/IfF/Switch-Case-Default/CaseF/DefaultF, Try/Try0/Try2/
  TryOr/TryWithErrorValue/TryCatch/TryCatchWithErrorValue over succeeding, failing and panicking
  callbacks, Validate, Must/Must0 (panic on an error or false), ErrorsAs.
- `hegel_iter_test.go` - *TestHegelIteratorVariantsAgreeWithTheSliceOnes*: about seventy `it` helpers
  collected over `slices.Values` of the same input give what the slice helper gives (Filter/Map/
  FilterMap/RejectMap/FlatMap/UniqMap/Reduce/ReduceLast = ReduceRight, Uniq/UniqBy/GroupBy/PartitionBy,
  Chunk/Window/Sliding/Interleave/Concat/Flatten/Reverse/Fill/Repeat/RepeatBy/Times, KeyBy/Associate/
  Keyify, Drop/DropLast = DropRight/Take/DropWhile/DropLastWhile/TakeWhile/DropByIndex/WithoutNth/
  TakeFilter, Count/CountBy/CountValues, Subset/Slice/Replace/ReplaceAll/Compact/IsSorted/Splice,
  CutPrefix/CutSuffix/Trim/TrimFirst = TrimLeft/TrimLast = TrimRight/TrimPrefix/TrimSuffix (bug 3
  gated)/HasPrefix/HasSuffix, IndexOf/LastIndexOf/Find*/FindUniques/FindDuplicates (as a set: the
  iterator version documents its own order), Min/Max/MinIndex/MaxIndex/First/Last/Nth/NthOr/Sample/
  Samples, Contains/Every/Some/None/Intersect/Union/Without/ElementsMatch, Range/RangeFrom/
  RangeWithSteps/Sum/Product/Mean/Mode, Keys/Values/Entries/FromEntries); `mutable` Filter/FilterI/Map/
  MapI/Reverse/Shuffle and `parallel` Map/Times/GroupBy/PartitionBy/ForEach likewise. `it.Subset`,
  `it.Splice` and `it.Nth` reject negative positions (a sequence has no length) and `it.DropByIndex`
  ignores negative indexes where the slice version counts from the end, so those are compared on
  non-negative positions only.
- `hegel_pins_test.go` - one deterministic reproduction per bug, listed in `target.toml`'s
  `[expected_failures]`.

Not covered: the channel, concurrency (Async*, Synchronize, WaitFor), retry/debounce/throttle and
time helpers, the Err variants beyond a few, the 4-to-9-ary tuple functions (generated like the 2/3-ary
ones), `exp/simd`, and the `WithLanguage` case converters.

## Bugs

Three at a94fb4b (`bugs.toml`): `Capitalize` title-cases every word instead of the first character
[1]; `Substring` with a negative offset reaching past the start of a non-ASCII string returns the wrong
window (the check compares against the byte length) [2]; `it.TrimSuffix` keeps the whole sequence when
the trailing run is not a whole number of copies of the suffix [3].

## History

- 2026-09-19: created at a94fb4b (v1.53.0+, 2026-09-09) with 9 properties and 3 bugs.
