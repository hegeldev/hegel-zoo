# uniseg

[rivo/uniseg](https://github.com/rivo/uniseg) implements Unicode Text Segmentation (UAX #29:
grapheme clusters, words, sentences), Unicode Line Breaking (UAX #14) and monospace string width,
all for Unicode 15.0.0, behind `Step`/`StepString` (one call giving cluster, word/sentence/line
flags and width), the `Graphemes` iterator, `FirstGraphemeCluster`, `FirstWord`,
`FirstSentence`, `FirstLineSegment` (byte and string forms), `GraphemeClusterCount`,
`StringWidth`, `ReverseString` and `HasTrailingLineBreak`. It is the segmenter under tview,
bubbletea/lipgloss and many terminal UIs. Pinned at 087b3e4194c1 (2024-04-13, past v0.4.7). MIT.
No CONTRIBUTING.md or AI policy; not archived. Checked 2026-09-15. Upstream embeds the four UCD
break-test files as table tests plus hand-written cases.

## Oracle

A Python reference implementation of the UAX #29 grapheme (GB1–GB999), word (WB1–WB999) and
sentence (SB1–SB998) rules for Unicode 15.0, written from the annex and checked against the
UCD's GraphemeBreakTest (602 cases), WordBreakTest (1823) and SentenceBreakTest (502) with zero
mismatches before use, plus the package's documented width rules (doc.go, "Monospace Width").
It reads the UCD 15.0.0 property files (GraphemeBreakProperty, WordBreakProperty,
SentenceBreakProperty, EastAsianWidth, emoji-data), which the target's `[run] setup` fetches once
into `~/.cache/hegel-zoo/ucd-15.0.0/` with sha256 checks (`HEGEL_UCD` overrides the directory).
The child is held open over JSON lines; a request carries the code point sequence (an invalid
byte is one U+FFFD, as `utf8.DecodeRune` reports it) and returns the three boundary sets, the
documented width of every cluster and the shapes it declines to judge. Line breaking has no
reference here: `FirstLineSegment` is checked against `Step`'s flags and the LB4/LB5 mandatory
break rule.

## Properties

- `TestHegelBoundariesFollowUAX29` — text of 0–24 pieces drawn from every property class
  (controls, CR/LF/NL, Extend incl. emoji modifiers and tags, ZWJ, regional indicators, spacing
  marks, Prepend, Hangul L/V/T/LV/LVT, text- and emoji-presentation pictographs, letters of
  several scripts, katakana, quotes, mid-letter/number punctuation, numerals, ExtendNumLet,
  spaces, terminators, closers, SContinue, the em dashes) plus random code points from 20 blocks
  and invalid UTF-8: cluster ends from `Step`, `StepString`, `FirstGraphemeCluster[InString]`
  equal the reference; `FirstWord[InString]`/`FirstSentence[InString]` equal it; `Step`'s
  word/sentence flags equal it at cluster ends; the final cluster carries all three boundaries
  and `LineMustBreak`; byte and string forms agree; `GraphemeClusterCount` is the cluster count.
  Clean.
- `TestHegelWidthsFollowTheDocumentedRules` — every cluster width from `Step` and
  `FirstGraphemeCluster`, and `StringWidth` as their sum, follow doc.go's rules with
  `EastAsianAmbiguousWidth` 1 or 2. Clean.
- `TestHegelGraphemesIteratorMatchesStep` — `Graphemes` before, during and after iteration and
  after `Reset`: `Positions` (0,0 / 1,1 sentinels), `Str`, `Bytes`, `Runes`, `Width`,
  `IsWordBoundary`, `IsSentenceBoundary`, `LineBreak`, `String`. Clean.
- `TestHegelLineSegmentsMatchStepFlags` — `FirstLineSegment[InString]` cut exactly where `Step`
  flags a break opportunity at a cluster end (cuts inside clusters are noted, see uniseg/3), the
  `mustBreak` flag equals `LineMustBreak`, the last segment must break (LB3), `HasTrailingLineBreak`
  both forms agree and match the final rune, and a mandatory break in the middle follows exactly
  BK/CR/LF/NL (the two pinned shapes noted, not judged). Clean.
- `TestHegelReverseStringReversesClusters` — the clusters in reverse order; an involution when
  the reversed text re-segments into the same clusters. Clean.

What the general generators avoid or do not judge (pinned separately): text-presentation
pictograph + modifier/ZWJ sequence widths (/1), LV/LVT + trailing jamo widths (/2), word,
sentence and line boundaries inside clusters (/3), the line flag after an emoji modifier (/4),
U+FFFD after an ATerm (/5), a terminator followed by a paragraph separator (/6), a newline
followed by a hyphen and a digit (/7), a ZWJ between spaces (/8). Not judged and
not recorded: clusters starting with a V or T jamo, VS16 after a non-pictograph (doc.go is
ambiguous on both), and ZWJ + Extend/Format + pictograph for WB3c (the UCD test file has no such
case; the package keeps them in one word, the literal rule order breaks).

## Bugs

| id | severity | title |
|----|----------|-------|
| uniseg/1 | low | A text-presentation emoji followed by an emoji modifier or a ZWJ sequence keeps width 1, though the documentation says any additional code point forces width 2 |
| uniseg/2 | low | A precomposed Hangul syllable followed by a trailing jamo is one cluster of width 3 |
| uniseg/3 | low | `Step` and `Graphemes` cannot report the word, sentence and line boundaries that fall inside a grapheme cluster, so they segment differently from `FirstWord`, `FirstSentence` and `FirstLineSegment` |
| uniseg/4 | medium | A mandatory line break is reported after every emoji modifier sequence (`return prAny` where a line-break state is meant) |
| uniseg/5 | low | The SB8 sentence look-ahead stops at U+FFFD, so a replacement character or invalid byte after a period forces a sentence break |
| uniseg/6 | medium | After a sentence terminator a CR LF pair is split into two sentences, and with spaces in between the sentence ends before the CR |
| uniseg/7 | medium | A hyphen followed by a digit removes the line break opportunity before it, including the mandatory break after a newline (`&&`/`\|\|` precedence in the LB25 look-ahead) |
| uniseg/8 | low | A ZWJ between two spaces joins them into one word, though WB3d does not apply through a ZWJ |

## Not bugs

- Unicode 15.0.0 has no GB9c (Indic conjuncts): "क्क" is two clusters here, as the version
  says; the reference implements 15.0 too.
- `ReverseString` is not an involution when a leading combining mark ends up after a base
  ("́a" → "á", one cluster): inherent, and the function only promises to keep clusters intact.
- `Graphemes.Positions()` returns (1, 1) past the end: documented sentinel.
- `Step` on a single trailing rune returns a state whose property bits differ between the byte
  and string forms (StepString drops them); no observable difference on a single string.
- `EastAsianAmbiguousWidth` is a package variable read at call time: the property sets it and
  resets it after.
- A lone VS16 (U+FE0F) is width 0 (Extend): doc.go's "clusters ending with VS16 have width 2"
  is read as applying to clusters of more than one code point.
