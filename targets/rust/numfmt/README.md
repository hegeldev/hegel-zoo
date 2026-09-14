# numfmt

[numfmt](https://github.com/kurtlawrence/numfmt) is a fast, configurable number formatter:
`Formatter` scales a number (`Scales::short/metric/binary` or custom), switches to scientific
notation outside 10^-3 ≤ |x| < 10^12, inserts a thousands separator, truncates at a
`Precision` (decimals or significant figures), and decorates with prefix, unit and suffix; a
small format-string grammar (`prefix[.2%/ ]suffix`) parses into a `Formatter`. Written in the
zoo at 1.2.0 (upstream HEAD `8e034f3`, 2025-07-16); tests in `tests/hegel.rs` (about two
minutes to build — criterion is a dev-dependency).

## The oracles

A model of the documented procedure written in the test: `Scales::scale` re-implemented from
its examples, the documented cut-offs for scientific notation (plus the crate's "low precision"
adjustment, 10^-d for d ≤ 3), the digits of the scaled value as **`dtoa`** prints them (the
crate copies dtoa's text, so `0.00316114` is `0.0031611399999999999` on both sides — Grisu2 is
not always shortest; that is dtoa's, not counted), grouping by threes from the decimal point,
truncation at the precision (the crate never rounds — documented by example), then prefix,
unit, suffix. The crate's own `fmt_string`/`fmt_into` and a fresh `Formatter` are the oracles
for the reused `fmt2`; the builder is the oracle for the parser.

## Properties

- **Plain path** (`plain_numbers_match_the_model`): random configurations (prefix/suffix up to
  12 bytes, separator, comma marker, precision, the four built-in scales or a custom one,
  percentage) and 1–17-digit decimals in the decades the scales bring below 10^12 format to the
  model's text; `fmt2` equals `fmt_string`.
- **Scaling** (`scaling_picks_the_largest_unit_reached`): `Scales::scale` is the model.
- **Scientific notation** (`scientific_notation_is_normalised`): outside the plain range the
  text is `prefix ±M e E suffix` with 1 ≤ |M| < 10, E the number's decimal exponent, M within
  the truncation tolerance of the precision. Fails when the generated decimal is a one-digit
  power of ten with an unlucky exponent — most runs, not all (numfmt/3; marked intermittent).
- **Statelessness** (`formatting_is_stateless`): `fmt2` after other calls, `fmt_string`,
  `fmt_into` after arbitrary text and a fresh formatter agree (special values only without a
  prefix — numfmt/1 is pinned).
- **Integers** (`integers_format_as_their_float_value`): every `Numeric` integer type formats as
  its `f64` (found numfmt/1's panic at 1000 cases: `€` prefix, value 0; zero with a prefix is
  now left to the pin).
- **Separator vs marker** (`separator_never_doubles_as_decimal_marker`): after any sequence of
  `separator`/`comma` calls, `1234567.891` prints with a marker distinct from the separator.
  **Expected failure** (numfmt/5).
- **Parser** (`format_strings_parse_to_their_builder_equivalent`): a generated format string —
  escaped brackets in prefix/suffix, `.d`/`,d`/`~d`/`.*`/`,*`, one scaler, `/c` or `/`,
  components in random order — parses to the builder-built formatter (by `==` and by formatting
  eight samples); `parsing_never_panics` on random strings over the grammar's alphabet.

Generators keep away from the pinned shapes: significance precision at |x| < 1 (numfmt/2),
`,` as separator with a comma marker or `.` without one (numfmt/5), subnormals and
percentages above 1e306 (numfmt/6, /7), two identical escaped brackets in a row in a suffix
(numfmt/8).

## Bugs (9)

- **numfmt/1** (crash, high; `special_values_leave_the_prefix_intact`): `0`, `NaN`, `±∞` are
  written at offset 0 of the reused buffer, over the stored prefix — `currency("$")` prints
  `01.0` after a zero, `N1.0` for ever after a NaN; over a multi-byte prefix (`currency("€")`)
  the result is invalid UTF-8 and `fmt_string(0.0)` / the next `fmt2` panic.
- **numfmt/2** (wrong-result, medium; `significance_ignores_leading_zeros`): significant
  figures count leading zeros: `0.5` at 1 s.f. is `0`, `0.001234` at 3 s.f. is `0.00`.
- **numfmt/3** (wrong-result, medium; `scientific_notation_is_normalised`,
  `scientific_mantissa_is_normalised_for_powers_of_ten`): `log10().trunc()` and
  `powi` make the mantissa 10 or 0.999…: `1e-5` → `10.0e-6`, `1e21` → `0.999999e21`, `1.05e21`
  → `1.049999e21`.
- **numfmt/4** (wrong-result, low; `grouping_is_by_three_digits_below_a_power_of_ten`):
  separators placed from `log10`, which rounds up just below a power of ten:
  `999999.9999999999` → `9,999,99.9999999999`.
- **numfmt/5** (wrong-result, low; `separator_never_doubles_as_decimal_marker`,
  `builder_keeps_separator_and_marker_apart`): `separator('.')` then `separator(',')`,
  `comma(true)` then `separator(',')`, `comma(true).comma(false)`, `"[,2n/,]"` → `12,345,67`
  / `12.345.67`.
- **numfmt/6** (wrong-result, low; `percentage_of_huge_numbers_is_not_nan`):
  `percentage().fmt2(f64::MAX)` = `NaNe2147483647%` (the ∞ check runs before `convert`).
- **numfmt/7** (wrong-result, low; `subnormals_format_as_numbers`): `5e-324` → `infe-324`
  (`powi(10, 324)` overflows).
- **numfmt/8** (wrong-result, low; `escaped_brackets_in_the_suffix_parse_pairwise`): `]]]]` in
  a suffix is one `]`, not two.
- **numfmt/9** (contract, low; `equality_reflects_formatting_behaviour`): `PartialEq`/`Hash`
  ignore the comma-marker flag.

## Not bugs

- Truncation instead of rounding (`1234.56789` at 2 decimals → `1234.56`) and no zero padding
  (`$1,234.0` at 2 decimals) are documented by the crate's own examples.
- Special values print bare — `percentage().fmt2(0.0)` is `0`, not `0%`; `NaN`/`∞` carry no
  prefix or suffix — the crate's tests assert the bare forms (the corruption they leave behind
  is numfmt/1).
- With a precision of d ≤ 3 digits, numbers below 10^-d switch to scientific notation (`0.5`
  at 0 decimals → `5e-1`): a code comment documents the adjustment.
- `0.00316114` → `0.0031611399999999999` is dtoa's (Grisu2) digit string; the model uses it.
