# go/dst

[dave/dst](https://github.com/dave/dst) (v0.28.0): the decorated syntax tree, a `go/ast` with
comments and line spacing attached to the nodes they belong to, so that a Go file can be
modified and printed with high fidelity. Tested here: `decorator.Parse` and `decorator.Fprint`
(the round trip through the decorated tree), `dst.Clone`, and the decoration points
(`dstutil.Decorations`), on generated Go source files.

## Build

The patch adds `hegel.dev/go/hegel` to `go.mod` and a `hegel/` package of five
`hegel_zoo_*_test.go` files that drive the public API: `go test -count=1 -run TestHegel -v ./hegel`.
Nothing else is needed (gofmt is `go/format`).

## Oracle

gofmt. dst's contract, which its own tests check over the standard library, is that a
gofmt-formatted file survives `Parse` + `Fprint` byte for byte; the generated file is formatted
with `go/format` first, and a file gofmt itself is not stable on (a second pass changes it, which
happens with some trailing-comment alignments) is not judged. For the comment attachment,
`go/parser`'s comment list is the reference.

## Generator

A Go source file with declarations (imports plain, aliased, dot and blank; grouped and single
var, const and type declarations; functions and methods, generic ones, external ones), types
(pointers, slices, arrays, maps, channels, functions, structs with tags and embedded fields,
interfaces with methods, embedded interfaces and type sets, qualified and instantiated names),
statements (assignments, if/else chains, the four for forms and range over an integer, switch and
type switch, select, return, go, defer, labels with goto/break/continue, blocks, declarations,
sends) and expressions (every literal form including multi-line raw strings, binary and unary
operators, calls with arguments on their own lines and variadic, selectors, indexes, slices,
type assertions, instantiations, composite literals single and multi-line, func literals,
conversions). Comments at most places the grammar allows them: whole-line `//` and `/* */`
comments, multi-line block comments, trailing comments, block comments between tokens, empty and
non-ASCII comments, tabs and trailing spaces inside, `//go:` directives; blank lines between
items. Two directed scenarios keep the recorded bugs' shapes frequent.

## Properties

- `TestHegelRoundTrip`: the gofmt-formatted file, parsed with `decorator.Parse` and printed with
  `decorator.Fprint`, is the same text.
- `TestHegelClone`: `dst.Clone` of the file prints the same text, and the original still does.
- `TestHegelDecorations`: the decorations of all nodes (`dstutil.Decorations` over
  `dst.Inspect`), the newlines left out, are exactly the file's comments as `go/parser` lists
  them, each attached once.
- `TestHegelAddComments`: 1-6 comments appended or prepended (`Decorations.Append`/`Prepend`)
  at random decoration points of random nodes - block comments anywhere, line comments and a
  `\n` decoration only at the Start and End of statements, declarations and specs, where a
  line may end - and the file printed: the output must be valid Go, its comments must be the
  file's plus the added ones (an empty `//` that go/printer puts between a doc comment and a
  `//go:` directive is allowed), and its syntax tree without positions and comments must equal
  the source's.
- `TestHegelPin…`: one pin per recorded bug (expected failures).

## Bugs

Three, recorded in `bugs.toml`, all round-trip differences: a comment after the `=` of a generic
type alias moves before the type parameters (dst/1); a multi-result return of which one result
spans lines, closed by a comment at the end of its block, has the results indented one level too
deep (dst/2); in a var or const block of several specs, the trailing comment of a spec whose
value is a multi-line raw string gets two spaces (dst/3).

## Modelled as recorded

Every bug has an `HZKnown` switch. While a switch is on the generator keeps away from the shape
(no comment between a generic alias's `=` and its type; no comment closing a block after a
multi-result return that spans lines; no trailing comment on a multi-line raw string spec in a
group of several) and the collector counts the avoidances. `ZOO_KNOWN_OFF=name` turns a switch
off and the property then fails on it.

## Not tested

Import management (`NewDecoratorWithImports`, `NewRestorerWithImports`, the resolvers, `Load`)
and the known open issue about several imports of one path; structural modifications of the
tree (`dstutil.Apply`, moving nodes, `Before`/`After` spacing changes) and the exact layout
added comments produce (only validity, presence and code identity are checked); `Decorator.Map`
and the scope/object information; files with syntax errors (the parser's error recovery); line
directives.

## History

- 2026-09-21: new target, four properties, 3 bugs.
