# decorum

[olson-sean-k/decorum](https://github.com/olson-sean-k/decorum): "making floating-point behave" —
a canonical total ordering, equivalence and hashing for IEEE 754 values (−∞ < … < 0 < … < ∞ < NaN,
all zeros equal, all NaNs equal), the `Total`/`NotNan` (`E64`)/`Real` (`R64`) proxy types with
composable constraints and divergences (`OrPanic`, `OrError<AsResult|AsOption|AsExpression>`),
`Expression`s that carry undefined results through arithmetic, and the `UnaryRealFunction`/
`BinaryRealFunction` traits. The 0.4 line on `master` (the crates.io release is still 0.3.1).

Written in the zoo (not imported from the predecessor), the same idea as the `ordered-float`
target: the primitives are the oracle and the documented relations the model. Default features;
the crate's own unit and doc tests run alongside `tests/hegel.rs`.

## What is tested

**`tests/hegel.rs`** — values are drawn as raw bit patterns (uniform bits, subnormals of either
sign, NaNs with any payload/sign, powers of two down to 2^−1074, small rationals, the special
constants) so that every class of the encoding is exercised.
- `canonical_relations_follow_the_documented_total_order` (+ an `f32` twin): `cmp_canonical`,
  `eq_canonical` and `to_canonical` against the model relation (antisymmetry, reflexivity,
  transitivity over three values; canonical forms equal exactly when the values are equivalent;
  `hash_canonical` equal for equivalent values); the same through `Total`'s `Ord`/`PartialOrd`/
  `Eq`/`Hash` (`Ord::max` keeps the second on ties); slices lexicographic then by length;
  `Total::from_slice` reinterprets bit for bit.
- `sorting_and_hashing_totals_matches_the_model`: sorting `Total`s agrees with the model order,
  a `HashSet<Total<f64>>` holds one element per equivalence class, NaNs sort last,
  `Iterator::min/max`.
- `empty_ordering_forwards_nans`: `EmptyOrd` (`is_empty`, `cmp_empty`) and `min_or_empty`/
  `max_or_empty`/`min_max_or_empty` for `f64`, `Total` and `Option` — NaN/`None` propagate, ties
  keep the first as minimum and the second as maximum.
- `constraints_admit_exactly_their_subsets`: `try_new`/`new`/`assert`/`TryFrom` for `Total`,
  `E64`, `R64` under every divergence (`Result`, `Option`, `Expression`, panic via
  `catch_unwind`) accept exactly the finite / non-NaN values and keep the bits; `from_subset`/
  `into_superset`/`From` conversions; `PartialEq<f64>`/`PartialOrd<f64>` never match a
  non-member; `try_from_slice` / `from_mut_slice`.
- `proxies_print_and_parse_like_primitives`: `Display`, `LowerExp`, `UpperExp`, precision,
  `Debug` (`Total(…)`/`Real(…)`), `FromStr` round trip, parsing a non-real into `R64<OrPanic>`
  panics, `Default`.
- `total_arithmetic_is_primitive_arithmetic`: every operator, assignment operator, unary and
  binary real function, `num_traits::Float` method (`classify`, `integer_decode`, `min`/`max`,
  `mul_add`, `signum`, constants), `Zero`/`One`, `sign`, `Sum`/`Product` (left folds),
  `ToPrimitive`/`FromPrimitive`/`NumCast` on `Total` equal the `f64` result bit for bit.
- `constrained_arithmetic_diverges_exactly_when_the_primitive_result_leaves_the_set`: for
  finite operands, `R64<OrError<AsResult>>` is `Ok(primitive result)` iff that result is finite,
  for `+ − × ÷ %`, mixed proxy/primitive operands, `recip`/`sqrt`/`ln`/`log2`/`exp`/`exp2`/
  `powi`/`tan`/`asin`/`acos`/`acosh`/`atanh`/`to_degrees`, `pow`/`log`/`hypot`/`div_euclid`/
  `rem_euclid`/`atan2`; `Option` and `Expression` divergences agree; `OrPanic` panics on the same
  cases; `NotNan` refuses exactly NaN results.
- `expressions_absorb_undefined_and_otherwise_compute`: chained `Expression` arithmetic equals
  the primitive when every intermediate is finite and is `Undefined` otherwise; `Undefined`
  absorbs every further operation; `map`/`defined`/`undefined`/`unwrap`/`Result::from`.
- `approx_comparisons_forward_to_the_primitives`: `abs_diff_eq`/`relative_eq`/`ulps_eq` on
  `Total` equal the `f64` versions.
- KNOWN FAILURES, one pinned test each: `is_one_means_equal_to_one` (decorum/1),
  `distinct_subnormals_are_not_equivalent` (decorum/2),
  `self_typed_functions_keep_the_constraint` (decorum/3).

## Oracles

The primitive `f64`/`f32` operations (bit-for-bit), the documented total order and equivalence
(`cmp` and `hash` module docs), the constraint definitions (`IsReal`: finite; `IsExtendedReal`:
not NaN; `IsFloat`: everything), `num_traits` and `approx` on the primitives.

## Not tested

`serde` (de)serialisation, the `unstable` `Try` feature, `Nan<T>` beyond `NAN`, custom
constraints, `no_std` builds, the `f32` proxies beyond ordering/equivalence, `Expression`
comparisons (`PartialEq`/`PartialOrd` on expressions), `sign()` of NaN (returns `Sign::Zero`;
implementation-defined).

## History

- 2026-09-13: written in the zoo against `d25892e62610` (2024-11-21, "Bump version to `0.4.0`")
  with hegeltest 0.44.1. **Three bugs on the first run, all found by reading the source and
  confirmed by the tests**: decorum/1 (`UnaryRealFunction::is_one` is `is_zero`), decorum/2
  (`to_canonical` merges pairs of `f64` subnormals — `Total` `Eq` disagrees with `Ord`),
  decorum/3 (`sin`/`cos`/`fract`/`sinh`/`cosh` bypass the constraint check — a `NotNan` holding
  NaN, a `Real` holding ∞; the 2018 issue #11 fixed the same hole for `sqrt`). Clean otherwise at
  100 + 3 × 1 000 + 10 000 cases.
