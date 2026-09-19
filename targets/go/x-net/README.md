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
the duplicate check, leaving two attributes of one name (12). Thirteen pins.

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
of the CONTEXTO rules, so a lone katakana middle dot or `a·b` passes (15).

Not judged: names node's URL parser acts on before the host (ASCII specials, controls, `%`,
IPv4 shapes, an empty host, a forbidden host code point after mapping), Bidi domain names
x/net/idna rejects (ada does not apply the Bidi rule; python idna applies it label by label),
ACE labels decoding to ASCII only or starting with a delimiter (x/net/idna rejects both on
purpose; the oracles are lenient), U+1E9E (ada maps it to `ss` as tables before 15.1 did),
U+FFFD in a Punycode encoding (refused since Unicode 16), the registration profile's rejection of
upper-case ASCII (it maps nothing) and of a trailing dot (a VerifyDnsLength error since Unicode
16, not an RFC 5891 one), and runes python's `unicodedata` does not know.
