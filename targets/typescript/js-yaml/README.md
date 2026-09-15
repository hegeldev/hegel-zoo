# js-yaml

[nodeca/js-yaml](https://github.com/nodeca/js-yaml) (npm `js-yaml`, the YAML parser and
writer most of the JavaScript ecosystem uses; 5.x is the TypeScript rewrite): `load`/`loadAll`
with the FAILSAFE, JSON, CORE (default), YAML11 and DUMP schemas, `dump` with its presenter
options, and the `realMapTag` variant that keeps mapping keys as they are. Pinned at 5.4.2
(494400bd, 2026-09-13). The tests are `test/hegel.test.mjs` with the zoo's harness
`test/hegel-zoo.mjs`, the generators and oracle bridge `test/hegel-yaml.mjs` and the oracle
itself `test/hegel-yaml-oracle.py`; they import `../src/index.ts` directly, as upstream's own
tests do (Node 22 strips the types), so there is no build step.

## What is tested

Values are generated from strings that look like something else (booleans of both YAML
versions, ints in every base, floats with `_`, `.inf`, timestamps valid and not, `---`, `...`,
`- `, `? `, `#`, `&`, `*`, `!`, `<<`, `=`, flow indicators, quotes, leading/trailing spaces,
tabs, every line break YAML ever had, BOM, NUL, ESC, DEL, a lone surrogate, emoji, keys and
lines past 1024 characters), numbers around 2^53 and the float edges, Dates from year 0 to the
largest Date, byte arrays, Sets, Maps with non-string keys, shared substructure and cycles.

- **TestHegelDumpLoadsBackTheSameValue** — `dump` with random presenter options (indent,
  `seqNoIndent`, `seqInlineFirst`, `lineWidth`, `flowLevel`, the flow padding/comma/colon
  switches, `quoteFlowKeys`, `quoteStyle`, `forceQuotes`, `sortKeys`, `noRefs`,
  `tagBeforeAnchor`) under the default schema, DUMP_SCHEMA or DUMP_SCHEMA + `realMapTag`, then
  `load` with the same schema: the value must come back equal (Map/Set/Date/bytes/NaN/-0/cycle
  aware), the text must end in one line break and `loadAll` must see exactly one document.
- **TestHegelPyYamlReadsWhatJsYamlWrites** — the same texts read by PyYAML's `CSafeLoader`
  (libyaml, YAML 1.1) must give the same value in a canonical form both sides compute (ints
  below 2^53 as such, other numbers by their IEEE bits, timestamps in UTC to the millisecond,
  Maps and Sets sorted by code point). DUMP_SCHEMA is documented to quote anything a 1.1 or
  1.2 resolver would take for a non-string; this is that promise, tested.
- **TestHegelJsYamlReadsWhatPyYamlWrites** — the other direction: PyYAML's `CSafeDumper` with
  random `default_flow_style`, `width`, `indent`, `default_style` (`"`, `'`, `|`, `>`) and
  `allow_unicode`, read with js-yaml's YAML11 schema (plus `realMapTag` for Maps): same value.

Each bug has a pin (`TestHegelPin…`, listed in `target.toml`) that fails while the bug is
present; the pins need only js-yaml.

## Oracles

PyYAML 6 with libyaml (`python3-yaml` on Debian/Ubuntu; the tests refuse to start without
`yaml.__with_libyaml__`), held open as a child process with two FIFOs and one JSON line per
request, so the oracle costs microseconds per case. eemeli/yaml 2.9 and js-yaml 4.3 were
consulted by hand where the two disagreed.

## Not tested

- The `Type`/schema extension API beyond `withTags(realMapTag)`, `%TAG` handles, the CLI, the
  browser bundle, `maxAliases`/`maxDepth`/`maxTotalMergeKeys` limits, `json: true`, `onWarning`,
  `filename`/error positions, the FAILSAFE and JSON schemas on their own.
- Arbitrary YAML *text*: there is no grammar generator yet, so the parser is exercised only on
  what js-yaml and PyYAML write.

Differences between js-yaml and PyYAML that are not counted (each skipped with a `limit/…`):
Python cannot hash a list or dict, so Sets with collection members and Maps with collection
keys are not sent across; Python folds `1`/`True` and `0`/`False` keys, so Map keys avoid 0
and 1; a lone surrogate has no UTF-8; `y`/`Y`/`n`/`N` are booleans in the YAML 1.1 type
definition and in js-yaml's YAML11 schema, PyYAML leaves them out; PyYAML's float regexp wants
a digit before the point (`+.5`, `._5` stay strings there, floats in js-yaml and the spec);
PyYAML writes U+2028/U+2029 (YAML 1.1 line breaks) raw inside quotes and then cannot read
them back itself; a forced style makes PyYAML write typed scalars as `! "1"`, whose `!` tag
means "resolve as plain" in 1.1 and `!!str` in 1.2, which js-yaml follows in every schema;
`noRefs` with a cyclic value recurses until the stack ends (the option asks for exactly that);
an empty `!!binary` as the last entry of a flow collection is written `[!!binary]`, which the
grammar allows (a tag ends at a flow indicator; eemeli/yaml reads it) but libyaml rejects
("while scanning a tag") — PyYAML writes `!!binary ""`, which everyone reads.

One divergence deserves a note: for a **top-level** block scalar with an indentation
indicator, js-yaml counts the indicator from the document's indentation of -1, as the spec's
productions (`l-bare-document ::= s-l+block-node(-1,…)`, content at `n+m`) literally say, so
it writes `|3` for two-space content and reads `|2\n  a\n` as `" a\n"`; libyaml/PyYAML and
eemeli/yaml count from column 0 and read `"a\n"`. A top-level multi-line string that starts
with a space therefore does not survive the trip either way (PyYAML fails on js-yaml's
header outright). The yaml-test-suite has no case that settles it, so it is recorded here and
skipped (`limit/top-level-indentation-indicator`), not counted against js-yaml.

## Bugs

Four, js-yaml/1–4 in `bugs.toml`: a flow-mapping key over 1024 characters is written as an
implicit key that libyaml rejects, while the block presenter switches to `? ` (/1); strings
shaped like YAML 1.1 timestamps with impossible fields ("2001-02-30", "23:59:60", "+25") are
written plain and 1.1 readers fail or, worse, read another date (/2); a Date outside years
0000–9999 becomes `!!timestamp '+010000-…'`, which `load` itself rejects (/3); a top-level key
beginning with `--- ` or `... ` is written plain at column 0, where it is a document marker, so
`load` fails on its own output or silently drops the marker (/4 — values get quoted, keys do
not). /1, /2 and /4 came out of the PyYAML direction of the differential, /3 out of the plain
round trip.

## History

- 2026-09-15: created at 494400bd (5.4.2); 3 bugs. Later the same day: js-yaml/4 (document-marker
  keys), found by the second run of the committed suite.
