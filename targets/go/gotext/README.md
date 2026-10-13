# gotext

[leonelquinteros/gotext](https://github.com/leonelquinteros/gotext) is a GNU gettext
implementation for Go: parsers for `.po` and `.mo` catalogs (`Po`, `Mo`, the shared `Domain`),
lookups with contexts and plurals (`Get`, `GetC`, `GetN`, `GetNC`, `Append*`, `IsTranslated*`),
`Locale` (files found under `<path>/<lang>/LC_MESSAGES/<domain>.po|mo` for several domains), the
package-level global locale, `MarshalText`/`MarshalBinary` serialisers and a compiler of C
`Plural-Forms` expressions (`plurals`). MIT (the `plurals` package BSD-3, from `x/text`), pinned
at `fd7620c` (master 2026-09-02, "Merge pull request #140"; v1.7.2 is the last tag, 48 commits
behind). AGENTS.md admits "human or AI agent" contributors under its guidelines; the zoo only
records bugs.

## Build

`go test -count=1 -run TestHegel -v .` in the module root (package `gotext_test`). The patch adds
`hegel_zoo_idioms_test.go` (the generator idioms shared with the other Go targets),
`hegel_zoo_test.go` (the harness, the judge, the classifier, the `known` switches, the oracle
drivers, `describeDomain`), `hegel_zoo_catalogs_test.go` (the catalog record and its generators,
the PO spelling), `hegel_zoo_plurals_test.go` (the plural-expression records, generators,
renderers and the two evaluators), `hegel_zoo_lookup_test.go` (the lookup model and the catalog
property), `hegel_zoo_marshal_test.go` (the MarshalText model and the round-trip, msgunfmt, gob
and broken-input properties), `hegel_zoo_locale_test.go` (the Locale lookup on disk),
`hegel_zoo_shapes_test.go` (one narrow property per recorded bug) and `hegel_pins_test.go` (one
plain test per bug), and requires `hegel.dev/go/hegel v0.6.33` in go.mod. The reference
implementations are GNU gettext's `msgfmt` and `msgunfmt` and Python's `gettext` module
(`python3`); properties needing one skip when it is absent (the CI installs `gettext`).
`HEGEL_TEST_CASES` sets the case count (default 100), `HEGEL_SEED` the seed, `HEGEL_COLLECT=1`
makes a property record its mismatches and print the counts instead of failing, and
`HEGEL_NO_KNOWN=1` looks past the recorded bugs (below).

## Oracles

- **Plural expressions evaluate as C** (`plurals.Compile(...).Eval(n)`): the 20 real Plural-Forms
  of the GNU manual and random C expressions (comparisons, `%`, `&&`, `||`, ternaries, bare tests,
  random parentheses and spacing) evaluated at boundary and random `n` (0…45, 2^31-1, 2^32-1) by
  Python's `gettext.c2py`, the reference evaluator of the same grammar; what Python accepts,
  `Compile` must. (`c2py` is not C for a bare operand - `n || x` evaluates to `n` there - so the
  oracle is asked the normalised spelling with `!= 0` tests and the library the bare one; a Go C
  evaluator of the drawn tree is checked against Python on every expression.)
- **Catalogs agree with gettext**: a generated catalog (headers, contexts, plural entries with
  every degree of translation, fuzzy entries, translator/extracted comments, `#:` references,
  `#|` previous msgids, `#,` flags, `#~` obsolete entries, escapes incl. octal, multi-line
  strings, entries whose msgid begins or ends with a newline) is spelled as PO, compiled by
  `msgfmt` (random `--no-hash` and `--endianness=big`), and both `Po.Parse` of the text and
  `Mo.Parse` of the MO answer `Get`/`GetC`/`GetN`/`GetNC` for every entry (own and foreign
  contexts, ten values of n) and a missing id as Python's `GNUTranslations` does on the MO; `Po`
  and `Mo` agree with each other; `IsTranslated*` agree with the entry's msgstr; `Headers`,
  `Language` and `PluralForms` read back. The model is the oracle's answers plus the documented
  differences below, a set of acceptable strings per query and side.
- **MarshalText round-trips**: the model states what `Po.Parse` must read from the catalog
  (headers, translations, contexts, references) and both the parsed catalog and `Po.Parse` of its
  `MarshalText` are compared with it; `msgfmt` accepts the output; a second `MarshalText` is
  identical.
- **msgunfmt agrees with Mo**: `msgunfmt` of the compiled MO, parsed as PO, gives the same domain
  as `Mo.Parse`, and both match the model's statement of the entries msgfmt compiles.
- **Binary round-trips**: `Po.MarshalBinary`/`UnmarshalBinary` and `Locale` with two translators
  through the gob encoding keep every lookup.
- **Locale finds the documented file**: for a random language tag (`de_DE.UTF-8@euro` and the
  like), domain and set of files placed at `<lang>/LC_MESSAGES/`, `<ll>/LC_MESSAGES/`, `<lang>/`
  and `<ll>/` in `.po` and `.mo`, `Locale.AddDomain` uses the first of the documented candidates
  (po before mo, the most specific place first), `GetActualLanguage` names the language whose
  file was found, `GetLanguage` is the simplified tag and `GetDomain`/`GetD` answer by domain.
- **Broken inputs never panic**: mutated PO text, mutated MO bytes and mutated plural
  expressions (deleted, duplicated, swapped and injected pieces) parse, fail or answer, in
  `Po.Parse`, `Mo.Parse`, `Locale` and `plurals.Compile`/`Eval`.

The cases are records drawn from package-level generators (a catalog is a Plural-Forms choice,
a language, the optional headers, a drawn header order, the file comments, a counted list of
entry records - context at 30 percent, plural at 45 with the three translation modes, fuzzy at
12, references at 35, comments, previous msgid and flags - with the (context, msgid) keys made
distinct and the newline edges msgfmt checks fixed by a pure function after the draw; a text is
a pool word at 60 percent or one to six pieces; the spelling - one-line or split strings, the
separator, octal escapes on 3 percent of the letters, the obsolete entry - is a record drawn
beside the catalog; a plural expression is a tree of bounded depth rendered with a drawn spacing);
every rate is measured over 3000 cases and written beside its weight. The oracle (msgfmt, then
Python) is asked once per case before the library, and the model is a pure function of the case,
the oracle's answers and the switch set.

## Bugs (8; details in bugs.toml)

| id | summary | severity |
|----|---------|----------|
| gotext/1 | the PO parser uses `#, fuzzy` translations (msgfmt and GNU gettext leave them out; `Mo` disagrees with `Po` on the same catalog) | medium |
| gotext/2 | `GetN` answers an untranslated plural lookup by the catalog's plural rule instead of `n == 1` (French `GetN(missing, missings, 0)` is `missing`; `GetNC` and GNU give `missings`; `Locale.GetN` and `AppendN` follow the rule too) | low |
| gotext/3 | `GetN`/`GetNC`/`AppendN` of a singular entry return `""` for a plural index other than 0 (libintl gives the translation, Python the plural msgid) | medium |
| gotext/4 | `IsTranslated` of a translated singular entry is false when the catalog's plural index of 1 is not 0 (Arabic, the only such rule of the twenty) | low |
| gotext/5 | `plurals`: a bare `n` or `n % k` test means `n == 1` / `n % k == 0`, and `Compile("n").Eval(2)` is 0; upstream tests codify it | low |
| gotext/6 | `MarshalText` keeps only the first byte of every multi-byte character (`naïve` → `na\xc3ve`, invalid UTF-8; the reparse reads U+FFFD per byte and corrupted msgids collide) | high |
| gotext/7 | `MarshalText` writes a backslash before a quote as `\"`, which reads back as `"` (one backslash lost per round trip) | medium |
| gotext/8 | the PO parser never clears its reference buffer: an entry without `#:` lines inherits the previous entry's references, and `MarshalText` persists them | medium |

How they were found: /1 to /4 by the msgfmt/Python property in its first hundred cases (Po
against the oracle and against Mo; empty answers; `IsTranslated` against msgstr), /5 by the
`c2py` property as soon as bare tests were generated, /6 by the MarshalText property on its first
non-ASCII catalog and /7 by the same property at 2 of 100 catalogs; each reduced to a one-line
probe. /8 by the MarshalText property at the rewrite (2026-10-13), once its model stated each
entry's references instead of comparing the library with itself. gotext/5 matches upstream's
`TestCompileEvalGNUExpressions` ("implicit equality", "modulo default"), so it may be intended;
real Plural-Forms never use a bare test.

Not bugs, noted (the documented differences, members of the model's expected sets): `Get` of a
plural entry returns msgstr[0] (C libintl agrees; Python's gettext returns the form for
`plural(1)`); an entry with an empty translated form answers the msgid or plural msgid where GNU
gettext returns `""` (a documented choice); an entry with an empty msgstr[0] and other forms
filled is used by the PO parser but is untranslated to msgfmt (so `Po` and `Mo` differ); `GetN`
of a singular entry for index 0 returns the translation as libintl does; the `!` operator is not
supported in plural expressions (not generated; no real Plural-Forms uses it); `MarshalText`
sorts headers in xgettext's order and entries by their first reference, context and id, and
rewrites escapes (`\x` hex escapes are not generated: C swallows following hex digits where Go
reads two; `\'` is rejected by both msgfmt and Go); `msgunfmt` prints nothing for a header-only
MO; `SimplifiedLocale` strips `:`, `@`, `.` suffixes and spaces; a `#, fuzzy` line before the
header entry is kept by msgfmt and Python alike.

## Properties and the recorded bugs

The model states the documented behaviour; the shape of every recorded bug is drawn by default at
its natural rate and named by the classifier, which runs the model per switch of `known` (eight
switches, one per bug, off by default; each replica transcribed from the library's lines: po.go's
`#,` handling and reference buffer, domain.go's `GetN`, `IsTranslated` and
`EscapeSpecialCharacters`, translation.go's `GetN`, plurals/compiler.go's bare tests) before the
library is called - sufficiency first (the one switch that changes the expected values), then
necessity, then a hole, which never occurs: over 3000 default cases the catalog property names
2786 (gotext/2 1074, /1 932, /3 780; /4 is always inside a /2 case, since every Arabic catalog's
missing-msgid lookups at n = 1 fall back by the rule first), the MarshalText property 2305
(/6 2289, /7 16, /8 129: an entry with references followed by one without is drawn in 54 percent
of its catalogs, but a non-ASCII string in the same catalog names the case first) and the
expression property 1277 (/5), the library agreeing with the replica on every named case. The wide
properties fail by the shape they shrink to over forty rounds at a hundred cases:
`TestHegelExpressionsEvaluateAsC` by gotext/5 (forty of forty), `TestHegelCatalogsAgreeWithGettext`
by gotext/2 (thirty-five: a missing msgid looked up under a non-Germanic rule is the simplest
failing case; gotext/3 four, gotext/1 one) and `TestHegelMarshalTextRoundTrips` by gotext/6
(thirty-eight: one non-ASCII entry; gotext/7 and gotext/8, two entries with a reference on the
first, once each). Eight narrow properties, one per bug, draw the bug's region with random
surroundings and fail every run:
`TestHegelFuzzyEntriesAreLeftOut`, `TestHegelUntranslatedPluralsFallBackByOne`,
`TestHegelSingularEntriesAnswerPluralLookups`, `TestHegelIsTranslatedIgnoresThePluralRule`,
`TestHegelBareTestsAreNonZeroTests`, `TestHegelMarshalTextKeepsNonASCII`,
`TestHegelMarshalTextRoundTripsBackslashBeforeQuote` and
`TestHegelReferencesStayWithTheirEntry`; the pins are the fixed examples beside them. The other
four properties pass.

`HEGEL_NO_KNOWN=1` switches the shapes off and every property but the pins passes: fuzzy entries
and bare tests are not drawn (weight zero), the MarshalText property draws ASCII text only and
rejects the catalogs holding a backslash before a quote (9 percent) and draws references on every
entry of a catalog or none (36 percent of the entries carry references, as by default); the
catalog property keeps every case and drops the checks the shapes
of gotext/2, 3 and 4 cover - the plural lookups of a missing msgid or an untranslated entry at an
n whose index differs from the Germanic rule, the plural lookups of singular entries at an index
other than 0, `IsTranslated` under the Arabic rule - about 9 percent of its checks, in 91 percent
of its cases; the narrow properties draw the region past their shape and pass.

## Shrinking

A shrink attempt here costs an msgfmt and a Python process, so the harness bounds a failure's
shrink by a budget of failing judgements and ends it with an undrawn rejection (the mergo
precedent); a default run takes about a minute, a thousand cases under two.

## History

- 2026-09-17: created at `fd7620c` with 7 bugs.
- 2026-10-13: rewritten to the standard (the six `Known` gates on by default turned into eight
  switches off by default, the generators as records with measured rates, eight narrow
  properties); gotext/8 found by the MarshalText model; the notes of gotext/2, 6 and 7 corrected
  after standalone checks.
