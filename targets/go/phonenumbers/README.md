# phonenumbers

[nyaruka/phonenumbers](https://github.com/nyaruka/phonenumbers) v2 (MIT), pinned at `0a7e43b1`
(v2.0.9, 2026-08-31): the Go port of Google's libphonenumber (tracking the Java reference), with
the metadata of libphonenumber 9.0.38 - parsing, validation, formatting, number types, short
numbers, the as-you-type formatter, the text matcher, geocoding, carrier and time-zone lookups.

The patch adds `hegel_test.go` and `hegel_oracle_test.go` (package `phonenumbers_test`) and the
`hegel.dev/go/hegel` requirement to `go.mod`. The oracle is Python's `phonenumbers` package at
the same metadata version (9.0.38), driven as a child process speaking one JSON request per line;
enumerations travel by their libphonenumber names. The tests need `python3` with that package on
PATH (CI installs `phonenumbers==9.0.38` into the Go job's venv). Where the two ports disagreed,
the Java reference (libphonenumber 9.0.38 with geocoder 3.39 and carrier 2.39 from Maven Central)
decided.

## What is tested

- `TestHegelParsingAgreesWithLibphonenumber` - `Parse`/`ParseAndKeepRawInput` on mutated example
  numbers in every format (E.164, international, national, RFC 3966 with `phone-context` and
  `isub`, IDD and national prefixes, fullwidth and Arabic-Indic digits, vanity letters,
  extensions, junk and over-long input) against 80 regions and odd region codes: the same error
  class or the same number (all eight fields).
- `TestHegelNumberQueriesAgreeWithLibphonenumber` - on a number both ports parse alike: validity,
  possibility (with reasons, per type), type, region, the four formats, out-of-country,
  original-format, carrier-code, mobile-dialling and alpha-keeping formatting, area-code and
  NDC lengths, geographical and international-dialling flags, truncation, `IsNumberMatch` with a
  second string or number, time zones, carrier names and area descriptions (English), and every
  short-number query.
- `TestHegelRegionAndTextHelpersAgree` - region metadata (country code, NDD prefix, NANPA,
  portability, example and invalid-example numbers, supported types, regions of a calling code,
  mobile token, non-geographic entities) and the string helpers (`IsAlphaNumber`,
  `ConvertAlphaCharactersInNumber`, `NormalizeDigitsOnly`, `NormalizeDiallableCharsOnly`,
  emergency numbers, `IsPossibleNumberFromRegion`, `IsNumberMatch` on two strings).
- `TestHegelAsYouTypeFormatterAgrees` - the text shown after every character, the remembered
  position and the state after `Clear`.
- `TestHegelNumberMatcherAgrees` - `FindNumbersWithLeniency` over random text with embedded
  candidates, all four leniencies and `maxTries` limits: the same matches (offsets in code points,
  raw strings, numbers).
- `TestHegelPin...` - one plain test per recorded bug.

## Bugs

See `bugs.toml`: area and carrier lookups do not fall back to English for languages without data,
returning the country name or nothing where libphonenumber returns "New Jersey" or "Globe" (1);
`FormatOutOfCountryKeepingAlphaChars` keeps a `+` or `*` of the raw input (2).

## Notes

- Oracle gaps (Python deviations from Java, so not recorded against the port): Python
  upper-cases region codes where Java treats `us` as unknown (no lower-case codes are generated);
  its matcher compares an x-less extension with `None` where Java compares with `""` (the oracle is
  patched to Java's reading, so "12 34 56 78 ext" is a VALID match on both sides); its country
  names come from its own table, not CLDR ("Antigua and Barbuda" against "Antigua & Barbuda"), so
  a description equal to Python's country name is not compared; and it still ships prefix data
  libphonenumber 9.0.38 has dropped (English geocoding for France, Malaysia, Latvia and Estonia,
  South Korea in other languages, carrier names under 549), gated by calling code.
- Carrier and area comparisons are made in English only because of bug 1; the pin covers the
  fallback with German, empty and unknown language codes.
