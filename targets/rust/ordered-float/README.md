# ordered-float

[reem/rust-ordered-float](https://github.com/reem/rust-ordered-float): the `ordered-float` crate
(5.5: `OrderedFloat<T>`, a total order on floats with NaN greatest, and `NotNan<T>`, a float that
can never be NaN; `num-traits` impls for both).

Written in the zoo (not imported from the predecessor).

## What is tested

**`tests/hegel.rs`** — every property is instantiated for `f64` (`f64_::…`) and `f32` (`f32_::…`).
- `ordering_is_total_and_as_documented`: `OrderedFloat`'s `Ord`/`PartialOrd`/`Eq` follow the
  documented order exactly (NaNs equal and above everything, `-0.0 == +0.0`, otherwise the
  float's order) and obey the `Ord` laws — antisymmetry, transitivity, reflexivity, agreement
  between `cmp`, `partial_cmp`, `==` and the four operators, `Ord::max`/`min`; `PartialEq<T>`
  compares with the raw float; `NotNan` orders like the float and agrees with `OrderedFloat`.
- `sorting_and_sets_agree`: sorting `OrderedFloat`s gives the documented order with all NaNs
  last; `BTreeSet` and `HashSet` agree on the number of distinct values with the model, contain
  every inserted value, and find it under an equal-but-different key (the other zero, another
  NaN); the same for `NotNan` sets.
- `hash_is_consistent_with_eq`: equal values hash alike for both wrappers (both zeros, NaNs of
  any sign and payload), unequal ones differently under `DefaultHasher`, and `NotNan` hashes like
  `OrderedFloat`.
- `not_nan_arithmetic_equals_the_float_or_panics`: `+ - * / %` on `NotNan` (by value, by
  reference, `*Assign`, and with a bare float on the right, which yields a bare float), `Neg`,
  `Sum`, `Product` and `Pow` (integer and float exponents) equal the float operation bit for bit
  when it is not NaN and panic exactly when it is (`catch_unwind`); `OrderedFloat` arithmetic is
  the float's, NaN and all.
- `not_nan_real_methods_equal_the_float_or_panic`: the 40 other `Real`/`Signed` methods of
  `NotNan` (`floor` … `atanh`, `powf`, `log`, `hypot`, `atan2`, `powi`, `sin_cos`, `abs_sub`, …)
  equal the float's result or panic when it is NaN, and the sign predicates are the float's.
- `not_nan_fract_and_mul_add_never_hold_nan`: the same for `Real::fract` and `Real::mul_add`.
  KNOWN FAILURE ordered-float/1 — both return a `NotNan` holding NaN.
- `conversions_parsing_and_formatting_are_transparent`: `NotNan::new`, `TryFrom`, `NumCast`,
  `FromPrimitive`, `FromStr` and `from_str_radix` reject exactly NaN (with `FloatIsNan` /
  `ParseNotNanError::IsNaN`; garbage is `ParseFloatError`); `Display`/`Debug`/`LowerExp`/
  `UpperExp` are the float's and round-trip through both parsers; `Deref`/`AsRef`/`into_inner`/
  `From<wrapper> for T`/`ToPrimitive`, `Bounded`/`Zero`/`One`, and every `FloatCore` method of
  `OrderedFloat` are the float's.
- `widening_and_narrowing` (once): `From<…<f32>>` for the `f64` wrappers is exact,
  `NotNan<f64>::as_f32` rounds like `as f32` and never yields NaN, and the integer/`bool` `From`
  impls are exact.

Inputs are `floats::<T>()` mixed 40/60 with the corners the wrappers are about: both zeros, both
infinities, NaNs with random sign and payload (`from_bits`), `MAX`/`MIN`/`MIN_POSITIVE`/
`EPSILON`, small constants and small integers.

## Oracles

The primitive float operations (`f32`/`f64` and `num-traits`' `Real` on them), the `Ord` laws,
the documented order as a model (`model_cmp`), `Hash`/`Eq` consistency via `DefaultHasher`, and
`std::panic::catch_unwind` around every `NotNan` operation: it must panic exactly when the float
result is NaN, and a `NotNan` whose value `is_nan()` is the worst outcome (`x == x` is then
false and `x.cmp(&x)` panics).

## Not tested

The feature-gated integrations (`serde`, `rand`, `arbitrary`, `bytemuck`, `rkyv`, `schemars`,
`speedy`, `borsh`, `facet`, `derive-visitor`, `num-cmp`, `proptest`), `Float`/`Real` methods on
`OrderedFloat` beyond `FloatCore` (no invariant to break), `AsPrimitive`, `no_std`/`libm` builds.

## History

- 2026-09-13: written in the zoo against `650b3dddbb8a` (2026-08-21, "Test code cleanup";
  5.5.0) with hegeltest 0.44.1. First run: **ordered-float/1** — `Real::fract` and
  `Real::mul_add` for `NotNan` wrap the float result unchecked, so `NotNan(∞).fract()` and
  `mul_add` with a `0 · ∞` product are `NotNan` values holding NaN (not reported upstream; a
  sweep of the special values over every other `Real`/`Signed` method found no other leak). The
  order, hashing, arithmetic panics and conversions hold at 3 × 10 000 cases.
