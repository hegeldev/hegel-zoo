# libphonenumber-js

[libphonenumber-js](https://github.com/catamphetamine/libphonenumber-js) is "a simpler and
smaller rewrite of Google Android's libphonenumber library in javascript": parsing, validation,
formatting (national, international, E.164, RFC 3966, out-of-country dialling), an as-you-type
formatter and phone number search, driven by Google's `PhoneNumberMetadata.xml`. Pinned at 1.13.7,
54c0209 (2026-06-19, the GitHub mirror's head; the primary repository is on GitLab), MIT.

The library is plain ESM run straight from `source/` with no build. Hegel and the oracle go under
`.hegel/`. Tests: `hegel/hegel.test.mjs`, run with `node --test`. `ZOO_FULL=1` widens the
generators to the shapes that hit known bugs and drops the gates around them; `ZOO_COLLECT=1`
prints mismatch statistics.

## Oracle and metadata

The oracle is google-libphonenumber 3.2.46, the Closure-compiled port of Google's own library,
built with libphonenumber 9.0.28. Both libraries are only as good as their metadata, and the
library's `metadata.max.json` is generated (at publish time, by the separate
libphonenumber-metadata-generator package) from whatever Google XML the author last pulled, so the
setup downloads the `PhoneNumberMetadata.xml` of the 9.0.28 release and runs the generator on it
(`hegel/generate-metadata.mjs`): every function is called through the `core` API with that
metadata, and the two sides agree on the data. A probe confirmed it: Google's example number of
every region and type (1377 numbers) parses as valid with the same country and type, with the one
exception recorded as bug 1.

Known, deliberate differences that the tests normalise or skip rather than record:

- the international format uses spaces where Google keeps the metadata's dashes (`+1 213 373 4253`
  vs `+1 213-373-4253`, as the README shows), so `INTERNATIONAL` and `IDD` are compared with
  separators mapped to spaces and `RFC3966` without dashes;
- local-only phone number lengths are ignored "for simplicity" (comments in `isPossible.js` and
  `checkNumberLength.js`): a number Google calls `IS_POSSIBLE_LOCAL_ONLY` is usually not possible
  here (`TOO_SHORT`/`INVALID_LENGTH`), sometimes possible through a type's own lengths (US UAN
  `+13101234`); no expectation is placed on such numbers;
- the metadata generator drops every number format whose `intlFormat` is `NA` (its source says
  "Screw local-only formats"), so 7- and 8-digit Chinese numbers, for instance, have no format on the
  library's side and are returned unformatted where Google formats them (`946 6180`). This is the
  generator's choice, not this library's code, so formats are compared only when the library has
  one for the number;
- google-libphonenumber keeps the national number in a JavaScript number: national numbers of 16
  or 17 digits are not exact on the oracle's side and are skipped;
- the as-you-type formatter's text differs from Google's for roughly a third of partial numbers
  (different choices of format for an incomplete number); the text is compared only under
  `ZOO_FULL`, while the formatter is held to its own contract (template, characters, the number it
  builds, whole-string vs incremental input) in every run.

## Properties

| Test | Checks |
| --- | --- |
| `TestHegelParseAgreesWithGoogle` | numbers written in every notation (E.164, international with separators, national, with national prefix, IDD-dialled, RFC 3966, extensions, whitespace) parse to the same calling code, national number, extension, country, possibility, validity, type and formats as Google |
| `TestHegelFormatsRoundTrip` | `format` in E.164, RFC3966, INTERNATIONAL and NATIONAL (with and without national prefix) parses back to the same number and extension; `getURI`/`formatNational`/`formatInternational` are the documented aliases |
| `TestHegelShortcutsMatchParsing` | `isValidPhoneNumber`/`isPossiblePhoneNumber` equal the strict parse followed by `isValid`/`isPossible`; `parsePhoneNumber` is `parsePhoneNumberWithError` without the throw; `validatePhoneNumberLength` matches Google's `isPossibleNumberWithReason` |
| `TestHegelAsYouTypeAgreesWithGoogle` | typing a number character by character: `getChars` are the typed characters, the template filled with them is the output, the output equals `formatIncompletePhoneNumber` of the same text, `getNumber`/`getNumberValue`/`isValid`/`isPossible` agree with parsing the same digits, `isInternational`/`getCallingCode`, `reset` |
| `TestHegelMetadataAccessorsAgreeWithGoogle` | `isSupportedCountry`, `getCountryCallingCode`, `getExampleNumber` (valid, right country, Google's type) and the rejection of unknown countries |
| `TestHegelPhoneNumberConstructorAgreesWithParse` | `new PhoneNumber(e164)` and the two-argument form equal the parsed number in number, national number, validity, type and formatting; `isEqual` and `setExt`; `getPossibleCountries` lists only countries of the calling code |
| `TestHegelPinCountriesMatchGoogle` | `getCountries()` is Google's set of supported regions |

Pins (`TestHegelPin*`) reproduce the bugs in `bugs.toml` and are listed as expected failures.

## Not tested

- `findPhoneNumbersInText`/`PhoneNumberMatcher` (the Closure port has no matcher to compare with)
  and the legacy API (`parseNumber`, `formatNumber`, `isValidNumber`, `getNumberType`).
- Carrier codes, `formatPhoneNumberForMobileDialing`, and the `min`/`mobile` metadata variants.
- Text with letters (vanity numbers) and full-width digits: only under `ZOO_FULL`.

## History

- 2026-09-20: created (turn 318); 9 bugs recorded.
