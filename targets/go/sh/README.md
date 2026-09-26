# sh

[mvdan/sh](https://github.com/mvdan/sh) (`mvdan.cc/sh/v3`) is the shell parser, formatter and
interpreter behind `shfmt`: POSIX sh, bash and mksh dialects, a `syntax` package with the lexer,
parser (`Parse`, `StmtsSeq`, `InteractiveSeq`, `WordsSeq`, `Document`, `Arithmetic`), AST
positions, a printer with formatting options (`Indent`, `BinaryNextLine`, `SwitchCaseIndent`,
`SpaceRedirects`, `KeepPadding`, `Minify`, `SingleLine`, `FunctionNextLine`/`BlockNextLine`),
`Simplify`, `Quote`, `Walk` and a `typedjson` encoding. BSD-3-Clause, pinned at `c6351e9` (master
2026-09-09, "doc: add a plan for v4"; v3.14.1 is the last tag). README and AGENTS.md say drive-by AI
patches are not helpful and ask for detailed issues instead; the zoo only records bugs.

## Build

`go test -count=1 -run TestHegel -v ./syntax` in the module root. The patch adds
`syntax/hegel_test.go` (the generator, the oracles and six properties) and
`syntax/hegel_pins_test.go` (one plain test per bug) and requires `hegel.dev/go/hegel v0.6.33` in
go.mod (`go get` also moved `x/mod`, `x/sync` and `x/tools` forward; go 1.26 stays). `bash`
(5.2 here) and `dash` are the oracles for the bash and POSIX dialects, run with `-n` on stdin; a
missing shell skips its checks. Upstream's own tests confirm against bash 5.3, dash, mksh and zsh.

## Oracles

- **A program generator**: one to five lines of and-or lists, pipelines (`|`, `|&`), negation,
  subshells, blocks, `if`/`while`/`until`/`for`/`for ((;;))`/`case`, functions (both spellings),
  `[[ ]]`, `(( ))`, `declare`/`local`/`export`, `time`, `coproc`, `let`, simple commands with
  assignments (arrays, appends, `x[i]=`), redirects of every operator including `{fd}>`, `&>>` and
  `>&-`, heredocs (`<<`, `<<-`, quoted and escaped delimiters, several per line), words made of
  literals, quotes, `$'...'`, `$"..."`, brace and tilde forms, every parameter-expansion operator,
  `$( )`, backquotes, process substitutions and arithmetic with all operators; comments are
  sprinkled when KeepComments is on. Every generated program is checked with the dialect's shell
  before it counts, and the generator is bounded (a command budget and depth cap) so hegel never
  runs out of choices.
- **The tree's shape**: `typedjson` with positions stripped, and a few documented printer
  normalisations removed (backquotes always print as `$( )`; comment trailing whitespace is
  trimmed; `<<-` bodies are re-indented and their tabs stripped; Minify writes `${x}` as `$x` and
  drops the last `;;`).
- **Formatting preserves the program**: parse (KeepComments), print with a random combination of
  printer options, reparse, same shape; print again, same text (idempotence); the shell accepts the
  printed program; a third of the trees also round-trip through `typedjson`.
- **Simplify is stable**: its return value says whether the tree changed; the result reparses to the
  same shape, a second `Simplify` reports no change, the shell accepts the output.
- **Quote round-trips**: `Quote(s, lang)` output, parsed as one word, expands (`expand.Literal`)
  back to `s`, and bash's `printf %s` agrees half the time; NUL and invalid UTF-8 are errors.
- **Positions match the source**: every node's `Pos`/`End` offsets, lines and columns agree with
  the source text; every statement's span reparses to the statement; `CallExpr.Args` and
  `WordIter.Items` spans reparse with `WordsSeq`.
- **Streaming parsers agree**: `StmtsSeq`, `InteractiveSeq` and `WordsSeq` yield the same nodes as
  `Parse`; `Arithmetic` agrees with `$(( ))`.
- **Broken inputs never panic**: mutated programs give `ParseError`/`LangError` (or parse, and then
  round-trip); `RecoverErrors` trees print and reparse.

## Bugs (28; details in bugs.toml)

| id | summary | severity |
|----|---------|----------|
| sh/1 | after a `let` clause a comment, `|&`, `|[` or `|{` is a parse error (Minify prints the glued forms) | medium |
| sh/2 | `time ! cmd` and `! ! cmd` are rejected; bash runs both | low |
| sh/3 | KeepPadding is not idempotent: a statement starting with a redirect grows spaces each pass; with space indentation a multi-line subshell gets trailing spaces after `(` | low |
| sh/4 | in `! a \| b` the first statement's position is the `!` | low |
| sh/5 | a heredoc body is printed inside a `$( )`, `( )`, `<( )` or backquotes that follow it on the line: an unclosed heredoc | high |
| sh/6 | a comment ending in a backslash swallows the next line (`echo a # b\` then `echo c` becomes `echo c`) | high |
| sh/7 | a comment after a heredoc redirect ending a pipeline or list is dropped or moved into a leading subshell | medium |
| sh/8 | `cat <<EOF && [[ a ]]` prints the delimiter before the body; the body becomes a command | high |
| sh/9 | `echo <(a)<(b)` prints as two words; `x[1]=<(a)` as `x[1]= <(a)` | medium |
| sh/10 | `coproc` takes its first word as a name candidate: wrong statement position, `coproc x=a x=b cmd` prints as `coproc x=b x=a cmd`, `coproc &>f x=a cmd` round-trips to a different program | medium |
| sh/11 | Minify prints `case a in b) ;; esac` as `case a in b);esac`, which does not parse | medium |
| sh/12 | `${x/}` prints as `${x//}`, then `${x///}` | low |
| sh/13 | `case aa in (a) esac`: the item has an invalid End | low |
| sh/14 | `function f ( a; )` is rejected; bash runs it | low |
| sh/15 | `"$`a`"` prints as `"$$(a)"`: the PID and a literal | medium |
| sh/16 | Simplify turns `"a${x:-"\`"}b"` into `"a${x:-'`'}b"`, an unclosed backquote | medium |
| sh/17 | `if { true & } <x1; then` prints as `if { true & } <x1 then`; the same before `do` | medium |
| sh/18 | SingleLine: `case a in a) b ;; esac; c` prints as `... esac c` | medium |
| sh/19 | SingleLine: `while a; do b & done; c` prints as `... done c`; same for `fi`, `}`, `)`, `esac` | medium |
| sh/20 | `$((+ ++x))` prints as `$((+++x))`, which the parser rejects and bash accepts; `$((+ +x))` becomes `$((++x))` | medium |
| sh/21 | SingleLine: the comment after a multi-line compound moves to its own line after a dangling `;` | low |
| sh/22 | the separator after a case statement is dropped: `{ case a in a) b ;; esac >x; }` prints as `... esac >x }` (also before `done`/`fi`), and `if $(case a in a) esac); then ]; fi` as `... esac) then ]; fi`; bash and dash reject them | high |
| sh/23 | `>$(a; return) c` formats to `>$(\n\ta; return\n) c`, which formats to `>$(\n\ta\n\treturn\n) c` | low |
| sh/24 | `RecoverErrors` panics (slice bounds out of range in `getAssign`) on `x=$((a b`, `x=$((a b))`, `x+=$((a b` | medium |
| sh/25 | Minify prints `a \| &>f b` as `a|&>f b`, which is `a \|& >f b`: stderr silently piped | high |
| sh/26 | `echo $( (a; b) )` prints with `) )`, which prints with `))`: not idempotent (also with Minify) | low |

How they were found: all by the six properties at 100 to 1000 cases, over about thirty iterations
of the generator. The shell oracle caught /2, /14, /17, /22 and the `|&`/Minify shapes of /1 (the
parser accepts what bash rejects, or rejects what bash accepts), the position property /4, /10 and
/13, the Simplify property /16, the broken-inputs property /24 (a 1 300-byte mutated program under
`RecoverErrors`, reduced to `x=$((a b`), and the rest the formatting round trip, idempotence or
comment comparison. Long cases (/17, /22, /23, /24, /26) were reduced with a ddmin and a
window-replacement reducer inside a Go test. sh/5, sh/6, sh/8, sh/22 and sh/25 silently turn a valid
script into a different or invalid one (/25 under `shfmt -mn`, the others with defaults), so they
matter most for `shfmt` users; the SingleLine ones (/18, /19, /21) affect only API users, as shfmt
has no such flag; /24 matters to editors using error recovery.

Not bugs, noted: the printer always writes backquotes as `$( )`, re-indents `<<-` bodies, trims
trailing whitespace of comments and, with Minify, drops the last `;;` and the braces of `${x}` (all
normalised away in the shape); `x[1]=v cmd` and `x=([x])` are rejected on purpose (bash errors at
run time for the first and takes `[x]` as a glob in the second); `${x~}` is undocumented; a heredoc
body line ending in `\` swallows the delimiter (bash only warns); a backslash at EOF is a literal
for the parser and printed as `\\` (upstream #1354) where bash drops it — the broken-inputs
property skips that shape; `>&-=` is accepted where bash rejects it; `a | time (b)` is accepted
where bash rejects it (bash does not treat `time` as a keyword after a pipe), and `x=a >f y=(a)` and
more than sixteen heredocs on a line are rejected by bash alone — the generator avoids those
shapes; `Parser.Incomplete` is meaningful only while a read is blocked.

The generators draw the shape of every recorded bug by default (STYLE.md rule 11): trailing
comments after `let` and on heredoc lines, `|&` after `let`, `!` inside `time`, `(`, backquotes and
`[[` after a heredoc redirect, comments ending in a backslash, glued process substitutions, coproc
commands with assignment words, empty case items and `${x/}`, `function f ( )`, backquotes after `$`,
case statements with trailing redirects, `esac` in conditions, parenthesised operands after a unary
sign, leading redirects ending in `; return`, substitutions starting with a subshell, heredoc bodies
after a `(` and near the parser's read boundary, and every printer option on every program. The five
wide properties each find several bugs; they fail on the first shape they meet and are listed in
`[expected_failures]` mapped to the basin the shrinker lands in most often (formatting on /3,
Simplify on /9, positions on /4, the broken inputs on /5, the streaming parsers on /20 and marked
intermittent, since their shapes are a few percent of cases at the default count), the pins beside
them as the regression examples. `HEGEL_NO_KNOWN=1`, read once into the `Known` switches, turns
the shapes off: the grammar stops drawing them (heredocs then sit only at line end, the region of
/5, /7 and /8), lines with a printer-mangled shape are filtered (below one percent), and every
property passes at 3000 cases.

Two found by the rewritten generators (2026-09-26): a heredoc body placed right after the `(` that
opens a subshell, a `$(` or a function's subshell body is rejected as an unclosed here-document,
where bash and dash accept it and the same body after `{` parses (/27, medium); `InteractiveSeq`
yields the statements before a heredoc twice when the heredoc sits at the parser's 1024-byte read
boundary (/28, medium).

## History

- 2026-09-17: created at `c6351e9` with 26 bugs.
- 2026-09-26: generators rewritten in combinator style (a program grammar built once per dialect
  from weighted choices, rendered by a pure writer that places heredoc bodies after the next
  newline; cases as records, mutations as a drawn list) and the known-bug gates turned off by
  default; latent model bugs of the old test fixed (the heredoc shape matched `<<<`, `<<=` and
  arithmetic `<<`; the done-redirect and substitution-subshell gates fired far too widely; the
  broken-inputs skip fired on 45% of cases). sh/27 and sh/28 recorded, found by the freed shapes
  and reproduced standalone. Oracle tolerance: bash 5.2.21 rejects a leading redirect followed by
  `&>>` with an assignment-like target, so the generator writes `&>` there.
