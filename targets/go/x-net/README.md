# go/x-net: golang.org/x/net/html against parse5 and html5lib, x/net/idna against ada and python idna

[golang/net](https://github.com/golang/net) is Go's supplementary networking library; its `html`
package is the HTML5 parser most of the Go ecosystem uses (goquery, cascadia, bluemonday, Hugo's
pipelines and thousands more). It pins the html5lib-tests tree-construction suite (1789 cases)
and passes it save six known exclusions, so the bugs are around the suite: in the tokenizer's
handling of comments and CDATA, in fragment parsing, in the renderer, and in the insertion modes
the suite touches lightly. Its `idna` package (UTS #46 and IDNA2008, the `Lookup`, `Display`,
`Registration` and `Punycode` profiles) is tested in `idna/hegel/`, see below.

## html

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

The generators are records rendered by pure functions: a document is a soup of token records
(start tags with attribute records, end tags, text, comments, doctypes, and by default the
recorded shapes as a modest alternative of their own - a comment or CDATA section holding a
character reference, a NUL in a doctype, `</>`, a raw text tag in a frameset, a foreign element
named like a void one with children, mixed whitespace in `<noscript>`, a raw text element under
`<math>`, a `&#xD;` after `<pre>`; a NUL attribute name beside a U+FFFD one is an alternative of
the attribute list), a structured document of depth-indexed element records, or either under a
list of edit records applied modulo the live length; a fragment context is a record (the raw
text and column-group contexts drawn as alternatives, a raw text context's own end tag inserted
at a drawn position, and text after `</html>` in a foreign context drawn in a fifth of the
chunked cases: text alone reaches the nil current node, a tag or comment after the ignored end
tag parses), the chunking a list of cut lengths, a reference text a list of reference pieces.
By default a mismatch the classifier in `known.go` names fails the property naming the bug, and
x-net/4's crash is recovered and named; under `HEGEL_NO_KNOWN=1` the shape alternatives have
weight zero, the classifier's answer is counted as a known bug, and the crash is assumed away
(under half a percent of the fragment and chunked cases).

Twelve bugs in `html`, all found 2026-09-19 at commit 520c891 (v0.59.0+): character references decoded
inside comments (1, medium: the tree is lossy and Render escapes every `&` of a comment to
compensate) and inside CDATA sections (7); a NUL kept in a doctype (2); `</>` becoming an empty
comment (3); `ParseFragment` in an SVG or MathML context returning a nil pointer dereference for
anything after `</html>` (4, medium); a raw text start tag ignored in frameset mode still
switching the tokenizer (5); `Render` failing with an error on a parsed tree holding an SVG
`<input>` or `<wbr>` with children (6, medium) and escaping the text of a `<style>` inside
`<mtext>` (9); whitespace misplaced when a text token mixes it with other characters in the
head-noscript and column-group modes (8); a raw text fragment context ending its text at an end
tag of its own name (10); a `&#xD;` after `<pre>` dropped like a newline (11); and an attribute name holding a NUL escaping
the duplicate check, leaving two attributes of one name (12). Thirteen pins, and one narrow
property per bug in `hegel_shapes_test.go`, each drawing the bug's shape region with random
contents and judged by the same vote: `CommentsKeepTheirCharacterReferences` (1),
`DoctypeNulBecomesReplacementCharacter` (2), `EmptyEndTagsAreIgnored` (3),
`ForeignFragmentsSurviveTheHtmlEndTag` (4), `IgnoredRawTextTagsLeaveTheTokenizer` (5),
`RenderAcceptsForeignElementsNamedLikeVoids` (6), `CDATAKeepsCharacterReferences` (7),
`MixedWhitespaceTextIsSplit` (8), `RawTextUnderMathRendersUnescaped` (9),
`RawTextContextsKeepTheirOwnEndTag` (10), `CarriageReturnReferencesSurviveAfterPre` (11) and
`NulAttributeNamesAreDeduplicated` (12); under `HEGEL_NO_KNOWN=1` each draws the neighbouring
region and passes.

Not judged (the oracles lag or the specification is silent): anything holding `<select` and the
select-related fragment contexts (the 2025 change), the head fragment context (the specification
pops the root element and the implementations part ways), four or more start tags of one
formatting element (Noah's Ark plus the adoption agency's step 2, which x/net/html follows and the
oracles lack). The fragment property counts cases where html5lib has no opinion (foreign
contexts) rather than judging them on parse5 alone.

## idna

`idna/hegel/` (added by the patch) runs generated domain names - labels of pieces from pools
covering every part of UTS #46 and IDNA2008 (mapped, ignored, deviation and disallowed runes,
joiners and viramas, the contextual-rule runes, right-to-left scripts and both Arabic digit
sets, combining marks, the dot variants, ACE labels raw and made by encoding, hyphen positions,
label and name lengths, runes assigned in Unicode 16-18 and random runes) - through x/net/idna
and two other implementations, again child processes speaking JSON lines:

- node's `url.domainToASCII` / `url.domainToUnicode` (ada), the URL standard's "domain to
  ASCII": UTS #46 with CheckHyphens, UseSTD3ASCIIRules and VerifyDnsLength off, against an
  x/net/idna profile built from the same flags (`TestHegelLookupAgreesWithWHATWG`: the same
  verdict and ASCII form, the ASCII form back to node's Unicode form, and that to the same ASCII
  form again);
- python's `idna` package (RFC 5891 registration rules, no mapping) against `idna.Registration`
  (`TestHegelRegistrationAgreesWithIDNA2008`, both directions), and python's punycode codec
  against `idna.Punycode` (`TestHegelPunycodeAgreesWithTheCodec`, with the exact round trip);
- `TestHegelLookupIsAFixedPoint`: for `Lookup` and `Display`, an accepted name's ASCII form is a
  fixed point, its Unicode form is accepted and maps back, and ToUnicode of the name and of its
  ASCII form agree.

The three sides are at three Unicode versions (ada 15.1, x/net/idna 17.0 under Go 1.27, python
idna 18.0 over a 15.0 `unicodedata`), and UTS #46's Unicode 16 revision changed the status of
23,000 code points, so `known.go` carries tables generated from the Unicode data files: the code
points whose status differs between the 15.1 and 18.0 mapping tables (a disagreement with node
on one is skew), the NV8/XV8 code points, and the ages of the code points assigned since 16.0.
A gauge (`HEGEL_IDNA_TESTS=IdnaTestV2.txt`) runs the comparisons over the conformance suite's
inputs: with the gates, x/net/idna and node agree on 5890 of 6389 cases and differ on none, and
x/net/idna and python idna on 6275 with none unexplained (56 are x-net/14).

Three bugs (13-15), all in the profiles' validation: a label that is the bare ACE prefix `xn--`
decodes to the empty string and is accepted by the lookup profiles as an empty label (13; UTS #46
records P4, the conformance suite has the case); `Registration` accepts the NV8/XV8 code points
IDNA2008 disallows, such as `¡` and `☕` (14; a TODO in the code); and `Registration` applies none
of the CONTEXTO rules, so a lone katakana middle dot or `a·b` passes (15). Three pins, and the
narrow properties `BareACEPrefixIsAnError`, `RegistrationRejectsNV8` and
`RegistrationAppliesContextO` in `hegel_shapes_test.go`. A domain name is a record (labels as
records of a kind - pieces from the pools, a raw or encoded ACE label, a word, a long label, an
empty one, an upper-case ACE label, and by default the bare `xn--` prefix in three names of ten
for the lookup properties and a lone NV8 rune or a CONTEXTO-marked label for the registration
property - with the separators, a leading or trailing dot and an over-length tail) rendered by a
pure function; the tame share of names draws one pool per label so that the Bidi rule holds.

Not judged: names node's URL parser acts on before the host (ASCII specials, controls, `%`,
IPv4 shapes, an empty host, a forbidden host code point after mapping), Bidi domain names
x/net/idna rejects (ada does not apply the Bidi rule; python idna applies it label by label),
ACE labels decoding to ASCII only or starting with a delimiter (x/net/idna rejects both on
purpose; the oracles are lenient), U+1E9E (ada maps it to `ss` as tables before 15.1 did),
U+FFFD in a Punycode encoding (refused since Unicode 16), the registration profile's rejection of
upper-case ASCII (it maps nothing) and of a trailing dot (a VerifyDnsLength error since Unicode
16, not an RFC 5891 one), an ACE label decoding to a label that begins with a combining mark
(UTS #46's fifth validity criterion; x/net/idna and python idna reject `xn--wzb`, U+08CA, and
ada accepts it), and runes python's `unicodedata` does not know.

## Known shapes drawn by default

The wide properties draw every recorded shape and fail on it, each mapped in `target.toml` to
the bug its shrunk failure lands on most often (forty rounds at a hundred cases with the shape
token first): `ParseAgreesWithTheOracles` to x-net/2 (forty of forty: the doctype NUL is the
first shape token the shrinker can keep; while the shape token was the last soup alternative the
draw-free `</>` of x-net/3 won the shrink, with /1, /2, /8, /10, /11 and /12 behind it),
`FragmentsAgreeWithTheOracles` to x-net/8 (thirty-four of forty; /3 and /10 the others),
`ChunkedReadsParseAlike` to x-net/4 (the crash, which the wild region reached at a thousand
cases anyway; the first version of the shape drew a tag or comment after `</html>` two times in
three, which parses, and a CI run at a hundred cases passed the property; the shape is now the
first alternative of the chunked choice, since the engine's bounded integer draw favours low
values unevenly from run to run: as the second alternative it was drawn between one and
thirty-four times in a hundred cases, as the first between six and fifty-two),
`RenderedTreesReparseAlike` to x-net/1 (a `&#13;` in a comment, forty of forty; it passed one
round in forty at a hundred cases while the shape token was the last alternative of the soup
token choice and the NUL attribute pair the last of the attribute list choice, so both are now
the first), `LookupAgreesWithWHATWG` to x-net/13 and `RegistrationAgreesWithIDNA2008` to x-net/14
(a lone NV8 rune is the first piece alternative, since the shrinker otherwise ends on a CONTEXTO
rune from the Greek pool, x-net/15). `TokenizerRawCoversTheInput`, `UnescapeAgreesWithEntities`,
`PunycodeAgreesWithTheCodec` and `LookupIsAFixedPoint` reach no recorded shape. Under
`HEGEL_NO_KNOWN=1` every property passes; the classifier still counts the known shapes the wild
region reaches (x-net/1 on about a tenth of the parse and fragment cases, from `&` in
comment bodies, which ends the case as known).

## History

- 2026-09-19: target added at 520c891 (html and idna), fifteen bugs with pins.
- 2026-10-08: generators rewritten in combinator style (batch 66): token, element, edit, context
  and label records rendered by pure functions, the idna generator's package-level pool state
  replaced by a drawn record; the classifiers' answers fail the wide properties by default and
  count under `HEGEL_NO_KNOWN=1`, x-net/4's crash drawn and recovered; fifteen narrow
  properties; `xn--` alone is x-net/13 rather than an empty host; an ACE label decoding to a
  leading combining mark is not judged (ada accepts it against UTS #46).
