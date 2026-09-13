# num-format

[bcmyers/num-format](https://github.com/bcmyers/num-format) (workspace member `num-format`):
integers formatted with thousands separators per the CLDR locale table (`1,000,000` en,
`10,00,000` en-IN, `1 000 000` fr) or a `CustomFormat` (separator, minus sign, grouping
`Standard`/`Indian`/`Posix`), through a stack `Buffer` (a hand-written digit loop with a
two-digit table and raw pointer writes), `ToFormattedString`, `WriteFormatted` for
`io::Write`/`fmt::Write` sinks and `num-bigint`; plus `parsing::ParseFormatted` for the way back.
0.4.4, last upstream commit 2022-12.

Written in the zoo (not imported from the predecessor). Built with `--features
with-serde,with-num-bigint` (`with-system-locale` reads the OS locale table and is not tested).
The crate's own tests run alongside `tests/hegel.rs`; `postcard` is added as a dev-dependency for
the binary serde check.

## What is tested

**`tests/hegel.rs`** — values are `i128` with a bias to every integer type's bounds, to powers
of ten ± 2 and to digit counts around the grouping boundaries; formats are the 542 locales and
custom ones with 16 separators (empty, ASCII, `\u{202f}`, `’`, 4-byte emoji, 8-byte strings)
and 7 minus signs (`-`, `−`, `🙌`, `neg `, …) in the three groupings. The oracle is a model that
groups the digits of `|n|.to_string()` (Standard: threes; Indian: three then twos; Posix or an
empty separator: none) and prepends the minus sign.
- `formatting_groups_the_digits_of_every_integer_type`: `Buffer::write_formatted` (text, byte
  count, `len`/`as_bytes`/`Deref`/`Display`/`Debug`), `to_formatted_string`, `write_formatted`
  on `String`, `Vec<u8>`, `io::Cursor` and `&mut fmt::Formatter`, for `i128` and every
  narrower type and `NonZero` type that holds the value; a `Buffer` reused for another number.
- `bigints_format_like_the_machine_integers`: `BigInt`/`BigUint` of the same value agree with
  the machine path; 1–90-digit numbers against the model; the `io::Write` and `fmt::Write`
  algorithms agree on text and count.
- `parsing_inverts_formatting`: `parse_formatted` of the formatted text gives the value back for
  every type that holds it (`Err` for types that do not, when the digits fit the crate's buffer),
  `NonZero` types, `BigInt`/`BigUint`, from `&str`, `String` and `Buffer`.
- `texts_that_are_not_numbers_are_errors`: empty text, the bare minus sign or separator, words
  and `∞`/`NaN` are errors; `ErrorKind::ParseNumber` and its message for the empty text.
- `custom_formats_enforce_the_documented_capacities`: separator, minus, plus and decimal up to 8
  bytes, `nan` 64, `infinity` 128 — the builder and the `utils::*Str` constructors accept exactly
  those and refuse longer ones with `ErrorKind::Capacity { len, cap }` and its message; accessors,
  `into_builder` round trip, serde JSON round trip, `Default == Locale::en`.
- `the_locale_table_is_consistent`: 542 sorted unique names, `from_name`/`FromStr` round trip,
  `CustomFormat::from(Locale)` copies every field, separators and minus signs hold no numerals,
  separator ≠ decimal, both `Format` implementations render alike, unknown names are
  `ParseLocale` errors, and `en`/`en-IN`/`de`/`de-CH`/`fr` spot values.
- `buffers_serialize_and_deserialize`: `Buffer` as a JSON byte array, round trip.
- Pinned: `overlong_texts_are_rejected_without_panicking` (num-format/1),
  `non_ascii_numerics_are_not_misread` (num-format/2), `an_empty_minus_sign_does_not_negate`
  (num-format/3), `out_of_range_texts_report_a_number_error` (num-format/4),
  `buffers_round_trip_through_binary_formats` (num-format/5),
  `texts_with_a_decimal_or_letters_are_rejected` (num-format/6).

## Oracles

`ToString` of the integer plus a grouping model; the crate's documented capacities and the
`Grouping` definitions; `serde_json` and `postcard` for the serde forms.

## Not tested

`with-system-locale` (OS-dependent); `no_std` builds; the correctness of the CLDR data itself
(which separator a given locale uses — only its internal consistency); `Locale::from_name` for
region names outside the table (open upstream #45 asks for `de-DE`).

## Bugs

The formatting core — the raw-pointer digit loop and the two `num-bigint` algorithms — is
clean; all six bugs are in `parsing.rs` (60 lines) and the serde glue, four of them visible
by reading.
- **num-format/1** (medium, panic): a text with more digits than the target type can have
  (`1,000` as `u8`) panics with an index out of bounds — the guard is `index > BUF_LEN`
  instead of `>=`.
- **num-format/2** (medium): non-ASCII numerals are kept by `is_numeric()` and truncated with
  `as u8`: CHAKMA DIGIT ZERO parses as 6, Hangzhou ten as 8; others become invalid UTF-8
  under `from_utf8_unchecked` (open upstream #52 reports the UB).
- **num-format/3** (low): an empty custom minus sign makes every text negative
  (`starts_with("")`).
- **num-format/4** (low): out-of-range numbers are reported as `ErrorKind::ParseLocale`.
- **num-format/5** (low): `Buffer`'s `Deserialize` visitor lacks `visit_bytes`, so binary
  formats fail (open upstream #40, verified with postcard).
- **num-format/6** (low): the parser ignores the format's decimal separator and letters —
  `1.5` (en) is 15, `0x10` is 10.

## History

- 2026-09-13: written in the zoo against `c2173715e17a` (2022-12-03, 0.4.4) with hegeltest
  0.44.1. The source was read first: the formatter's separator arithmetic checked out on paper
  and in the tests; `parsing.rs` showed the off-by-one guard, the `is_numeric`/`as u8`
  truncation, `starts_with(minus_sign)` and the `parse_locale` error (num-format/1–4) at a
  glance; the first run added num-format/6 (`0x10` → 10) and confirmed #40 (num-format/5).
  Formatting properties clean at 100 + 3 × 1 000 + 10 000 cases. Test defects on the way:
  `10^37 × 999` overflowed `i128` in a generator; a width-padding check on the
  `fmt::Formatter` path (the crate writes with `write_str`, so `{:>w}` cannot pad — by design).
