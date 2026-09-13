# noisy_float

[SergiusIW/noisy_float-rs](https://github.com/SergiusIW/noisy_float-rs): `N32`/`N64` (no NaN)
and `R32`/`R64` (finite only) wrappers that `debug_assert!` their invariant after every
operation, with `Eq`/`Ord`/`Hash`, the `num_traits` float traits, `serde` and `approx`
integrations, and custom `FloatChecker`s.

Written in the zoo (not imported from the predecessor), the same recipe as `ordered-float` and
`decorum`: the primitives are the oracle, the checkers the model. Built with `--all-features`
(`serde`, `approx`); the test profile keeps `debug_assert!` on, so the checks are live (in
release builds the crate deliberately checks nothing). The crate's own unit and doc tests run
alongside `tests/hegel.rs`.

## What is tested

**`tests/hegel.rs`** — values are drawn as raw bit patterns (uniform bits, subnormals, NaN
payloads, powers of two, the special constants).
- `constructors_admit_exactly_the_checked_values`: `try_new`/`try_borrowed(_mut)`/`TryFrom`/
  `NumCast`/`FromPrimitive` accept exactly the non-NaN (finite) values; `new`/`n64`/`r64`/
  `borrowed`/`from_f64` panic exactly on the rest (`catch_unwind`); accepted values are kept bit
  for bit through `raw`/`From`/`AsRef`/`const_raw`/`R64 → N64`; `Display`/`Debug`/`LowerExp`/
  `UpperExp`/precision and `Num::from_str_radix` match the primitive; `PartialEq<f64>`/
  `PartialOrd<f64>` against any primitive including NaN.
- `ordering_equality_and_hashing_are_consistent`: `Ord`/`PartialOrd`/`Eq` equal the primitive
  partial order (±0 equal), equal values hash alike, the inherent `min`/`max` (`Ord`, second on
  ties) and `Float::min/max` agree with the primitive, sorting and `HashSet` size against the
  model, `f32` twins and the `f32 → f64` conversions.
- `arithmetic_equals_the_primitive_or_panics_on_an_invalid_result`: every operator (by value,
  by reference, with a primitive right-hand side, assignment forms), `Neg`, and every
  `num_traits::Float` function (`recip`…`atanh`, `mul_add`, `to_degrees`, `abs_sub`, `signum`,
  `floor`, `fract`) on `R64` and `N64` either equals the primitive result bit for bit or panics
  exactly when that result is non-finite (`R64`) / NaN (`N64`), including `∞ − ∞`, `∞ × 0`,
  `sin(∞)`, `fract(−∞)`, `0/0`; predicates, `integer_decode`, `ToPrimitive`, `Signed::abs`.
- `constants_sums_products_and_casts`: `FloatConst`, `Float`/`Bounded` bounds, `Zero`/`One`/
  `neg_zero`/`Default`, `N64::infinity`; `R64::infinity`/`nan` panic; `Sum`/`Product` (left folds,
  panicking when the total is invalid); `FromPrimitive`/`NumCast` from `i64`/`u128`/`i32`;
  `from_str_radix` on finite, overflowing, infinite, NaN and malformed text (panic exactly when
  the primitive parses to a non-finite value, as the crate's panic rule says).
- `serde_and_approx_forward_to_the_primitive`: transparent JSON (equal to the primitive's,
  read back through the checker — a custom positive-only checker refuses `≤ 0`), `null`
  refused; `abs_diff_eq`/`relative_eq`/`ulps_eq` and the default tolerances equal the
  primitive's; a custom `FloatChecker` panics on the values it rejects for `new`, `+`, `-`, `Neg`.

## Oracles

The primitive `f64`/`f32` operations (bit-for-bit), the two checkers' definitions (`NumChecker`:
not NaN; `FiniteChecker`: finite), the crate's stated rule ("if an invalid value would ever be
returned from a method, the method panics instead; methods returning `Option` return `None`"),
`num_traits`, `approx`, `serde_json`.

## Not tested

Release-profile behaviour (no checks by design), `no_std`, `Hash` byte layout beyond equality,
`f32` beyond ordering and conversions, `serde_json`'s own float parsing (it is a ULP off without
its `float_roundtrip` feature, so the JSON round trip is compared with `serde_json`'s `f64`
parse, not with the original value).

## History

- 2026-09-13: written in the zoo against `7103ad04808c` (2026-01-05, "updated version"; 0.2.1)
  with hegeltest 0.44.1. The whole crate (1 900 lines) was read first: every method forwards to
  the primitive and re-checks — nothing found by eye and **nothing found by the tests**; clean at
  100 + 3 × 1 000 + 10 000 cases. Test defects on the way: `Ord::max` keeps the second argument
  on ties, `serde_json` refuses `1e400` itself and parses tiny values a ULP off.
