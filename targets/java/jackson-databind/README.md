# jackson-databind

[FasterXML/jackson-databind](https://github.com/FasterXML/jackson-databind): the data-binding layer
of Jackson 3 — `ObjectMapper`/`JsonMapper`, the `JsonNode` tree model (`ObjectNode`, `ArrayNode`,
the scalar nodes and their coercions), POJO/record/collection/map (de)serialization, polymorphic
types, `MappingIterator`/`SequenceWriter`, and the built-in `java.time` support. Pinned on `3.x` at
3.3.0-SNAPSHOT (2a428d9b, 2026-09-16; packages `tools.jackson.databind`, annotations still
`com.fasterxml.jackson.annotation`). Apache-2.0; the repository's CLAUDE.md is build and architecture
guidance for agents and declares no restriction. The tests are the Maven module `hegel/` the patch
adds at the repository root (`hegel/pom.xml` depends on the jackson-databind artifact `[run] setup`
installs from this checkout, on `dev.hegel:hegel` and on JUnit 5), with the harness `Zoo.java`
(`run(name, body)` wraps `Hegel.test` and, with `ZOO_COLLECT=1`, prints one line per distinct
failure message and the `count()` statistics), the judge's `ZooListener`, and the tests in
`hegel/src/test/java/zoo/`. See HACKING.md for the Java mechanics.

## What is tested

The oracle for the tree model is `Ref.java` (from the jackson-core target): a reference JSON reader
and writer on plain Java values (LinkedHashMap, List, String, an exact `Num` of lexeme + BigDecimal,
Boolean, a null marker) with random-whitespace/escape spellings and mutations. `Model.java` maps a
reference value to the `JsonNode` jackson should build (Int/Long/BigInteger by range; Double, or
Decimal under `USE_BIG_DECIMAL_FOR_FLOATS`) and to the plain Java value `readValue(text, Object)`
should return, and compares trees to values (floats as doubles unless exact). The value-binding
properties generate their own records (`Point`, `Bag` of collections/maps/optionals/bytes/big
numbers/UUID/nested records/arrays, a `@JsonTypeInfo(NAME)` sealed `Shape`, a `DEDUCTION`-typed
`Deduced`, `Nested` with `Object` and `Map<String,Object>` members) and the sixteen `java.time` types.

- **TreesTest**
  - *treeReadsTheReferenceValue* — a valid text read through every source (String, byte[], Reader,
    InputStream, DataInput, byte range, JsonParser, TokenBuffer) equals the modelled tree (and
    hashCode agrees); `writeValueAsString`/`toString`/pretty output re-reads to the same tree and
    equals the reference writer's compact text; `WRITE_PROPERTIES_SORTED`, `WRITE_NULL_PROPERTIES`
    off and `READ_NULL_PROPERTIES` off follow their models; the exact mappers build Decimal nodes and
    `STRIP_TRAILING_BIGDECIMAL_ZEROES` strips; a mutated text is accepted iff the reference accepts it.
  - *treesAreEqualWhenTheirValuesAre* — readTree, node-builder, `deepCopy`, `valueToTree` and
    `convertValue` trees of the same value are equal (size/isEmpty agree; deepCopy is independent);
    trees of different values are not, unless the values are the same and only number types differ
    (`IntNode(1)` ≠ `LongNode(1)` by design); `equals(Comparator, other)` with a by-value comparator
    bridges exact and double trees.
  - *objectNodeFollowsAMapModel* / *arrayNodeFollowsAListModel* — random sequences of the mutators
    (put/set/replace/remove/removeAll/retain/without/setAll/putIfAbsent/removeIf/putNull/putArray/
    putObject/removeNulls; add/insert/set/remove/setNull/insertNull/addNull/addAll/removeIf/removeNulls)
    against a LinkedHashMap / ArrayList model, including the documented edge rules (insert index
    clamped, set out of range throws, remove out of range returns null); the readers
    (`properties`, `propertyNames`, `values`, `valueStream`, `get`/`path`/`optional`/`has`/
    `hasNonNull`/`required`, size, equals, toString) agree with the model.
  - *pointersAndFindersFollowTheModel* — `at`/`requiredAt` with random `JsonPointer`s (the index rule:
    1–10 digits, no leading zero, ≤ Integer.MAX) against a path model; `findValue`/`findPath`/
    `findParent`/`findValues`/`findParents`/`findValuesAsString` against a document-order model
    (bugs 1 and 2 gated).
  - *withObjectAndWithArrayCreatePaths* — `withObject`/`withArray(pointer, OverwriteMode, preferIndex)`
    against a model of traversal, creation and the four overwrite modes.
- **CoercionsTest**
  - *numberNodesCoerceAsDocumented* — a BigDecimal from a boundary pool as Short/Int/Long/BigInteger/
    Double/Float/Decimal nodes: the exact accessors (`intValue`…) throw iff the value is not
    representable, `asX` truncates fractions and throws out of range, `asXOpt`/`asX(default)` are
    empty/the default exactly when `asX` throws, `canConvertToInt/Long/Short/ExactIntegral` agree,
    the nodes agree with each other, and the `StringNode` of the same lexeme coerces like the number
    (bugs 3, 4, 7 and 8 gated). `asBoolean` of floating-point nodes is unspecified and only counted;
    a Float/Double node's `decimalValue`/`bigIntegerValue`/`asString` is its shortest representation
    (`BigDecimal.valueOf`), compared as the same float/double rather than the exact value.
  - *otherNodesCoerceAsDocumented* — null, missing, booleans, strings (numeric per the RFC grammar or
    not), binary, object, array and POJO nodes through every accessor per the Javadoc table.
- **ValuesTest**
  - *valuesRoundTripThroughJsonAndTrees* — a random `Point`/`Bag`/`Shape`/`Nested`: `readValue(write)`
    writes the same text and equals the value (records); write→read→write is idempotent;
    `valueToTree`, `treeToValue`, `convertValue` (to the type and to `Object`) write the same text;
    every source reads it; `writeValueAsBytes` is the UTF-8 of the text; pretty output re-reads as the
    same tree.
  - *sequencesReadBackTheValuesWritten* — `SequenceWriter` (roots or array) → `MappingIterator`
    returns the values; hand-made separators (whitespace required after a scalar root, optional after
    a container or string) read the same.
  - *mapKeysRoundTrip* — `Map<K, String>` for 28 key types (numbers, Character, Boolean, UUID, enums,
    `java.time`, ZoneId/Offset, Period, Duration…): exact round trip and key order; re-written text
    identical; `ORDER_MAP_ENTRIES_BY_KEYS` orders as `TreeMap` for Comparable keys (bug 6 gated).
  - *javaTimeValuesRoundTrip* — the sixteen `java.time` types alone and in a `List` under the default,
    timestamp, `ADJUST_DATES_TO_CONTEXT_TIME_ZONE`-off and `WRITE_DATES_WITH_ZONE_ID` mappers: round
    trip (same instant at UTC when adjusting, exact otherwise), idempotent text, the node type the
    features promise (bug 5 gated).

Conventions, not bugs: a lexeme such as `1e309` overflows to a Double `Infinity`, which is written
as the string `"Infinity"` (`WRITE_NAN_AS_STRINGS`), so such values are left out of the tree
properties and `Object`-typed members; a `Set` reads back as a HashSet (the properties use
`LinkedHashSet`); `ADJUST_DATES_TO_CONTEXT_TIME_ZONE` (default on) normalises Offset/ZonedDateTime
and OffsetTime to UTC on the way in, and a ZonedDateTime's zone id is not written without
`WRITE_DATES_WITH_ZONE_ID`; `readValues` over a root array iterates its elements; `DataInput` with
a root scalar at the end of input (jackson-core/1) and byte sources with lone surrogates in names
(jackson-core/3) are routed to other sources.

Not covered: annotations beyond `@JsonTypeInfo` (views, filters, `@JsonFormat`, `@JsonCreator`
variants, mix-ins), `@JsonIdentityInfo`, `JsonSchema`/format visitors, `ObjectReader` update-in-place,
`DeserializationProblemHandler`s, injectables, `@JsonAnySetter`/`@JsonUnwrapped`, `TypeFactory`
generics resolution, `MapperFeature`s other than `SORT_PROPERTIES_ALPHABETICALLY`, custom modules,
`java.sql`/`java.util.Date` types, and the coercion configuration (`CoercionConfigs`).

## Bugs

Eight, all pinned (`pin…` tests in `PinsTest`) and recorded in `bugs.toml`: `ObjectNode.findValue`/
`findPath`/`findParent` return this node's own property before an earlier match in a descendant,
against the documented document order (jackson-databind/1); `findValuesAsString` throws when a match
is a container (/2); a `StringNode` holding a number with a fraction or exponent (`"92.1"`) cannot
be coerced with `asInt`/`asLong`/`asShort`/`asBigInteger` while the numeric node truncates (/3);
`StringNode.asDouble`/`asFloat` return `Infinity` for `"1E+400"` where the numeric node throws (/4);
`Duration.ofSeconds(Long.MIN_VALUE)` cannot be written as a nanosecond timestamp — the serializer
takes its absolute value and overflows with a raw `ArithmeticException` (/5); a `YearMonth` map key
with a year of 10000 or more is written as `10000-12`, which the key deserializer's strict parser
rejects while the value deserializer accepts it (/6); `FloatNode(2^31).intValue()` is
`Integer.MAX_VALUE` and `DoubleNode(2^63).longValue()` is `Long.MAX_VALUE` — the range check compares
against the bound rounded up to a float/double and the cast saturates (/7); `FloatNode(1e10f).longValue()`
and `bigIntegerValue()` throw "value has fractional part" because `hasFractionalPart` rounds through
`Math.round(float)`, an `int` (/8).

## History

- 2026-09-19: created at 2a428d9b569e (3.3.0-SNAPSHOT, 2026-09-16) with 12 properties and 8 bugs.
