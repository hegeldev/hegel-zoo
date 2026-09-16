# java/sbe — Simple Binary Encoding (sbe-tool)

[aeron-io/simple-binary-encoding](https://github.com/aeron-io/simple-binary-encoding) is the reference
implementation of the FIX SBE binary message format: `sbe-tool` parses an XML message schema into an
intermediate representation (IR) of tokens, and from the IR generates codecs for Java, C, C++, C#, Go and
Rust (plus DTO classes for Java, C++ and C#), encodes/decodes the IR itself (`sbe-ir.xml`), decodes messages
"on the fly" from the IR (`OtfMessageDecoder`, `JsonPrinter`) and transforms schemas to older versions.
Upstream has three jqwik properties (`DtosPropertyTest`, `JsonPropertyTest`, `ParserPropertyTest` under
`sbe-tool/src/propertyTest`) built on a 1200-line random schema generator; this target ports their idea to
Hegel with an independent model and pushes the schemas further (big-endian, offsets, custom ranges and null
values, versions, tricky names).

Upstream builds with Gradle, so the patch adds a Maven module `hegel/` that compiles `sbe-tool/src/main/java`
as its own main sources (dependencies: agrona 2.6.0 and org.json, the versions of `gradle/libs.versions.toml`)
and runs the properties from `hegel/src/test/java/zoo`. The generated Java codecs are compiled in memory
with javac (`CompilerUtil.compileInMemory`, so surefire runs with `useManifestOnlyJar=false`); the C++ round
trip uses `g++` when present.

## The oracles

- **An independent encoder written from the IR** (`SbeGen`): walks the message tokens, draws values and
  writes them into a buffer by hand (header, block, groups with dimension headers, var data), keeping a
  JSON model of what it wrote in the printer's conventions (enums by name or "null", sets as
  `{choice: bool}`, groups as arrays, var data as strings or hex dumps, not-present fields as their null
  values, constants from the IR).
- **The JSON printer** (`JsonPrinter` over `OtfMessageDecoder`) must show exactly the model.
- **The generated Java codecs and DTOs**, compiled in memory: DTO decode → encode must reproduce the bytes,
  and the re-encoded message must print the same.
- **The generated C++ codecs and DTOs**, compiled with g++ and driven by upstream's own
  `CppDtosPropertyTest/main.cpp` (decode → DTO → encode must reproduce the bytes).
- **The IR codec**: encoding the IR to its binary form and decoding it must give the same tokens and the
  same generated Java.
- **Schema evolution**: a message of an older version of the schema (the XML pruned to that version) must
  decode with the current schema's printer and DTO as the old values plus the null/empty defaults of what
  was added later.

## Properties (`SbeTest`)

Every property draws a random schema from `SchemaGen` (70 % "extended": big-endian, field/member offsets,
custom ranges and null values, constants, deprecated and versioned members, tricky names such as `type3`,
`length7`, `Class12`; 30 % the shapes of upstream's generator).

1. `schemasParseAndIrRoundTrips` — the schema parses leniently and strictly (warnings fatal); the IR has
   the schema's id and version; `IrEncoder` → `IrDecoder` reproduces id, version, package, byte order,
   semantic version, the header tokens and the message tokens (as text), and the Java generated from
   both IRs is identical except `package-info` (the IR frame has no description field).
2. `printerShowsTheEncodedValues` — `JsonPrinter` output parses as JSON and equals the model
   (`JSONObject.similar`); the three `print` entry points agree.
3. `javaDtosRoundTrip` — Java codecs (random generator options: group-order annotation, interfaces,
   decode-unknown-enum-values, precedence checks) and DTOs are generated and compiled in memory; the DTO
   decoded from the message prints `[TestMessage](…)`, `encodeWithHeaderWith` reproduces the bytes, and
   the DTO of the re-encoded message prints the same.
4. `otherGeneratorsAcceptEverySchema` — the C, C++ (+DTO), C# (+DTO), Go struct, Go flyweight and Rust
   generators run without exception on every schema (in memory, Rust in a temporary directory).
5. `cppDtosRoundTrip` (skipped without `/usr/bin/g++`, at most 12 cases) — C++ codecs and DTOs generated
   into a temporary directory, compiled with `g++ --std=c++17` together with upstream's round-trip driver,
   run on the message; the output bytes must equal the input.
6. `olderMessagesDecodeWithNewerCodecs` — for a schema of version ≥ 1 and an older version v, the XML
   pruned to v (members with `sinceVersion > v` removed) gives the old IR from which a message is
   encoded; the current schema's `JsonPrinter` must show the old values plus defaults for everything added
   after v (`addDefaults`), and the current DTO must decode it (acting version v) and re-encode it as a
   current message that prints the same. Where the message has no groups, upstream's
   `SchemaTransformerFactory("*:v")` must give the same message tokens as the pruned XML.

`SbePinsTest` holds one pin per recorded bug; each asserts the correct behaviour on a minimal schema and is
listed in `[expected_failures]`.

## What the generator avoids

- Parser rules found by running: `nullValue` only with `presence="optional"`; enum `encodingType` in
  {char, uint8, int8, int16, uint16, int32}; `numInGroup` uint8/uint16; `semanticType` not differing
  between a type and its field; fields with `sinceVersion` are optional and sorted after earlier ones;
  var data with `sinceVersion` only at message level (the C# generator refuses "Cannot extend var data
  inside a group"); constant chars from a safe alphabet, no `"` or control characters in attributes.
- Groups are never named `type<n>` (bug sbe/6: a group named like a type used inside it does not compile).
- The model writes bit sets (and enum null values) in the schema's byte order rather than the set token's
  (bug sbe/2), and records uint64 values as the signed longs the printer shows (bug sbe/1).
- In the evolution property the acting version is chosen so that every composite field, and every composite
  member, of the message is present (bugs sbe/3 and sbe/4; the parser cannot express members newer than the
  schema), the older schema is derived by pruning the XML rather than by upstream's transformer (bug sbe/7,
  whose var-data offsets are also stale), and the DTO route expects zeros for not-present optional numeric
  arrays (bug sbe/8); a not-present set is expected with all choices true on the printer route (bug sbe/9).
- Messages are printed from a buffer with eight bytes of slack (bug sbe/10: a trailing constant enum field makes
  the printer read past the message); float constants and null values are expected as the printer shows them,
  widened to double (1.0E-10 prints as 1.000000013351432E-10).
- Only valid values and choices with `sinceVersion <= actingVersion` are written; UTF-8 var data is valid
  UTF-8 within the type's `maxValue`.

## Not tested

Compiling or running the C, C#, Go and Rust output (Go was run once by hand for sbe/5); the C++ OTF decoder;
dotnet; enums with a named encoding type; message-level `sinceVersion`, `deprecated` on types, `epoch`/
`timeUnit`; the Gradle build, `SbeTool`'s command line and system properties (`sbe.xinclude.aware`,
`sbe.target.language` …); XInclude; `SbeTool.generate` file output; the generated Java codecs' own
API beyond what the DTOs use (group iteration, var-data accessors, `appendTo`); precedence-check runtime
behaviour; `IrDecoder` on hand-crafted IR frames.

## Bugs found

| id | severity | what |
|---|---|---|
| sbe/1 | low | `JsonPrinter` prints uint64 values as signed longs (18446744073709551585 → -31) |
| sbe/2 | low | the IR's BEGIN_SET token lacks the schema byte order (little-endian in a bigEndian schema; Go flyweight `Clear`/`IsEmpty` follow it) |
| sbe/3 | medium | `OtfMessageDecoder`/`JsonPrinter` read a composite field added after the message's version from the buffer (IndexOutOfBounds or garbage) |
| sbe/4 | medium | the Java DTO's `decodeFrom` throws NullPointerException on an older message when a composite field was added later |
| sbe/5 | medium | the Go flyweight codec's `RawValue()` of a multi-byte set returns only its first byte |
| sbe/6 | low | Java codecs do not compile when a group is named like a type used inside it (`pair` / `Pair`) |
| sbe/7 | medium | `SinceVersionSchemaTransformer` zeroes the block length of every group |
| sbe/8 | low | the Java DTO re-encodes a not-present optional array as zeros, a not-present scalar as its null value |
| sbe/9 | low | `JsonPrinter` shows every choice of a not-present bit set as true (the null value is all ones) |
| sbe/10 | low | `JsonPrinter` reads one byte past a message ending in a constant enum field (IndexOutOfBounds on an exact-length buffer) |

## Observed, not recorded

- The IR frame (`sbe-ir.xml`) has no field for the schema description, so `IrDecoder` yields
  `description == null` and `package-info.java` differs after an IR round trip.
- The C# generator refuses var data with `sinceVersion` inside a group ("Cannot extend var data inside a
  group"), a documented limitation the other generators do not share.
- The generated DTOs define no `equals`/`hashCode`.
- The generated `MessageHeaderDecoder` of a bigEndian schema is fine, but the one in `uk.co.real_logic.sbe.ir.generated`
  (used for the IR itself) is little-endian only; harnesses must read message headers in the schema's byte order.
- The C++ DTO generator writes char-array constants as string literals padded with raw NUL bytes to the array
  length (`return "3-2bb\0\0\0";` with literal zero bytes): g++ warns "null character(s) preserved in literal"
  (an error under `-Werror`), though the `const char*` semantics are unaffected.
- The Rust generator names the codec module of a message `M` `mc_odec` (`toLowerSnakeCase("MCodec")`),
  consistently referenced from `lib.rs`, so it compiles; cosmetic.
- The Java DTO's range validation for composite members is not applied uniformly (a `uint64` member with
  `minValue` in one composite was validated, the same type in another composite was not); not isolated.

## History

- 2026-09-16: created (turn 177) at 89bb53644fad (1.41.0-SNAPSHOT of 2026-09-09); 10 bugs.
