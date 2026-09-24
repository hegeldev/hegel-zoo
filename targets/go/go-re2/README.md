# go-re2

[wasilibs/go-re2](https://github.com/wasilibs/go-re2) is a drop-in replacement for Go's
`regexp` package backed by Google's C++ RE2, compiled to WebAssembly and then to Go (or, with
a build tag, wrapped through cgo), for speed on large inputs. Its README promises the `regexp`
API and behaviour "with just a few behavior differences" (invalid UTF-8 in the input, which RE2
stops at, and `reflect.DeepEqual` on `Regexp` values), and an `experimental` package with
`CompileLatin1` and pattern sets. The pin is `7f13331` (2026-09-15, seventeen commits after
`v1.12.0`).

The repository has LICENSE (MIT); the README, RATIONALE.md and CODE_OF_CONDUCT.md say nothing
about AI-written code, there is no CONTRIBUTING.md and no agent instructions. The zoo keeps its
tests in its own patch and files nothing upstream.

## Build

`GOWORK=off go test -count=1 -run TestHegel -v .` in the module root, with the default wasm2go
build (no cgo, nothing to install; the first build compiles the generated RE2 module, about ten
seconds). `GOWORK=off` because upstream carries a `go.work` (the root module and `./build`) and
workspace mode refuses the zoo's `GOFLAGS=-mod=mod`.
The patch adds, as the external package `re2_test`, `hegel_test.go` (harness, the
`HEGEL_NO_KNOWN` switch), `hegel_gen_test.go` (pattern and text generators), `hegel_methods_test.go`,
`hegel_experimental_test.go`, `hegel_shapes_test.go` (one narrow property per recorded bug) and
`hegel_pins_test.go` (one plain test per bug), and requires
`hegel.dev/go/hegel v0.6.33` in go.mod. RE2 logs every pattern it rejects to stderr
(`E0000 ... re2.cc:242] Error parsing ...`); those lines are noise from the patterns both
packages reject, not failures. Not to be run under `ulimit -v`: the wasm2go runtime reserves
its module memory up front and, refused, panics with a nil interface conversion in
`getChildModule`.

## Oracles

- **Go's `regexp`**, the package go-re2 replaces. Both implement the RE2 syntax with
  leftmost-first semantics (leftmost-longest after `Longest` and under `CompilePOSIX`), so on a
  pattern both accept and a valid UTF-8 text every method must return the same value, nil and
  empty slices included. The generator draws patterns from the shared grammar: literals in
  their several spellings (`\x41`, `\x{1f600}`, `\141`, `\Q...\E`), `.`, `\d \w \s` and
  negations, Unicode classes (`\pL`, `\p{Greek}`, `\P{Han}`, `\p{^Lu}`, `\p{Any}`), bracket
  classes with ranges, POSIX names and escapes, `^ $ \A \z \b \B`, capturing, named
  (`(?P<n>`, `(?<n>`, duplicate names), non-capturing and flag groups, bare flag settings
  (`(?i)`, `(?ms)`, `(?U)`, `(?-i)`), greedy and lazy `* + ? {n} {n,} {n,m}`, alternation with
  empty branches; texts over `a b A B k K K(U+212A) s S ſ 0 1 space \n - _ é É 日 😀 .`, so
  that simple case folding, ASCII word boundaries next to non-ASCII letters and three- and
  four-byte characters all occur. Replacement templates mix literal text, `$$`, `$n`, `${n}`,
  `$nx`, `${name}`, references to groups that do not exist and malformed `$`.
- **Each pattern's own `MatchString`** for `experimental.CompileSet`: the set must report
  exactly the patterns that match, and with a limit n at most n of them, all matching.
- **`regexp` on the UTF-8 text** for `experimental.CompileLatin1`: the same characters (all
  below U+0100) given to go-re2 as Latin-1 bytes must give the same matches, offsets mapped
  between the encodings.

## Method

| Property | Checks |
|---|---|
| MethodsAgreeWithRegexp | `String`, `NumSubexp`, `SubexpNames`, `SubexpIndex`, `Match`/`MatchString`, the four `Find` and four `FindSubmatch` methods, the eight `FindAll` methods and `Split` with n ∈ {-1, 1, 2, 3}, the six `ReplaceAll` methods (with the sequence of calls a `Func` sees), `Expand`/`ExpandString` on `regexp`'s match, on string and `[]byte` inputs |
| LongestAgreesWithRegexp | after `Longest()`: `MatchString`, `FindStringSubmatchIndex`, `FindAllStringSubmatchIndex`, `FindAllSubmatch(2)`, `ReplaceAllString`, `Split`; `Longest` twice |
| POSIXAgreesWithRegexp | `CompilePOSIX` on generated ERE patterns: acceptance, `NumSubexp`, first and all matches, `ReplaceAllString`, `Split` |
| PackageFunctionsAgreeWithRegexp | `MatchString`, `Match` and their errors, `QuoteMeta` (and matching the quoted text), `MustCompile` panics on the same patterns, `Copy` gives the same results |
| SetAgreesWithEachPattern | `CompileSet` of 1–4 patterns: `FindAllString`/`FindAll` with n = -1 equal the set of matching patterns, n = 0 gives nil, a positive n gives min(n, matching) of them |
| Latin1AgreesWithRegexp | `CompileLatin1`: acceptance, `FindAllStringSubmatchIndex` (offsets transcoded) and `MatchString` against `regexp` on the UTF-8 text |
| FindAllWithZeroLimitAgreesWithRegexp | a `FindAll` method with n = 0 on a generated pattern and text gives nil, as `regexp` does (go-re2/1) |
| NonBoundaryOnMultiByteTextAgreesWithRegexp | a pattern with `\B` on a text with a word character before a multi-byte character (go-re2/2) |
| POSIXNegatedClassOnNewlineAgreesWithRegexp | a POSIX pattern with a negated class on a text containing a newline (go-re2/3) |
| SubmatchLimitPastEmptyMatchAgreesWithRegexp | a `FindAll...Submatch...` method with a positive limit on a nullable pattern whose text has an empty match before a non-empty one (go-re2/4) |

Compile acceptance is compared on every pattern (a disagreement is a mismatch); patterns both
reject are counted. The generators draw the recorded bugs' shapes by default: the limit 0 is
among the `FindAll` limits (about half of Methods' cases, so Methods fails every run on go-re2/1
and shrinks to `FindAllString("", 0)`), texts beside `\B` include multi-byte characters, POSIX
negated classes run on texts with newlines, and the Submatch methods are compared with positive
limits on nullable patterns too; a mismatch names the bug whose shape it has. The wide
properties reach /2, /3 and /4 rarely (0.1-0.5% of cases: Longest is an intermittent expected
failure for /4, the wide POSIX property for /3, and PackageFunctions and Set can reach /2 only
in principle), so each bug also has a narrow property in `hegel_shapes_test.go` over its shape
region with random contents, which fails every run; the pins assert `regexp`'s behaviour beside
them. `HEGEL_NO_KNOWN=1` switches the shapes off for a run that looks past the bugs: the limit 0
is left out, a pattern with `\B` draws its texts from a pool without characters above U+007F, a
POSIX pattern with a negated class from a pool without a newline, and a /4-shaped mismatch is
skipped (under 1% of Methods' and Longest's cases); every property then passes.

## Accepted differences

- Syntax RE2 accepts and Go rejects, or the reverse, kept out of the generator: `\C` (any
  byte), repeat counts beyond the Go limit spelled with more digits than fit (`a{9876543210}`,
  a documented gap; both reject `a{1001}`), non-ASCII group names (`(?P<é>x)`), `\p{Cn}` (Go
  only). Error messages differ in wording ("bad repitition argument" against "invalid repeat
  count"); only acceptance is compared.
- Invalid UTF-8 in the text: documented ("this library will stop consuming strings when
  encountering invalid utf-8"); the texts are valid UTF-8.
- `CompileLatin1` rejects `\x{17f}` and other code points above U+00FF in a Latin-1 pattern;
  the Latin-1 generator stays below U+0100.
- `reflect.DeepEqual` on two `Regexp` values: documented; not compared.

## Bugs found

Four, in bugs.toml: the `FindAll` methods return every match when n is 0 (`regexp`: nil); `\B`
matches between the bytes of a multi-byte character, so `Split` and `ReplaceAll` cut characters
into invalid UTF-8 and `MatchString` (and a `Set`) says true where `regexp` says false;
`CompilePOSIX` lets a negated class match a newline; the
`FindAll...Submatch...` methods count a skipped empty match against a positive n and return too
few matches.

## History

- 2026-09-21 (turn 337): target added at 7f13331 (v1.12.0+17) with six properties, 4 pins.
- 2026-09-23: generators rewritten in combinator style: the pattern is a syntax tree drawn by
  a recursive `Composite` and rendered by a pure function, three dialects replace the
  perl/latin/posix flags, the known-bug skips became the text pool per pattern, and the
  `ZOO_COLLECT` collector is gone. The PackageFunctions property, which had no go-re2/2
  gate, now shares the pool. No new bug.
- 2026-09-24: unsteered (STYLE.md rule 11): the known shapes are drawn by default, Methods and
  (intermittently) Longest and POSIX are the expected failures with four narrow properties in
  `hegel_shapes_test.go`; `HEGEL_NO_KNOWN=1` switches the shapes off; the `Known` struct is gone.
