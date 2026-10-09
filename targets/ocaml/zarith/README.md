# zarith

`Z` and `Q`, against Python's `int` and `fractions.Fraction`, and their parsers against
`int_of_string`/`float_of_string`, the references upstream's own tests use.

## What is tested

Integers are drawn on both sides of the small-int boundary (2^62) and across 64-bit limbs.

- `arithmetic_agrees`, `unary_agrees`, `division_agrees`, `division_pairs_agree`,
  `divexact_agrees`: every rounding of division, including by zero.
- `bitwise_agrees`, `shifts_agree`, `bit_counts_agree`, `hamdist_agrees`, `testbit_agrees`,
  `extract_agrees`: two's-complement semantics on negatives.
- `sqrt_agrees`, `root_agrees`, `pow_agrees`, `perfect_powers_agree`, `gcd_agrees`,
  `gcdext_is_bezout`, `invert_agrees`, `primality_agrees`, `nextprime_agrees`.
- `int_conversions_agree`, `fits_agree_with_conversions`, `to_float_agrees`, `of_float_agrees`.
- `format_agrees`, `of_string_agrees`, `of_string_base_agrees`,
  `of_string_agrees_with_int_of_string`.
- `results_hash_as_reparsed`: results are in canonical form.
- `q_make_is_canonical`, `q_arithmetic_agrees` (inf, -inf and undef as IEEE), `q_compare_agrees`,
  `q_to_float_agrees`, `q_of_float_agrees`, `q_of_string_agrees`,
  `q_of_string_signs_agree_with_float_of_string`, `q_of_string_parts_agree_with_float_of_string`.

## Setup

Upstream builds with `configure` and `make`, so `hegel/` is a dune project of its own over
symlinks to the checked-out sources, with GMP found through `pkg-config` (`libgmp-dev` on
Linux, `gmp` from Homebrew on macOS).

## Not tested

`Big_int_Z`, marshalling, the `nativeint` conversions, `Q.of_string`'s binary and octal forms.

## History

- 2026-10-09: created at 7bbc77f0 (1.14+), hegel-ocaml 0.26.1; zarith/1-4.
