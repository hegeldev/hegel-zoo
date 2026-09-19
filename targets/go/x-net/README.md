# go/x-net: golang.org/x/net/html against parse5 and html5lib

[golang/net](https://github.com/golang/net) is Go's supplementary networking library; its `html`
package is the HTML5 parser most of the Go ecosystem uses (goquery, cascadia, bluemonday, Hugo's
pipelines and thousands more). It pins the html5lib-tests tree-construction suite (1789 cases)
and passes it save six known exclusions, so the bugs are around the suite: in the tokenizer's
handling of comments and CDATA, in fragment parsing, in the renderer, and in the insertion modes
the suite touches lightly.

The tests live in `html/hegel/`, a package added by the patch. Two oracles are other
implementations of the HTML parsing algorithm, run as child processes speaking JSON lines:
parse5 8.0.1 (node; installed under `html/hegel` by the target's setup) and html5lib 1.1 (python).
Every tree is printed in the .dat format of html5lib-tests, the format x/net/html's own test dump
prints, and compared as a string. Neither oracle is the specification: parse5 and html5lib lack
the 2025 `<select>` parser change (x/net/html has it) and the adoption agency's step 2, and
html5lib predates template, search and the current ruby rules. So the parse properties take a
vote: x/net/html agreeing with either oracle passes, x/net/html alone against two agreeing oracles
fails, three different trees are counted. A gauge test (`HEGEL_GAUGE=1`) scores both oracles on
the pinned suite first: parse5 1759/1789, html5lib 1529/1789 (64 no opinion), x/net/html
1784/1789 - and the 30 cases where the vote would go against x/net/html are all the select change.

Properties (`HEGEL_COLLECT=1` counts mismatches instead of failing, `HEGEL_TEST_CASES=n` sets the
case count):

- `TestHegelParseAgreesWithTheOracles`: a generated document (a token soup of the shapes the
  algorithm has rules for, a structured document, or a mutation of either) parses without error
  to a consistent tree, and to the oracles' tree by vote.
- `TestHegelFragmentsAgreeWithTheOracles`: the same through `ParseFragment` in a generated context
  (any HTML element, sometimes an SVG or MathML one).
- `TestHegelChunkedReadsParseAlike`: reading the input in random byte-sized pieces gives the tree
  a single read gives.
- `TestHegelTokenizerRawCoversTheInput`: the `Raw` texts of the tokens partition the input (an
  unfinished tag at the end excepted, which the specification drops), and the token stream does
  not depend on how the input is chunked.
- `TestHegelUnescapeAgreesWithEntities`: `UnescapeString` decodes character references like the
  `entities` package (python's `html.unescape` deciding when they differ), and
  `UnescapeString(EscapeString(s)) == s`.
- `TestHegelRenderedTreesReparseAlike`: `Render` of a parsed document, parsed again, gives the same
  tree - for trees that are well formed in the sense of Render's documentation (no element inside
  one of its own name where the content model forbids it, no plaintext, no raw text holding its
  own end tag, no text where a table or select structure cannot hold it).

Twelve bugs, all found 2026-09-19 at commit 520c891 (v0.59.0+): character references decoded
inside comments (1, medium: the tree is lossy and Render escapes every `&` of a comment to
compensate) and inside CDATA sections (7); a NUL kept in a doctype (2); `</>` becoming an empty
comment (3); `ParseFragment` in an SVG or MathML context returning a nil pointer dereference for
anything after `</html>` (4, medium); a raw text start tag ignored in frameset mode still
switching the tokenizer (5); `Render` failing with an error on a parsed tree holding an SVG
`<input>` or `<wbr>` with children (6, medium) and escaping the text of a `<style>` inside
`<mtext>` (9); whitespace misplaced when a text token mixes it with other characters in the
head-noscript and column-group modes (8); a raw text fragment context ending its text at an end
tag of its own name (10); a `&#xD;` after `<pre>` dropped like a newline (11); and an attribute name holding a NUL escaping
the duplicate check, leaving two attributes of one name (12). Thirteen pins.

Not judged (the oracles lag or the specification is silent): anything holding `<select` and the
select-related fragment contexts (the 2025 change), the head fragment context (the specification
pops the root element and the implementations part ways), four or more start tags of one
formatting element (Noah's Ark plus the adoption agency's step 2, which x/net/html follows and the
oracles lack). The fragment property counts cases where html5lib has no opinion (foreign
contexts) rather than judging them on parse5 alone.
