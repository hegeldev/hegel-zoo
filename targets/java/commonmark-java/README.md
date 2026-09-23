# commonmark-java

[commonmark-java](https://github.com/commonmark/commonmark-java) (`org.commonmark:commonmark` and its ten extension
modules, 0.30.1-SNAPSHOT, pinned at the main commit of 2026-08-07): the Java CommonMark parser (spec 0.31.2) with HTML,
Markdown and plain-text renderers, source positions, and the GFM extensions (tables, strikethrough, task list items,
autolinks, alerts, footnotes, heading anchors, ins, image attributes, YAML front matter).

The tests are a Maven module `hegel/` added by the patch; `[run] setup` installs the reactor's modules from the pinned
tree into the local Maven repository (Javadoc, sources, signing and JaCoCo skipped, the integration-test module left
out; about half a minute) and npm-installs commonmark.js 0.31.2 into `hegel/node/` from the patch's `package.json`. The
repository's CONTRIBUTING.md asks for tests and the existing style and says nothing about AI.

## The oracles

- **commonmark.js**, the reference implementation of the same spec version, as a child process
  (`hegel/node/oracle.js`, one JSON-quoted document per request, the HTML back): the HTML of every generated document
  must match. Five differences are the reference's, not the library's, and are normalised or avoided (checked against
  the spec text): commonmark.js knows no tabs between the parts of link and definition syntax (`spnl` matches spaces
  only), so the generator writes none there; it counts a trailing lone CR as an extra line; it trims Unicode spaces
  (U+00A0, U+2028, …) off paragraphs and headings with JavaScript's `trim`, where the spec's blank characters are space
  and tab (the ASCII spaces next to them and a line made of such spaces alone, with its line ending, go too; the library
  rightly keeps them), so for documents with such characters the spaces at the edges of paragraphs and headings are
  ignored; it cuts the info string's first word (the code's `language-` class) at JavaScript whitespace
  (`split(/\s+/)`, Unicode spaces included) where the library and cmark cut at an ASCII space, so a fence whose first
  info word holds a Unicode space is skipped (`Known.UNICODE_SPACE_IN_FIRST_WORD`); and it omits an empty `title`
  attribute where the library writes `title=""`. Otherwise ASCII spaces in the HTML must match exactly. The library's `maxInlineNesting`/
  `maxOpenBlockParsers` limits (100) are never reached by the generator.
- **The library against itself**: rendering a parsed document to Markdown and parsing that must give the same document
  (compared as HTML, which prints every field of the tree) and rendering it again must give the same Markdown
  (`MarkdownRenderer`'s Javadoc: "if the Markdown was parsed again and compared against the original AST, it should be
  the same"); `parse(String)` and `parseReader` agree; rendering the same tree twice gives the same output; including
  source spans changes nothing.
- **The input text**: every source span points into the input (line start + column = input index, no line ending
  inside, no overlap within a node, inside the parent's spans), and the text under a node's span has the shape its
  syntax requires (ATX heading level and `#`s, fence characters, list markers, `>`, backticks, emphasis delimiters,
  link/image brackets, HTML angle brackets, definition brackets, non-blank paragraph lines).
- **Models of the extensions**: YAML front matter (the documented subset: `key: value`, quoted values, indented
  `- item` lists, empty keys, `---`/`...` closers) against the map it must produce and the body against its own parse;
  a well-formed GFM table against its cells, alignments and `<th>`/`<td>` structure.

## Properties (`CoreTest`, 1; `RoundTripTest`, 2; `SpansTest`, 2; `GfmTest`, 3)

`MdGen` writes the documents: structured ones from every block and inline construct of the spec (paragraphs with soft
and hard breaks, ATX and setext headings, fenced and indented code, thematic breaks, the seven kinds of HTML block, link
reference definitions, block quotes and lists nested three deep with lazy continuation lines and odd indentation,
emphasis with unbalanced runs and Unicode punctuation, code spans, inline/reference/collapsed/shortcut links and images,
autolinks, raw inline HTML, entity and numeric references, backslash escapes, tabs; with `gfm` also tables, task lists,
strikethrough, footnotes, alerts, ins and image attributes) and unstructured ones drawn from an alphabet of Markdown
punctuation; a tenth get CRLF line endings, a tenth lose the final line ending.

- `htmlMatchesCommonmarkJs`: the core parser and `HtmlRenderer` (`percentEncodeUrls(true)`, as the spec's HTML assumes)
  against commonmark.js.
- `markdownRendererRoundTrips`, `markdownRendererRoundTripsWithExtensions`: the Markdown round trip, core only and with
  tables, strikethrough, task lists, footnotes, alerts, ins and YAML front matter.
- `sourceSpansPointIntoTheInput` (BLOCKS_AND_INLINES), `readerAndStringParseAlike`.
- `renderingIsPure` (HTML and text, all extensions), `yamlFrontMatterMatchesTheModel`, `tablesRenderTheirCells`.

The properties skip the shapes of the recorded bugs (`Known.java`: a tight list with a blank line inside an item, tabs
in indented or quoted fenced code, tabs in info strings, unbalanced `(` in destinations, `<!` + lowercase, mixed fence
characters, surrogate references, raw HTML in image descriptions, declarations without whitespace, control characters,
a literal backtick after a code span; for the round trip an item whose non-paragraph block is followed by a blank line
(tightness), hard breaks at the start of a paragraph or line, after another break, after a task marker or after a
space, definitions inside containers or right after a list, items starting with an indented nested list, empty
destinations with a title, HTML blocks with tabs, info strings
starting with the fence character or containing `&`, nested or adjacent emphasis and every strong emphasis, multi-line
inline HTML, links in links, thematic breaks first in an item, `+`/`~~~` at a line start, list numbers of two or more
digits, entities after delimiters, `&` in destinations and titles, empty footnote definitions, header rows without
cells, backslashes in table cells; for the differential also HTML blocks inside containers; for spans a child starting
before its parent with only whitespace or `>` between and the paragraph after a definition; for purity documents with
image attributes); the pins carry them.

## Not tested

The `TextContentRenderer`'s output beyond purity (its line-break modes and separators), `HtmlRenderer` options
(`escapeHtml`, `sanitizeUrls`, `omitSingleParagraphP`, attribute providers), the autolink extension against the GFM
autolink rules (it wraps `org.nibor.autolink` and claims no spec), the heading-anchor id model, alerts and footnotes
beyond the round trip, `enabledBlockTypes`, custom block/inline parsers, the `parser.beta` API, the `DingusApp`,
Android module. The YAML property writes only closed front matter (bug 29) at the document start (bug 41).

## Bugs (59 open; each has a pin in `CommonmarkPinsTest`)

| id | severity | what |
|---|---|---|
| commonmark-java/1 | medium | a blank line after a thematic break, heading, HTML block or indented code in a list item does not make the list loose |
| commonmark-java/2 | medium | a tab partly consumed by the fence indent or a container marker is kept whole in fenced code and HTML block content |
| commonmark-java/3 | low | the language class takes the info string up to the first space only (a tab is kept) |
| commonmark-java/4 | low | an unbalanced `(` in a link destination is accepted before whitespace or the end of the line |
| commonmark-java/5 | low | HTML block kind 4 needs an uppercase letter after `<!` (spec: any ASCII letter) |
| commonmark-java/6 | medium | `&#xD800;` yields a lone surrogate instead of U+FFFD |
| commonmark-java/7 | medium | ```` ```~ ```` and `~~~`` are not code fences |
| commonmark-java/8 | low | alt text drops raw inline HTML while keeping code spans |
| commonmark-java/9 | low | an inline `<!DECLARATION>` needs whitespace after its name |
| commonmark-java/10 | low | vertical tab counts as whitespace between the parts of a link |
| commonmark-java/11 | low | link label normalisation strips control characters at the ends |
| commonmark-java/12 | low | `insertAfter`/`insertBefore` on a node without a parent throw NullPointerException |
| commonmark-java/13 | medium | MarkdownRenderer: a hard break at the start of a paragraph or line becomes two spaces and vanishes |
| commonmark-java/14 | medium | MarkdownRenderer: an info string starting with the fence character is glued to the fence |
| commonmark-java/15 | medium | MarkdownRenderer: nested or adjacent emphasis with the same delimiter merges on re-parse |
| commonmark-java/16 | medium | MarkdownRenderer: strong emphasis always `**`, so `__*a*__` flips to `em(strong)` |
| commonmark-java/17 | low | MarkdownRenderer: multi-line inline HTML whose next line starts with `>` becomes a block quote |
| commonmark-java/18 | low | MarkdownRenderer: an autolink inside link text is written `[text](dest)` and does not re-parse |
| commonmark-java/19 | medium | MarkdownRenderer: `* ***` — a thematic break first in a `*` item re-parses as a thematic break |
| commonmark-java/20 | low | MarkdownRenderer: an entity right after an emphasis closer is decoded, and the closer stops closing |
| commonmark-java/21 | medium | MarkdownRenderer: `+` at a line start is never escaped (text becomes a list) |
| commonmark-java/22 | medium | MarkdownRenderer: item padding follows the original content indent and can exceed four columns |
| commonmark-java/23 | medium | MarkdownRenderer: `~` is never escaped (`~~~` text becomes a fence) |
| commonmark-java/24 | low | MarkdownRenderer: decoded info strings and destinations are written raw (entities decoded twice) |
| commonmark-java/25 | low | TextContentRenderer throws NullPointerException on a BulletList without a marker |
| commonmark-java/26 | low | on a lazy line inside a quote the paragraph's span starts before its list item's |
| commonmark-java/27 | low | on a lazy line inside a quote the list item's span starts before its list's |
| commonmark-java/28 | low | after `>` + tab the paragraph's span starts at the tab, before its text |
| commonmark-java/29 | high | an unterminated YAML front matter block swallows the whole document |
| commonmark-java/30 | medium | rendering an image with attributes to HTML removes the attributes from the tree |
| commonmark-java/31 | medium | inside a YAML literal block, indented `key: value` lines become keys |
| commonmark-java/32 | medium | MarkdownRenderer: an empty footnote definition takes the next block as its content |
| commonmark-java/33 | low | a header row of `\|` alone makes a table with no columns |
| commonmark-java/34 | low | in a loose list the task checkbox is rendered outside the paragraph |
| commonmark-java/35 | low | heading ids join the words of multi-line and tab-separated headings |
| commonmark-java/36 | low | footnote reference ids collide (`fnref-foo-2` twice) |
| commonmark-java/37 | low | a delimiter row with more cells than the header still makes a table |
| commonmark-java/38 | medium | a table continues over a block start (`> b\|c`, `# h\|x`, ```` ```\| ````) |
| commonmark-java/39 | low | heading ids and alert classes depend on the default locale |
| commonmark-java/40 | low | the autolink extension links text inside an image description |
| commonmark-java/41 | low | YAML front matter is recognised after leading blank lines |
| commonmark-java/42 | low | `{ width=5}` is rejected while `{width=5 }` is accepted |
| commonmark-java/43 | low | the alerts HTML/text renderers throw on an Alert of an unknown type |
| commonmark-java/44 | low | MarkdownRenderer: `^` before `[` is not escaped with inline footnotes enabled |
| commonmark-java/45 | low | MarkdownRenderer: a backslash hard break becomes trailing spaces, losing the spaces of the text before it |
| commonmark-java/46 | low | an HTML block of kind 1–5 closed by its container drops the blank line that closed it |
| commonmark-java/47 | low | a table row treats `\\\|` (escaped backslash, then a pipe) as an escaped pipe |
| commonmark-java/48 | low | a paragraph after a link reference definition whose title line failed has no source spans |
| commonmark-java/49 | low | MarkdownRenderer: link reference definitions are dropped, changing the structure around them (a list loose only because of one becomes tight, a block after one joins the list before it, a quote gets a stray `> ` line) |
| commonmark-java/50 | low | MarkdownRenderer: the indent of a nested list starting an item is written on the item's first line, so later blocks of the item fall out |
| commonmark-java/51 | medium | MarkdownRenderer: an empty destination `<>` with a title is written as nothing, so the title re-parses as the destination |
| commonmark-java/52 | high | a code span after an unclosed backtick string and another code span is left as text (`` `` `a` `c` ``: the backtick position cache is overwritten with earlier positions) |
| commonmark-java/53 | low | MarkdownRenderer: an entity right before an emphasis opener is decoded, and the opener stops opening (bug 20's mirror) |
| commonmark-java/54 | medium | MarkdownRenderer: a footnote definition's text is not escaped at its line start (`[^1]: \#` comes back as a heading, `\- a` as a list) |
| commonmark-java/55 | medium | a blank line inside a nested list makes the outer list loose when a block follows the nested list on the next line |
| commonmark-java/56 | medium | MarkdownRenderer: inside a tight list item, blocks in a block quote are separated by one line ending, so two paragraphs merge |
| commonmark-java/57 | medium | a footnote definition inside a container reads its later blocks against the absolute column 4, so a paragraph becomes indented code (and the Markdown rendering grows by four columns each time) |
| commonmark-java/58 | medium | a list item that may not interrupt a paragraph (`2.`, an empty item) does so right after a link reference definition |
| commonmark-java/59 | low | MarkdownRenderer: a footnote reference at a line start followed by `:` re-parses as a footnote definition (found by this turn's 1000-case run) |

Observed and left unrecorded (arguable or cosmetic): the renderer's text escaping is not a fixed point (`[^a]:**.**Æ`
renders unescaped once and escaped the second time, with equal HTML); the Markdown renderer discards `TableCell.getWidth()` and
the alignment of extra delimiter columns; the YAML subset parser turns a one-item list into a scalar on re-rendering,
drops keys that do not match `[A-Za-z0-9._-]+` and adds blank lines after a front-matter-only document; `{width=5=9}`
truncates silently; `TextContentRenderer` drops footnotes, task-list markers and front matter (no renderer registered)
and a `ListItem` outside a list; the autolink extension keeps trailing `_` and `&hl;` in URLs where the GFM autolink
rules stop before them (the extension claims no spec); autolinks accept U+007F (spec: ASCII control), as does
commonmark.js.

## History

- 2026-09-16: created (turn 184) at b89e72fdb259 (0.30.1-SNAPSHOT, 2026-08-07); 52 bugs.
- 2026-09-23: 53..59 recorded (53..58 the generator rewrite's shake-outs, reproduced standalone against the installed
  jars, commonmark.js and cmark-gfm; 59 from the 1000-case round-trip run that verified them); two more of the
  rewrite's findings extend bugs 2 (a thematic break's literal keeps the partial tab) and 46 (the blank line at the
  document end, and the mechanism is the HTML writer's, not the parser's).
