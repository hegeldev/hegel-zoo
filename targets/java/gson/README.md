# gson

[google/gson](https://github.com/google/gson): Google's JSON library for Java — a streaming
`JsonReader`/`JsonWriter`, the `JsonElement` tree, and reflection-based `toJson`/`fromJson` over
Java objects. Pinned at 2.14.1-SNAPSHOT (8fe07781, 2026-09-14; the last release is 2.14.0).
Apache-2.0; the repository declares no AI policy (it is in maintenance mode). The first Java
target of the zoo: the tests are the Maven module `hegel/` that the patch adds at the repository
root (`hegel/pom.xml` depends on the gson artifact `[run] setup` installs from this checkout, on
`dev.hegel:hegel` and on JUnit 5), with the harness `Zoo.java`, the judge's `ZooListener` and
the tests in `hegel/src/test/java/zoo/`. See HACKING.md for the Java mechanics.

## What is tested

The oracle is `Ref.java`, a reference JSON reader and writer written from RFC 8259 on plain Java
values (LinkedHashMap, List, String, an exact `Num` of lexeme + BigDecimal, Boolean, a null
marker), with generators for random trees (strings over an alphabet of quotes, backslashes,
control characters, U+2028/2029, HTML characters, surrogate pairs and lone surrogates; numbers
from a pool of boundary lexemes — 2^31, 2^53±1, 2^63, 2^64, 1e400, 4.9e-324, -0 — and random
ones), for valid texts with random whitespace and escape spellings, and for mutations that break
a text (junk tokens, deletions, truncation). The other models come from the Javadoc: the exact
placement rules of `FormattingStyle`, `JsonReader.getPath`/`getPreviousPath`, `JsonPrimitive`'s
equality and coercion rules, the `ToNumberPolicy` results, and the `nextInt`/`nextLong` contract.

- **treesRoundTripThroughText** — a random tree (numbers as a random Number class fitting the
  lexeme: LazilyParsedNumber, int, long, BigInteger, BigDecimal, or the double whose shortest
  form the lexeme is) `toString()`s to exactly the compact, non-HTML-escaped text the reference
  writes; `JsonParser.parseString` gives an equal tree with an equal hash; `Gson.toJson` with
  random `serializeNulls`, HTML escaping, strictness and formatting (compact, `setPrettyPrinting`,
  a random `FormattingStyle`) is exactly the documented layout and reads back with the
  reference and with `fromJson`; `deepCopy` is equal and independent.
- **strictReaderAgreesWithTheReference** — a valid or mutated text through a STRICT `JsonReader`
  accepts iff the reference accepts (unpaired surrogates and a leading BOM excepted, both
  documented), with the same value; LEGACY_STRICT, LENIENT and `parseString` accept everything
  STRICT does with the same value; `parseString` and `Gson.fromJson(String)` throw on trailing
  data (skipped after a top-level null: gson/2).
- **recordsRoundTripThroughJson** — a record universe (primitives and their boxes, float/double
  with `serializeSpecialFloatingPointValues`, char, enum, BigDecimal, BigInteger, lists with
  nulls, `Map<String,Integer>`, `Map<Integer,String>`, `Map<Double,Boolean>`, `Map<Boolean,String>`,
  nested records) round-trips through `toJson`/`fromJson`, through `toJsonTree`, inside
  `List<Pojo>` and `Map<String,Pojo>`, and `int[]`/`String[]`/`double[][]` do too; the text is
  valid JSON unless NaN/Infinity were asked for.
- **objectsReadPerTheNumberPolicy** — `fromJson(text, Object.class)` under each `ToNumberPolicy`
  and strictness gives the documented plain-Java value (ArrayList, LinkedHashMap in order,
  Double / LazilyParsedNumber of the lexeme / Long-or-Double / BigDecimal), and writes back to the
  same value.
- **arraysAndObjectsMatchTheCollectionModels** — `JsonArray` against an ArrayList (add/set/
  remove(int)/remove(element)/addAll/asList view/getAs* on one element) and `JsonObject` against
  a LinkedHashMap (add/addProperty/remove/has/keySet order/asMap view; re-adding keeps the
  position; equality ignores member order, printing does not); equal collections hash equally.
- **primitivesFollowTheDocumentedEqualityAndCoercions** — `JsonPrimitive` pairs of random
  holders (Boolean, String, Character, Integer, Long, Double incl. NaN/-0.0, BigDecimal,
  BigInteger, LazilyParsedNumber) follow the documented `equals` (integral classes by long or
  BigInteger, BigDecimals by compareTo, other numbers by double with NaN equal) with consistent
  hashes; `isNumber`/`isString`, `getAsString`, `getAsBoolean`, `getAsNumber` (throws for a
  boolean), `getAsInt`/`getAsDouble` (numbers truncate, strings parse or throw), `toString`.
- **numbersReadIntoTypedFieldsExactly** — a number lexeme, quoted or not, into `int`/`long`
  (accepted iff the value is an exact int/long, documented; the double-fallback shape is gson/1),
  `double`, `BigDecimal`, `BigInteger`, `String` (keeps the lexeme) and `Number`
  (LazilyParsedNumber of the lexeme), and the typed values back to the same JSON value.
- **writerEventsReadBackAsTheSameEvents** — random writer events (with `setHtmlSafe`,
  `setSerializeNulls`, `setIndent`, strictness) produce the compact text the escaping table
  documents, read back as the same events, and `getPath()`/`getPreviousPath()` after every
  event match the documented path model.

Not covered: `Date`/`Calendar`/`Locale`/`Currency`/`InetAddress` adapters (locale, time-zone or
network dependent), `@SerializedName`/`FieldNamingPolicy`, `@Expose`/exclusion strategies,
custom `TypeAdapter`s and `JsonSerializer`/`JsonDeserializer`, `JsonStreamParser`, the lenient
grammar beyond "accepts what strict accepts", `enableComplexMapKeySerialization`, `Unsafe`-based
instantiation, nesting-limit behaviour.

## Bugs

- **gson/1 (medium)** — `nextInt`/`nextLong` accept values that are not exact ints/longs through
  their `Double.parseDouble` fallback: `9223372036854775808` reads as Long.MAX_VALUE,
  `123456789012345678.0` as 123456789012345680, `1.00000000000000001` as 1 (documented: "if the
  numeric value cannot be exactly represented … this method throws").
- **gson/2 (low)** — `JsonParser.parseString("null 1")` returns JsonNull; the trailing-data check
  is skipped after a top-level null although the docs promise an exception.
- **gson/3 (medium)** — with an explicit STRICT or LEGACY_STRICT strictness, `toJsonTree` throws
  `IllegalArgumentException("JSON forbids NaN and infinities: 1E+309")` for a finite BigDecimal
  or BigInteger beyond the double range (`JsonTreeWriter` checks `doubleValue()` whatever the
  class), while `toJson` writes the same value and `fromJson` reads it back.

All three are pinned (`pin…` tests) and recorded in `bugs.toml`.
