# markdown-it

[markdown-it](https://github.com/markdown-it/markdown-it) is the CommonMark parser behind a large
part of the JavaScript ecosystem (VS Code's Markdown preview, Docusaurus, VitePress, many static
site generators; ~21M weekly downloads). Version 15 (July 2026) is a rewrite in TypeScript with
bundled declarations; the pin is 15.0.2 at `3c51991`, spec 0.31.2.

CONTRIBUTING.md says "AI tools may assist, but the submitter must remain the author of the change".
The zoo keeps its tests in its own patch and files nothing upstream, so the clause is not engaged.

## Build

`src/` is TypeScript with `.ts` import specifiers; node 22 runs it with `--experimental-strip-types`
(the upstream tests import `../../src/index.ts` the same way), so there is no build step. The
runtime dependencies (entities, linkify-it, mdurl, punycode.js, uc.micro, argparse) come from a
root `npm install --omit=dev`; Hegel and the oracles go under `.hegel/`. Everything runs with
`node --experimental-strip-types --test --test-reporter=tap hegel/hegel.test.mjs`.

## Oracles

- **commonmark.js 0.31.2** — the reference implementation, same spec version as the pinned
  `test/fixtures/commonmark/spec.txt`. With the `commonmark` preset (xhtml output, HTML on) the two
  agree byte for byte on 399 of 400 random documents before any normalisation; the one difference
  is `<blockquote>\n</blockquote>` versus `<blockquote></blockquote>`, which upstream's own spec
  test normalises too.
- **micromark 4.0.2** — tiebreaker on the CommonMark side, and with `micromark-extension-gfm`
  (single tildes off) the oracle for the default preset's tables and strikethrough.
- **markdown-it 14.3.0** — the last release before the TypeScript rewrite; the 15.0 CHANGELOG
  lists the intentional differences (IPv6 brackets kept, image alt text from the whole inline
  content, lowercase `<!doctype`, space-only code spans, code spans after unclosed link labels,
  backslash before a terminating space in destinations) and the property skips those shapes.

## Method

The generator builds structured Markdown: paragraphs, ATX and setext headings, thematic breaks,
fenced and indented code, blockquotes, bullet and ordered lists with varied marker gaps and
tightness, HTML blocks, reference definitions, GFM tables; inline emphasis of every delimiter
shape, code spans, inline and reference links and images, autolinks, entities (valid and not),
backslash escapes, hard and soft breaks, raw HTML, typographer triggers and punctuation soup —
with random indentation, tabs, CRLF/CR line endings, a BOM or NUL bytes now and then. The
properties:

| Property | Checks |
|---|---|
| CommonMarkPresetAgreesWithCommonmarkJs | exact HTML agreement with commonmark.js on documents without unsafe URL schemes (markdown-it drops those links on purpose); micromark's verdict is added to every mismatch |
| DefaultPresetAgreesWithMicromarkGfm | the default preset (tables, strikethrough, HTML off) against micromark + GFM, on documents whose CommonMark core the two reference implementations agree on |
| RewriteAgreesWithVersion14 | 15.0.2 against 14.3.0 for both presets, minus the CHANGELOG's intentional changes |
| OutputIsWellFormedHtml | with HTML off: balanced known tags, quoted attributes, every `&` an escape, no `javascript:`/`vbscript:`/`file:` href or src |
| TokenStreamIsWellFormed | `md.parse`: nesting/level bookkeeping, `map` ranges inside the parent's and the document, `block`/`children` flags, `renderer.render(parse(src)) === render(src)` |
| RenderInlineMatchesTheParagraphBody | `renderInline` equals the body of the single paragraph `render` gives |
| ReferencesInEnvMatchTheLinks | `env.references` keys are normalised, entries well-typed |
| UtilsMatchTheirModels | `escapeHtml`, `unescapeAll` (backslash escapes, entities with the `;` requirement, invalid code points), `normalizeReference`, `isPunctChar`, `isMdAsciiPunct`, `isWhiteSpace` (Zs + ASCII whitespace controls), `isSpace` |
| LinkNormalisationIsIdempotentAndSafe | `normalizeLink` idempotent and ASCII-clean; `validateLink` against the documented blacklist (javascript:, vbscript:, file:, data: except the four image types) |
| ReplacementsMatchTheDocumentedTable | typographer replacements `(c) (r) (tm) +- ... ?.... !.... ,, -- ---` on plain text against a regex model |
| RenderingTimeIsNotSuperLinear | random repeated units (openers, closers, markers, entities, links) at 1500 and 6000 repetitions with random option sets; a 25× ratio or 3 s flags a blow-up (nothing found — the pathological suite upstream has done its work) |
| Pin UpstreamFixturesStillPass | the 652 spec examples and the ten fixture files, rendered exactly as upstream's tests do (passes) |

Mismatches are classified before they count: a `Known` switch per recorded bug either gates the
input shape (regexes and two small scanners for list-item offsets) or compares the two outputs
after a shape-specific normalisation, applied to both sides. Accepted differences are normalised
the same way: non-ASCII hosts are punycoded by markdown-it (documented) and percent-encoded by the
oracles; IPv6 brackets kept versus encoded; commonmark.js copies raw HTML into `alt` unescaped
(which is its problem); an HTML block ending the document without a final newline gets none
(micromark agrees); micromark's own readings (trailing whitespace-only lines kept in indented code
at EOF, trailing tabs before a soft break stripped, `*_*a` as emphasis, `src`/`href` sanitising,
GFM autolink literals, single-tilde strikethrough, a pipeless header row, `~~` touching `*`).

Each shape was shrunk by hand (line-drop, character-drop, character-replace) with the gates of the
test file applied, so the pins are minimal.

## Bugs (16)

All wrong-result, all still open at the pin. The parser is spec-exact on the ordinary paths — the
spec fixtures pass and random documents agree with commonmark.js — and the bugs sit where two
mechanisms meet: containers and tabs (4, 11, 12), containers and lazy lines (10, 12), the
reference rule taking definitions out of the paragraph flow (10, 13), the table rule running
before the container rules (9), unclosed fences at boundaries (3, 8), the URL normaliser (6, 14),
renderer rules that bypass `renderToken` (7), inline parsing on stripped-but-not-quite content
(5, 15), the two decoding paths for entities (2), and the GFM strikethrough rule cutting a run of
three or more tildes into `~~` pairs where GFM has text (16, found by the micromark differential
on CI). Medium: 4, 8, 9, 10, 12, 15.

## Not tested

Plugins and the `Ruler` API beyond `parse`/`render`, `linkify: true` output (linkify-it has its
own rules; only well-formedness and speed are checked), smartquotes (the pairing model would be as
long as the rule), the CLI, source maps, the browser bundles.

## History

- 2026-09-17: created at 15.0.2 (`3c51991`); 15 bugs.
- 2026-09-18: markdown-it/16 (tilde runs of three or more), found by the CI run of the micromark
  differential; gate `known-long-tilde-run`.
