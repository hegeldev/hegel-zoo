# go/termenv — muesli/termenv

Terminal colour and style helpers used by lipgloss, glamour and most Bubble Tea programs:
colour profiles (`TrueColor`, `ANSI256`, `ANSI`, `Ascii`) with conversion between them,
`Style` rendering to SGR sequences, `Profile.Color` parsing, template helpers, and `Output`
querying the terminal's foreground/background colours through OSC 10/11 with a `COLORFGBG`
fallback. Pinned at 368a357 (2025-09-22, after v0.16.0). MIT; no CONTRIBUTING/AGENTS
policy; the README asks for issues.

## Oracles

- **The xterm palette**, computed rather than copied: 16 basic colours, the 6×6×6 cube
  (levels 00/5f/87/af/d7/ff), 24 greys (8+10k). `ANSI256Color(i).String()`,
  `ConvertToRGB`, and the round trip `Profile.Convert(RGBColor(hex_i)) == i` are judged
  against it.
- **The documented conversion** (tmux's `colour_find_rgb`, which the code cites): nearest
  cube colour, nearest grey from the channel average, the nearer of the two by HSLuv
  distance (the code's choice of metric); 256 → 16 is the nearest basic colour by HSLuv.
- **The SGR table**: `30+c`/`90+c-8` (+10 for backgrounds), `38;5;n`, `38;2;r;g;b`,
  attribute codes 1/2/3/4/53/5/7/9; a style is `CSI <params joined by ;> m text CSI 0 m`,
  or the bare text when there are no styles or the profile is `Ascii`.
- **X11 `rgb:` replies** on a fake TTY (`NewOutput(f, WithUnsafe(), WithTTY(true),
  WithEnvironment(env))` with a `bytes.Buffer` answering the queries): a four-digit
  `rgb:rrrr/gggg/bbbb` reply with BEL or ESC\ terminator, optional junk before it, then a
  cursor-position reply, must yield the colour and consume the whole reply; a
  cursor-only reply must fall back to `COLORFGBG` (`f;b` or `f;default;b`), then to
  ANSIColor(7)/ANSIColor(0); `screen*`/`tmux*`/`dumb` are never queried;
  `HasDarkBackground` is HSL lightness < 0.5 of the result.
- **The `NO_COLOR`/`CLICOLOR`/`CLICOLOR_FORCE` rules** from the doc comments, applied on
  top of the library's own `ColorProfile()`, plus the spot rules the comments state
  (COLORTERM truecolor → TrueColor except under screen, `yes` → ANSI256, `256color` →
  ANSI256, `dumb` → Ascii, no TTY → Ascii).

## Properties

| Test | What it checks | Finds |
| --- | --- | --- |
| `PaletteConversionsRoundTrip` | table = computed palette; Convert identities per profile; hex of entry *i* converts back to *i* | termenv/1 (grey entries convert back to a cube colour) |
| `ConvertFollowsTheDocumentedAlgorithm` | random RGB → ANSI256 equals the model; idempotence; ANSI via ANSI256; result ranges; `FromColor` | termenv/1 (25 % of random colours are nearest a grey) |
| `ColourSequencesFollowTheSGRTable` | `Sequence(bg)` of every colour kind; `ConvertToRGB` of `#rgb`/`#rrggbb` | termenv/2 (all 256 channel values are drawn) |
| `StyledFollowsTheSGRTable` | styles built through the methods in every profile vs the SGR model; `Styled` = `String`; `String(a, b)` joins with a space; `Width` | termenv/3, intermittent (a `NoColor` step in 3 % of styles) |
| `ProfileColorParsesTheDocumentedForms` | `#rgb`/`#rrggbb`/0–15/16–255/invalid strings → the converted colour or nil | termenv/4 (numbers outside 0–255 are one of five text forms) |
| `TemplateHelpersRenderStyles` | `Color`/`Foreground`/`Background`/attribute helpers vs the style model, in every profile | termenv/2, intermittent (1 % of cases) |
| `OutputReadsTheTerminalsColours` | fake-TTY OSC 10/11 replies, fallbacks, written queries, full consumption, `HasDarkBackground`, multiplexers not queried | termenv/7 (component widths 1–4, `rgba:` replies and right-length garbage are drawn; it reaches /5 and /6 too but shrinks to /7) |
| `EnvColorProfileFollowsNoColorAndCliColor` | `EnvNoColor`, `EnvColorProfile`, `NewOutput`'s profile, spot rules | — |
| `Examples` | fixed sanity examples | — |

The generators draw every recorded bug's shape by default (STYLE.md rule 11) and the wide
properties are expected failures mapped to the bug they shrink to. `hegel_shapes_test.go` adds
one narrow property per bug over its shape region with random contents, each failing every
run: `PaletteGreysConvertBackToTheirIndex` (/1), `RGBSequencesCarryEveryChannelValue` (/2),
`NoColorInAStyleIsANop` (/3), `ProfileColorRejectsNumbersOutsideThePalette` (/4),
`ColorFGBGOutsideThePaletteFallsBackToTheDefaults` (/5), `MalformedColourRepliesFallBack`
(/6, the reply panics the parser; recovered and named), `ColourRepliesOfEveryComponentWidthAreRead`
(/7). Each `TestHegelPin…` reproduces one bug as a regression example. `HEGEL_NO_KNOWN=1`
switches the known shapes off (the narrow properties then draw the neighbouring region: cube
entries, exact channels, in-range numbers, four-digit replies) and every property passes.
`TERMENV_COLLECT=1` turns failures into a tally per property.

## Bugs

| id | severity | title |
| --- | --- | --- |
| termenv/1 | medium | 256-colour conversion averages cube indices, so greys are (almost) never chosen |
| termenv/2 | low | `RGBColor.Sequence` truncates 24 of 256 channel values by one (upstream #217) |
| termenv/3 | medium | `NoColor`/invalid `RGBColor` in a Style emits an empty SGR parameter (a reset) |
| termenv/4 | medium | `Profile.Color` accepts numbers outside 0–255; the result panics in `String()` |
| termenv/5 | medium | `COLORFGBG` outside 0–15 → `ANSIColor` that panics in `HasDarkBackground` |
| termenv/6 | medium | malformed OSC reply of the right length panics the parser (upstream #144) |
| termenv/7 | low | replies judged by byte length: 2-digit/`rgba:` rejected, garbage accepted |

## Not bugs

- `Ascii.Color("#gggggg")` is `NoColor{}` while `Ascii.Color("red")` is nil: `Ascii.Convert`
  does not look at the string. Inconsistent but harmless; the property models it.
- `Profile.Color("+5")` and `"05"` are `ANSIColor(5)`: `strconv.Atoi` accepts them.
- `Style` methods do not convert colours to the style's profile; only `Profile.Color`
  converts. Documented usage.
- `HasDarkBackground()` on a non-TTY is `true` (`NoColor` converts to black).
