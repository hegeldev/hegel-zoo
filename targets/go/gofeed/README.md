# gofeed

[mmcdole/gofeed](https://github.com/mmcdole/gofeed) parses RSS (0.9x, 1.0, 2.0), Atom (0.3,
1.0) and JSON Feed into one universal `Feed` (about 2,900 stars; the feed parser of most Go
readers and aggregators): format detection, a pull parser per format on top of `encoding/xml`
with entity and CDATA handling, xml:base resolution and a control-character filter, extension
maps for namespaced elements (Dublin Core and iTunes typed), a date parser with some 200
layouts, and translators mapping each format's fields onto `Feed` and `Item` (links, authors,
dates with fallbacks, categories, enclosures, images). The pin is `253ddbe` (2026-09-07,
master, ten commits after v1.4.2).

The repository has LICENSE (MIT) and CONTRIBUTING.md (issues first, fixture pairs, the CI
commands); no agent instructions, nothing about AI-written code. The zoo keeps its tests in its
own patch and files nothing upstream.

## Build

`go test -count=1 -run TestHegel -v .` in the module root, with `python3` on PATH able to
`import feedparser` (feedparser 6.0.12; the setup command checks the import). The patch adds
`hegel_test.go` (harness, the model, the three writers, the universal-feed mapping and the
three format properties), `hegel_dates_test.go` (date layouts, detection and robustness),
`hegel_oracle_test.go` (the feedparser child) and `hegel_pins_test.go` (one plain test per
bug), all in the external package `gofeed_test`, and requires `hegel.dev/go/hegel v0.6.33` in
go.mod (the `go` directive moves from 1.25.0 to 1.26.0 for it).

## Oracles

- **A model feed and the documented mapping.** A feed (title, description, link, self link,
  language, copyright, generator, dates, author(s), image, categories) with items (title, link,
  id, description, content, published and updated dates, author(s), categories, enclosures,
  unknown children) is generated once and written by the harness as RSS 2.0, Atom 1.0 or JSON
  Feed 1/1.1: children in any order (repeatable elements keep theirs), text as entity escapes,
  decimal or hexadecimal character references, CDATA sections split at random or a mixture,
  optional elements present or absent, attributes in any order, Atom text constructs typed
  `text`, `TEXT` or `html`, links with and without `rel`, numeric JSON ids, `content_html` or
  `content_text`, `author` or `authors`. The expected universal `Feed` follows the mapping the
  translators document: RSS `pubDate`/`lastBuildDate` to Published/Updated, `dc:date` to an
  item's Updated (and Published when `pubDate` is absent), `managingEditor`/`author`/
  `dc:creator` through the "name (email)" forms, an `image/*` enclosure as the item image,
  unknown children in `Custom`; Atom alternate and self links, label over term for categories,
  the first author as Author, Published falling back to Updated, `rel="enclosure"` links as
  enclosures; JSON `home_page_url`/`feed_url`, `icon` as the image, the first item's dates as
  the feed's, `size_in_bytes` as the enclosure length, tags as categories.
- **feedparser 6.0.12** (Python) reads the same RSS and Atom documents (it has no JSON Feed
  support): version, title, link, subtitle, language, rights, generator, author, image, tags,
  dates in UTC, and per entry title, link, id, summary, content, dates, authors, tags and
  enclosures, compared with its own conventions (the last Atom author is `author`, updated
  mirrors published when absent, summary falls back to content, categories are deduplicated).
- **Go's time.Parse on the layout a date was written in**, with gofeed's own zone table, for
  the date property.

## Method

| Property | Checks |
|---|---|
| RSSFollowsTheModel | the RSS 2.0 writing of a model feed parses to the documented universal mapping; feedparser reads the same values |
| AtomFollowsTheModel | the same for Atom 1.0 |
| JSONFeedFollowsTheModel | the same for JSON Feed 1 and 1.1 (no second reader) |
| DatesFollowTheirLayout | a date written with any of 130 layouts from gofeed's list (numeric offsets, zone names from its table, two-digit years) parses as an RSS `pubDate` to what `time.Parse` gives for that layout, and feedparser agrees whenever it reads the text (its own misreadings excepted) |
| DetectionSurvivesTheProlog | a document with a byte order mark, XML declaration, comments, DOCTYPE, processing instructions, leading whitespace, RSS names in another case or an ISO-8859-1 encoding is detected as its type and parses to the same feed as the plain document; every prefix parses or fails within five seconds without panic |

Mismatches are classified before they count: a `Known` switch per recorded bug gates the input
shape (author strings kept to the four supported forms, no HTML named entities, no BOM before
JSON, RFC 3339 in upper case, two-digit years within Go's window, JSON items following the
current no-inheritance rule); the pins assert the correct behaviour and fail while the bug
exists. `ZOO_COLLECT=1` records mismatches instead of failing and prints the class counts.

## Accepted differences

- The purely numeric ambiguous layouts (`1/2/2006` against `2/1/2006`, `02.01.2006`, `6/1/2`)
  are not generated: gofeed reads a day-first layout first and a US date such as 3/4/2006 as
  3 April, which its list cannot resolve either way.
- Unknown zone abbreviations (JST, AEST ...) are read as UTC, as RFC 5322 4.3 prescribes for
  unknown zones; the generators use the table's names. feedparser does the same.
- feedparser's own quirks are left out of its comparison: 12-hour clocks (12:00 AM is noon to
  it), `2006 January 02` and `2006/01/02` (day and month swapped), `2006-01-02 15:04:05 MST`
  and `2006-01-02 at 15:04:05` (the time dropped), offsets with minutes such as -0330 (hours
  only), its century rule for two-digit years, a title that looks like HTML (sanitized),
  HTML-typed Atom text (entities decoded); its `author_detail` accumulating over an element's
  Atom authors is modelled rather than skipped.
- Text values are generated without leading or trailing blanks (both parsers trim, gofeed
  with `strings.TrimSpace`, which also removes a leading NBSP) and without control characters
  (gofeed filters them before the XML decoder).

## Bugs found

Ten, in bugs.toml: author strings outside four shapes are dropped or misread (`Name <email>`
becomes the email, `@handle` vanishes); `itunes:keywords` are split without trimming; HTML
named entities are decoded in core elements but not in extension elements; an item's
`atom:link` is not promoted while the channel's is; JSON Feed items do not inherit the feed's
authors; RFC 3339 with a lower-case `t`/`z` is rejected; two-digit years 50-68 are 20xx against
RFC 5322; an enclosure `url` is not resolved against xml:base; an RSS 1.0 item's `rdf:about`
is not its GUID; a JSON Feed with a byte order mark is detected and then rejected.

## History

- 2026-09-20 (turn 333): target added at 253ddbe with five properties, ten pins.
