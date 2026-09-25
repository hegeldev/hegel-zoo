# bitset

[bits-and-blooms/bitset](https://github.com/bits-and-blooms/bitset) is the widely used Go
bitset: a growable set of bits with a length (`Len`) and the usual algebra (union,
intersection, difference, symmetric difference and their in-place and cardinality forms),
ranges, flips, shifts, insertion and deletion, rank and select, navigation (`NextSet`,
`NextClear`, `PreviousSet`, `PreviousClear`, `NextSetMany`, `EachSet`), PEXT/PDEP
(`Extract`, `Deposit`), copying, comparison, word-level access and a binary and JSON form.
About 1 500 lines, BSD-3-Clause, pinned at `828abff` (2026-09-03, after v1.25.0). README,
SECURITY.md and LICENSE are the project documents and say nothing about AI-written code.
The package has thirteen Go fuzz tests of its own (`bitset_fuzz_test.go`), mostly
self-consistency checks; the zoo's properties compare against an independent model.

## Build

`go test -count=1 -run TestHegel -v .` in the module root. The patch adds `hegel_test.go`
(the model and the wide properties), `hegel_shapes_test.go` (one narrow property per bug) and
`hegel_pins_test.go` (one plain regression example per bug) and requires
`hegel.dev/go/hegel v0.6.33` in go.mod.

## Oracles

- **A model of the documented semantics**: a bitset is `Len` bits, some set, and bits at
  or beyond `Len` are clear. Every operation is written against a `[]bool`: `Set`, `Flip`,
  `SetRange` and `FlipRange` extend the length, `Clear` does not; `InsertAt` and `DeleteAt`
  shift the bits above the index and change the length by one; `ShiftLeft` moves the set
  bits up and extends the length to cover them; `Complement` flips within the length;
  `Union` and `SymmetricDifference` take the longer length, `Intersection` the shorter,
  `Difference` the receiver's; `Copy` copies `min(Len)` bits and leaves the rest of the
  destination; `CopyFull` makes the destination identical; `Extract` packs the bits at the
  mask's set positions, `Deposit` spreads them back, both reading clear bits beyond the
  source's length; `Rank(i)` counts set bits at or below `i`, `Select(j)` is the `j`-th set
  bit or `Len`, `OnesBetween` clamps to the length; `NextClear` and `PreviousClear` only see
  bits within the length; `String` is `{a,b,c}`, `DumpAsBits` the words high to low in
  binary with a dot after each.
- **The binary format** as `WriteTo` documents it: a 64-bit length then the words, big-endian
  by default or little-endian after `LittleEndian()`, encoded independently in the test;
  `BinaryStorageSize` is its size; the JSON form is that encoding in base64 (URL alphabet).
- **The documented contracts**: chaining methods return their receiver; `From` shares its
  slice and `Words` gives the live representation; `FromWithLength` panics on a short slice;
  `Cap` is the range of `uint`; a truncated binary input is an error that leaves the set
  empty or unchanged; trailing bytes stay in the stream.

## Properties

| Property | Checks |
|---|---|
| SingleSetOperations | a set from `New`, `MustNew`, the zero value, `From` or `FromWithLength`, then 1–25 operations among Set, Clear, Flip, SetTo, SetRange, FlipRange, ClearAll, SetAll, InsertAt, DeleteAt, ShiftLeft, ShiftRight, Shrink, Compact, Complement and Clone at positions up to 5000 (mostly under 200, with word boundaries): after each, Len, Count, every bit up to Len+70, Any/All/None, Words, EachSet, AppendTo, AsSlice, String, DumpAsBits, Clone/Equal and BinaryStorageSize agree with the model, and at random indices NextSet, NextClear, PreviousSet, PreviousClear, Rank, OnesBetween, GetWord64AtBit, NextSetMany and Select do too |
| TwoSetOperations | two sets (sometimes clones): Equal, IsSuperSet and IsStrictSuperSet against the model; one of Union, Intersection, Difference, SymmetricDifference with its cardinality and in-place form (operands unchanged, in-place result Equal to the functional one); Copy (returned count, copied bits, the rest of the destination) and CopyFull |
| ExtractAndDeposit | Extract and ExtractTo (into a clear destination of random length) against PEXT, Deposit and DepositTo (into a destination with bits of its own) against PDEP, operands unchanged |
| Serialization | MarshalBinary and WriteTo equal the independent encoding in both byte orders, BinaryStorageSize equals its size; UnmarshalBinary and ReadFrom (into a fresh or a used set, with trailing bytes left in the stream) give an Equal set; MarshalJSON is the base64 of the encoding and round-trips; truncated inputs fail and leave the set empty or unchanged |
| WordsAndConstructors | From shares its words (changes show through), SetBitsetFrom replaces the content, writing through Words changes the set, Bytes is Words, Cap, FromWithLength panics on a short slice |

The generators draw the shapes of the seven recorded bugs and the properties that meet them
are the expected failures mapped to the bugs (STYLE.md rule 11): SingleSetOperations lands on
/2 (queries beyond the length; half of its cases also meet /1), TwoSetOperations on /3
(operands of different lengths; /4 in a few percent of cases), ExtractAndDeposit on /5
(zero-value sources; /6 in some; it passed one run in a hundred cases, so it is mapped
intermittent), Serialization on /7 (a quarter of its cases carry a header
of 2^52 to 2^64-1 - smaller impossible headers, 2^51 say, are a fatal out-of-memory rather
than a recoverable panic, so the test does not draw them). One narrow property per bug in
`hegel_shapes_test.go` draws the bug's shape region with random contents and fails every run:
`PreviousSetLooksBackBeyondTheLastWord` (/1), `PreviousClearStaysWithinTheLength` (/2),
`InPlaceIntersectionEqualsIntersection` (/3, both length orders), `CopyLeavesTheRestOfTheDestination`
(/4), `ExtractToExtendsForAnEmptySource` (/5), `DepositToClearsBeyondTheSource` (/6) and
`ReadFromRejectsAnImpossibleLength` (/7). `HEGEL_NO_KNOWN=1` switches the shapes off (the
`Known` gates come on and the generators draw the neighbouring regions: queries below the
length, equal lengths, masks within the source's words, honest headers) and all twelve
properties pass, at 1000 cases in about two seconds. `BITSET_COLLECT=1` records mismatches
instead of failing and prints them shortest-first with the case's description; `HEGEL_VERBOSE=1`
turns on the engine's log.

## Bugs (7; details in bugs.toml)

| id | summary | severity |
|----|---------|----------|
| bitset/1 | `PreviousSet` and `PreviousClear` answer "not found" for an index beyond the last allocated word, whatever bits are set (`PreviousSet(100)` on `{3}` of Len 8) | medium |
| bitset/2 | `PreviousClear` reports positions at or beyond Len as clear bits, and "found" on a full set | low |
| bitset/3 | `InPlaceIntersection` extends the receiver to the other set's length while `Intersection` keeps the shorter, so the two results are not `Equal` | low |
| bitset/4 | `Copy` clears the destination's bits between the source's length and the end of the source's last word (5 bits into a full 100-bit set leaves 37 set, not 96) | medium |
| bitset/5 | `ExtractTo` does not extend the destination when the source has no words (`Extract` does) | low |
| bitset/6 | `DepositTo` leaves mask positions unchanged, instead of clearing them, once the source's words are exhausted | low |
| bitset/7 | `ReadFrom`/`UnmarshalBinary` allocate for whatever length the header claims: an 8-byte input panics (`makeslice: len out of range`) or asks for gigabytes instead of returning an error | medium |

How they were found: the first six by the first collect round of the model properties
(navigation at indices beyond the length, the in-place/functional comparison, Copy into a
longer destination, ExtractTo from a zero-value source, DepositTo into a destination with
bits and a mask wider than the source's word), each then reduced by a probe to the one-line
shape in bugs.toml; bitset/7 by a probe of `ReadFrom` with a corrupt length header after
reading its allocation code. Everything else agrees with the model: the algebra and its cardinalities, ranges,
shifts, insertion and deletion, rank and select, iteration, the textual forms, the binary
and JSON formats in both byte orders, and the word-level constructors.

## Accepted differences (not bugs)

- `ShiftRight` leaves the length alone except when the shift is a whole number of words,
  when it subtracts them; the properties only require the length to cover the bits and not
  to grow, and re-synchronise the model.
- `Compact` sets the length to a whole number of words (64 for an empty set, even one of
  length 10); documented as minimising memory, not length. `Shrink(i)` sets the length to
  `i+1` even when that grows it within the allocated words (`Shrink(40)` on a 10-bit set
  gives 41), and is a no-op when `i+1` needs more words than allocated — the documentation
  says the new length is `i+1`; the properties model the implementation here.
- `InsertAt` and `DeleteAt` are exercised only at indices below the length, and
  `AsSlice` only with a large enough buffer, as documented.
- `Base64StdEncoding()` switches the JSON alphabet for the rest of the process with no way
  back; the properties leave it at the default.

## Not tested

Behaviour at the capacity limit (`Cap`), allocation failure paths, the 32-bit build,
`cmd/`, and performance.
