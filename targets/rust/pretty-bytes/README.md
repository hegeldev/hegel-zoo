# pretty-bytes

[pretty-bytes](https://github.com/banyan/rust-pretty-bytes) "converts bytes to a human readable
string: 1337 → 1.34 kB" — `convert(num: f64) -> String`, a port of sindresorhus/pretty-bytes
(decimal units B … YB, two decimals with trailing zeros dropped, values below one byte
verbatim); 1.1M downloads. Written in the zoo at 0.2.2 (upstream HEAD `1079021`, 2017-10-02, the
last commit); tests in `tests/hegel.rs`. `[run] setup` runs `cargo update -p getopts` first (0.2.14 →
0.2.24): the 2017 `Cargo.lock` does not compile on a current rustc (E0503 in getopts), and the
zoo's patches leave lockfiles alone.

## The oracle

Arithmetic: the output splits as `<mantissa> <unit>`, and `mantissa × 1000^unit` must be
`num` to within half of the last decimal shown, with the unit the largest whose mantissa is at
least 1.

- `output_is_num_to_two_decimals`: at most two decimals, no trailing zero, and the value.
- `unit_is_the_largest_that_fits`: the exponent of the input is the unit (capped at YB).
- `output_is_monotone`: a larger size never reads as a smaller one.
- `sign_is_a_prefix_and_fractions_are_verbatim`: `convert(-x)` is `-` + `convert(x)`, zero is
  `0 B`, a fraction of a byte is printed as it is.
- `doc_examples`.
- The general generators avoid mantissas in [999.995, 1000), pinned as pretty-bytes/1.

## Bugs (2)

- **pretty-bytes/1** (wrong-result, medium; `mantissa_stays_below_1000`): `convert(999_999.0)`
  is `1000 kB`, `convert(999.995)` is `1000 B` — the unit is chosen before the mantissa is
  rounded.
- **pretty-bytes/2** (wrong-result, low; `negative_zero_is_zero`): `convert(-0.0)` is `-0 B`.

## Not bugs

- `NaN B`, `inf YB`, `-inf YB`: the original throws a `TypeError`; this `convert` has no error
  path and nothing says what a non-finite byte count should print.
- Two decimals (`12.35 kB`, `123.46 kB`) where pretty-bytes 4.x printed three significant digits
  (`12.3 kB`, `123 kB`): the README's only example agrees with both, and more precision is not
  wrong.
- Beyond YB (`1e27` → `1000 YB`, `f64::MAX` → a 285-digit mantissa) and far below a byte
  (`1e-320` → its full decimal expansion): the units run out; `format!("{}", f64)` never uses an
  exponent.
