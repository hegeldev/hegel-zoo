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
The patch adds, as the external package `re2_test`, `hegel_test.go` (harness, the `Known`
switches), `hegel_gen_test.go` (pattern and text generators), `hegel_methods_test.go`,
`hegel_experimental_test.go` and `hegel_pins_test.go` (one plain test per bug), and requires
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

Compile acceptance is compared on every pattern (a disagreement is a mismatch); patterns both
reject are counted. Mismatches are classified by method before they count: a `Known` switch per
recorded bug gates the input shape (the limit 0 is left out; `\B` is not run on texts with a
character above U+007F; POSIX patterns with a negated class are not run on texts with a
newline; the `FindAll...Submatch...` methods are compared with a positive limit only when the
pattern cannot match the empty string, decided on `regexp/syntax`'s tree); the pins assert
`regexp`'s behaviour and fail while the bug exists. `ZOO_COLLECT=1` records mismatches instead
of failing and prints the class counts.

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
