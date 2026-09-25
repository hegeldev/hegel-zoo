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
   current message that prints the same. Upstream's `SchemaTransformerFactory("*:v")` must give the
   same message tokens as the pruned XML, offsets included.
7. One narrow property per recorded bug, a generator over the bug's shape region with random contents
   (schemas without uint64 fields, so each shrinks to its own bug), judged by the oracles above:
   `largeUint64ValuesPrintUnsigned` (1), `bigEndianSetsPrintTheirChoices` (2),
   `olderMessagesPrintWithoutLaterComposites` (3), `olderMessagesDecodeIntoDtosWithLaterComposites` (4),
   `goFlyweightSetsReadTheirWholeRawValue` (5: every set type's generated Go `RawValue()` must read the
   set's whole width), `javaCodecsCompileWithGroupsNamedLikeTheirTypes` (6),
   `transformerAgreesWithPruningOnGroups` (7), `dtosReencodeLaterArraysAsNulls` (8),
   `laterSetsPrintNoChoicesOnOlderMessages` (9), `constantEnumTrailersPrintFromExactBuffers` (10).

`SbePinsTest` holds one pin per recorded bug; each asserts the correct behaviour on a minimal schema and is
listed in `[expected_failures]`.

## What the generators draw

The generators draw every recorded bug's shape by default (STYLE.md rule 11) and the properties fail on
them: the wide ones are listed in `[expected_failures]` mapped to the bug they shrink to
(`printerShowsTheEncodedValues` to sbe/1, in a quarter of the runs landing on sbe/2's big-endian set;
`olderMessagesDecodeWithNewerCodecs` to sbe/9, sometimes on sbe/7's stale var-data offset;
`javaDtosRoundTrip` to sbe/6 intermittently, a `type` group colliding with a `Type<n>` in one case in a
few hundred), the narrow ones every run. `SbePinsTest` keeps one pin per bug as the regression example.

- uint64 fields span 0..2^64-2 and the model expects the unsigned value the printer should show (sbe/1);
  bit sets are encoded trusting the IR, in the `BEGIN_SET` token's byte order, so big-endian schemas
  with multi-byte sets print wrongly (sbe/2; the codec round trips encode per schema, since a
  token-order message is invalid input for them).
- A group drawn as `type` is named after the first set or composite type among its fields (`type0` for
  `Type0`; sbe/6).
- In the evolution property the acting version keeps only the composite *members* present (composite
  fields added later are drawn; sbe/3, sbe/4), the message buffer is exactly the message (sbe/10, also
  for the printer properties), the transformer is compared on every message with offsets unmasked
  (sbe/7), and the DTO route expects nulls for not-present optional arrays (sbe/8) and no choices for a
  not-present set on the printer route (sbe/9).
- `HEGEL_NO_KNOWN=1` (read once into `Zoo.NO_KNOWN`) switches the shapes off for a run past the known
  bugs: uint64 values stay within `long`, sets are written in the schema's order, every composite field
  is present at the acting version, buffers get eight bytes of slack, the transformer is compared on
  group-free messages with offsets masked, zeros and all-true are expected, `type` groups are renamed
  `member<id>`, the Go check judges 8-bit sets and the sbe/3-4 region takes a version-0 composite; every
  property then passes.
- Parser rules found by running are kept: `nullValue` only with `presence="optional"`; enum `encodingType`
  in {char, uint8, int8, int16, uint16, int32}; `numInGroup` uint8/uint16; `semanticType` not differing
  between a type and its field; fields with `sinceVersion` are optional and sorted after earlier ones;
  var data with `sinceVersion` only at message level (the C# generator refuses "Cannot extend var data
  inside a group"); constant chars from a safe alphabet, no `"` or control characters in attributes.
- Float constants and null values are expected as the printer shows them, widened to double (1.0E-10
  prints as 1.000000013351432E-10). Only valid values and choices with `sinceVersion <= actingVersion`
  are written; UTF-8 var data is valid UTF-8 within the type's `maxValue`.

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
- 2026-09-17: base bumped 89bb53644fad → 1c38f620763e (2026-09-17, "post release bump"; 1.41.0-SNAPSHOT); 10 bug(s) still reproduce. 6 tests pass.
- 2026-09-25: unsteered under rule 11: the known-bug gates run only under `HEGEL_NO_KNOWN=1`, ten narrow
  properties added; two latent test bugs fixed (`minimumActingVersion` read composite members' versions
  from the IR tokens, where the IR raises them to the field's, so the sbe/3-4 region had rejected every
  case; a compile error of the generated Java NPE'd instead of being reported). 3 tests pass, 22-23
  expected failures.
