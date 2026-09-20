# culori

[culori](https://github.com/Evercoder/culori) is a colour library for JavaScript: thirty colour
spaces (sRGB and the other CSS predefined RGB spaces, CIE Lab/LCh in D50 and D65, Luv, Oklab/Oklch,
Okhsl/Okhsv, Jzazbz, ICtCp, DIN99o, cubehelix, HSL/HSV/HSI/HWB, XYB, YIQ), a CSS Color Level 4
parser and serializers, interpolation with the CSS Images colour-stop rules, gamut mapping, colour
differences, blending, WCAG contrast and colour-deficiency filters. Pinned at 4.0.2, 435a1fc
(2026-07-02), MIT.

The library is plain ESM run straight from `src/` with no build and no runtime dependencies;
Hegel and the oracle (colorjs.io 0.7.1) are installed under `.hegel/` so the package's own lock
file stays untouched. Tests: `hegel/hegel.test.mjs`, run with `node --test`. `ZOO_FULL=1` widens
the generators to the shapes that hit known bugs (the differential properties then report them
as counted mismatches instead of gating them); `ZOO_COLLECT=1` prints mismatch statistics.

## Properties

| Test | Checks |
| --- | --- |
| `TestHegelConversionsAgreeWithColorjs` | in-gamut sRGB converted to 20 shared spaces agrees with colorjs.io; rec2020 both ways and sRGB to HSL agree with the CSS Color 4 sample code |
| `TestHegelEveryModeRoundTripsRgb` | rgb to every mode and back is the identity (with per-space tolerances); converting via an intermediate mode gives the same colour as converting directly |
| `TestHegelParseFollowsCssColor4` | generated CSS colour strings (hex, named, legacy comma, modern space-separated, `color()` with every profile, hue units, `none`, alpha, whitespace) parse to the expected colour; mutated strings return undefined |
| `TestHegelFormatFollowsTheDocumentation` | `formatCss`/`formatHex`/`formatHex8`/`formatRgb`/`formatHsl` match a model of the documented output; `parse(formatCss(c))` gives back `c` up to the documented clamping |
| `TestHegelInterpolateFollowsTheDocumentation` | `interpolate` with positions, hints, easings and hue fixups equals a model of the documented algorithm (CSS Images 4 position fixup, shorter hue arc, alpha fixup) |
| `TestHegelAverageFollowsTheDocumentation` | `average` is the per-channel arithmetic mean, circular for hue channels |
| `TestHegelBlendFollowsTheSpecification` | `blend` equals the Compositing and Blending Level 2 separable formulas with source-over alpha |
| `TestHegelDifferencesAgreeWithColorjs` | `differenceCie76/Ciede2000/Hyab/Cmc` equal colorjs.io's formulas on the same Lab numbers; ITP, Oklab and Euclidean differences match their definitions; differences are symmetric and zero on equal colours; `nearest` agrees with a brute-force sort |
| `TestHegelGamutFunctionsAreSound` | `displayable`/`inGamut` agree with the channel ranges; `clampRgb`, `clampGamut`, `clampChroma` and `toGamut` return in-gamut colours and leave in-gamut colours alone |
| `TestHegelWcagAgreesWithColorjs` | `wcagLuminance` and `wcagContrast` agree with colorjs.io |
| `TestHegelFiltersFollowTheSpecification` | the Filter Effects matrices (`filterBrightness`, `filterContrast`, `filterSepia`, `filterSaturate`, `filterGrayscale`, `filterInvert`, `filterHueRotate`) match the specification, filters keep alpha, and severity 0 deficiency filters are the identity |

Pins (`TestHegelPin*`) reproduce the bugs in `bugs.toml` and are listed as expected failures.

## Oracles

- colorjs.io 0.7.1 for the shared colour spaces, the Lab-based difference formulas and WCAG. Its
  Lab/LCh (D50) differ from culori's in matrix precision by up to 4e-5, its Okhsl/Okhsv by up to
  2e-3 (both approximate the sRGB gamut boundary); Jzazbz by 5e-4 (culori/19). colorjs 0.7.1
  implements rec2020 with a different transfer function, so rec2020 is checked against the
  CSS Color 4 sample code instead; its Luv is D65 where culori's is D50, so Luv/LChuv are only
  round-trip tested.
- The CSS Color 4 sample conversion code (rational matrices) for rec2020 and for rgb to hsl.
- Models of the documentation (`hegel/model.mjs`) for the serializers, interpolation, average
  and blend.

## Not tested or not recorded

- Documentation drift not recorded as bugs: the `itp` channel ranges in the docs differ from the
  definition and from the sRGB-derived range; `round()` defaults to 4 digits where the docs say
  8; `okhsl`/`okhsv` carry `gamut: 'rgb'` while the docs say they have no gamut limits; the
  hsl/hwb/lch/oklch serializers write `none` for a missing hue where the docs say `0`; api.md's
  `color(--srgb-linear ...)` example is written `color(srgb-linear ...)` by the library.
- `fixupHueLonger` keeps a hue difference of 0 (rather than 360), `differenceHueNaive` has a
  sign convention of its own, `blend([])` throws, and `parseHex` accepts hex digits without `#`
  (documented) — all left alone.
- Hue interpolation with `interpolatorSplineMonotone` and the `easing*` helpers beyond
  `easingMidpoint`/`easingSmoothstep`/`easingGamma`/`easingInOutSine` are not modelled.

## History

- 2026-09-20: created (turn 317); 20 bugs recorded.
