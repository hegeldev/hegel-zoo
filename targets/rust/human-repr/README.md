# human-repr

[human-repr](https://github.com/rsalmei/human-repr) prints counts (`43.21GB`, `540.5kPackets`),
durations (`15.6µs`, `3.44s`, `19:20.4`, `1:14:48`) and throughputs (`1.2MB/s`, `6.1tests/min`,
`9/d`) from any primitive number or `std::time::Duration`, choosing the prefix or clock form
after rounding so that `0.000999999` s is `1ms`, with no allocation, `PartialEq<&str>` against
the text, a `Debug` that shows value and text, and optional serde. Written in the zoo at 1.1.0
(upstream HEAD `2e8f831`, 2023-04-19); tests in `tests/hegel.rs`, run with `--features serde`
(about a minute to build — criterion is a dev-dependency).

## The oracles

Each representation is parsed back in the test and checked against the documented structure —
the SI prefix table with its decimal budget (1, 1, 1, then 2), the printed number below 1000
(24, 60 for the throughput scales; 60 for seconds) and at least 1 unless no prefix applies, no
trailing zero decimals, the `M:SS[.s]` and `H:MM:SS` forms with fields below 60 — and against
the input: the value read back is within half a unit of the last allowed decimal. That pins the
output up to rounding ties without re-implementing the algorithm. The three faces of a
representation (`Display`, `PartialEq<&str>`, `Debug`) and the serde round trip are checked
against each other, and `-x` must print as `-` followed by the text of `x`.

## Properties

- **Counts** (`counts_read_back`, `negative_counts_mirror_positive_ones`): eight units (bare,
  `B`, words, `°C`, an emoji), magnitudes 10^-3…10^26 of either sign; the convenience forms
  `human_count_bare`/`_bytes`, integer inputs, `PartialEq<&str>` (also against a lengthened and a
  shortened text), `Debug`, serde.
- **Durations** (`durations_read_back`): 10^-10…3600 s from `f64` and from `Duration`
  (`from_secs_f64`, read back against the exact `secs + nanos`); the form matches the value shown
  (no colon below a minute, one below an hour). `hours_form_is_well_formed`: `H:MM:SS` fields
  in range and within a second of the value.
- **Throughputs** (`throughputs_read_back`, `negative_throughputs_mirror_positive_ones`):
  `/d`, `/h`, `/min` and `/s` with SI prefixes; a per-second rate is the count of the same
  value followed by `/s`, to within the last decimal.
- The general generators keep to values below 10^26 (from 999.995 Y the documented `+` overflow form takes over), to
  durations below an hour for the exact read-back (human-repr/2), and skip values that print as
  zero in the mirror properties (human-repr/3).

## Bugs (4)

- **human-repr/1** (wrong-result, medium; `negative_durations_mirror_positive_ones`): negative
  durations from a minute up have no sign handling: `-61` s → `-1:-1`, `-125.825` → `-2:-5.8`,
  `-3661` → `-61:-1` (the hours branch is never reached), `-100000` → `-1666:-40`.
- **human-repr/2** (wrong-result, low; `hours_form_rounds_to_the_second`): `H:MM:SS` truncates
  the seconds after rounding to a tenth: `3600.9` → `1:00:00`, `3659.94` → `1:00:59`, `3659.95`
  → `1:01:00`.
- **human-repr/3** (wrong-result, low; `values_rounding_to_zero_have_no_sign`): values rounding
  to zero keep the sign: `-0B`, `-0ns`, `-0B/d`.
- **human-repr/4** (contract, low; `non_finite_durations_are_not_clock_times`): infinite
  durations print `inf:NaN:NaN` / `-inf:0NaN`; `1e300` s overflows to the same; NaN is `NaNns`.

## Not bugs

- Beyond yotta the count prints `<value / 10^27>+<unit>` (`u128::MAX` → `340282366920.94+B`),
  pinned by upstream's tests; fractional bytes (`23.5B`) likewise.
- `NaNB`, `inf+B`, `NaNB/d` for non-finite counts and throughputs: legible degradation.
- Huge durations lose precision in `f64` (`1e20` s → `27777777777777776:56:36`); a per-second
  throughput reaches `human_count` through `×86400/24/60/60`, so on an exact decimal tie its
  last digit can differ from the count of the same value by one (float round-off, not counted).
- `serde_json` needs its `float_roundtrip` feature to read its own floats back exactly; the
  patch enables it on the dev-dependency.
