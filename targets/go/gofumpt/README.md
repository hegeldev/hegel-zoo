# go/gofumpt

[mvdan/gofumpt](https://github.com/mvdan/gofumpt) (v0.12.0): a stricter gofmt, a fork of
`cmd/gofmt` that adds formatting rules (grouped declarations, no empty lines around blocks,
short assignments for var statements, std imports first, spaced comments, balanced calls and
grouped parameters behind `-extra`, ...) on top of gofmt's, applied by moving newlines in the
file's line table before the vendored `go/printer` prints the syntax tree. Tested here:
`format.Source` with every combination of `format.Options` (LangVersion, ModulePath,
ExtraRules, Extra.GroupParams, ClotheReturns and BalanceCalls), on generated Go source files.

## Build

The patch adds `hegel.dev/go/hegel` to `go.mod` and a `hegel/` package of six
`hegel_zoo_*_test.go` files that drive the public API: `go test -count=1 -run TestHegel -v ./hegel`.
Nothing else is needed.

## Oracles

gofumpt's own contract, stated in its conventions: every rule is idempotent in a single pass,
and the output is gofmt-stable (running gofmt after gofumpt changes nothing). gofmt is the
`go/format` gofumpt vendors under `internal/govendor`, so the toolchain's version does not
matter. For the code, `go/parser` with a normaliser that applies gofumpt's documented rewrites
(gofmt -s simplifications, var statements as short assignments, `0o` octal literals, grouped and
ungrouped declarations, std imports first, useless parentheses removed, parameters with equal
types grouped, naked returns clothed) to both trees; for constants, `go/types`. A generated file
gofmt itself is not idempotent on, or whose gofmt output does not parse (go/printer's doc-comment
reflow and a few comment placements), is not judged: the bugs there are gofmt's.

## Generator

A Go source file with a package clause, imports (lone, grouped, aliased, dot and blank, std and
third-party paths, `test/`, `example/` and module-prefixed paths, in and out of order, with
empty lines and comments in the group), declarations (grouped and lone var, const and type
declarations, iota constants, functions and methods, generic ones, external ones, calls split
after the parenthesis), types (pointers, slices, arrays, maps, channels, functions, structs,
interfaces, empty types over one or two lines, parenthesised types, instantiated names),
statements (assignments, var statements in every spelling, if/else chains, the for forms,
switch and type switch with single- and multi-line case lists, select, return, go, defer,
labels, blocks, sends) and expressions (every literal form including multi-line raw strings,
operators, calls with arguments on their own lines, composite literals, func literals,
conversions, instantiations). Comments at most places the grammar allows them, in every
spelling gofumpt's rules look at: `//c`, `// c`, `//  c`, `//\tc`, empty `//`, directives
(`//go:`, `//nolint`, `//#nosec`, `//NOSONAR`, `//sys`, `//noinspection`, `//lint:ignore`,
`//export`, `//line`), code-like comments, block comments between tokens, multi-line block
comments, trailing spaces and non-ASCII text; empty lines between items and inside blocks. Half
the time gofumpt gets the raw file, the other half its gofmt-formatted form. Two directed
scenarios keep rare shapes frequent (a case list of a length around gofumpt's short-line limit
with a trailing comment; a std import sorting after a third-party one with a comment group
ending the file). A text-level `fixup` pass, and a parse-based one, keep the recorded bugs'
shapes out of the file (below).

## Properties

- `TestHegelIdempotent`: a second `format.Source` run with the same options changes nothing.
- `TestHegelGofmtStable`: the vendored gofmt changes nothing in gofumpt's output.
- `TestHegelSyntax`: the output parses, keeps every comment's text (spacing after `//`
  aside), and its syntax tree, normalised as above, equals the input's.
- `TestHegelConstValues`: the values of the file's constants (`go/types`) are the same before
  and after formatting, on files of lone and grouped const declarations with iota.
- `TestHegelPin…`: one pin per recorded bug (expected failures).

## Bugs

Fifteen, recorded in `bugs.toml`. Grouping adjacent lone const declarations changes iota's
value in the later ones (gofumpt/1, silent corruption of the program's constants), and two
shapes reach that join only in the second run: a third-party directive comment that go/printer
respaces (gofumpt/8) and a declaration spanning lines only for a two-line empty type or literal
(gofumpt/11). Comments move: the trailing comment of a lone import ends up after the `)` of the
joined group, which is also unsorted until the second run (gofumpt/4), and a comment group
directly after two lone imports becomes a trailing comment of the `)` (gofumpt/14). The
comment-spacing rule lengthens a comment's text without moving its position, so its end spills
onto the next line: empty lines before a closing brace survive the first run and balance_calls
skips the call (gofumpt/2). Output that gofmt then changes: a var statement with a comment
before its value on the next line (gofumpt/3), a doc comment with an indented line and a
respaced last line (gofumpt/5), a one-spec var group whose opening-line comment becomes the doc
comment (gofumpt/9). Second-run changes: a one-spec var group with a comment at the end of a
block (gofumpt/6), an import group with comments and a std import to move up (gofumpt/7), an
empty type with a comment inside a parameter list (gofumpt/10), balance_calls after a trailing
comment directly followed by another multi-line declaration (gofumpt/12), group_params on types
equal only once printed (gofumpt/13), a case list collapsed only when its measured length has
shrunk (gofumpt/15).

## Modelled as recorded

Every bug has an `HZKnown` switch. While a switch is on the generator keeps away from the shape:
lone const declarations with iota get an empty line between them; empty lines between a line
ending in a respaced comment and a closing brace or parenthesis are removed, and such comments
on the closing line of a multi-line call, in a parameter list or in an import group get their
space; a var statement's comment goes after the value; adjacent lone declarations with a comment
or spanning lines, and a comment group after two lone imports, get an empty line; a doc comment
with an indented line has its last line spaced; third-party directives before lone declarations
are spaced; one-spec var groups carry no comment and get an empty line after a comment line;
import groups with a std import to move up carry no comments; a comment before the spec of a
one-spec top-level var group is not generated; empty types in parameter lists carry no comment
and stay on one line, parenthesised types are unwrapped there; a multi-line top-level
declaration with a trailing comment gets an empty line after it; a case list spanning lines
holds no expression over lines and its trailing comment has no trailing spaces. The collector
counts the avoidances; `ZOO_KNOWN_OFF=name,name` turns switches off and the properties then
fail on them.

## gofmt's business

Left out as the vendored go/printer's, not gofumpt's: the doc-comment reflow instabilities
(`//` groups with tabs and text, `/* c\n\t\n*/`, groups of empty `//` lines before code, which
go/printer drops), `x(a, //c\n)`, comment-only declaration groups and empty groups (gofmt -s
removes them), an empty struct or interface type with a comment in a result list, and
`//go:build` constraints (their sync with `// +build` lines is gofmt's).

## Not tested

The command line (`gofumpt`, `-d`, `-l`, `-w`, `-lang` and `-modpath` from go.mod, the
`GOFUMPT_SPLIT_LONG_LINES` experiment, the skipping of generated and vendored files),
`format.File` on a tree built by hand, and the rules' postconditions in themselves (that a rule
was applied where it should be: only its stability and its effect on the syntax and the
comments are checked).

## History

- 2026-09-22: new target, four properties, 15 bugs.
