# goldmark

[goldmark](https://github.com/yuin/goldmark) is the CommonMark parser of the Go world (Hugo,
Gitea/Forgejo, Sourcegraph, many static site generators and documentation tools). Version 2
(`github.com/yuin/goldmark/v2`, go 1.25) is a rewrite of the AST and renderer interfaces with
the v1 extensions folded in; the pin is the default branch at `710cc26` (2026-09-15, just past
v2.1.1), spec 0.31.2.

AGENTS.md (which CLAUDE.md includes) tells agents how to build, lint, benchmark and word commits;
the README recommends LLMs for migrating from v1. Nothing restricts AI-written tests, and the zoo
keeps its tests in its own patch and files nothing upstream.

## Build

`go test -count=1 -v .` in the module root. The patch adds `hegel_test.go` (properties),
`hegel_pins_test.go` (one plain test per bug) and `hegel_oracle.mjs` (a node child process that
answers render requests over stdin/stdout), and requires `hegel.dev/go/hegel v0.6.33` and
`github.com/yuin/goldmark v1.8.6` in go.mod. The `[run] setup` step installs commonmark.js,
micromark and `micromark-extension-gfm` under `.hegel/` (4 MB, excluded from the patch); node 22
is on the Go job's path in CI (`actions/setup-node`). The child process honours `HEGEL_NODE`.

## Oracles

- **commonmark.js 0.31.2** — the reference implementation, same spec version as
  `testdata/spec.json`. With XHTML and raw HTML on, goldmark and commonmark.js agree byte for
  byte on most random documents; the systematic differences (below) are normalised on both sides.
- **micromark 4.0.2** — tiebreaker on the CommonMark side (every mismatch says which of the two
  it sides with), and with `micromark-extension-gfm` (tables, strikethrough with single tildes,
  task lists, autolink literals) the oracle for the GFM extensions.
- **goldmark v1.8.6** — the last v1 release, for the rewrite: every CommonMark and GFM document
  is rendered by both major versions; a difference is a regression or a fix, and the v2 bugs
  below say which are regressions (4, 8, 11, 29).

## Method

The generator (ported from the markdown-it target) builds structured Markdown: paragraphs, ATX
and setext headings, thematic breaks, fenced and indented code, block quotes, bullet and ordered
lists with varied marker gaps and tightness, HTML blocks of all seven kinds, reference
definitions, GFM tables; inline emphasis of every delimiter shape, strikethrough, code spans,
inline and reference links and images, autolinks and autolink literals, entities, backslash
escapes, hard and soft breaks, raw HTML, typographer triggers, Unicode spaces — with random
indentation, tabs and CRLF line endings, and (under the `Known` switches) a BOM, lone CRs or
NUL bytes.

| Property | Checks |
|---|---|
| CommonMarkAgreesWithCommonmarkJs | exact HTML agreement (XHTML, unsafe) with commonmark.js; micromark's verdict on every mismatch |
| GfmAgreesWithMicromark | tables + strikethrough + task lists against micromark + gfm, on documents whose CommonMark core the two reference implementations agree on |
| RewriteAgreesWithVersion1 | v2 against v1.8.6, CommonMark then GFM, minus the documented v2 changes |
| LinkifyAgreesWithGfmAutolinkLiterals | the Linkify extension against `micromark-extension-gfm-autolink-literal` on runs of URLs, emails and words separated by the GFM start characters |
| SafeOutputIsWellFormedHtml | every extension on, raw HTML off: balanced tags, quoted attributes, every `&` an escape, no `javascript:`/`vbscript:`/`file:`/`data:` (except images) href or src |
| AstIsWellFormed | parent/sibling links, `ChildCount`, `OwnerDocument`, `Source()` segments inside the source and in order, `Dump` runs, rendering the same tree twice and from a string source gives the same HTML |
| HardWrapsOnlyAddBreaks | `WithHardWraps()` output equals the default output with soft breaks turned into `<br />` |
| AutoHeadingIdsAreUniqueAndWellFormed | `WithAutoHeadingID()`: every heading has an id, ids are `[a-z0-9-]+` and unique |
| UtilsMatchTheirModels | `util.IsPunct`, `IsSpace`, `IsAlphaNumeric`, `IsPunctRune`, `IsSpaceRune` (against the spec's Unicode whitespace, minus the four code points below), `TrimLeftSpace`/`TrimRightSpace`/`IsBlank`, `EscapeHTML`, `URLEscape` (against `encodeURI` with `%` kept), `ToLinkReference` laws, `TabWidth`, `DoFullUnicodeCaseFolding` |
| TypographerMatchesTheDocumentedTable | `'` `"` `--` `---` `...` `<<` `>>` on plain text against the documented substitutions |
| RenderingTimeIsNotSuperLinear | random repeated units at 1500 and 6000 repetitions; nothing found |
| Pin UpstreamFixturesStillPass | the 652 spec examples through `testutil.DoTestCases` (passes) |

Mismatches are classified before they count: a `Known` switch per recorded bug gates the input
shape (regexes and two small scanners for table cell counts), and accepted differences are
normalised on both sides. With everything gated the four differential properties run clean at
500–800 cases; `ZOO_COLLECT=1 go test -run TestHegel... -v .` prints the class counts and the
first 25 mismatches instead of failing.

## Accepted differences (not bugs)

- goldmark writes `%` unencoded even when it does not start `%XX` (cmark does the same);
  commonmark.js and goldmark v1 write `%25`.
- CRLF line endings are kept verbatim inside code blocks and HTML blocks (commonmark.js
  normalises them to LF).
- No newline after an HTML block that ends the document or a container without a final newline.
- An empty title is omitted (`title=""` in v1 and micromark; commonmark.js omits it too).
- v2 writes `align` on the cells of short table rows (v1 did not; micromark agrees with v2).
- Raw HTML inside image alt text is dropped (cmark does the same; commonmark.js copies it
  unescaped).
- A tab before a soft break is kept (the spec speaks of spaces).
- Header rows of pipes only make a table (micromark: no); `a|` + `-` is a setext heading and
  `a\n-|` a table in every implementation.
- Linkify: `ftp://`, `mailto:` and `xmpp:` literals are goldmark's documented extras; an
  upper-case `HTTP://` scheme is not linked (micromark links it; the spec is silent); `;` is
  kept at the end of a URL (spec text; micromark strips it); a `|` is not part of a URL (micromark
  keeps it as `%7C`); an email domain containing `_` right before `www.`/`http://` is read either
  way; micromark starts a new autolink right after `)` where goldmark continues the current one.
- Table body rows indented four or more columns: micromark ends the table and reads indented
  code, goldmark reads a row; the GFM spec says nothing.
- `util.IsSpaceRune` follows `unicode.IsSpace`, so U+000B, U+0085, U+2028 and U+2029 count as
  whitespace where the spec's list has only Zs, tab, LF, FF and CR. cmark excludes them,
  commonmark.js and micromark (JavaScript's `\s`) include them; no rendering difference found.
- `util.IsSpace` is space, tab, LF and CR; `TrimLeftSpace`/`TrimRightSpace` also trim FF and VT;
  `IsBlank` follows `IsSpace`. Internally inconsistent but with no rendering consequence found.
- commonmark.js quirks the classifier accepts when micromark sides with goldmark: an empty
  paragraph for a definition followed by a `---` line, JavaScript `trim()` of Unicode spaces at
  paragraph and heading ends, `<blockquote>\n</blockquote>`, `%25` for a stray `%`.
- micromark quirks the GFM property skips: `*_*a` emphasis, a `5)` list after code, indented
  rows, `&#1;` to U+FFFD, `www.x`/`Www.` and after-`)` autolinks, `;` trailing punctuation.

## Bugs

Twenty-nine, all with commonmark.js and micromark (and where they apply, cmark or the GFM text)
agreeing on the correct answer; see `bugs.toml`. By theme: line endings (2, 3, 14; a leading
BOM, 1), tabs inside containers (9, 16, 28), image alt text (4, 5, 6), link destinations and
titles (25, 26), HTML block starts (11, 17), fences (10, 13, 21), NUL handling (7), emphasis after
a bare quote marker (12), list tightness (15), tables (8, 23, 29), and seven in the Linkify
extension (18, 19, 20, 22, 24, 27). Bug 29 is the most visible: a paragraph line followed by a
tab-indented `---` becomes a one-column table. Four are v2 regressions (4, 8, 11, 29); the rest are shared
with v1.8.6.

## Not tested

Footnotes, definition lists, attributes (`WithAttribute`), typographer quotes inside markup,
East Asian line breaking, CJK options, the `text` package's readers directly, and the
`Renderer`/`Parser` option plumbing beyond what the configurations above exercise.
- 2026-09-17: base bumped 710cc2656aa3 → c4c7034e4ff2 (2026-09-17, "chore: delete debug print"; v2.1.3); 29 bug(s) still reproduce. 36 tests pass.
