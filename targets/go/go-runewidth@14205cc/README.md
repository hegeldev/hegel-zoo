# go-runewidth@14205cc

A sibling of [`go-runewidth`](../go-runewidth/README.md) kept at base `14205cc90ece` (v0.0.30,
2026-09-10) so that the five bugs recorded there, all fixed upstream since (#114, #115, #116),
keep reproducing under the pinned Hegel: the zoo doubles as an evaluation of Hegel's bug finding
and shrinking, which needs failing suites. The base is pinned (`zoo bump` and `zoo drift` skip
it); `zoo bump-hegel` moves it with every other target. It has no `bugs.toml`: its expected
failures map to `go-runewidth`'s bug ids, which TROPHIES.md counts once.

The test is the main target's as it stood before the bump, with the steering taken off: the
generators draw the recorded shapes by default (CJK locales with no charset or one outside the
package's list, one-byte strings that are not UTF-8, cuts anywhere in any text, padding beside
skin tone modifiers and Prepend runs, texts ending in an incomplete sequence, CRLF in ASCII text
at non-positive widths). The oracle is the same Python child (`unicodedata`, `uax29`) and the
same cluster model.

## Which property finds which bug

| bug | property (expected failure) | shrinks to |
|---|---|---|
| go-runewidth/1 | `TestHegelWrapKeepsCRLFTogether` | `Wrap(" \r\n", 0)` = `"\n \n\r\n"` |
| go-runewidth/2 | `TestHegelIsEastAsianFollowsTheLocaleGrammar` | `LC_ALL="ja"` reported not East Asian |
| go-runewidth/3 | `TestHegelOneByteStringMeasuresAsItsRune` | `StringWidth("\x80")` = 1 in an East Asian locale, want 2 |
| go-runewidth/4 | `TestHegelExtendAndPrependRunesAddTheirOwnCells` | `StringWidth("\u0600\u0600 ")` = 2, want 3 |
| go-runewidth/5 | `TestHegelIncompleteSequenceAtTheEndKeepsItsCells` | `StringWidth(" \xc2")` = 2 in an East Asian locale, want 3 |

The narrow properties draw one bug's shape region each with random contents around it. The wide
properties reach the bugs at their natural rates and are intermittent expected failures at 100
cases: `TestHegelTruncateFamilyFollowsTheClusterModel` shrinks to the `"\xff"` affix of /3
(`Truncate("   ", 2, "\xff")` three cells wide), `TestHegelFillAndConditionsAreConsistent` to
`FillLeft("\U0001f3fb", 9)` eight cells wide (/4), `TestHegelStringWidthIsTheClusterSum` to the
lone byte of /3 or a halves cut ending in an incomplete sequence (/5, the shape only it draws;
mapped there), and `TestHegelWrapFollowsTheClusterModel` to `Wrap("\r\n", -1)` (/1), which it
reaches about once in 5000 cases. At 1000 cases the first three fail in every run.

`HEGEL_NO_KNOWN=1` switches the shapes off, for a run that looks past the bugs: the locale
grammar draws only listed charsets, the affix pool loses `"\xff"`, skin tones, multiple
Prepends, `w <= 0` with CRLF and incomplete tails are not drawn, and the remaining skips are
rare (one-byte strings 0.14%, CRLF at `w <= 0` 0.02%, halves cut inside an incomplete tail
1.9%, Fill measure beside a joining rune 2.3% left, 0.3% right). Every property then passes at
1000 cases; the five pins keep failing.

Not drawn (correct answer unrecorded): a CJK language with a non-CJK charset
(`ja_JP.ISO-8859-1`) and a non-CJK language with an unlisted CJK charset (`en_US.GB18030`).

## History

- 2026-09-24: scaffolded from `go-runewidth` at 14205cc90ece when go-runewidth/1-5 were fixed
  upstream; unsteered the same day (five narrow properties added, the wide ones intermittent).
