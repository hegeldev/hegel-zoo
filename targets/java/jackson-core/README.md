# jackson-core

[FasterXML/jackson-core](https://github.com/FasterXML/jackson-core): the streaming layer of
Jackson 3 — `JsonParser` (over `String`/`char[]`/`Reader`, `byte[]`/`InputStream`, `DataInput`,
and the non-blocking `ByteArrayFeeder` parser), `JsonGenerator` (Writer-based and UTF-8),
`JsonPointer`, `DefaultPrettyPrinter`, `Base64Variant`s. Pinned on master at 3.3.0-SNAPSHOT
(104aab73, 2026-09-14; packages `tools.jackson.core`). Apache-2.0; the repository's CLAUDE.md is
build/architecture guidance for agents and declares no restriction. The tests are the Maven module
`hegel/` the patch adds at the repository root (`hegel/pom.xml` depends on the jackson-core artifact
`[run] setup` installs from this checkout, on `dev.hegel:hegel` and on JUnit 5), with the harness
`Zoo.java`, the judge's `ZooListener` and the tests in `hegel/src/test/java/zoo/`. See HACKING.md for
the Java mechanics.

## What is tested

The oracle is `Ref.java`, a reference JSON reader and writer written from RFC 8259 on plain Java
values (LinkedHashMap, List, String, an exact `Num` of lexeme + BigDecimal, Boolean, a null marker),
extended with jackson-core's escaping table (`"` `\` and the control characters; `\/`,
`ESCAPE_NON_ASCII`, hex case and lone-surrogate escapes as options) and its root-value model
(several root values, whitespace required after a number, a literal not followed by an identifier
character). Generators produce random trees (strings over quotes, backslashes, control characters,
U+2028/2029, HTML characters, surrogate pairs and lone surrogates; numbers from a boundary pool and
random lexemes), valid texts with random whitespace and escape spellings, and mutations. The
generators are values built from the binding's combinators over a small `Gen.java` (weighted
choice, `chance`, `maybe`, `pick`, `ints`, `many`, `word`): each property draws one record for its
case — the value tree, a `Spelling` (two tapes of whitespace gaps and escape choices, empty for the
compact text), a list of `Edit`s applied at positions taken modulo the live length, the parser kind,
the generator configuration, the write methods and number classes as tapes applied per event, and a
`Feed` (a chunk size and cut positions taken modulo what is left) for the non-blocking parser — and
renders it with pure functions. Each case runs its text through one drawn parser kind — `Src`:
String, char[], Reader, throttled Reader, byte[], InputStream, throttled InputStream, DataInput, or
the non-blocking parser fed at the drawn cuts (`Tokens` hides NOT_AVAILABLE and treats a
NOT_AVAILABLE with `needMoreInput()` false as a stall). The shapes of the recorded bugs are drawn by
default, so the wide properties fail on them and are mapped to the bug each shrinks to
(`intermittent` where the shape is a few percent of cases); `HEGEL_NO_KNOWN=1` (read once) switches
the shapes off, and a shape known only after the draw is counted and skipped for that check;
`zoo.JacksonCoreShapesTest` holds one narrow property per bug over its shape region, which draws
the neighbouring region under `HEGEL_NO_KNOWN=1`.

- **generatorEventsReadBackThroughEveryParser** — random events written by either generator with
  random `ESCAPE_FORWARD_SLASHES` / `ESCAPE_NON_ASCII` / `WRITE_HEX_UPPER_CASE` /
  `WRITE_BIGDECIMAL_AS_PLAIN` / `USE_FAST_DOUBLE_WRITER` and random write methods (String, char[],
  Reader, SerializedString; int/long/BigInteger/double/BigDecimal/String numbers) produce exactly the
  modelled compact text; the reference reads it as the denoted value; every parser kind returns the
  same tokens, names, strings, number lexemes (`getString()`), `getNumberType()` and, after each
  token, `streamReadContext().pathAsPointer()` per a pointer model.
- **parsersAgreeWithTheReference** — a valid or mutated text: the parser accepts iff the reference's
  root-value model accepts, with the same values (lone surrogates, which bytes cannot carry, and a
  leading BOM, which the byte parsers skip by documentation, excepted for the byte sources).
- **numbersDecodeExactlyInEveryParser** — a lexeme (pool, int/long boundaries, 998–1002 digits
  around `maxNumberLength`, random doubles' shortest forms, random BigDecimals), with and without the
  fast parsers: token kind, `getString`, `getNumberType`, `getNumberValue` class,
  `getNumberValueExact`, `getDoubleValue`/`getFloatValue` vs `Double.parseDouble`/`Float.parseFloat`,
  `getDecimalValue`, `getBigIntegerValue` (truncation), `getIntValue`/`getValueAsInt`/`getLongValue`
  (exact ints, or the documented truncation through the double, else `InputCoercionException`),
  `getShortValue`/`getByteValue` (byte allows -128..255), the 1000-digit `StreamConstraintsException`.
- **longStringsCrossTheBufferBoundaries** — strings and names of 199–8002 chars with escapes,
  multi-byte characters and a surrogate pair placed at the 200/500/1000/4000/8000 boundaries: exact
  text, and `getString`, `getStringCharacters`+offset+length, `getString(Writer)`, `readString(Writer)`.
- **binaryRoundTripsThroughEveryBase64Variant** — random bytes (incl. 3000±1 and 4000, the codec
  buffer) through MIME / MIME_NO_LINEFEEDS / PEM / MODIFIED_FOR_URL: the variant round-trips, the
  generator (byte[] with offset, InputStream, throttled InputStream) writes exactly
  `variant.encode(data, false)`, every parser's `getBinaryValue`/`readBinaryValue` decodes it.
- **jsonPointersFollowTheDocumentedModel** — random segments (`~`, `/`, `~0`, `~1`, `~2`, `01`,
  `2147483648`, `-`, `1e0`, empty, spaces, emoji): `compile`/`toString`/`length`/`equals`/`hashCode`,
  building by `appendProperty`/`appendIndex`, per-segment `getMatchingProperty`/`getMatchingIndex`
  (digits only, no leading zero, ≤ 10 chars, int range) / `mayMatch*` / `matches*` / `match*` /
  `tail`, `head`, `last`, `append`, `startsWith`.
- **prettyPrinterLayoutIsExact** — `DefaultPrettyPrinter` with random `DefaultIndenter`
  (indent, eol) / `FixedSpaceIndenter` / `NopIndenter` per container kind and random `Separators`
  (characters, `Spacing`, empty-container and root separators), on both generators with several
  root values: exact layout per the model, and the text reads back with the reference when the
  separators are standard.
- **lenientFeaturesReadTheirSpellingsAsTheStrictValue** — a lenient spelling for one
  `JsonReadFeature` (Java/YAML comments, single quotes, unquoted names, unescaped control chars,
  backslash-escaping any char, leading zeros / plus / decimal point, trailing decimal point, trailing
  comma) reads as the strict value with the feature on and is rejected with it off, in every parser kind.

Not covered: `FilteringParserDelegate`/`TokenFilter`, `JsonParserSequence`, `TreeCodec`, symbol
tables and `INTERN_PROPERTY_NAMES`, `StreamReadConstraints` other than the number length,
`ErrorReportConfiguration`, `TokenStreamLocation` offsets and line/column numbers, UTF-16/UTF-32
input, `writeRaw*`/`writeRawValue`, `ALLOW_NON_NUMERIC_NUMBERS`, `ALLOW_HEXADECIMAL_NUMBERS`,
`ALLOW_MISSING_VALUES`, `ALLOW_RS_CONTROL_CHAR`, duplicate detection, `nextName`/`nextIntValue`
shortcuts, `JsonPointer.forPath` with `includeRoot`.

## Bugs

Fourteen, recorded in `bugs.toml`, each found by a wide property, held by a narrow property in
`zoo.JacksonCoreShapesTest` and pinned by a `pin…` regression example: the DataInput parser fails on a root
number/literal at the end of input and on an empty document (jackson-core/1); `getNumberValueExact()`
turns lossy after `getNumberType()` (/2); the byte-based parsers reject a lone-surrogate `\u` escape
in a property name that the UTF-8 generator writes (/3); the non-blocking parser drops the sign of
`-0` (/4); `"<NUL>…` is sniffed as UTF-16 under `ALLOW_UNESCAPED_CONTROL_CHARS` (/5);
`getLongValue()` saturates for a floating-point lexeme whose double is 2^63 (/6);
`writeString(Reader)` splits a surrogate pair at its 4000-char reads into two escapes (/7);
`writeString(SerializableString)` throws `IllegalArgumentException` for an unpaired surrogate (/8);
under `ALLOW_BACKSLASH_ESCAPING_ANY_CHARACTER` the byte parsers truncate an escaped 4-byte character
(/9) and the non-blocking parser fails on any escaped multi-byte character (/10); an escaped
surrogate pair in a name split between feeds stalls the non-blocking parser (/11); the non-blocking
parser accepts an object's trailing comma without the feature when the brace comes in a later feed (/12);
the DataInput parser skips C0 control characters between tokens (`<0x01> []` reads as `[]`) where
every other parser throws "Illegal character (CTRL-CHAR)" (/13); the non-blocking parser accepts a
root integer directly followed by another root value (`1-40`, `1null`) when both arrive in one
feed, where every blocking parser demands a separating space (/14, found 2026-09-26 by the mutation
property once the recorded shapes were drawn by default).

Known upstream and skipped, not counted: mangled numbers inside containers such as `[123true]` are
not reported (core#1557, `tofix` tests in the repository); the mutation property's root-value model
only applies jackson's separator rule at the root.
- 2026-09-16: base bumped 104aab73ca89 → 6f505ccb2e77 (2026-09-15, "Add `StreamReadConstraints.getMaxBigIntegerScale()` (#1715)"; 3.3.0-SNAPSHOT); 12 bug(s) still reproduce. 8 tests pass.
- 2026-09-17: base bumped 6f505ccb2e77 → 917360f2b0a0 (2026-09-16, "Merge branch '3.2' into 3.x"; 3.3.0-SNAPSHOT); 12 bug(s) still reproduce. 8 tests pass.
- 2026-09-17: base bumped 917360f2b0a0 → 6c2090cda7a8 (2026-09-16, "Merge branch '3.2' into 3.x"; 3.3.0-SNAPSHOT); 12 bug(s) still reproduce. 8 tests pass.
- 2026-09-18: base bumped 6c2090cda7a8 → fa07beee3b21 (2026-09-17, "Merge branch '3.2' into 3.x"; 3.3.0-SNAPSHOT); 13 bug(s) still reproduce. 8 tests pass.
- 2026-09-20: base bumped fa07beee3b21 → d37d7e25139f (2026-09-18, "Merge branch '3.2' into 3.x"; 3.3.0-SNAPSHOT); 13 bug(s) still reproduce. 8 tests pass.
- 2026-09-26: generators rewritten in combinator style over `Gen.java` (one record per property, `Spelling`/`Edit`/`Feed` values); the thirteen inline sidesteps of the recorded bugs removed, so the wide properties draw the shapes by default and are mapped to the bug they shrink to, `HEGEL_NO_KNOWN=1` switching them off; `zoo.JacksonCoreShapesTest` added with one narrow property per bug; jackson-core/14 found and recorded.
