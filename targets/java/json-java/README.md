# json-java

[JSON-java](https://github.com/stleary/JSON-java) (`org.json:json`, Public Domain), pinned at
`87467357` (20260814, 2026-09-13): the reference JSON library for Java — `JSONObject`,
`JSONArray`, `JSONTokener`, `JSONWriter`, `JSONPointer`, the strict/lenient
`JSONParserConfiguration`, and the converters `XML`, `JSONML`, `CDL`, `Cookie`, `CookieList`
and `HTTP`.

The patch adds a Maven module `hegel/` that depends on the library at its pom version (installed
by the setup step with `mvn -DskipTests install`), on `dev.hegel:hegel` 0.6.0, JUnit 5, and on
Jackson and Gson as independent parsers. The properties are JUnit tests driven by `Hegel.test`;
`Zoo.java` is the small harness shared by the Java targets (case counts from `HEGEL_TEST_CASES`,
a collect mode under `ZOO_COLLECT=1`), `Gen.java` generates JSON values and their canonical
forms, and `ZooListener` prints one `ZOO ok|FAILED <method>` line per test for the judge.

## What is tested

- `RoundTripTest` — `toString` (compact and indented) parses back to the same value; the output
  is RFC 8259 text that Jackson (BigDecimal/BigInteger, trailing-token and duplicate detection
  on) and Gson read to the same tree; `JSONWriter` agrees with `toString`; `toMap`/`toList` and
  the Map/Collection constructors keep the value (`useNativeNulls` on; the default's dropping of
  null members is documented); `valueToString` agrees with `quote`/`numberToString`.
- `ParseTest` — RFC-valid text with every freedom the grammar gives (whitespace, escapes, number
  spellings) parses to its value in both modes; a differential of strict mode against Jackson on
  mutated text (both accept or both reject); the documented lenient spellings (bare words, single
  quotes, `=`/`=>`, `;`, comments, trailing commas, hex escapes) parse to the value; integer texts
  get the narrowest type (Integer, Long, BigInteger) and decimal texts keep their value;
  `quote` reads back and is standard; `stringToValue` is total; nesting up to the default depth.
- `PointerTest` — an RFC 6901 model (escaping, evaluation, the RFC 3986 fragment form,
  `array-index`) against `JSONPointer` built from tokens and parsed from text, with decoy
  siblings in the documents; `JSONObject.query`/`optQuery`.
- `XmlTest` — `XML.escape`/`unescape` against the JDK's parser; `XML.toString` produces
  well-formed XML or rejects the key (JDK `DocumentBuilder` as oracle); `XML.toJSONObject`
  against a DOM model (attributes, text, repeated children, `keepStrings`); JSON → XML → JSON
  keeps string values; the `XMLParserConfiguration` builders are order-independent and lossless.
- `ConvertersTest` — CDL rows and single rows round-trip; `Cookie.escape`/`unescape`; `Cookie`
  and `CookieList` against their documented models; `HTTP` headers round-trip; JSONML arrays.
- `ApiTest` — `similar` is value equality up to number type (following `isNumberSimilar`'s
  documented algorithm); `JSONParserConfiguration` builders; `maxNumberLength`; the nesting-depth
  limit for text and the negative-means-no-limit rule; Collection constructor and `putAll`
  agree; `put(index)` pads with null; `increment`/`accumulate`/`append`.
- `PinsTest` — one plain JUnit test per recorded bug.

## Bugs

See `bugs.toml`: `\u` escapes accept a sign (1); strict mode accepts Java number spellings
(`0x1.8p1`, `1.5f`, `1e5D`, `01.5`, `1.E5`) (2) and control characters as whitespace (3);
`JSONPointer` unescapes tokens twice, so `/~01` finds `/` (4), its URI fragment form is not RFC
6901 §6 (5) and it accepts `01`, `+1`, `-0`, `00`, `١` as array indexes (6); `XML.unescape`
rejects the character references `XML.escape` emits (7); every `XMLParserConfiguration.with*`
resets `keepStrings` (8) and both configuration classes lose `maxNumberLength` (9); an attribute
value `null` ignores `keepStrings` (10); `XML.toString`/`JSONML.toString` emit non-well-formed
XML for non-name keys (11); CDL cannot read back a value starting with `'` (12) and loses edge
whitespace (13); `HTTP.toJSONObject` cannot read `HTTP.toString` (CRLF) (14); JSONML with
`keepStrings` unescapes twice (15); `maxNestingDepth` is ignored for text (16) and a negative
value throws instead of meaning no limit (17); NOTES.md's `1.2e6.3` claim (18).

## Notes

- Documented behaviour the properties follow rather than flag: `JSONObject(Map)` drops null
  values unless `withUseNativeNulls(true)`; `putAll` does not wrap the items (NOTES.md);
  `numberToString` strips trailing zeros (`1.10` → `1.1`); `similar` on two numbers of the same
  class uses `compareTo`, so `Double 0.0` and `-0.0` differ while `0.0` and `BigDecimal 0` are
  similar; `XML.toString(JSONArray)` is an element sequence without a root and an object whose
  only key is `content` collapses to its text; `Cookie.toJSONObject` lower-cases attribute names
  and trims; `CookieList` keeps empty values; `&#X41;` (capital X) is accepted by the XML reader;
  the lenient parser ignores one trailing comma in an array (`[1,]` is `[1]`).
- Lenient mode treating `0x1.8p1` or `1.5f` as numbers, controls as whitespace, and `1.2e6.3` as
  a bare string is the library's choice; only strict mode's acceptance is recorded (2, 3) plus
  the NOTES.md claim (18).
- `JSONArray.put((Object) null)` stores a raw Java null that `get` reports as "not found" and
  that makes `similar` asymmetric; not recorded, since `put(null)` is outside the documented API
  (the null-safe spelling is `JSONObject.NULL`).
- The mutated-text differential skips inputs Jackson rejects only because of its own size limits
  ("Too many ...").
- Not tested: bean introspection (`JSONObject(Object bean)`, `@JSONPropertyName`), `JSONString`,
  `Property`, the `Enum` conversions.
