# typescript/fast-xml-parser — NaturalIntelligence/fast-xml-parser (against expat)

fast-xml-parser validates and parses XML into JavaScript objects (and builds XML back through
the separate `fast-xml-builder`), ~60M weekly downloads (the AWS SDK, many CLIs). The patch
checks `XMLParser` and `XMLValidator` against Python's `xml.parsers.expat` on generated
well-formed documents and mutations of them, and pins 11 bugs.

## How it is built

No build: `src/fxp.js` is a plain ES module. Its six runtime dependencies are installed at the
versions the lock file resolves to (`--no-save --no-package-lock --omit=dev`), Hegel goes under
`.hegel/`. The oracle needs `python3` on PATH (stdlib only: `xml.parsers.expat`, `json`).

## How it is tested

`hegel/hegel.test.mjs` runs under `node --test`; `hegel/hegel-zoo.mjs` is the zoo's shared
harness. `hegel/oracle.py` is held open for the whole run and answers over two FIFOs (one JSON
line per document, see `hegel/xml.mjs`); it reports expat's view of a document with namespace
processing off, internal entities expanded, character references decoded, attribute values
normalised and CRLF normalised. Both sides are brought to one canonical form: `{decl, prolog,
root, epilog}` with elements `{n, a, c}`, text (adjacent pieces merged, CDATA and text alike,
empty text dropped), comments, and PIs by target only (fast-xml-parser reads a PI's data as
attributes: not compared).

| Property | What it checks |
|---|---|
| `TestHegelParseAgreesWithExpat` | `XMLParser` with `preserveOrder`, attributes, comments, entities and `htmlEntities` on and trimming/value parsing off reads a generated document exactly as expat does |
| `TestHegelPlainShapeMatchesTheModel` | the default (folded) shape — children grouped by name into a value or an array, `#text`, `@_` attributes, `""` for an empty element — matches a fold of expat's tree |
| `TestHegelBuilderRoundTrip` | `XMLBuilder` on the ordered output writes well-formed XML that expat reads as the original document and that parses again to the same ordered object |
| `TestHegelValidatorAgreesWithExpat` | a well-formed document validates (and parses with validation on); after 1–3 random mutations, whatever expat still accepts is not rejected; what the validator accepts and expat rejects is counted by expat's reason (the validator is lenient by design in places) |
| `TestHegelHostileInputNeverCrashes` | junk strings and heavily mutated documents: `parse` (three option sets, with and without validation) returns or throws a plain `Error` within 2 s, `validate` returns `true` or an `{err}` object |

The generator (`hegel/xml.mjs`) writes an optional declaration, an internal subset with 1–3
general entities (values with quotes, `>`, non-ASCII, LF, duplicates), parameter entities,
comments and element declarations, up to two comments/PIs on either side of the root, elements
with prefixed and non-ASCII names, `xmlns`/`xml:lang`/`xml:space` attributes in both quote kinds
with whitespace around `=`, self-closing tags, text with the predefined entities, character
references (including tab, LF, CR and astral characters), DTD entity references, CDATA sections,
comments, PIs, and repeated child names; the generator's own expectation of the document is
compared with expat's reading on every case, so a disagreement between them is a harness error
reported loudly. `ZOO_COLLECT=1` turns mismatches into `# COLLECT` counts; `HEGEL_TEST_CASES`
(default 100) widens the sweep. Known bugs are gated in `hegel/known.mjs` by the shape of the
document (a parameter entity, a quote in PI data, a duplicate declaration) or by the shape of
the disagreement (only attribute whitespace, only whitespace-text outside the root);
`ZOO_NO_KNOWN=1` lifts the gates.

## Bugs

11 open, all pinned (see `bugs.toml`). In 1000-case sweeps the parser and expat agree on every
document not touched by bugs 1–5 (after gating, about 30% of the documents are otherwise
untouched):

- Attribute values are not normalised: a literal tab, LF or CR stays instead of becoming a
  space, including in the replacement text of a referenced entity (1).
- Whitespace before a comment or PI outside the root becomes a `#text` node of the document (2).
- A parameter-entity declaration in the internal subset throws `Invalid entity name %` (3).
- A PI whose data contains a quote throws `Pi Tag is not closed.` or swallows the tags up to
  the next quote (4).
- Of two declarations of one entity the last binds; XML says the first (5).
- The validator rejects an entity reference longer than 20 characters (6), reads a `>` inside
  a quoted entity value as the end of the DOCTYPE (7), accepts a second root or trailing text
  when a top-level tag is self-closing (8), misses an XML declaration inside or after the root
  (9), and accepts `]]>` in text, `<` in attribute values, `&#;` and `--` inside comments (10).
- `captureMetaData` offsets index the CRLF-normalised text, so the documented
  `xml.slice(startIndex, endIndex)` is off after a CRLF (11).

## Accepted differences and notes (not counted as bugs)

- Documented behaviour: numeric character references are decoded only with `htmlEntities: true`
  (the tests set it); an entity whose value contains `&` is not expanded ("parameter entity
  blocking"), so the generator does not write one; entity replacement text is not re-parsed as
  markup and unknown entity references stay literal (the generator references only declared
  entities); PI data is read as attributes and the PI's `#text` is always empty (PI data is not
  compared); comments, PIs and CDATA fold by `node2json.js`'s rules; `maxNestedTags` (100),
  `strictReservedNames`, `unpairedTags`.
- `XMLBuilder` is a re-export of the separate `fast-xml-builder` package, and `@nodable/entities`
  does the entity decoding: their bugs are not this target's. Seen and not judged: the builder
  writes a tab, LF or CR of an attribute value literally (so it reads back as a space; counted in
  the round trip), and entity names of more than 32 characters are not decoded (the generator's
  longest is 21).
- Ill-formed input the parser accepts or reads differently is the validator's business, judged
  only in `TestHegelValidatorAgreesWithExpat` (mutated documents); the validator's laxness beyond
  bug 10 (an unclosed declaration, an undefined entity, `&` in text) is counted by expat's reason
  and not judged — the README recommends the separate `fast-xml-validator` for strictness.
- With namespace processing off in expat, `xmlns` attributes are attributes and names keep their
  prefixes on both sides; `xml`-prefixed and dangerous names (`__proto__`, `constructor`) are not
  generated.
- Text is compared after merging adjacent pieces (text, CDATA, entity expansions), and PI data
  and the DOCTYPE's own content are not compared.

## Not tested

The CJS build (`lib/fxp.cjs`, built with rollup), `XMLBuilder` on hand-made objects (a separate
package), the CLI (`src/cli`), streaming/`Uint8Array` input, the `stopNodes`, `updateTag`,
`tagValueProcessor`/`attributeValueProcessor`, `isArray`, `alwaysCreateTextNode`,
`transformTagName` and `numberParseOptions` options, JS-path options
(`path-expression-matcher`), and the `strnum` value parsing (`parseTagValue`/`parseAttributeValue`
are off).

## History

- 2026-09-20: created at bb2ec6c (v5.11.1), 5 properties, 11 bugs.
