# json-gold

[piprate/json-gold](https://github.com/piprate/json-gold) (`github.com/piprate/json-gold/ld`),
a JSON-LD 1.1 processor for Go: expansion, compaction, flattening, RDF serialization and
parsing, URDNA2015 normalization, against pyld, Digital Bazaar's Python processor of the same
specification, on the same generated documents.

## What is tested

Documents are generated over a small vocabulary with inline contexts (terms as IRIs, compact
IRIs or expanded definitions with `@type` coercions, `@container` `@list`/`@set`/`@index`/
`@language`, default and per-term languages, `@reverse` terms, `@vocab`, `@base`, aliases of
`@id`/`@type`, `@version`, terms set to null); nodes with absolute, relative and blank node
identifiers, types, nested nodes, value objects, lists, sets, index values, reverse properties
and named graphs; arrays of nodes at the top level. Both processors get the JSON-decoded
document, `processingMode` json-ld-1.1, the same base IRI and no document loader.

**`hegel/hegel_algos_test.go`**
- `TestHegelExpandMatchesPyld`: `Expand` gives pyld's expanded document (or both refuse the
  document).
- `TestHegelCompactMatchesPyld`: `Compact` with the document's context or another generated
  one, `CompactArrays` on or off, gives pyld's compacted document.
- `TestHegelFlattenMatchesPyld`: `Flatten` with no context, the document's or another gives
  pyld's flattened document (blank node labels included: the node map algorithm fixes them).
- `TestHegelCompactExpandRoundTrip`: expanding json-gold's compaction of the expanded document
  gives the expanded document again (values compared as sets outside `@list`); pyld runs the
  same round trip for the vote when it does not close.

**`hegel/hegel_rdf_test.go`**
- `TestHegelToRDFMatchesPyld`: `ToRDF` (N-Quads) gives pyld's dataset, exactly or up to blank
  node relabelling (json-gold canonicalises both when the labels differ).
- `TestHegelNormalizeMatchesPyld`: `Normalize` (URDNA2015) gives pyld's canonical N-Quads.
- `TestHegelFromRDFMatchesPyld`: `FromRDF` of generated N-Quads (IRIs, blank nodes, plain,
  language-tagged and typed literals with valid and invalid lexical forms, named graphs,
  rdf:List structures; `UseNativeTypes` and `UseRdfType` on or off) gives pyld's document.
- `TestHegelNQuadsParseMatchesPyld`: `ParseNQuads` then `NQuadRDFSerializer.Serialize` gives
  what pyld's parser and serializer give.
- `TestHegelRDFRoundTrip`: `Normalize(FromRDF(ToRDF(doc)))` is `Normalize(doc)`; pyld's
  `from_rdf` of json-gold's N-Quads votes when it is not.

**`hegel/hegel_pins_test.go`**: one deterministic reproducer per recorded bug.

## Oracles and normalisations

pyld 3.3.0 in the CI venv (`pip install PyLD==3.3.0`), as one persistent `python3` child
(`hegel/oracle.go`: hex-encoded arguments in, one JSON object out per request) with a document
loader that refuses every URL. JSON is compared after re-encoding with sorted keys through Go's
decoder (numbers as float64; integers stay below 2^53); N-Quads as sorted lines. Both erroring
on a document counts as agreement (error codes are not compared). Not judged: a `@set` object
directly inside a `@list` (the spec's expansion splices its items, which json-gold does; pyld
and jsonld.js nest a list); `xsd:boolean` lexical forms `1` and `0` with native types (pyld
converts them, the spec names only `true`/`false`); an `xsd:integer`/`xsd:double` literal with
an invalid lexical form under `UseNativeTypes` (the spec's literal reading drops the type,
which json-gold and jsonld.js do, pyld and the test suite's fromRdf#t0027 keep it) and an
integral `xsd:double` (a JSON number that is an integer comes back as `xsd:integer`, in pyld
too); a string value under an `xsd:double` coercion in RDF output (the spec's object-to-RDF
conversion keeps a string's lexical form, which json-gold does; pyld and jsonld.js canonicalise
it as a double, `"1"` giving `"1.0E0"`); a top-level node with `@graph` and no `@id` in the compact-expand round trip (its
compaction is the document's `@graph`, lossy by design); an empty `@reverse` (survives
expansion, not compaction, in both); a compaction pyld produces byte for byte too when its
re-expansion does not give the expanded document back (what is lost, the specification loses:
a number under a `@language` container lands under `@none`); repeated values the node map
does not merge (empty lists), which give the same quad twice in all three processors, in the
RDF round trip; a keyword-like key in a language map; the order of
`@type` values in flattened output (a node merged from a `@graph` and a `@reverse` collects
them in traversal order, which differs; compared sorted); a document pyld raises a Python
exception on rather than a JSON-LD error (a `TypeError` on a node under a reverse term with an
`@index` container: no vote from it). Not generated: relative IRIs with
spaces or newlines (both processors' resolution is arbitrary), an empty node under a reverse
property, a reverse term with an `@index` container (both compact it to an index map inside an
array and then expand that differently).

## Known bugs (gated)

Fourteen bugs (`bugs.toml`): relative IRI compaction against a base ending in `/` climbs one
directory too many (the compacted `@id` denotes another resource); IRI resolution
percent-encodes non-ASCII; `Compact` loses `@context` on empty output; `Flatten` returns a
re-serialised context (none on empty output), panics on a null term, and drops a named graph
without properties; `FromRDF` with native types yields `int64` values that `ToRDF` panics on,
and fails on numbers beyond int64/float64; the N-Quads parser mangles a literal starting with
`@` that has a language tag; the serializer writes an empty language tag for rdf:langString
without a language; `ToRDF` writes `<@id>`; errors inside `@set`/`@list` items are swallowed;
an empty `@list` under a typed term is not compacted to the term; a documentation default.
`hegel/known.go` gates them by generated shape or by the shape of the one disagreement;
`HEGEL_NO_KNOWN=1` lifts the gates.

## Not tested

Framing (`Frame`; json-gold's conformance report lists most framing tests as failing), remote
contexts and document loaders, HTML extraction, `@json` literals, `@direction`/`rdfDirection`,
`@nest`, `@propagate`, `@protected`, scoped contexts, `@included`, the Turtle serializer,
`ProduceGeneralizedRdf`, `SafeMode`, processing mode json-ld-1.0.

## History

- 2026-09-20: written against 667ee761535c9c52c0d5c40b7dd863fa56454be9 (2026-09-12, v0.8.0+8)
  with hegel.dev/go/hegel v0.6.33; 14 bugs.
