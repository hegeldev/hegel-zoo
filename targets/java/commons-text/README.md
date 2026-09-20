# commons-text

[apache/commons-text](https://github.com/apache/commons-text): Apache Commons Text — string
escaping (`StringEscapeUtils` and the `translate` package), `StringSubstitutor` with its lookups
and streaming reader, `WordUtils`/`CaseUtils`, the `similarity` metrics, the Myers diff in `diff`,
`numbers.DoubleFormat`, `TextStringBuilder`, `StringTokenizer`, `AlphabetConverter`,
`RandomStringGenerator`, `FormattableUtils` and `ExtendedMessageFormat`. Pinned at
1.15.1-SNAPSHOT (ae3d36b8, 2026-09-09; the last release is 1.15.0). Apache-2.0; the ASF's
Generative Tooling Guidance asks for disclosure of AI use in a PR and forbids nothing (the zoo only
records). The third Java target: the patch adds the Maven module `hegel/` at the repository root
(`hegel/pom.xml` depends on the commons-text artifact `[run] setup` installs from this checkout —
Maven >= 3.9 is needed, the rat plugin refuses 3.8 — on `dev.hegel:hegel` and on JUnit 5), with
the harness `Zoo.java`, the judge's `ZooListener` and two test classes in
`hegel/src/test/java/zoo/`. See HACKING.md for the Java mechanics.

## What is tested

Every model is written from the Javadoc: the escaping tables and ranges, the Java literal grammar,
numeric and named entities, the `${name:-default}` / `$${escaped}` syntax, the wrap and
capitalisation rules, the textbook edit distances, `DoubleFormat`'s half-even rounding with
`BigDecimal` as the oracle, and `java.lang.StringBuilder`/`String` for `TextStringBuilder`.

`CommonsTextTest`:

- **escapersMatchTheirDocumentedTablesAndUnescapeBack** — strings mixing printable ASCII, the
  escaped specials, controls, Latin-1, BMP, surrogate pairs and lone surrogates: `escapeJava`,
  `escapeEcmaScript` and `escapeJson` equal a per-UTF-16-unit model (quotes, backslash, the named
  controls, `\uXXXX` outside 0x20..0x7f — 0x7e for JSON — plus `'` and `/` where documented) and
  unescape back; `escapeHtml4`/`escapeHtml3` equal the BASIC + ISO-8859-1 (+ HTML 4.0 extended)
  tables and unescape back; `escapeXml10`/`escapeXml11` remove exactly the documented invalid
  ranges and lone surrogates, write the five entities and `&#N;` for [#x7F-#x84] | [#x86-#x9F]
  (1.1: the low controls too), and `unescapeXml` gives back the filtered input; `escapeCsv`
  quotes iff a comma, quote or line break is present and `unescapeCsv` inverts it; `escapeXSI`
  backslashes its 23 characters, drops `\n` and `\r\n`, and `unescapeXSI` inverts it on texts
  without line breaks.
- **javaUnescapeFollowsTheLiteralGrammar** — random soups of escapes and text against a decoder
  for the Java literal grammar (octal escapes of 1–3 digits, `\u`+ with any number of `u`s and an
  optional `+`, the named controls and quotes, a lone backslash dropped); a malformed `\u` must
  throw `IllegalArgumentException`; `unescapeEcmaScript`/`unescapeJson` agree; `escapeJava` of the
  result is a fixed point.
- **entityUnescapersDecodeNamedAndNumericEntities** — texts of plain runs, `&#N;`/`&#xH;`
  entities (leading zeros, mixed-case hex, supplementary code points), entities without a
  semicolon or out of range (left alone), the four basic names, `&apos;` (XML only), the ISO-8859-1
  and HTML 4.0 names, unknown names: `unescapeHtml4`, `unescapeHtml3` and `unescapeXml` each decode
  exactly their documented set.
- **stringSubstitutorFollowsTheDocumentedSyntax** — templates from a grammar of literals,
  `${name}`, `${name:-default}`, `$${escaped}`, stray `$`/`}` and an unclosed variable, with
  default or custom prefix/suffix, `setPreserveEscapes`, `setDisableSubstitutionInValues` (values
  may then contain syntax verbatim; otherwise they are templates over later variables) and
  `setEnableUndefinedVariableException`, against an interpreter of the documented rules:
  `replace(String)`, `replace(char[])`, `replace(CharSequence)`, `replaceIn(StringBuilder)`,
  `replaceIn(StringBuffer, offset, length)`, the static `replace(Object, Map)`, and
  `StringSubstitutorReader` drained with random `read()`/`read(buf, 0, n)` calls (for distinct
  prefix and suffix, bug /10, and not for a text ending in `$` with a one-character prefix, bug
  /13) all agree; a case where a substituted value ending in `$` is directly followed by the prefix
  is skipped (bug /14).
- **wordUtilsFollowTheirJavadocRules** — `wrap` (all wrap lengths, custom newline strings, long
  words wrapped or not, wrapping on `/`) against the greedy model of the Javadoc's examples;
  `capitalize`, `uncapitalize`, `capitalizeFully`, `initials`, `swapCase`, `abbreviate`,
  `containsAllWords` and `CaseUtils.toCamelCase` against their rules, with null, empty and
  explicit delimiter sets.
- **similarityScoresAndDiffsMatchTheTextbookDefinitions** — pairs of nearby strings:
  `LevenshteinDistance` (and its threshold form, -1 above the threshold) against the DP,
  `LevenshteinDetailedDistance`'s counts sum to its distance, which is at least the Levenshtein
  distance (equality is bug /8), `HammingDistance`,
  `LongestCommonSubsequence` (length and an actual common subsequence of that length),
  `LongestCommonSubsequenceDistance`, `JaroWinklerSimilarity`/`Distance` against the definition,
  `JaccardSimilarity`/`Distance` on distinct characters, `FuzzyScore`, `CosineDistance` in [0, 1],
  symmetric and 0 for a text with itself; `StringsComparator`'s edit script replays both strings,
  has `getLCSLength()` = the LCS and minimal `getModifications()`, and `ReplacementsFinder`'s
  replacements rebuild the second string.

`CommonsTextMoreTest`:

- **doubleFormatRoundTripsAndRoundsHalfEven** — random doubles (random bits, short decimals,
  the extremes) through PLAIN, SCIENTIFIC, ENGINEERING and MIXED: the documented
  `Double.parseDouble` round trip with unlimited precision, the layout of each type (one integer
  digit, exponents multiple of 3, MIXED's thresholds), `maxPrecision` and `minDecimalExponent`
  as half-even `BigDecimal` rounding (a lone digit 5 rounded at the position above it is bug
  /12 and skipped), `includeFractionPlaceholder`, `allowSignedZero`,
  `alwaysIncludeExponent`, `groupThousands`, custom digits/separators mapping one-to-one onto the
  default output, and MIXED's thresholds applied after rounding.
- **textStringBuilderTracksStringBuilder** — random operation sequences (append, insert,
  delete, deleteAll, replaceAll/First, reverse, trim, setLength, fixed-width padding, separators,
  appendln, readFrom, asWriter, ...) against `java.lang.StringBuilder`, then the queries
  (`indexOf`/`lastIndexOf`/`contains` with start indices — a multi-character needle matching
  exactly at the start index is bug /11 and skipped —, the lenient `leftString`/`midString`/
  `rightString`/`substring`, `hashCode` = the String's, `equals`/`equalsIgnoreCase`, `asReader`,
  `asTokenizer`, `getChars`, ...) against `String`.
- **stringTokenizerSplitsWhatItsGrammarJoins** — fields joined by a delimiter and quoted with
  doubled quotes where needed, through the CSV/TSV instances (trimmed, empty tokens kept) and
  custom delimiter/quote tokenizers with `ignoreEmptyTokens`/`emptyTokenAsNull`; the token list,
  array, size, the ListIterator forwards and backwards, `reset` and `clone` agree.
- **alphabetConverterRoundTrips** — random original (any code points), encoding (BMP) and
  do-not-encode alphabets: `decode(encode(s)) == s`, fixed-width encoding, only encoding
  characters used, `createConverterFromMap(getOriginalToEncoded())` equal, characters outside the
  alphabet refused, the documented refusal of fewer than two usable encoding characters.
- **randomStringGeneratorHonoursItsBounds** — `withinRange`, `filteredBy` and `selectFrom`
  configurations with a seeded `usingRandom`: `generate(n)` has n code points, all in range,
  none surrogate/private-use/unassigned, all matching a predicate; `generate(min, max)` within
  bounds inclusive; the same seed reproduces the string.
- **formattableUtilsAndExtendedMessageFormatKeepTheirShape** — `FormattableUtils.append`
  through `String.format` with random width/precision/flags/pad/ellipsis (length, padding side,
  truncation with the ellipsis, the documented refusal of an ellipsis longer than the precision);
  `ExtendedMessageFormat` with quoted text, `''`, `{n}`, `{n,number,...}` and a registered custom
  `{n,upper}` format formats like `MessageFormat` (upper-cased where the custom format applies),
  and `toPattern()` reparses to the same output and is a fixed point.

Not covered: the `lookup` package beyond the map lookup (files, URLs, scripts, DNS, XML, system
properties), `StringMatcher`s beyond the char matcher, the deprecated `Str*` twins,
`DamerauLevenshteinDistance`, `IntersectionSimilarity`, `CompositeFormat`.

## Bugs

Fourteen, all pinned (`pin…` tests) and recorded in `bugs.toml`: `CosineDistance` throws for blank
text (/1); `ReplacementsFinder` drops a trailing replacement (/2); `JaroWinklerSimilarity` of two
equal empty non-String CharSequences is 0 (/3); `TextStringBuilder.equalsIgnoreCase(null)` throws
(/4); `TextStringBuilder.indexOf("")` is -1 at the end of the builder (/5);
`RandomStringGenerator.generate` spins forever on an unsatisfiable configuration (/6);
`StringSubstitutorReader.read(char[], int, int)` returns 0 when a variable is empty (/7);
`LevenshteinDetailedDistance` reports a distance above the Levenshtein distance (/8);
`ExtendedMessageFormat.toPattern()` drops custom formats after a literal `}` (/9); the substitutor
reader and `replace` disagree when prefix equals suffix (/10); `TextStringBuilder.lastIndexOf(str,
start)` misses a match beginning at `start` (/11); `DoubleFormat` with `minDecimalExponent` throws
when rounding a lone digit 5 at the position above it — `0.5` to a whole number (/12); the
substitutor reader throws for a text ending in `$` with a one-character prefix (/13); a variable
value ending in `$` escapes the variable that follows it in the template (/14).

Observed and not recorded, since the code's own tests pin them or no contract is broken: the
Javadoc of `unescapeCsv` says a quoted value without special characters is "returned unchanged",
but `unescapeCsv("\"foo.bar\"")` is `foo.bar` and `StringEscapeUtilsTest` asserts exactly that;
`NumericEntityUnescaper`'s class comment says the semicolon is optional while the default requires
it (the test models the default); `CaseUtils.toCamelCase` treats only the space as whitespace and
always as a delimiter, explicit set or not (the `@param` text says "null and/or empty array means
whitespace", but the Javadoc's own example `toCamelCase(" to @ Camel case", true, '@')` needs the
space as a delimiter too; the model follows the examples); `AlphabetConverter.toString()` prints `char -> <code
point>` instead of the encoding (no contract); `FuzzyScore` consumes the whole term on a missed
query character, so later query characters cannot score (the Javadoc gives only the scoring rule).
- 2026-09-20: base bumped ae3d36b8cea5 → 00be782c2bb4 (2026-09-19, "Bump github/codeql-action/* from 4.37.9 to 4.38.1"; 1.15.1-SNAPSHOT); 14 bug(s) still reproduce. 12 tests pass.
