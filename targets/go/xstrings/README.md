# xstrings

[huandu/xstrings](https://github.com/huandu/xstrings) is a collection of string functions
Go's `strings` lacks, most of them ports of Ruby's and Python's String methods: `Translate`,
`Delete`, `Count` and `Squeeze` with Ruby's `tr` pattern language, `Successor` (Ruby's
`succ`), `Center`, `LeftJustify` and `RightJustify` with cycling pads, `ExpandTabs`,
`Reverse`, `Slice` and `Insert` by rune index, `Partition`/`LastPartition`, `Scrub`,
`Squeeze`, `SwapCase`, `FirstRuneToUpper`/`Lower`, `Shuffle`, `WordCount`/`WordSplit`,
`Width`/`RuneWidth`, and the case conversions `ToCamelCase`, `ToPascalCase`, `ToSnakeCase`,
`ToKebabCase`. About 1 500 lines, MIT, pinned at `559cb39` (v1.6.0, 2026-09-14). README,
CONTRIBUTING.md and LICENSE are the project documents and say nothing about AI-written code.
The package's own tests are example tables; a September 2026 audit added `regression_test.go`
for six defects (#62–#67: `Successor` carries, camel-case connectors, `Translate` on invalid
bytes and NUL), all fixed at the pin.

## Build

`go test -count=1 -run TestHegel -v .` in the module root, with `ruby` installed (3.2 in
CI; the `ruby` package of Ubuntu): the tests start one Ruby process as the oracle for the
ported methods and fail without it. The patch adds `hegel_test.go` (the oracle client, the
models and the properties) and `hegel_pins_test.go` (one plain test per bug) and requires
`hegel.dev/go/hegel v0.6.33` in go.mod.

## Oracles

- **Ruby's String**, which the package ports: `length`, `reverse`, `center`/`ljust`/`rjust`
  (a pad string is repeated and cut, the left half of `center` gets the smaller share),
  `count`/`delete`/`squeeze`/`tr` (the same pattern language: ranges, a leading `^`,
  backslash escapes, a shorter `to` padded with its last rune, an empty `to` deleting),
  `succ`, `swapcase`, `partition`/`rpartition`, `insert`. The requests go over a pipe as JSON
  lines; Ruby is asked only where its semantics are the documented ones (see Accepted
  differences).
- **A model of the pattern language** as `Translate` documents it: a pattern is a list of
  runes and inclusive ranges in either direction, `^` first negates, `\` escapes; the i-th
  rune of `from` maps to the i-th of `to` or to its last rune, a rune listed twice takes the
  later mapping, a negated pattern maps everything else to the last rune of `to`, an empty
  `to` deletes. It judges the shapes Ruby rejects (descending ranges) as well.
- **Models from the documentation**: `ExpandTabs` (columns by `RuneWidth`, reset at a
  newline), `Slice` and `Insert` on the rune slice with the documented panics, `Scrub`
  (each maximal run of invalid bytes becomes `repl`), `WordSplit` (runs of letters that are
  not Han ideographs, continuing through `'` and `-`) with `WordCount` its length, the
  `Width` table (0 for controls, 2 from U+2000 except halfwidth forms).
- **Laws**: the case conversions keep every non-connector rune in order up to case;
  `ToSnakeCase` and `ToKebabCase` are idempotent, differ only in the connector, and produce
  no upper-case letters, spaces or the other connector; `ToCamelCase` and `ToPascalCase`
  differ only in the case of the first word's first rune and keep leading connectors;
  `FirstRuneToUpper`/`Lower` change only the first rune; `Shuffle` is a permutation and
  `ShuffleSource` is deterministic for a seed; the documented samples, verbatim.

## Properties

| Property | Checks |
|---|---|
| RubyPorts | strings of 0–24 runes from ASCII, Latin, Greek/Cyrillic, CJK, fullwidth, emoji, combining marks and U+FFFD: Len, Reverse (and its involution), SwapCase, Partition/LastPartition with a random or substring separator, Insert at a rune index, Center/LeftJustify/RightJustify with random lengths and pads (empty pad returns the string), Successor — all against Ruby |
| TranslatePatterns | generated from/to patterns (single runes, ranges either way, `^`, escapes, empty `to`) on such strings: Translate against the model and Ruby, `NewTranslator` reuse, `HasPattern`, `TranslateRune` rune by rune, Delete and Count against model and Ruby, Squeeze (with repeats injected) with and without a pattern against model and Ruby |
| DocumentedModels | strings with invalid bytes mixed in: ExpandTabs (tabs and newlines injected, tab sizes 1–9, the panic for 0 or less), Slice in range and the four out-of-range shapes, Insert and its panic, Scrub, WordSplit/WordCount, RuneWidth/Width/Len, Shuffle/ShuffleSource |
| CaseConversions | word-like and arbitrary strings through the four conversions: content preserved, idempotence of the lower-case forms, kebab = snake with `-`, no upper case or separators left, the camel/pascal relation, FirstRuneToUpper/Lower |
| DocumentedSamples | every sample in the package documentation (except the three wrong `Count` samples, below) |

| ScrubKeepsTheReplacementCharacter | strings holding U+FFFD among invalid bytes and other runes through Scrub: the character stays, the invalid bytes become the replacement (bug 1) |
| IdeographsAreNotWordCharacters | ideographs from the blocks added since Unicode 6.1 among letters and spaces: WordSplit/WordCount treat them as the model does (bug 2) |
| CamelCaseCapitalisesAOneLetterWord | words whose last one is a single letter through ToCamelCase/ToPascalCase (bug 3) |
| ConnectorsNextToPunctuationAreConverted | connectors inside punctuation runs through ToSnakeCase/ToKebabCase (bug 4) |
| RangeMapsOntoSingleRunes | a from range whose runes land on single runes of the to pattern, through Translate and the model (bug 5) |
| ReplacementCharacterInAPattern | patterns with a U+FFFD followed by another rune, through Translate/Delete/Count (bug 6) |

The generators draw the known bugs' shapes at their natural rates and the wide properties fail
on them naming the shape: DocumentedModels lands on bug 2 (or 1), CaseConversions on bug 3 (or
4) and TranslatePatterns on bug 5 (or 6), the last two passing a default run now and then
(intermittent). The six narrow properties, one per bug, draw the bug's region with random
contents and are the deterministic expected failures. The `TestHegelPin*` tests are regression
examples of the recorded cases. `HEGEL_NO_KNOWN=1` (read once) looks past the recorded bugs:
the shape pools drop U+FFFD and the stale ideographs, the to pattern is drawn so that no range
runs onto singles, case-conversion texts are filtered clean, and the narrow properties draw the
neighbouring region instead; every property then passes. (`XSTRINGS_COLLECT=1` records
mismatches instead of failing and prints them shortest-first with the case's description;
`HEGEL_VERBOSE=1` turns on the engine's log.)

## Bugs (6; details in bugs.toml)

| id | summary | severity |
|----|---------|----------|
| xstrings/1 | `Scrub` treats the valid rune U+FFFD as an invalid byte and replaces it; a second pass removes the markers the first wrote | medium |
| xstrings/2 | `WordCount`/`WordSplit` count CJK ideographs added since Unicode 6.1 (U+9FCD–9FFF, U+4D86–4DBF, Extensions E–I, compatibility ideographs) as word characters | low |
| xstrings/3 | `ToCamelCase` lower-cases a one-letter last word (`"point_X"` → `"pointx"`; `ToPascalCase` gives `"PointX"`) | medium |
| xstrings/4 | `ToSnakeCase`/`ToKebabCase` leave a `-` or `_` unconverted when it touches other punctuation (`"a.-b"` stays) | low |
| xstrings/5 | `Translate` leaves the last rune of a `from` range untranslated when `to` lists single runes (`Translate("abc", "a-c", "xyz")` = `"xyc"`) | medium |
| xstrings/6 | a U+FFFD listed in a pattern is dropped when another rune follows it, shifting the mapping | low |

How they were found: xstrings/1 and 2 by the first collect round of the documented models
(U+FFFD and post-2012 ideographs are in the alphabet); xstrings/3 by the camel/pascal law
(`"hk2_L"`); xstrings/4 by the kebab-equals-snake law (`"\"_"`) and the no-hyphen law; xstrings/5
by the pattern model on descending ranges (`"2-3F-Dc-fe-c"` to `"A_ #-!"`), then reduced by a
probe to `"a-c"`/`"xyz"` where Ruby agrees with the model; xstrings/6 by the pattern model with
U+FFFD in the pattern alphabet. Everything else agrees with Ruby and the models: the
justifications with cycling pads, `Successor` on ASCII, `Partition`, `Insert`, `Slice`,
`ExpandTabs`, `Squeeze`, `Delete`, `Count`, `Reverse`, the width table, `Shuffle`, and the
case conversions on ordinary identifiers.

## Accepted differences (not bugs)

- **Documentation errors**: the `Count` samples say `Count("hello", "aeiou")` is 3,
  `Count("hello", "a-k")` is 3 and `Count("hello", "^a-k")` is 2; the answers are 2, 2 and 3
  (`hello` has two vowels, `l` is not in `a-k`), and `Delete`'s samples agree with those.
- **Where the port departs from Ruby by documentation**: `Successor` treats only ASCII
  letters and digits as alphanumeric (Ruby: any Unicode letter or digit, so `"é9".succ` is
  `"ê0"`); `SwapCase` uses simple case mappings (Ruby's `"ß".swapcase` is `"SS"`); `Center`,
  `LeftJustify` and `RightJustify` return the string for an empty pad (Ruby raises); a bare
  `"^"` pattern is the negation of the empty set, every rune (Ruby: a literal `^`);
  `Squeeze` with an empty pattern squeezes everything (Ruby's `squeeze("")` nothing).
- **Undocumented pattern corners**: an unescaped `-` at the start or end of a pattern, and
  a trailing `\`, are silently ignored (`Translate("a-b", "-a", "x")` = `"x-b"`; Ruby takes
  them literally). Ruby itself mishandles a one-rune range (`"abc".tr("^z", "q-q")` is
  `"rrr"`) and a range with an escaped end, so those shapes are judged by the model only.
- `ToCamelCase`/`ToPascalCase` are not idempotent by design: a run of connectors loses one
  per pass (`"_complex__case_"` → `"_complex_Case_"` → `"_complexCase_"`) and an all-caps
  first word is lowered after its first letter (`"yU"` → `"YU"` → `"Yu"`).
- The package assumes valid UTF-8 (package documentation); functions that re-encode runes
  (`SwapCase`, `ExpandTabs` after a tab, `Squeeze`, the case conversions, `Successor`)
  turn invalid bytes into U+FFFD. Only `Scrub`, `Translate` (fixed in #65), `Reverse`,
  `WordSplit` and `Slice` are checked on invalid input.
- `Width` follows PHP's `mb_strwidth` table as documented (combining marks count 1, all of
  U+2000–U+FF60 counts 2), not Unicode's East Asian Width.

## Not tested

Performance, `Shuffle`'s randomness beyond being a permutation, and the deprecated
`stringbuilder` shim for old Go versions.
