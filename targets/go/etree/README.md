# etree

[beevik/etree](https://github.com/beevik/etree) is a lightweight XML element tree for Go
(about 1,700 stars), modelled on Python's ElementTree and built on `encoding/xml`: a `Document`
of tokens (elements with prefixes and attributes, text and CDATA, comments, processing
instructions, directives), reading from and writing to strings, files and readers with
`ReadSettings`/`WriteSettings`, `Indent`/`Unindent`, a mutation API (`AddChild`,
`InsertChildAt`, `RemoveChildAt`, `Remove`, `SetText`/`SetTail`, `CreateAttr`, `SetRoot`,
`Copy`), namespace resolution, and XPath-like paths (`FindElements`, `CompilePath`) with
selectors and `[...]` filters. The pin is `02c461a` (2026-09-07), one commit after the v1.8.0
tag.

The repository has LICENSE (BSD-2-Clause), README, RELEASE_NOTES and CONTRIBUTORS; no
CONTRIBUTING, no agent instructions, nothing about AI-written code. The zoo keeps its tests in
its own patch and files nothing upstream.

## Build

`go test -count=1 -run TestHegel -v .` in the module root, with `python3` and
[lxml](https://lxml.de/) on the path (CI installs `lxml` in its venv; it is already there for
go/xpath). The patch adds `hegel_test.go` (harness, model, generators, the writer/reader
properties), `hegel_api_test.go` (paths, mutations, indentation), `hegel_pins_test.go` (one
plain test per bug) and `hegel_oracle_test.go` (the lxml child), and requires
`hegel.dev/go/hegel v0.6.33` in go.mod (the `go` directive moves from 1.23.0 to 1.26.0 for it;
etree itself has no dependencies).

## Oracles

- **A model tree**, generated with elements (prefixes `p`/`q` declared on the root, sometimes a
  default namespace, sometimes redeclarations below), attributes, text, CDATA, comments,
  processing instructions and a DOCTYPE, over an alphabet with `<>&'"`, whitespace, `]]>`, `--`,
  `?>`, non-ASCII, carriage returns and forbidden characters. It is built through the API
  (`CreateElement`, `CreateAttr`, `CreateText`, ...), or written by the harness in varied
  well-formed syntax (character and entity references, either quote, whitespace inside tags,
  empty-element or open/close forms, duplicate attributes). What etree should read back is the
  model after the documented sanitisation (forbidden characters to U+FFFD, `- -` in comments,
  `? >` in instructions, `]]>` split) and the parser's line-end normalisation, with adjacent
  character data merged.
- **The documented token semantics** on the model: `Text` (leading character data, comments
  skipped) and `Tail`, `SetText`/`SetCData`/`SetTail`, `AddChild`/`InsertChildAt` (moving a
  token within its parent included), `RemoveChildAt`/`RemoveChild`/`Remove`,
  `CreateAttr`/`RemoveAttr`/`SortAttrs`/`SelectAttr`, `SetRoot`, `Copy` (deep, independent),
  `NextSibling`/`PrevSibling`/`Index`/`Parent`, `Indent` with every `IndentSettings` field and
  `Unindent`, namespace URIs through the declaration chain, `MaxDepth`, `PreserveCData`,
  `PreserveDuplicateAttrs`.
- **The documented path grammar**: selectors `.`, `..`, `*`, `//`, `tag`, `p:tag`, absolute
  paths, and the filters `[@a]`, `[@a='v']`, `[tag]`, `[tag='v']`, `[n]` (negative n from the
  end, as implemented), `[fn()]` and `[fn()='v']` for the five functions, evaluated
  breadth-first with deduplicated results as etree does, an unprefixed name matching any
  prefix.
- **lxml** (Python, one persistent child) parses what etree writes and what the harness writes,
  reporting resolved namespaces, attributes, flattened text, comments, instructions and the
  DOCTYPE; and evaluates etree paths translated to XPath (`tag` to `*[local-name()='tag']`,
  `//` to `descendant-or-self::*`, `[@a]` to `[@*[local-name()='a']]`) on the subset both read
  alike: no `[tag='v']`/`[text()]` (etree compares `Text()`, XPath the string value), no
  zero or negative positions, no `namespace-prefix()`, no filters on `//`, no redeclared
  prefixes.

## Method

| Property | Checks |
|---|---|
| WriteThenReadIsIdentity | a tree built through the API, written with any `WriteSettings` and read back (with or without `PreserveCData`, any `MaxDepth`) is the model after the documented sanitisation; every whitespace-only text read is `IsWhitespace` |
| LxmlReadsTheOutput | lxml parses etree's output and sees the model: namespaces of elements and attributes, values, character data, comments, instructions, DOCTYPE |
| ParsesLikeLxml | XML written by the harness in varied syntax reads into the model with the CDATA and whitespace flags and the resolved namespaces; lxml reads the same; duplicate attributes follow `PreserveDuplicateAttrs` |
| PathsFollowTheModel | `CompilePath` accepts the grammar; `FindElements` from any element (the document included) equals the model's set with no duplicates, `FindElement` is its first, the `Seq` forms agree and stop early; lxml's XPath agrees on the shared subset |
| MutationsFollowTheModel | up to 25 random operations keep the tree equal to the model, every child's `Index`/`Parent` right, `Text`/`Tail`/siblings/attribute lookups as documented, copies independent, and the result writable and readable |
| IndentFollowsTheModel | on a parsed document, `IndentWithSettings` (spaces, tabs, CRLF, PreserveLeafWhitespace, SuppressTrailingWhitespace) gives the modelled tokens, is idempotent, reads back to itself, and `Unindent` restores the whitespace-stripped tree |

Mismatches are classified before they count: a `Known` switch per recorded bug gates the input
shape (unparented `Remove`, negative indices, copy indices, API-created whitespace text, comments
among leading text, `[tag]` before `[n]`, `[0]`, `[` in quoted values, raw whitespace under the
default escaping, prefixed attributes shadowing unprefixed ones, forbidden characters in CDATA).
With everything gated the properties run clean; `ZOO_COLLECT=1` prints class counts and the
first 25 mismatches instead of failing.

## Accepted differences (not bugs)

- `encoding/xml` is the parser: it does not enforce well-formedness (`<a/>x`, text after the
  root, duplicate attributes), does not normalise tabs and newlines in attribute values, does not
  check characters in comments and instructions, and hands comments and instructions over raw
  (no line-end normalisation). etree documents this in `ReadSettings.ValidateInput`.
- Directives are sanitised losslessly only when balanced: `a>b` is written `<!a&gt;b>` and reads
  back as `a&gt;b`; `<!--x-->` inside a directive is dropped by the decoder. The zoo writes only
  `DOCTYPE r`.
- Comments and instructions cannot escape `--`, a trailing `-` or `?>`; the documented space
  insertion is lossy by design, and a carriage return in them is normalised by every parser.
- An unprefixed name in a path or `SelectElement` matches any prefix (`a` finds `p:a`); an
  unprefixed attribute has no namespace; `..` from the root element is the document element.
- `[n]` with a negative n counts from the end (`[-1]` is the last); undocumented but coherent.
- `PreserveDuplicateAttrs = false` keeps the last value in the first attribute's slot.
- Fractions of the processing-instruction syntax: leading whitespace of the instruction is
  dropped by the decoder, trailing whitespace kept.

## Bugs found

Eleven, recorded in `bugs.toml` with a pin test each. Two medium: `Remove()` on a token without
a parent dereferences nil instead of returning false (**etree/1**, a v1.8.0 feature); the
`[tag]` filter keeps a candidate once per matching child, so `a[b][2]` returns the first `a`
when it has two `b` children (**etree/6**). Low: `RemoveChildAt(-1)` and `InsertChildAt(-1)`
panic (etree/2); `Copy()` keeps the original's `Index()` without a parent (etree/3);
whitespace-only text created through the API is not `IsWhitespace`, so `Indent` treats a built
tree and the same parsed tree differently (etree/4); `SetText` replaces only the text before
the first comment while `Text()` reads past it (etree/5); `[0]` selects the first element
(etree/7); a quoted filter value containing `[` does not compile (etree/8); the default escaping
writes carriage returns (and attribute tabs and newlines) raw, so they do not survive a round
trip (etree/9); `SelectAttr("x")` returns a preceding `p:x` (etree/10); CDATA contents are not
sanitised of forbidden characters and the output cannot be read back (etree/11). All found on
2026-09-20 (turn 330). Parsing, namespace resolution, the write/read round trip, indentation
and the path engine otherwise agreed with the model and lxml throughout.

## History

- 2026-09-20 (turn 330): target created at `02c461a` (v1.8.0+1); 11 bugs.
