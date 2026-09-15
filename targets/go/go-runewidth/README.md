# go-runewidth

[mattn/go-runewidth](https://github.com/mattn/go-runewidth) measures text in terminal cells:
`RuneWidth` from Unicode's East_Asian_Width and combining-mark data (tables generated from
Unicode 17.0.0), `StringWidth` over grapheme clusters (uax29 segmentation, a cluster capped at
two cells), `Truncate`/`TruncateLeft`/`TruncatePrefix`, `Wrap`, `FillLeft`/`FillRight`, a
`Condition` with the `EastAsianWidth` and `StrictEmojiNeutral` flags and an optional lookup
table, `IsEastAsian` from the locale environment, and `IsAmbiguousWidth`/`IsCombiningWidth`/
`IsNeutralWidth`. Pinned at 14205cc90ece (= v0.0.30, 2026-09-10; the release that added rune
fast paths beside the grapheme segmenter). MIT. No CONTRIBUTING.md or AI policy (SECURITY.md
only); not archived. Checked 2026-09-15. Upstream has checksum tests over the tables and
seeded random comparisons of the fast paths against a cluster loop.

## Oracle

Python 3.12's `unicodedata` (Unicode 15.0.0) held open as a child over JSON lines: the
East_Asian_Width, general category and name of a code point, from which the model applies the
generator's own rules (W/F → 2, A → 2 in an East Asian locale, Mn/Me/"COMBINING"/variation
selectors → 0, the package's hand-picked zero-width list). Code points unassigned in 15.0 are
skipped, and six ranges that changed in Unicode 15.1/16.0 are listed in the test; a probe over
every code point showed the tables equal to the 17.0.0 data files read by the generator's rules
and Python's data equal to the tables everywhere else. The string functions are modelled on the
uax29 grapheme segmenter the package uses, with its documented cluster rule, so that every fast
path (ASCII, single rune, rune loop, lookup table) is measured against the segmenter path. This
is an internal test (package `runewidth`) so the generators can sample the package's tables;
the properties call the exported API only.

## Properties

- `TestHegelRuneWidthAgreesWithUnicode` — every flag combination, with and without a lookup
  table, the package-level function, and the three classification functions agree with the
  Unicode data; invalid runes are 0; `StrictEmojiNeutral=false` can only widen a neutral rune to
  2 and only in an East Asian locale. Clean.
- `TestHegelStringWidthIsTheClusterSum` — rich text (all table classes, ZWJ/VS/skin tones,
  regional indicators, Hangul jamo, Prepend and virama sequences, tag characters, controls,
  CRLF, invalid bytes): `StringWidth` is the cluster sum under every condition, equals
  `RuneWidth` for one rune, and splitting valid text between runes never makes it narrower.
  Clean.
- `TestHegelTruncateFamilyFollowsTheClusterModel` — `Truncate`, `TruncateLeft`, `TruncatePrefix`
  with widths −2..40 and affixes (empty, ASCII, wide, combining, Prepend, invalid) equal the
  documented cell arithmetic on cluster boundaries; the result fits when the affix does. Clean.
- `TestHegelWrapFollowsTheClusterModel` — `Wrap` only inserts newlines, equals the cluster model,
  and no line exceeds the width unless it is a single cluster. Clean.
- `TestHegelFillAndConditionsAreConsistent` — `FillLeft`/`FillRight` pad by exactly the missing
  cells and reach the width; `NewCondition`/`DefaultCondition` carry the package flags;
  `CreateLUT` reproduces the plain widths and is rebuilt after the flags change. Clean.
- `TestHegelIsEastAsianFollowsTheLocaleGrammar` — `LC_ALL` > `LC_CTYPE` > `LANG`; C/POSIX/C.*
  never; a known CJK charset always; UTF-8 with ja/ko/zh; `@cjk_narrow` (any case) off. Clean.

What the general generators avoid (pinned separately): CRLF in ASCII text at `w <= 0` (/1), CJK
locales with no charset or a charset outside the package's list (/2), one-byte strings that are
not UTF-8 (/3), padding whose space joins a capped cluster (/4), text ending in an incomplete
UTF-8 sequence for the width-reaching checks (/5).

## Bugs

| id | severity | title |
|----|----------|-------|
| go-runewidth/1 | low | `Wrap` at a non-positive width breaks before a CRLF in ASCII text but not in text with other bytes |
| go-runewidth/2 | medium | `IsEastAsian` reports false for CJK locales without a charset or with a CJK charset outside its list (`ja_JP`, `zh_CN.GB18030`, `ko_KR.EUC-KR`, `zh_HK.big5hkscs`, `zh_TW.euctw`) |
| go-runewidth/3 | low | `StringWidth` of a single byte that is not UTF-8 ignores the East Asian flag: 1 cell alone, 2 cells inside longer text |
| go-runewidth/4 | low | A space or letter before a two-cell Extend rune (skin tone modifier), or after Prepend runes, is swallowed by the two-cell cluster cap, so `FillLeft`/`FillRight` come out a cell short |
| go-runewidth/5 | low | An incomplete UTF-8 sequence at the end of the text is attached to the preceding cluster and measured as zero cells |

## Not bugs

- `StrictEmojiNeutral=false` has no effect outside an East Asian locale (`runeWidthNoLUT`
  returns before the emoji table is consulted): the flag is described as a workaround for
  broken CJK fonts; the property allows it to widen only there.
- A cluster of ZWJ emoji, a flag pair or Hangul jamo is two cells however many runes it has:
  the documented cap, and what terminals do.
- `Wrap(s, w)` with `w <= 0` starts with a newline and breaks before every cluster: upstream's
  TestWrapNonPositiveWidth fixes that behaviour.
- `IsEastAsian` accepts `@cjk_narrow` in any case and `en_US.SJIS` as East Asian, and reads
  `LC_ALL`, then `LC_CTYPE`, then `LANG` without consulting `setlocale`: POSIX precedence.
- `RUNEWIDTH_EASTASIAN` is only honoured as `"1"`/other at init (`handleEnv`); not exercised
  beyond upstream's TestEnv since it rewrites the package globals.
- Runs of invalid bytes inside the text are one cluster of up to two cells in the segmenter,
  and the rune fast paths defer to it on U+FFFD: consistent between paths, and the pinned case
  (/5) is only the incomplete sequence at the very end.
- Python 3.12's `unicodedata` is Unicode 15.0.0 while the tables are 17.0.0: the 15.1 East Asian
  Width changes (trigrams, hexagrams, Tai Xuan Jing, counting rods) and the 16.0 category
  change of U+1171E are skipped by the property, not recorded.
