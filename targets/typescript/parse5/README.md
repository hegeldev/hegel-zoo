# parse5

[parse5](https://github.com/inikulin/parse5) (MIT), pinned at `7c1e77d` (8.0.1, 2026-09-16): the
WHATWG HTML parsing algorithm in TypeScript, with a serializer, pluggable tree adapters (the default
one and `parse5-htmlparser2-tree-adapter`), a `Writable` parser stream, a SAX-style token stream
(`parse5-sax-parser`, a tokenizer plus a "parser feedback simulator" standing in for the tree builder),
a rewriting stream built on it and a plain-text-to-document stream. The monorepo is compiled with
`tsc` by the setup; the tests import the six packages' `dist/` output.

The patch adds `hegel/`: `hegel-zoo.mjs` (the zoo's harness), `gen.mjs` (random HTML), `dat.mjs`
(the html5lib-tests `.dat` tree format for any tree adapter), `oracles.mjs` and the two oracle
children, `common.mjs` (the vote, source-position arithmetic), `trees.mjs` and `streams.mjs`
(properties), `known.mjs` (one gate per recorded bug) and `pins.mjs` (one plain test per bug).

## Oracles

Two other implementations of the same algorithm answer over FIFOs, one JSON line per request:
**html5ever** (Servo's parser, Rust; `hegel/oracle`, built by the setup with cargo) and **html5lib**
(Python 1.1, in a venv the setup creates). Both print the tree in the `.dat` format of the
html5lib-tests suite that parse5's own tests use, so the three trees compare as strings. Neither is
the spec as parse5 reads it: html5lib 1.1 predates `<template>`, `<search>`, the current ruby and
adoption-agency rules and the 2023 fragment cases (185 of the 1764 pinned tree-construction cases
fail); html5ever 0.39 follows the 2025 `<select>` parser change that parse5 does not have (19 of
1764). So the properties **vote**: parse5 agreeing with html5ever is the norm, parse5 agreeing with
html5lib alone means the oracles read different spec versions (counted), parse5 alone against two
agreeing oracles is a mismatch; three different trees and foreign fragment contexts (html5lib has
none) are counted and, in collect mode, printed. In 4000 documents and 4000 fragments parse5's tree
never lost a vote: the parser is conformant; the bugs are around it.

## What is tested

- `TestHegelParseMatchesTheOracles`, `TestHegelParseFragmentMatchesTheOracles`: random documents
  (token soup, structured documents, mutations; every element class the algorithm has rules for,
  foreign content, raw text, comments, doctypes, character references, NULs, CR/LF) and fragments in
  random HTML and foreign contexts, with and without scripting, against the vote; when the trees
  agree, `serialize()` against html5ever's serialization of the same tree (templates excepted:
  html5ever's serializer skips their contents).
- `TestHegelSerializeRoundTrips`: `parse(serialize(parse(html)))` equals `parse(html)` for trees the
  spec says round-trip (the document mode is restored with a doctype that forces it, since the
  serializer keeps only the doctype name); the hazards skipped are odd element or attribute names,
  `<` in raw text, comment data the syntax cannot hold, `plaintext`, CR from character references,
  adjacent text nodes, an element nested in one of its own name (foster parenting builds those) and
  raw text fragment contexts.
- `TestHegelTreeAdaptersAgree`: the htmlparser2 adapter builds the same tree and `serialize` /
  `serializeOuter` through it give the same markup.
- `TestHegelLocationsPointIntoTheSource`: with `sourceCodeLocationInfo`, every location is inside
  the input, its line and column match its offset (LF, CR and CR LF ending lines; columns in code
  units), start tags, end tags and attributes hold what their names say, text without references
  or tags is its own slice, comments and doctypes start with their syntax.
- `TestHegelParseErrorsAreReported`: error codes are known, their locations consistent, and the
  tree is the same with or without the error handler and location info.
- `TestHegelStreamedParseMatchesTheOneShot`: `ParserStream` and `getFragmentStream` fed random
  chunks (boundaries anywhere, empty chunks) build the same tree with the same locations and the
  same parse errors as the one-shot parse.
- `TestHegelSaxTokensMatchTheParser`: the SAX parser emits the same tokens one-shot and in chunks;
  their raw locations tile the input (gaps only where the tokenizer drops input: the newline after
  `<pre>`, an empty end tag `</>`, an unfinished tag at the end); and the token stream equals the one the real parser's
  tree builder receives from its tokenizer (hooked on a `Parser`), modulo the simulator's deliberate
  adjustments (`image` to `img`, SVG name case, NUL replacement).
- `TestHegelRewritingStreamPassesTheSourceThrough`: a `RewritingStream` without handlers writes
  the input through unchanged, in chunks; `TestHegelReemittedTokensParseAlike`: handlers that
  re-emit every token with `emitStartTag`/`emitEndTag`/`emitText`/`emitComment`/`emitDoctype`
  produce a document that parses to the same tree.
- `TestHegelPlainTextBecomesAPreElement`: `PlainTextConversionStream` builds
  `html/head/body/pre` with the text as the spec's "load a text document" describes.

## Known bugs (13, see bugs.toml)

The serializer leaves `<` and `>` unescaped in attribute values (the 2025 spec change, 1). Source
locations: a newline right after `&` is counted twice (2), an unterminated comment ends one past the
input (3), an error at an astral character has the offset of its low surrogate (4), text from a
character reference after an ignored NUL is located at its last character (5).
`PlainTextConversionStream` puts a newline before the text (6). `RewritingStream` drops `</>`
between tokens (7) and an unfinished tag at the end of the input (8); `emitStartTag` drops the
prefixes of foreign attributes, `xlink:href` becoming `href` (9); `emitDoctype` writes
`<!DOCTYPE null>` for a nameless doctype (10). The SAX parser's feedback simulator stays in foreign
content after a self-closing `<svg/>` or `<math/>` (11) and switches to raw text for a `<style>` or
`<title>` the tree builder ignores inside `<select>` or `<frameset>` (12). The htmlparser2 adapter
serializes integer-named attributes first (13).

## Conventions followed, not recorded

The `.dat` format names an attribute's namespace (`xmlns xmlns=""`) where parse5's own test
serializer prints the token prefix; `dat.mjs` prints the namespace. `&#13;` yields a CR that the
serializer writes as is and a parser reads as LF: not round-trippable, by the spec. A fragment's text
is escaped whatever the context element. The SAX parser reports adjusted SVG tag and attribute names
and `image` as `img`, and hands out foreign attributes as `{ prefix, name }`. The `select` and
`frameset` divergences of the feedback simulator (12) are recorded once, not per element.
