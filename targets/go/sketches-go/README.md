# go/sketches-go

[DataDog/sketches-go](https://github.com/DataDog/sketches-go) is the Go implementation of
DDSketch, a mergeable quantile sketch with a relative-error guarantee: for any quantile the
returned value is within a relative accuracy alpha of the true one. It has three index
mappings (logarithmic, linearly and cubically interpolated), five stores (dense, sparse,
buffered-paginated, collapsing-lowest and collapsing-highest), a variant tracking exact
count/sum/min/max, and byte and protobuf encodings. Pinned at `228b76a` (v1.4.8, 2026-08-06,
Apache-2.0; CONTRIBUTING.md has no AI policy).

## Build

The tests live in a new package directory `hegel/` of the upstream module and use the
library as a black box; `go.mod` gains `hegel.dev/go/hegel`. The run command is
`go test -count=1 -run TestHegel -v ./hegel`. No oracle outside Go is needed.

## Oracle

Every sketch is built beside its exact model: the list of (value, count) pairs added.
Values below the mapping's minimum indexable value count as zero, as the sketch documents.
The model applies the sketch's own rank rule (rank = q(count-1), the first value whose
cumulative count exceeds it, negative values by magnitude from the top) to the exact values,
and the DDSketch guarantee is asserted against that value with the mapping's reported
relative accuracy: quantiles, minimum, maximum, and the sum for same-sign data. Counts are
1, small integers or dyadic fractions, so every sum is exact on both sides. Stores are
checked against a map from index to count, with the collapsing rule (bins beyond the limit
folded into the edge bin) applied to the model. Summary statistics are checked against exact
running count, sum (within 1e-9 of the sum of magnitudes), min and max.

## Properties

- `TestHegelMapping`: each mapping (by accuracy or by gamma and offset) maps every indexable
  value, the ends of the range included, to a bin whose representative is within the
  accuracy; Index monotone and within int32; LowerBound brackets the value and the
  representative; Equals; proto and byte round trips, truncated bytes refused; bad
  parameters refused.
- `TestHegelAccuracy`: the guarantee over every mapping and store with values of both signs,
  zeros, untrackably small values and enormous ones (too large refused with the documented
  error), fractional counts; count and zero count exact; quantiles monotone and within
  [min, max]; the collapsing stores keep the guarantee for the quantiles whose bins survive;
  bad quantiles and bad additions refused without changing the sketch; the exact-summary
  sketch returns exact statistics and quantiles clamped to them.
- `TestHegelOperations`: MergeWith across store types is the union of the data (mappings
  must match; empty sketches; the argument and copies unchanged); Copy independent; Clear
  empties and the sketch is reusable; Reweight scales every count and keeps the quantiles;
  ChangeMapping keeps the count and the zero count and the quantiles within the combined
  bin ratio.
- `TestHegelStores`: the five stores against a map under Add, AddWithCount, AddBin, MergeWith
  (any type), Reweight, Copy, Clear; TotalCount, IsEmpty, MinIndex, MaxIndex, ForEach, Bins,
  KeyAtRank (including negative ranks and ranks beyond the total); proto round trip and
  MergeWithProto; copies independent.
- `TestHegelEncoding`: byte round trips into every store type with and without the mapping,
  DecodeAndMergeWith, a missing or mismatched mapping refused, re-encoding; protobuf via
  ToProto/proto.Marshal/FromProto, EncodeProto and the collection builder; the exact-summary
  sketch's statistics survive; truncated data refused; damaged bytes never panic.
- `TestHegelSummaryStatistics`: stat.SummaryStatistics under Add, MergeWith, Reweight,
  Rescale (negative factors swap min and max), Copy, Clear; FromData validation.

## Bugs

Nine recorded (bugs.toml), each with a pin. Three of note: a sketch whose total count is
below 1 (fractional counts) answers every quantile from the *empty negative store* (-0 or
-(1 + alpha) for a sketch holding only 5), because the rank q(count-1) is negative; and
`DecodeDDSketch` cannot read an encoded exact-summary sketch as documented, since it skips 8
bytes for a count that is a varfloat64; and merging into an empty collapsing store another
collapsing store whose bins span more than the receiver's limit panics. The rest: NaN accepted as a count, as a quantile and
as a relative accuracy; ChangeMapping loses or NaN-poisons the topmost bin when its upper
bound overflows, and panics (dense store) or files counts at MinInt64 when the scaled values
leave the new mapping's range; FromProto/MergeWithProto do not apply MaxDecodeIndexRange.

## Modelled as recorded, not counted

- KeyAtRank of an empty store differs by store type (MinInt32 sentinel for the dense ones, 0
  for the others); the source carries a FIXME for it, and the sketch never asks (except
  through bug 3).
- Reweight(0) returns "can't reweight by a negative factor"; the doc requires a factor
  strictly above 0, so only the message is off.
- The interpolated mappings' `WithGamma` constructors take gamma in their own convention
  (gamma^ln2, gamma^(10 ln2/7)), so a mapping built by accuracy is not Equals to one built
  from the logarithmic gamma; the properties rebuild through the same constructor.
- A dense store allocates its whole index range ("bound only by the size of the slice that
  can be allocated"): the int32 extremes are fed only to the sparse and collapsing stores.
- After ChangeMapping the split proportions of a bin may sum to 1 - 1e-16, so a quantile at
  an exact rank boundary may answer with the value one rank below; accepted.
- Reweight(0) of summary statistics whose sum has already overflowed to +-Inf leaves a NaN
  sum; not counted.
- One development run of `TestHegelEncoding` (500 cases) saw a single proto round trip of a
  one-point sketch (linear mapping, alpha 0.2, sparse store) decode by `FromProto` to a bin
  tens of indexes away (-2.5e11 for -0.6). It did not recur in 3300 further cases, with and
  without the race detector, and the dense store has no shared state; the diagnostic now
  prints both stores' bins so a recurrence can be read. Unreproduced, not recorded.
