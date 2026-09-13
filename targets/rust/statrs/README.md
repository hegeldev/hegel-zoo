# statrs

[statrs-dev/statrs](https://github.com/statrs-dev/statrs).

## What is tested

**`src/distribution/internal.rs`**
- `prop_cdf_of_inverse_cdf_recovers_p`: PROPERTY 1 (crown round-trip, q side): for p in (0,1), cdf(inverse_cdf(p)) recovers p — checked against the tail mass q = min(p, 1-p) via whichever of cdf/sf is well conditioned on that side, so the deep tails are actually probed. Tolerance: rel_c()·q for the implementation's relative error under tail conditioning (see rel_c), plus pdf(x)·4ε|x| for the quantile's own representation limit (the true quantile can be off by half an ulp of x, which forward-maps through the density; e.g. Normal(1e5, 1e-6) deep tails are representation- not implementation-limited), plus abs_q() for Exp's absolute-accuracy cdf formula, plus a MIN_POSITIVE floor so subnormal tolerances don't underflow to zero.
- `prop_inverse_cdf_of_cdf_recovers_x`: PROPERTY 2 (crown round-trip, x side): inverse_cdf(cdf(x)) recovers x wherever cdf(x) is not saturated to 0 or 1. Tolerance in x-space: rel_c()·|x| for the inverse's relative error, plus the cdf's own error (1e-13 relative to the tail mass — 10x the crate's 1e-14 target — plus Exp's absolute floor) back-mapped through the density, plus the gamma family's documented 1e-9-absolute Newton stop, plus a MIN_POSITIVE underflow floor.
- `prop_cdf_monotone_nondecreasing_and_bounded`: PROPERTY 3: cdf is non-decreasing and stays within [0, 1] for *all* real inputs (inside or outside the support) and all valid parameters, including extreme magnitudes. Exact assertions — order and bounds are not subject to rounding. A NaN cdf value also fails these asserts.
- `prop_cdf_limits_at_support_bounds`: PROPERTY 4: cdf/sf limits are exact at the support boundaries: cdf(-∞) = 0, cdf(∞) = 1 (and the sf mirror images), and for finite support endpoints cdf(min) = 0 and cdf(max) = 1 — continuous distributions place no atom at their endpoints. These are exact branch behaviors of the implementations, so no tolerance applies.
- `prop_pdf_nonnegative_on_support`: PROPERTY 5: pdf is non-negative (and never NaN) everywhere on the support, for all valid parameters including extreme magnitudes. +∞ is allowed (density poles, e.g. Beta with shape < 1 at 0).
- `prop_sf_plus_cdf_is_one`: PROPERTY 6: sf(x) + cdf(x) = 1. The trait default computes sf as 1 - cdf, but Normal, Gamma, Exp, StudentsT and Uniform override sf with independent formulas, so this checks real consistency. Tolerance: both terms lie in [0, 1] and each is computed to ~1e-14 relative accuracy (crate target), so the sum is exact to ~2e-14 absolute; 1e-13 gives 5x headroom.
- `prop_mean_and_variance_match_closed_form`: PROPERTY 7: mean() and variance() match the documented closed-form formulas for the drawn parameters (formulas written in an equivalent but differently-ordered form where possible). Also pins the None-returning moment cases (StudentsT with small freedom).
- `prop_pdf_is_derivative_of_cdf`: PROPERTY 8: pdf is the derivative of cdf (central finite difference). The step is h = 1e-4·q/pdf(x) (q = tail mass at x): large enough that the cdf difference 2h·pdf ≈ 2e-4·q clears the cdf's ~1e-14·q error by ten orders, small enough that the truncation term (h·d(ln pdf)/dx)² is ≲1e-6 for the drawn parameter range. Parameter magnitudes are kept in [1e-1, 1e2] to protect the finite-difference *oracle* from roundoff blowup at power-law density poles — this bounds the test's arithmetic, not the library's contract (extreme parameters are covered by the exact-shape properties above). Tolerance 1e-3 relative: ~100x the worst expected truncation + roundoff.
- `prop_discrete_pmf_sums_to_cdf`: PROPERTY 9: for the discrete distributions, each pmf value is a probability, the running pmf sum reproduces the cdf at every point of the (truncated) support, and the total mass reaches 1. Tolerances: 1e-10 absolute for sum-vs-cdf, matching the crate's own `density_util::check_sum_pmf_is_cdf` precedent (a few hundred additions of values ≤ 1 accumulate ≲1e-13; the cdf itself targets ~1e-14). Binomial sums its whole support; Poisson is truncated at λ + 20√λ + 30, beyond which the omitted tail is < 1e-40, so the total must be within 1e-9 of 1. The size bounds (n ≤ 300, λ ≤ 100) protect the test's runtime, not any library contract.
- `prop_checked_constructors_reject_invalid_parameters`: PROPERTY 10: checked constructors reject out-of-domain parameters with Err (not panic, not silent acceptance), across every documented violation class for each distribution.

## Oracles

## Not tested

## History

- 2026-07-20: predecessor base commit `102945824c83` (chore: update MSRV lockfile).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/statrs.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1 (`floats().exclude_min(true)` → `min_value_exclusive`).
- 2026-09-13: base bumped 102945824c83 → 52248ee4f94e (2026-09-07, "fix: return None from Empirical::variance for a single sample"; 0.19.1); 8 bug(s) still reproduce; fixed upstream: statrs/1. 1036 tests pass. statrs/1 was fixed upstream (Gamma::pdf via ln_pdf with a frexp-based product; upstream's regression test is the zoo's case), and statrs/3 and statrs/9 are partially fixed (two of three pins each now pass and were dropped). The bump's runs also reached statrs/7's unwrap through Gamma::inverse_cdf from the two generic cdf/inverse_cdf round-trip properties, now listed as intermittent expected failures for statrs/7.
