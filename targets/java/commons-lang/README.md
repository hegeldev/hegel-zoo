# commons-lang

[apache/commons-lang](https://github.com/apache/commons-lang): Apache Commons Lang — `StringUtils`,
`ArrayUtils`, `NumberUtils`/`Fraction`/`IEEE754rUtils`, `Conversion`, `CharSet`/`CharSetUtils`/
`CharUtils`, `BooleanUtils`, `EnumUtils`, `LocaleUtils`, `ClassUtils`, `Range`/`IntegerRange`, the
`time` package (`DurationFormatUtils`, `DateUtils`, `FastDateFormat`, `DateFormatUtils`), the
`builder` package (`ToStringBuilder` and its styles, `EqualsBuilder`, `HashCodeBuilder`,
`CompareToBuilder`, `DiffBuilder`), `mutable`, `tuple`, `SerializationUtils`, `RandomStringUtils`,
`Validate` and `ObjectUtils`. Pinned at 3.21.0-SNAPSHOT (01a66dd2, 2026-09-15; the last release is
3.20.0). Apache-2.0; the ASF's Generative Tooling Guidance asks for disclosure of AI use in a PR and
forbids nothing (the zoo only records). The fourth Java target: the patch adds the Maven module
`hegel/` at the repository root (`hegel/pom.xml` depends on the `commons-lang3` artifact `[run]
setup` installs from this checkout — Maven >= 3.9 — on `dev.hegel:hegel` and on JUnit 5), with the
harness `Zoo.java`, the judge's `ZooListener` and two test classes in `hegel/src/test/java/zoo/`.
See HACKING.md for the Java mechanics.

## What is tested

Every model is written from the Javadoc's rules and example tables, with `java.lang.String`,
`java.util.List`, `BigInteger`/`BigDecimal`, `java.time` and `SimpleDateFormat` as the oracles.

`CommonsLangTest`:

- **stringUtilsSubstringsAndPaddingFollowTheirTables** — strings of ASCII words, blanks (space,
  tab, newlines, NUL, U+00A0), punctuation, `é`/`İ`/`ß` and `😀` pairs: `substring` (negative
  indices from the end, clamping), `left`/`right`/`mid`/`truncate` (exact without surrogate pairs;
  with pairs a well-formed piece at most one unit shorter, since the code never splits a pair),
  `abbreviate` in all its forms against the example table (tail, head and recursive branches, the
  `IllegalArgumentException` widths) plus the documented promises "never longer than maxWidth" and
  "the left edge appears in the result" on strings of distinct letters (bug /1 skipped),
  `abbreviateMiddle`, `leftPad`/`rightPad`/`center` with cyclic pad strings, chars, null/empty pads
  and the 8192 pad limit, `repeat`, `reverse`, `rotate` (and back), `overlay`, `chomp`, `chop`,
  `strip*`/`trim*`/`*ToNull`, `normalizeSpace` (with idempotence; strings with U+00A0 are bug /9),
  `deleteWhitespace`, `swapCase`/`capitalize`/`uncapitalize`/`toRoot*Case`/`getDigits`/`toCodePoints`,
  `wrap`/`unwrap`/`wrapIfMissing`, `removeStart/End`, `appendIfMissing`/`prependIfMissing`,
  `substringBefore/After(Last)`, `substringBetween`, `substringsBetween`.
- **stringUtilsSearchSplitJoinAndReplaceAgreeWithStringModels** — `indexOf`/`lastIndexOf` (with
  start), `contains`, `startsWith`/`endsWith`, `countMatches` (non-overlapping),
  `ordinalIndexOf`/`lastOrdinalIndexOf` (overlapping, as documented), the `IgnoreCase` family
  against `regionMatches(true, …)` and the `Strings.CI`/`Strings.CS` instances, `indexOfAny`/
  `indexOfAnyBut`/`containsAny`/`containsNone`/`containsOnly` by code point, `indexOfDifference`/
  `getCommonPrefix`/`difference`; the `split` family (`split`, with max, on whitespace, on a char
  set, `splitPreserveAllTokens`, `splitByWholeSeparator[PreserveAllTokens]`,
  `splitByCharacterType[CamelCase]`) against models of the documented merging rules, `join` of
  arrays/lists/iterators/ranges (`join(Object[], String, start, end)` on valid ranges — bug /3),
  `joinWith`, `splitPreserveAllTokens` then `join` as the identity; `replace`/`replaceOnce`/
  `replaceIgnoreCase`/`replace(max)`/`remove*`, `replaceChars`, `replaceEach` (earliest match,
  ties to the first entry); the `is*` predicates against `Character`, `compare[IgnoreCase]`,
  `defaultIfBlank`, `firstNonBlank`, `reverseDelimited`.
- **arrayUtilsFollowsItsClampingRules** — `int[]` against an `ArrayList` model: `indexOf`/
  `lastIndexOf` (with start), `contains`, `isSorted`, `toObject`/`toPrimitive`, `toString`, `add`/
  `addFirst`/`addAll`/`insert` (out-of-range index throws — with values; bug /5), `remove(index)`,
  `get` with default, `removeElement`/`removeAllOccurrences`/`removeElements`/`removeAll(indices)`,
  `subarray` clamping, `reverse`/`shift`/`swap` on ranges (clamping, never throwing, involution and
  rotation laws), `shuffle` as a permutation, `nullToEmpty`, `isSameLength`.

`CommonsLangMoreTest`:

- **numberUtilsCreateNumberFollowsItsGrammar** — `createNumber` on generated integrals (the
  `Integer → Long → BigInteger` ladder, `l`/`f`/`d` suffixes with their promotions on overflow and
  underflow), decimals with exponents (Float/Double/BigDecimal, the result printing back to the same
  number when no suffix asks for a type), hexadecimal with `0x`/`0X`/`#` (the documented width
  rule), octal (a leading zero; `8`/`9` invalid) and junk; `isCreatable` ⇔ no exception,
  `isParsable`, `toInt`/`toLong`/`toDouble` defaults, `createBigInteger`/`createDouble`; `min`/
  `max` over arrays with `NumberUtils` propagating NaN and `IEEE754rUtils` ignoring it. A plus sign
  with the `L` suffix is bug /11 and skipped.
- **fractionArithmeticMatchesBigIntegerRationals** — `getFraction(n, d)` (sign normalisation, no
  reduction, zero denominator), `getReducedFraction`/`reduce`, component-wise `equals`, `compareTo`
  by cross-multiplication, `add`/`subtract`/`multiplyBy`/`divideBy`/`invert`/`negate`/`abs`/`pow`
  against reduced `BigInteger` rationals (|power| = 1 checks the value only — bug /8), `toString`
  and `toProperString` parsing back, the proper parts, and `getFraction(double)` recovering
  denominators up to 60 exactly.
- **conversionRoundTripsAndMatchesTheBitOrder** — `intToHex`/`longToHex`/`shortToHex`/`byteToHex`
  (little-endian LSB0: reversed, they are `%08x` etc.) and back, `intToBinary`/`longToBinary`/…
  and back with the bit order checked, `intToByteArray`/`longToByteArray`/`shortToByteArray` and
  back, partial `hexToInt` conversions preserving the untouched destination bits, `intArrayToLong`/
  `longToIntArray`/`shortArrayToInt`, the hex digit functions against `Character.forDigit` and the
  bit-reversed `Msb0` table, `uuidToByteArray`/`byteArrayToUuid`, the documented
  `IllegalArgumentException`s for overflowing widths.
- **charSetGrammarAndCharSetUtilsFollowTheirRules** — random set strings over `a b c A - ^ 0 9 z`
  against the positional grammar (`^a-z`, `a-z`, `^a`, `a`, negated ranges as unions), `CharSet`
  equality and the union of pieces; `CharSetUtils.count`/`keep`/`delete`/`squeeze`/`containsAny`
  against the same predicate; `CharUtils` predicates against the ASCII table, `unicodeEscaped`,
  `toIntValue`, `toChar`, `compare`.
- **booleanEnumLocaleAndClassUtilsFollowTheirTables** — `BooleanUtils.toBooleanObject(String)`
  (the length switch, no trimming), `toBoolean(str, true, false)`, `and`/`or`/`xor`/`oneHot`,
  `compare`, the `toString*` forms; `EnumUtils` bit vectors on an eight-constant enum and their
  inverses (extra high bits ignored), `getEnum[IgnoreCase]`, `isValidEnum`, `getEnumList`/`Map`;
  `LocaleUtils.toLocale` on generated `language_COUNTRY_variant` strings with `_` or `-` (ISO
  country codes as bare strings, the leading-separator forms, the variant taking the rest) against
  the documented grammar; `ClassUtils.getShortClassName`/`getPackageName` on generated
  package/inner/array names (an array of a default-package class `C` is bug /10 and skipped),
  `getAbbreviatedName`'s examples, boxing/widening `isAssignable`.
- **rangeAlgebraMatchesIntervals** — `Range.of` with swapped bounds, `contains`, `isAfter`/
  `isBefore`/`isStartedBy`/`isEndedBy`, `elementCompareTo`, `fit`, `containsRange`,
  `isOverlappedBy` (symmetric), `isAfterRange`/`isBeforeRange`, `intersectionWith` (symmetric, IAE
  when disjoint), `toString[(format)]`, class-exact `equals`, `IntegerRange.toIntStream`,
  `Range.is`, a reversed comparator, NaN and null refusals.
- **durationFormatUtilsMatchesArithmetic** — durations up to 100 days: `d H m s S` and padded
  patterns, roll-up of absent tokens (`formatDurationHMS`, `s`, `m`, `S`, `H:mm`),
  `formatDurationISO`, optional blocks (`[d'd']…`, all-optional), quoted literals and `''`,
  `formatDurationWords` against a model of the documented string surgery and plural fixes,
  `formatPeriod` between two instants, the documented `IllegalArgumentException`s for negatives,
  reversed periods and malformed patterns (nested/unopened/unclosed optional, unmatched quote).
- **dateUtilsRoundingAndFormattingAgreeWithJavaTime** — instants across 1900–2090 in UTC:
  `truncate`/`ceiling`/`round` (Date, Calendar and Object forms) for SECOND, MINUTE, HOUR[_OF_DAY],
  DATE, MONTH and YEAR against `java.time` (round: the most significant dropped field decides,
  exactly half rounds up), MILLISECOND as identity, unsupported fields throw; the `getFragmentIn*`
  family; `add*`/`set*` against `plus*`/`with*`; `isSameDay`/`isSameInstant`/`truncatedEquals`/
  `truncatedCompareTo`/`toCalendar`; `FastDateFormat` against `SimpleDateFormat` for nine patterns
  (eras, week/day numbers, am/pm, zones), `DateFormatUtils.format`, parsing back with
  `FastDateFormat.parse`/`parseDate`/`parseDateStrictly` and the "Unable to parse the date" message,
  `ZZ` as ISO 8601 (`Z` for UTC).
- **buildersMutablesTuplesAndSerializationBehave** — a `Person(name, age, smoker)` through the
  seven `ToStringStyle`s (identity hash, `<null>`, JSON escaping of quotes, backslashes and
  non-ASCII, the mandatory JSON field name, `reflectionToString` sorted by field name);
  `EqualsBuilder`/`reflectionEquals`, `HashCodeBuilder` (formula, odd-number check),
  `CompareToBuilder` (nulls first), `DiffBuilder` counts and field names; `MutableInt`/`MutableLong`
  operation sequences with pre/post semantics against a `long`, type-exact `equals`, `MutableDouble`
  NaN/signed zero; `Pair`/`Triple` accessors, `toString[(format)]`, `equals` with any `Map.Entry`,
  `hashCode` formulas, `compareTo`, immutability; `SerializationUtils` clone/roundtrip/serialize/
  deserialize; `RandomStringUtils.insecure()` lengths, alphabets, well-formed UTF-16, the
  documented refusals (a negative count's message is bug /6); `Validate`'s exception mapping and
  messages; `ObjectUtils.max`/`min`/`median`/`mode`/`firstNonNull`/`defaultIfNull`/`compare`/
  `identityToString`.

Not covered: `text` (deprecated twins of commons-text), `concurrent`, `event`, `exception`,
`function`, `reflect`, `stream`, `AnnotationUtils`, `ArchUtils`, `SystemUtils`/`JavaVersion`,
`ThreadUtils`, `RandomUtils`, `StopWatch`, `CalendarUtils`, `WeekFields`-style week ranges and
`DateUtils.iterator`, `StringEscapeUtils` (deprecated), `CharSequenceUtils` and `RegExUtils`
directly.

## Bugs

Eleven, all pinned (`pin…` tests) and recorded in `bugs.toml`: `abbreviate` with an offset drops
the left edge it promises to keep (/1); `EnumUtils.generateBitVector(Class, Iterable)` throws NPE
where IAE is documented (/2); `join(Object[], String, start, end)` throws the wrong exception for a
negative start and none for an out-of-range end (/3); `replaceEachRepeatedly` rejects a convergent
six-link chain as an endless loop (/4); `ArrayUtils.insert` without values skips its bounds check
(/5); the negative-count message of `RandomStringUtils` reports the end code point (/6);
`Conversion.intToHexDigit`'s Javadoc says `'A'`, the code returns `'a'` (/7); `Fraction.pow(±1)`
is not reduced although documented so (/8); `normalizeSpace` turns U+00A0 into spaces without
collapsing them and is not idempotent (/9); `getShortClassName("[LC;")` is `char[]` (/10);
`createNumber("+7L")` is rejected while `"+7"`, `"-7L"`, `"+7f"` are accepted (/11).

Observed and not recorded, since the code's own tests or comments pin them or no contract is
broken: `left`/`right`/`mid`/`truncate`/`abbreviate`/`overlay`/`chop` never split a surrogate pair
(undocumented but sensible; `substring` does split them); an `S` token following an `s` token is
printed with at least three digits whatever the padding flag (a source comment says so);
`createNumber("010")` is octal 8 while `"08"` is invalid (documented); `LocaleUtils.toLocale`
tries `_` before `-`, so `"en-GB-a_b"` is invalid while `"en_GB_a_b"` has the variant `a_b`;
`toDouble(" 1")` parses (Double.parseDouble trims); `reflectionToString` orders fields by name.

## History

- 2026-09-16: created at 01a66dd2 (3.21.0-SNAPSHOT), 12 properties, 11 bugs.
- 2026-09-18: base bumped 01a66dd238cb → d235f1e99752 (2026-09-18, "LANG-1834 Fix Fraction reduction for Integer.MIN_VALUE (#1794)."; 3.21.0-SNAPSHOT); 11 bug(s) still reproduce. 12 tests pass.
