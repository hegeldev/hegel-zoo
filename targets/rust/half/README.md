# half

[VoidStarKat/half-rs](https://github.com/VoidStarKat/half-rs): the `half` crate, IEEE 754 binary16
(`f16`) and bfloat16 (`bf16`) with conversions, arithmetic, `num-traits` impls and vectorised slice
conversions.

Written in the zoo (not imported from the predecessor). Run with `--features num-traits` so the
`Float` impls (`mul_add`) are compiled.

## What is tested

**`tests/hegel.rs`**
- `f16_from_f32_is_correctly_rounded`: `f16::from_f32` (and the software `from_f32_const`) round to nearest, ties to even, as documented ("rounded to the nearest representable value"), including into subnormals and to infinity on overflow; NaN stays NaN.
- `bf16_from_f32_is_correctly_rounded`: `bf16::from_f32` (and `from_f32_const`) round to nearest even.
- `f16_from_f64_is_correctly_rounded`: `f16::from_f64` rounds the `f64` to the nearest `f16` directly — the docs promise the nearest representable value, which rounding through `f32` first does not give near the midpoints (a value just above an `f16` midpoint that `f32` rounds *onto* the midpoint is then rounded to even, i.e. the wrong way). KNOWN FAILURE half/1 (upstream #116).
- `f16_from_f64_const_is_correctly_rounded`: Same for the software (`const`) path, which must not truncate mantissa bits before deciding how to round. KNOWN FAILURE half/2 (upstream #151).
- `bf16_from_f64_is_correctly_rounded`: `bf16::from_f64` / `from_f64_const` round to nearest even directly from the `f64`. KNOWN FAILURE half/2.
- `widening_is_exact_and_round_trips`: Widening is exact: `to_f32`/`to_f64` (and the `const` variants) give the exact value of the bit pattern, so every finite `f16`/`bf16` round-trips through `f32` and `f64`; infinities and NaNs keep their kind and sign.
- `slice_conversions_match_elementwise`: The slice conversions (vectorised in chunks, with a scalar tail) agree bit for bit with the element-wise conversions, for every length up to a few chunks, and `to_f32_vec`/`to_f64_vec` agree with `to_f32`/`to_f64`.
- `f16_arithmetic_is_correctly_rounded`: `+ - * /` on `f16` are correctly rounded (a single rounding of the exact result; computing in `f32` and rounding once more is fine here because `f32` carries more than 2·11+2 bits).
- `bf16_arithmetic_is_correctly_rounded`: `+ - * /` on `bf16` are correctly rounded.
- `f16_mul_add_is_fused`: `num_traits::Float::mul_add` is documented as a *fused* multiply-add: "Computes `(self * a) + b` with only one rounding error". So the result must be the exact `a·b + c` rounded once to `f16`. KNOWN FAILURE half/3 (upstream #141), intermittent at the default budget.
- `bf16_mul_add_is_fused`: Same for `bf16`. KNOWN FAILURE half/3, intermittent.
- `classification_follows_the_bits`: `classify`, `is_nan`, `is_infinite`, `is_finite`, `is_normal`, the sign predicates, `signum` and `copysign` follow the bit pattern (a subnormal `f16` is *subnormal*, even though it widens to a normal `f32`).
- `ordering_matches_values_and_total_order`: `total_cmp` is IEEE 754's totalOrder (−NaN < −∞ < … < −0 < +0 < … < +∞ < +NaN, NaNs by payload); `PartialOrd`/`PartialEq` agree with the exact values (NaN unordered, `-0 == +0`); `max`/`min`/`clamp` follow their documentation (NaN arguments are ignored).
- `formatting_round_trips_through_from_str`: `Display`, `Debug`, `LowerExp` and `UpperExp` print a decimal that parses back (via `FromStr`) to the same value, for every finite value and both infinities.
- `from_str_rounds_to_nearest`: `FromStr` rounds a decimal to the nearest `f16`/`bf16`. Two kinds of input: a short random decimal, whose nearest value the oracle gets by parsing it as `f64` (exact enough: a decimal of ≤ 12 significant digits is never within an `f64` rounding error of an 11-bit midpoint without being that midpoint) and rounding once; and a *crafted* decimal — the exact decimal expansion of a midpoint between two adjacent values (a tie, rounds to even), that expansion with a `1` appended (just above: rounds up), or a decimal just below it (rounds down) — whose answer is known by construction. Parsing via `f32` first loses the side information for the crafted inputs. KNOWN FAILURE half/4 (new).

## Oracles

Exact arithmetic: every finite `f16`/`bf16`/`f32`/`f64` is `mantissa · 2^exp`, so conversions,
`+ - * /` and `a·b + c` are evaluated exactly as `num / den · 2^exp` in `i128` and rounded to
nearest-even by hand (`round_magnitude`, generic over the format; terms more than 2^100 apart are
replaced by a sticky bit). Inputs are aimed at the hard cases: midpoints between adjacent values
and their `f64`/`f32` neighbours. Classification, sign, ordering and formatting are checked
against the bit patterns and against `f64`.

## Not tested

`rand_distr` impls (feature-gated; upstream #152 reports out-of-range samples), `serde`/`bytemuck`/
`zerocopy`/`rkyv` integrations, the transcendental `Float` methods (`sqrt`, `exp`, `ln`, `powf`,
… — computed in `f32` and rounded; no exactness promise), `Sum`/`Product` accumulation order,
`FromPrimitive`/`ToPrimitive`, `HalfBitsSliceExt::reinterpret_cast`, non-x86 intrinsic paths (the
zoo runs on x86-64 with F16C, like GitHub's runners).

## History

- 2026-09-13: written in the zoo against `688f1e2c2a54` (2026-02-11, "Merge pull request #139
  from VoidStarKat/dependabot/cargo/bytes-1.11.1"; 2.7.1) with hegeltest 0.44.1. First run:
  **half/1** (`f16::from_f64` through the F16C intrinsics double-rounds via `f32`; upstream #116),
  **half/2** (software f64 conversions truncate the low 32 mantissa bits before rounding;
  upstream #151), **half/3** (`mul_add` is not fused; upstream #141, fix PR #146 open) and
  **half/4** (`FromStr` parses as `f32` and rounds again — not reported upstream). Arithmetic,
  widening, slice conversions, classification, ordering and formatting hold at 10 000 cases.
