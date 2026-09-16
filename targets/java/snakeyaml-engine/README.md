# snakeyaml-engine

[snakeyaml-engine](https://github.com/snakeyaml/snakeyaml-engine) (`org.snakeyaml:snakeyaml-engine`,
mirror of the Codeberg home; 3.2-SNAPSHOT at the pinned commit, 2026-08-10) is the YAML 1.2 processor
of the SnakeYAML family — the parser and emitter under Jackson's YAML module, Quarkus, Micronaut and
others. It has a high-level API (`Load`/`Dump` with the JSON, core or failsafe schema chosen through
`LoadSettings`/`DumpSettings`) and a low-level one (`Parse` → events → `Present`, `Compose` → nodes
→ `Serialize`). The zoo's `java/snakeyaml` target covers SnakeYAML 2.x (YAML 1.1); this one covers the
1.2 engine, whose scanner, parser and emitter are largely the same code.

The tests are a Maven module `hegel/` added by the patch; `[run] setup` builds the engine from the
pinned tree into the local Maven repository (`mvn install` with tests, javadoc, the formatter and the
licence check skipped — the build needs no network beyond the plugins). No child process is used.

## The oracle

There is no other YAML 1.2 processor in the JVM to compare against, so the properties use

- **the generator's own value**: a randomised YAML writer (`YamlGen`, the zoo's SnakeYAML writer
  re-targeted to Gson trees and the engine's `JsonScalarResolver`/`CoreScalarResolver`) produces
  documents whose value is known by construction, in the spellings the chosen schema accepts — block
  and flow collections, every scalar style, comments, anchors and aliases on collections, `---`/`...`
  markers, CRLF, tabs, BOM, unusual keys;
- **the specification's own grammar** for scalar typing: the JSON and core schema regexes of YAML 1.2
  §10.2.1/§10.3.2 written independently of the engine's resolvers, and the values they denote;
- **the engine against itself**: `Dump` → `Load`, `Parse` → `Present` → `Parse`, `Compose` →
  `Serialize` → `Present` → `Compose`, `dumpNode` against `Serialize` + `Present`, and the three
  input paths (`String`, `Reader`, `InputStream`).

Values are compared as a canonical Gson form (`Canon`): integers by their digits, floats by the bits of
the double, binary by base64, mappings as key-sorted pairs, so a `LinkedHashMap` and the generator's
tree compare equal.

## What is tested

`EngineTest`:

- **`writtenDocumentsLoadAsTheirTrees`** — a generated stream of 1–4 documents loads, under the schema
  it was written for, as exactly the generator's values: through `loadAllFromString`, again through a
  `Reader` or an `InputStream`, and (one document) through `loadFromString`; `Compose` gives as many
  nodes as documents; the failsafe schema loads the same stream with every scalar a string.
- **`mutatedDocumentsFailCleanly`** — the stream with 1–3 random edits (indicators, tags, anchors,
  directives, a BOM, escapes, line swaps, deletions) either loads or fails with a `YamlEngineException`
  that does not wrap a `NumberFormatException`, `ClassCastException` or `NullPointerException`; the
  three input paths agree on success and on the documents; composing succeeds exactly when loading does,
  unless the failure is a construction failure (`ConstructorException`, duplicate key).
- **`scalarsTypeLikeTheSpec`** — a plain scalar drawn from a table of edge spellings (`0o17`, `0x_1`,
  `+.inf`, `.NaN`, `1e5`, `5.`, `.5`, `-0`, `08`, `0b1`, `yes`, `~`, `Null`, `1_000`, `1:20`, …) or
  generated from the digit/sign/dot/exponent alphabet is typed by the engine's resolver as the spec's
  regexes say, and constructed to the spec's value (`0o`/`0x` bases, any-case `.inf`/`.nan`, `-0.0`,
  `5.` and `3.e2`), in six positions (root, sequence item, mapping value, mapping key, flow item,
  after `---`), under both schemas.

`EngineDumpTest`:

- **`dumpedValuesLoadBack`** — the generator's Java values dumped with random `DumpSettings` (indent
  1–10, indicator indent, `indentWithIndicator`, width 1–1000, line break, `splitLines`,
  `maxSimpleKeyLength`, canonical, explicit markers, a `%YAML 1.2` directive, flow and scalar styles
  including `JSON_SCALAR_STYLE`, `multiLineFlow`, ASCII-only output, one or several documents) load
  back as the same values under the same schema; the text ends with the line break; no line holds a
  bare backslash; `Compose` gives one node per value.
- **`eventsSurvivePresentAndParse`** — the events of a generated stream (`Parse`), presented with random
  settings and parsed again, are the same events up to style (scalar style, flow/block, explicit
  markers, the `!` tag the emitter adds when it quotes an implicit plain scalar), and the presented
  text loads as the generator's values (in canonical mode: loads, with the same document count — see
  below).
- **`nodesSurviveSerializeAndCompose`** — the nodes of a generated stream (`Compose`), serialised and
  presented with random settings and composed again, have the same tags and values at every position;
  for one node, `Dump.dumpNode` writes the same text as `Serialize` + `Present`.

`EnginePinsTest` holds one pin per bug (below); each asserts the YAML 1.2 behaviour and fails while the
bug exists.

## Not tested

Comments beyond their survival as trivia (`dumpComments` is set at random but comment events are dropped
from the comparison), anchors and aliases on scalars and recursive structures, `LoadSettings` beyond
the schema (code-point/alias limits, `allowDuplicateKeys`, `parseComments`, env-variable substitution,
label/anchor generators), custom constructors and representers, `Representer` for Java beans, tag
directives and custom tags, timestamps and other tags outside the three schemas, the `%YAML 1.1`
directive, marks and error positions, thread-safety.

## Bugs (10)

All at 93ecc0a (3.2-SNAPSHOT, 2026-08-10), all open, none reported upstream (the zoo only records).

- **snakeyaml-engine/1** (crash, medium; `pin1`): `+.inf` under the core schema is resolved as a
  float and then fails with `NumberFormatException` inside a `YamlEngineException`
  (`ConstructYamlJsonFloat` strips the sign and calls `Double.valueOf(".inf")`).
- **snakeyaml-engine/2** (crash, low; `pin2`): the escapes `\L` (U+2028) and `\P` (U+2029) of §5.7
  are rejected by the scanner.
- **snakeyaml-engine/3** (wrong-result, medium; `pin3`): `dumpAll` with a `%YAML` directive writes no
  `...` before the second document's directive unless the first document was a plain scalar, and the
  engine's own parser rejects the stream.
- **snakeyaml-engine/4** (wrong-result, medium; `pin4`): with `indicatorIndent > 0` and no
  `indentWithIndicator`, a block scalar starting with a space or a newline gets an indentation
  indicator that does not match the content's indentation (`[["\n x"]]` loads back as `["\nx"]`,
  `[" a\nb"]` does not parse). Sibling of snakeyaml/14.
- **snakeyaml-engine/5** (contract, low; `pin5`): `DumpSettingsBuilder` accepts
  `indicatorIndent >= indent`; without `indentWithIndicator` a block mapping inside a sequence is then
  written level with the `-` and the dump does not load.
- **snakeyaml-engine/6** (wrong-result, medium; `pin6`): `writeDoubleQuoted` splits a deeply indented
  scalar into a line holding only `\` when the indentation reaches the width, and `"x \n y"` loads back
  as `x \n\  y`. Sibling of snakeyaml/16.
- **snakeyaml-engine/7** (crash, medium; `pin7`): the failsafe schema's resolver tags empty scalars
  `!!null` and the schema has no constructor for it — `a:` fails with `ConstructorException`, the empty
  stream with a raw `NullPointerException`.
- **snakeyaml-engine/8** (crash, low; `pin8`): a standard tag on the wrong node kind (`!!int [1]`,
  `!!map x`, `!!str [1]`, `!!set 1`, …) fails with a wrapped `ClassCastException` instead of a
  constructor error. Sibling of snakeyaml/13.
- **snakeyaml-engine/9** (contract, low; `pin9`): `setIndent(1)` and `setIndent(10)` are accepted
  (the documented range is 1..10) but the emitter's range check is strict at both ends and indents
  by 2 — which also turns a legal `indent 10, indicatorIndent 3` into the unloadable shape of /5.
- **snakeyaml-engine/10** (crash, low; `pin10`): an explicit `!!int`, `!!float` or `!!binary` tag on a
  scalar it does not fit (`!!int abc`, `!!float ''`, `!!binary '***'`) leaks a `NumberFormatException`,
  `StringIndexOutOfBoundsException` or `IllegalArgumentException` inside the `YamlEngineException`,
  and `!!bool maybe` is silently `null`. Siblings of snakeyaml/10 and /11.

## Observed and not recorded

- **Canonical presentation of parsed events makes strings.** Events from `Parse` carry no tag (the
  resolver runs in the composer); `Present` in canonical mode double-quotes every scalar and must then
  write a tag, and `Emitter.processTag` writes the non-specific `!` — so `false`, `null`, `12` come back
  as the strings `"false"`, `"null"`, `"12"`. libyaml and PyYAML's event API do the same; `Dump` and
  `Serialize` (which resolve tags) are unaffected. `eventsSurvivePresentAndParse` only checks that the
  canonical text loads with the right document count.
- **Non-printable strings under `NonPrintableStyle.BINARY`** come back as `byte[]` (by design; the
  property skips them).
- **`!!null [1]`** constructs `null` silently (the null constructor ignores the node kind); the
  mismatched-kind pin does not cover it.
- The sign-stripping in `ConstructYamlJsonFloat` also means `+1.5e3` works only because
  `Double.valueOf` accepts the sign itself; the code path is fragile rather than wrong.

## History

- 2026-09-16: created (turn 173) at 93ecc0a7cf12 (3.2-SNAPSHOT); 10 bugs, 6 of them first seen through
  the zoo's jackson-yaml target the day before and reproduced here with the engine alone, 4 new
  (the failsafe schema's empty scalars, ClassCastException on mismatched tags, the ignored indent 1/10,
  raw exceptions from explicit tags on unfit scalars).
