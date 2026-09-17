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
`hegel_test.go` (the `Known` gates, generators, the catalog model, the msgfmt/msgunfmt/Python
drivers), `hegel_props_test.go` (the properties) and `hegel_pins_test.go` (one plain test per
bug), and requires `hegel.dev/go/hegel v0.6.33` in go.mod. The reference implementations are GNU
gettext's `msgfmt` and `msgunfmt` and Python's `gettext` module (`python3`); properties needing
one skip when it is absent (the CI installs `gettext`). `HEGEL_TEST_CASES` sets the case count
(default 100; the properties run clean at 1000 in about 100 s, msgfmt and Python dominating).

## Oracles

- **Plural expressions evaluate as C** (`plurals.Compile(...).Eval(n)`): the 20 real Plural-Forms
  of the GNU manual and random C expressions (comparisons, `%`, `&&`, `||`, ternaries, random
  parentheses and spacing) evaluated at boundary and random `n` (0…45, 2^31-1, 2^32-1) by Python's
  `gettext.c2py`, the reference evaluator of the same grammar; what Python accepts, `Compile`
  must.
- **Catalogs agree with gettext**: a generated catalog (headers, contexts, plural entries with
  every degree of translation, translator/extracted comments, `#:` references, `#|` previous
  msgids, `#,` flags, `#~` obsolete entries, escapes incl. octal, multi-line strings, entries whose
  msgid begins or ends with a newline) is spelled as PO, compiled by `msgfmt` (random `--no-hash`
  and `--endianness=big`), and both `Po.Parse` of the text and `Mo.Parse` of the MO answer
  `Get`/`GetC`/`GetN`/`GetNC` for every entry (own and foreign contexts, ten values of n) and a
  missing id as Python's `GNUTranslations` does on the MO; `Po` and `Mo` agree with each other;
  `IsTranslated*` agree with the entry's msgstr; `Headers`, `Language` and `PluralForms` read
  back. Where Python and C libintl differ the property accepts either (see below).
- **MarshalText round-trips**: `Po.Parse` → `MarshalText` → `Po.Parse` gives the same domain
  (headers, translations, contexts, references); `msgfmt` accepts the output; a second
  `MarshalText` is identical.
- **msgunfmt agrees with Mo**: `msgunfmt` of the compiled MO, parsed as PO, gives the same domain
  as `Mo.Parse`.
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

## Bugs (7; details in bugs.toml)

| id | summary | severity |
|----|---------|----------|
| gotext/1 | the PO parser uses `#, fuzzy` translations (msgfmt and GNU gettext leave them out; `Mo` disagrees with `Po` on the same catalog) | medium |
| gotext/2 | `GetN` answers an untranslated plural lookup by the catalog's plural rule instead of `n == 1` (French `GetN(missing, missings, 0)` is `missing`; `GetNC`, `Locale` and GNU give `missings`) | low |
| gotext/3 | `GetN`/`GetNC`/`AppendN` of a singular entry return `""` for a plural index other than 0 (libintl gives the translation, Python the plural msgid) | medium |
| gotext/4 | `IsTranslated` of a translated singular entry is false when the catalog's plural index of 1 is not 0 (Arabic) | low |
| gotext/5 | `plurals`: a bare `n` or `n % k` test means `n == 1` / `n % k == 0`, and `Compile("n").Eval(2)` is 0; upstream tests codify it | low |
| gotext/6 | `MarshalText` keeps only the first byte of every multi-byte character (`naïve` → `na\xc3ve`, invalid UTF-8) | high |
| gotext/7 | `MarshalText` writes a backslash before a quote as `\"`, which reads back as `"` | medium |

How they were found: /1 to /4 by the msgfmt/Python property in its first hundred cases (Po
against the oracle and against Mo; empty answers; `IsTranslated` against msgstr), /5 by the
`c2py` property as soon as bare tests were generated, /6 by the MarshalText property on its first
non-ASCII catalog and /7 by the same property at 2 of 100 catalogs; each reduced to a one-line
probe. gotext/5 matches upstream's `TestCompileEvalGNUExpressions` ("implicit equality", "modulo
default"), so it may be intended; real Plural-Forms never use a bare test.

Not bugs, noted: `Get` of a plural entry returns msgstr[0] (C libintl agrees; Python's gettext
returns the form for `plural(1)`); an entry with an empty translated form answers the msgid or
plural msgid where GNU gettext returns `""` (a documented choice); an entry with an empty
msgstr[0] and other forms filled is used by the PO parser but is untranslated to msgfmt (so `Po`
and `Mo` differ — the property allows it); `GetN` of a singular entry for index 0 returns the
translation as libintl does; the `!` operator is not supported in plural expressions (not
generated; no real Plural-Forms uses it); `MarshalText` sorts headers in xgettext's order and
entries by their first reference, context and id, and rewrites escapes (`\x` hex escapes are not
generated: C swallows following hex digits where Go reads two; `\'` is rejected by both msgfmt
and Go); `msgunfmt` prints nothing for a header-only MO; `SimplifiedLocale` strips `:`, `@`, `.`
suffixes and spaces.

Gates while the bugs are open (`Known` in hegel_test.go): no entry is fuzzy (/1); an
untranslated plural lookup accepts either msgid when the oracle and gotext both answered a msgid
(/2); plural lookups of singular entries that answered `""` are skipped (/3); `IsTranslated` of
singular entries is not checked when plural(1) != 0 (/4); no bare tests are generated (/5); the
MarshalText property maps non-ASCII runes to ASCII (/6) and removes backslashes before quotes
(/7). The properties run clean at 1000 cases.

## History

- 2026-09-17: created at `fd7620c` with 7 bugs.
