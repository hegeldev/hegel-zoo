# snakeyaml

[snakeyaml/snakeyaml](https://github.com/snakeyaml/snakeyaml) (the GitHub mirror of
codeberg.org/snakeyaml/snakeyaml): the YAML 1.1 processor for Java — `Yaml.load`/`loadAll`,
`dump`/`dumpAll`, the event (`parse`/`Emitter`) and node (`compose`/`serialize`) layers,
`SafeConstructor` with the 1.1 tag repository (int with `0x`/`0b`/`0o`/sexagesimal forms, float,
bool, null, timestamp, binary, set, omap, pairs, merge), `SafeRepresenter`, and `DumperOptions`
(flow and scalar styles, indent, indicator indent, width, line breaks, canonical, explicit
markers, non-printable handling, version directive). Pinned at the 2.8-SNAPSHOT commit 7b8b171c
(2026-08-30); Apache-2.0. The README's "Contribute" section asks for bug reports and mailing-list
discussion, there is no CONTRIBUTING.md and nothing about AI — the zoo only records bugs, it
contributes nothing. The eighth Java target: the patch adds a Maven module `hegel/` depending on
`org.yaml:snakeyaml:2.8-SNAPSHOT`, which `[run] setup` builds and installs from the pinned tree
(tests, Javadoc, sources, enforcer, GPG and the bound formatter plugin skipped). The harness
`Zoo.java`, the judge's `ZooListener`, the oracle bridge `Oracle.java`, the YAML writer/generator
`YamlGen.java` and three test classes live in `hegel/src/test/java/zoo/`; the PyYAML side of the
oracle is `hegel/src/test/resources/hegel-yaml-oracle.py`. See HACKING.md for the Java mechanics.

## The oracle

PyYAML (6.0.3 with libyaml, `python3-yaml` on the CI runners) is the second YAML 1.1
implementation: `Oracle` starts `hegel-yaml-oracle.py` once per JVM and talks JSON lines over
stdin/stdout — `load` with the `CSafeLoader` (libyaml) or `CBaseLoader`, `dump` with the
`CSafeDumper`. Both sides reduce loaded values to one canonical JSON form (`{"$n": "…"}` for
integers of any size, `{"$f": hex bits}` for floats, `{"$t": UTC millis}` for timestamps,
`{"$b": base64}` for binary, `{"$set": […]}`, `{"$m": [[k, v], …]}` for mappings compared as
unordered pairs so that non-string keys work) and the tests compare those. Where libyaml and
pure-Python PyYAML disagree, libyaml is taken as the reference for the scanner and the Python
side for the resolver, as noted per case below.

## What is tested

`YamlGen` writes random trees (null, bool, int, float, string, timestamp-free — strings from a
pool with Unicode, controls, NEL, BOM, emoji, indicator characters and YAML-looking words —
sequences, mappings with scalar and, rarely, collection keys) as YAML in random styles: block and
flow collections, plain/single/double-quoted/literal/folded scalars with indentation indicators,
explicit `---`/`...`, `%YAML 1.1`, comments, CRLF variants. It uses SnakeYAML's own `Resolver`
only to decide when a string must be quoted.

`SnakeYamlTest`:

- **writtenDocumentsLoadAsTheirTrees** — every written stream loads as its trees in SnakeYAML
  and in PyYAML, `new Yaml()` agrees with the `SafeConstructor`, `composeAll` yields one node per
  document, and the CRLF variant loads the same.
- **mutatedDocumentsLoadLikePyYAML** — the written stream with 1–3 random edits (indicator
  characters, tags, anchors, directives, tabs, BOM, CR inserted, characters deleted or replaced,
  lines re-indented or swapped): both accept → same value; one rejects → a finding; and whatever
  happens SnakeYAML throws a `YAMLException`, not a `NumberFormatException`, `ClassCastException`
  or the like. Shapes listed in `knownDifference` (below and bugs /1, /2, /5, /7, /10, /11, /13,
  /15) are compared no further.
- **plainScalarsResolveLikePyYAML** — YAML 1.1 bool/null/float words, ints in every base with
  signs and underscores, sexagesimals, floats, timestamps, and a list of odd spellings, each as a
  document, after `---`, as a mapping value, a sequence item, in a flow sequence and a flow
  mapping: SnakeYAML and PyYAML give the same typed value, and the base loader gives the raw
  string.

`SnakeYamlDumpTest`:

- **dumpedValuesLoadBackAndPyYAMLReadsThem** — random Java values (Integer/Long/BigInteger,
  Double incl. NaN and infinities, Date, byte[], String, List, LinkedHashMap with sometimes
  non-string keys, LinkedHashSet) dumped under random `DumperOptions` (flow and scalar styles,
  indent 1–10, `indentWithIndicator`, `indicatorIndent`, width 1–1000, `splitLines`,
  `allowUnicode`, canonical, `prettyFlow`, explicit start/end, UNIX/WIN/MAC line breaks,
  `maxSimpleKeyLength`, `nonPrintableStyle`, `%YAML 1.1`): the text ends with the line break,
  canonical/explicitStart give `---`, explicitEnd gives `...`; it loads back as the value (strings
  with non-printable characters as their UTF-8 bytes under the BINARY style, by design) in
  SnakeYAML and in PyYAML; `dumpAll` of 1–3 values loads back as the list; `new Yaml().dump` round
  trips. Bugs /6, /12, /14, /16 are skipped by shape; PyYAML is not asked about Java-style float
  exponents (/7) or a plain `=` (its own gap).
- **eventsAndNodesSurviveEmitting** — `parse` of a written stream gives a framed event list;
  emitting it with random options and re-parsing gives the same values and the same events up to
  style; `composeAll` → `serialize(node, writer)` → `compose` keeps the node shape (tags and
  values); `serialize(node)` returns a framed event list.

`SnakeYamlPinsTest` — one pin per bug in bugs.toml, asserting the documented (or YAML 1.1)
behaviour; each fails while its bug exists and is listed in `target.toml` `[expected_failures]`.

## Not tested

Anchors and aliases (the generator writes none; mutations only insert `&a`/`*a`), merge keys
(`<<`), custom tags and the `Constructor`/`Representer` for arbitrary JavaBeans, `TypeDescription`,
`LoaderOptions` limits (`codePointLimit`, `maxAliasesForCollections`, `allowRecursiveKeys`,
`processComments`) beyond the nesting-depth pin, the comment-preserving `Composer`, `Yaml.parse`
of multi-megabyte input, `%TAG` directives, `!!omap`/`!!pairs`/`!!set` on the dump side, the
`java.util.Date` representation of times before 1583 (the generator stays after the cutover; /4
covers the load side), and YAML 1.2 semantics (SnakeYAML is a 1.1 processor; 1.2-isms are noted
below, not counted).

## Bugs

See bugs.toml. Sixteen so far: a plain scalar continuation line starting `---x` ends the
document (/1); the non-specific tag `!` is ignored so `! 123` is an int and `! ` is null (/2);
timestamps with out-of-range fields roll over instead of failing (/3); dates before 1582-10-15 are
Julian (/4); sexagesimal ints overflow `int` (/5); indent 1 and 10 silently become 2, and with an
indicator indent of 2 or more the dump does not parse (/6); doubles dump as `1.0E10`, not a YAML
1.1 float (/7); `dumpAs` leaks its flow style after an exception (/8); `nestingDepthLimit` counts
scalars (/9); `!!bool maybe` is null (/10); `!!int abc` and `!!binary '***'` throw
`NumberFormatException`/`IllegalArgumentException` (/11); U+0085 in a block scalar loads as `\n`
(/12); a tag on the wrong node kind throws `ClassCastException` (/13); block scalars needing an
indentation indicator under an indicator indent do not parse back (/14); `?` inside a plain
scalar in flow context ends the scalar (/15); double-quoted scalars indented past the width gain a
backslash when dumped (/16). All still reproduce.

## Observed and not recorded

- The resolver takes `1e3`, `1E3`, `.5e3` and `1.0E10` (no dot, or no exponent sign) as floats;
  YAML 1.1's float regexp requires both, and PyYAML's resolver does — these are YAML 1.2
  spellings, useful in practice, so the differences are only excluded from comparison. On the
  dump side the same spelling is bug /7 because the text is meant for 1.1 readers.
- PyYAML reads `+.5`/`-.5` and `._5` as strings and `0_`/`0x_` as 0; SnakeYAML follows the 1.1
  regexps (`+.5` a float, `0_` a string) — PyYAML's deviations.
- A tab as separation after `-`, `:` or `?` is rejected by SnakeYAML and by pure-Python PyYAML
  and accepted by libyaml; a comment glued to a block scalar header (`|-#x`) likewise.
- `[a:]` is a single-pair flow mapping (the YAML 1.2 reading) where PyYAML reports an error.
- The `\/` escape is rejected — correct for YAML 1.1 (it arrived in 1.2); PyYAML accepts it.
- A plain `=` is `!!value` in YAML 1.1: SnakeYAML gives the string "=", PyYAML has no
  constructor for the tag and fails — neither implements it; the dump tests do not ask PyYAML
  about texts holding one.
- A lone surrogate in the input is a `ReaderException` here and passed through by PyYAML.
- Timestamp fractions are rounded to milliseconds by SnakeYAML and truncated to microseconds by
  PyYAML; `%YAML 1.2` is accepted silently; `!!binary` accepts unpadded Base64.
- Javadoc says `LoaderOptions.warnOnDuplicateKeys` defaults to true and `enumCaseSensitive` to
  false; both are the other way round.
- PyYAML cannot load a mapping with a sequence or mapping key (`unhashable`), so those documents
  are compared only within SnakeYAML.

## History

- 2026-09-16: created at 7b8b171c (2.8-SNAPSHOT); bugs /1–/16.
