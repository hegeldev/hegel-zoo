# jackson-yaml

[jackson-dataformats-text](https://github.com/FasterXML/jackson-dataformats-text), module `yaml`
(`tools.jackson.dataformat:jackson-dataformat-yaml`, Jackson 3.x line, 3.3.0-SNAPSHOT): the YAML
backend for Jackson's streaming, tree and databind APIs. It parses with
[snakeyaml-engine](https://github.com/snakeyaml/snakeyaml-engine) 3.0.1 (a YAML 1.2 processor) and
types plain scalars with the engine's schema resolver — the JSON schema by default,
`YAMLFactory.builder().yamlSchema(YAMLSchema.CORE)` for the core schema — but decodes numbers itself
(`_decodeNumberScalar`: `0x`/`0o`/`0b`, underscores, the 1.1-compatibility `PARSE_OCTAL_NUMBERS`).
Writing goes through the engine's emitter with Jackson choosing every scalar's style (double quotes
by default; `MINIMIZE_QUOTES`, `LITERAL_BLOCK_STYLE`, `ALWAYS_QUOTE_NUMBERS_AS_STRINGS`, `INDENT_ARRAYS`,
`CANONICAL_OUTPUT`, `ALLOW_LONG_KEYS`, `USE_YAML_NONFINITE_NOTATION`, native type/object ids as tags and
anchors, or a caller-supplied `DumpSettings`).

The pinned commit is on the `3.x` branch (2026-09-07). The tests are a Maven module `hegel/` added by
the patch; `[run] setup` builds and installs the `yaml` module (and its parent pom) from the pinned
tree. **Fragility:** `yaml` depends on jackson-core/databind `3.3.0-SNAPSHOT`, which the root pom (and
`hegel/pom.xml`) fetch from `https://central.sonatype.com/repository/maven-snapshots`. Those snapshots
float and are purged once 3.3.0 is released, so this target can change or stop building without any
change to the pinned commit; when that happens, re-pin to a commit on a released line.

## The oracle

Three views of the same document must agree:

- **snakeyaml-engine in-process**, `Load.loadAllFromString` with the same schema (`JsonSchema` or
  `CoreSchema`) that the Jackson factory uses — the processor Jackson wraps, so what it reads is what
  the YAML text means to Jackson's own parser generation;
- **Jackson's JSON reader** (`JsonMapper` with `ALLOW_NON_NUMERIC_NUMBERS`) on the JSON text of the same
  tree — for token streams and canonical forms;
- **the generator's own value**: a randomised YAML writer (`YamlGen`, a port of the zoo's SnakeYAML
  writer to Jackson trees and the engine's resolvers) produces documents whose value is known by
  construction, in the spellings each schema accepts.

Values are compared as a canonical `JsonNode` form (`Canon`): integers by their digits, floats by the
bits of the double (`Float` nodes through their decimal text, as Jackson writes them), binary by
base64, maps as key-sorted pairs. Jackson's property names are always strings, so documents where the
engine builds a non-string key are not compared.

## What is tested

`hegel/src/test/java/zoo/JacksonYamlTest.java`:

- `writtenDocumentsReadAsTheirTrees` — `YamlGen` documents (block and flow styles, all scalar styles,
  comments, indentation, explicit keys, document markers, multi-document streams, `-0`, `0x`/`0o`/`+`
  and `Null`/`True` spellings in core mode, the 1.2 float forms) through `readValues` equal their
  trees, the engine reads the same, the JSON reader on the tree's JSON gives the same canonical form,
  the YAML token stream (kind, names, texts, number type and exact value, binary) equals the JSON
  token stream, the `String`/`byte[]`/`Reader`/`InputStream`/`char[]` parsers give the same tokens,
  and `readTree` agrees with `readValues`.
- `mutatedDocumentsReadLikeTheEngine` — the same documents with 1–3 random edits (indicators, tags,
  markers, anchors, line swaps, re-indentation): Jackson and the engine both succeed with the same
  value or both fail; when Jackson fails the exception is a `JacksonException`, never a
  `NullPointerException`, `ClassCastException`, `NumberFormatException`, `YamlEngineException` or
  `StackOverflowError`. Anchors/aliases (bug 7), tags, mid-stream BOMs, merge keys, duplicate keys
  (the engine rejects them, Jackson keeps the last unless `STRICT_DUPLICATE_DETECTION`) and the
  engine-only defects below are not compared.
- `scalarsTypeLikeTheSchema` — plain scalars (a table of edge spellings plus generated ints, other
  bases, floats, words) in six positions under both schemas: Jackson's token kind is the schema
  resolver's (int/float/bool/null/string), the value matches (exact for JSON-schema ints and floats,
  `Double.parseDouble`), the engine agrees, and the `NumberType` follows the value for JSON-schema
  ints.

`hegel/src/test/java/zoo/JacksonYamlWriteTest.java`:

- `treesWrittenByJacksonReadBack` — random trees (null, booleans, `int`/`short`/`long`/`BigInteger`,
  `float`/`double`/`BigDecimal` incl. `1E+3`, `-0.000`, `1E-400`, non-finite, binary, strings from a pool
  of YAML-hostile shapes) written by a `YAMLMapper` with every `YAMLWriteFeature` toggled at random,
  both schemas, sometimes custom `DumpSettings` (indent, width, indicator indent, line breaks,
  `splitLines`, `maxSimpleKeyLength`, non-printable style, flow/scalar styles, explicit end), sometimes
  `WRITE_BIGDECIMAL_AS_PLAIN` and `yamlVersionToWrite(1.1)`: the text ends with the line break, has
  the document start marker and `%YAML` directive exactly when expected, reads back as the tree in
  Jackson and in the engine; several root values through one generator read back as several
  documents; the engine's own `Dump` of the Java value reads back in Jackson.
- `generatorCallsAgreeWithTheTreeWriter` — the same trees written through random streaming entry
  points (`writeString(String/char[]/SerializableString)`, `writeUTF8String`, `writeName` variants,
  `writeStringProperty`, `writeNumberProperty`, `writeNumber(int/long/short/BigInteger/double/float/
  BigDecimal/String)`, `writeBinary` variants, `writeStartArray/Object` with the value and size,
  `writeArray(int[])`, `writeTree` of subtrees, `writePOJO` of scalars) read back as the tree and,
  unless a number was spelled by the caller, produce the tree writer's text byte for byte; type ids
  and object ids on collections are readable (`getTypeId`, `getObjectId`, the
  `YAMLAnchorReplayingFactory` replays the `writeObjectRef` alias, the engine resolves it).

`hegel/src/test/java/zoo/JacksonYamlPinsTest.java`: one pin per bug below; each asserts the correct
behaviour and fails while the bug exists.

Known shapes are skipped by the properties and carried by the pins: strings resolving to numbers
under `MINIMIZE_QUOTES` without `ALWAYS_QUOTE_NUMBERS_AS_STRINGS` (documented), Java spellings of
non-finite numbers (documented), `CANONICAL_OUTPUT` (bug 8), a lone NEL (bug 1), core-schema number
strings (bug 5), the merge key (bug 11), `writeBinary(InputStream)` (bug 10), leading zeros under the
core schema (`017` = 15 is the `PARSE_OCTAL_NUMBERS` feature, `08` is bug 4), and the engine-only
defects listed below.

## Not tested

Databind of POJOs, `@JsonTypeInfo`/`@JsonIdentityInfo` beyond native type/object ids on the streaming
API, `YAMLParser` read features other than `EMPTY_DOCUMENT_AS_EMPTY_OBJECT` and `PARSE_OCTAL_NUMBERS`
(`STRICT_DUPLICATE_DETECTION`, `EMPTY_STRING_AS_NULL`), `LoadSettings` overrides (`loadSettings(...)`,
code-point and nesting limits), custom `StringQuotingChecker`s, comments in the tree, the CSV,
Properties and TOML modules, and the engine's own bugs (see below).

## Bugs

See `bugs.toml` (11: jackson-yaml/1 … 11). In short: a lone U+0085 string written plain reads back as
null (1); `EMPTY_DOCUMENT_AS_EMPTY_OBJECT` leaves the parser without a context (NPE in `currentName`)
and `---` still reads as null (2); `!!int +` ends the token stream mid-document (3); under the core
schema `08`/`09`/`0128…` throw "Invalid base-8 number" (4); `ALWAYS_QUOTE_NUMBERS_AS_STRINGS` uses the
JSON schema's number shapes so `0x1F`/`.Inf`/`.NaN` strings become numbers under the core schema (5);
an object id before `writeBinary` lands on the next property name (6); the tree model reads aliases
as the anchor's name — upstream #2 (7); `CANONICAL_OUTPUT` double-quotes every scalar without tags,
losing all types (8); `writeTypeId` before a scalar is dropped (9); `writeBinary(InputStream)` is
unsupported (10); `MINIMIZE_QUOTES` leaves the merge key `<<` plain (11).

## Observed and not recorded

Jackson behaviour that is documented, deliberate or a matter of taste:

- `PARSE_OCTAL_NUMBERS` (default on) reads `017` as 15 under the core schema where the engine (YAML
  1.2) says 17 — a documented 1.1-compatibility feature.
- `NumberType` follows digit counts for other bases: `0x7fffffff` and `+1234567890` are `LONG`
  though they fit an `int`; the JSON reader says `INT`.
- Explicit-tag mismatches fall through to strings: `!!int 12abc` → "12abc", `!!int 1.5` → "1.5",
  `!!bool yes` → "yes"; `!!int 1_` → 1.
- `MINIMIZE_QUOTES` alone writes number-like strings plain (`"12"` → `12`); documented, opt out with
  `ALWAYS_QUOTE_NUMBERS_AS_STRINGS`.
- `USE_YAML_NONFINITE_NOTATION` off writes `NaN`/`Infinity`, which no YAML schema reads as numbers.
- `ALLOW_LONG_KEYS` switches to the explicit `? key` form above 128 characters; its javadoc says the
  key would otherwise be "truncated" — it is written in explicit form, not truncated.
- The `USE_PLATFORM_LINE_BREAKS` javadoc references survive in 3.x although the feature is gone.
- A caller-supplied `dumperOptions(DumpSettings)` replaces everything `buildDumperOptions` would set:
  `INDENT_ARRAYS*`, `CANONICAL_OUTPUT`, `SPLIT_LINES`, `yamlVersionToWrite` and comment output are
  silently ignored (documented as "overrides").
- Anchors on scalars are not readable (`_currentAnchor` is cleared for scalar values); anchors on
  collections are reported at START_OBJECT/START_ARRAY or the first property name.
- `readTree("")` gives a `MissingNode`, `readTree("---\n")` a `NullNode`.
- Duplicate keys: last wins by default (the engine rejects them); `STRICT_DUPLICATE_DETECTION` opts in.

Defects whose root cause is in snakeyaml-engine 3.0.1 (reproducible with the engine alone; Jackson
inherits them — candidates for a `snakeyaml-engine` target):

- The core schema's float constructor fails on `+.inf`/`+.Inf`/`+.INF` (`NumberFormatException: For
  input string: ".inf"`, wrapped in a `YamlEngineException`); Jackson's own decoder reads them as
  Infinity.
- The scanner rejects the YAML 1.2 escapes `\L` (U+2028) and `\P` (U+2029) in double-quoted scalars.
- `dumpAll` with a `%YAML` directive writes no `...` before the second document's directive, so a
  two-document stream with `yamlVersionToWrite` is unreadable by both the engine and Jackson.
- With an indicator indent smaller than the indent (Jackson's `INDENT_ARRAYS`, or `indicatorIndent`
  without `indentWithIndicator`) a literal block whose content starts with a space or a line break
  gets an indentation indicator computed for the wrong column: `[["\n x"]]` reads back as `"\nx"`,
  `[" a\nb"]` does not parse.
- Deeply indented double-quoted strings with a small `width` are split into `x \n\\  y` and change
  value (the snakeyaml `Emitter.writeDoubleQuoted` lineage bug, snakeyaml/16).
- `DumpSettings` accepts an indicator indent ≥ the indent and then writes block mappings left of
  their sequence indicator.

## History

- 2026-09-16: created (turn 172); 11 bugs.
