# go-colorful

[lucasb-eyer/go-colorful](https://github.com/lucasb-eyer/go-colorful) is the Go colour library:
an sRGB `Color` with conversions to and from HSV, HSL, hex, linear RGB (and a fast approximation),
CIE XYZ, xyY, L\*a\*b\*, L\*u\*v\*, HCL, LCh(uv), HSLuv, HPLuv, Oklab, Oklch, the CSS Color 4
wide-gamut spaces (Display P3, A98, ProPhoto, Rec. 2020, XYZ D50 through Bradford), distances
(RGB, linear RGB, Lab, Luv, CIE94, CIEDE2000, Riemersma), blends in each space, random "warm" and
"happy" colours and palettes, a colour sort, and `HexColor` for JSON/YAML/SQL. MIT, pinned at
`315b482` (v1.4.1, 2026-08-02, the head of master). The repository has no CONTRIBUTING file and
no AI policy; the zoo only records bugs.

## Build

`go test -count=1 -run TestHegel -v .` in the module root (package `colorful_test`). The patch
adds `hegel_test.go` (the `Known` gates, generators, the colorsys driver), `hegel_model_test.go`
(the model), `hegel_props_test.go` (the properties) and `hegel_pins_test.go` (one plain test per
bug), and requires `hegel.dev/go/hegel v0.6.33` in go.mod (the module's `go` directive moves to
1.26). Python 3's `colorsys` is the one external oracle; its property skips without `python3`.
`HEGEL_TEST_CASES` sets the case count (default 100; the properties run clean at 1000 in about
80 s, the palette generators dominating).

## Oracles

- **An independent model** of the formulas: the sRGB transfer function and matrix (IEC 61966-2-1
  / CSS Color 4, the inverse computed, not copied), xyY with Lindbloom's black rule, CIE 15:2004
  L\*a\*b\* and L\*u\*v\* with the library's 1/100 scaling and either reference white, polar forms by
  `atan2`, Oklab from Ottosson's published forward matrices with computed inverses, the Bradford
  D65↔D50 matrix, CIE94 (graphic arts), CIEDE2000 (Sharma, Wu and Dalal 2005) and Riemersma's
  metric. The model's CIEDE2000 is itself checked against seven of Sharma's published pairs to
  four decimals, and so is the library's.
- **Conversions match the model** for generated colours (8-bit and 4-bit levels, fine random
  values, greys, near-greys, two equal channels, primaries, the transfer-function thresholds):
  every decomposition (`Xyz`, `Xyy`, `Lab`, `Luv`, `Hcl`, `LuvLCh`, `OkLab`, `OkLch`, `XyzD50`, the
  `WhiteRef` variants with D50) to 1e-9, the polar forms compared through their rectangular
  coordinates, the constructors from model coordinates, and `FastLinearRgb` within its advertised
  half a percent.
- **HSV and HSL agree with Python's colorsys** both ways (hue modulo 360; saturation and
  value/lightness to 1e-9).
- **Every space round-trips**: `Space(c.Space())` returns `c` for all of the above plus HSLuv,
  HPLuv, Display P3, A98, ProPhoto and Rec. 2020, `Hex` within half an 8-bit level, `MakeColor`
  within half a 16-bit level, `HexColor` through JSON, `Scan`/`Value` and `Decode`; and
  **coordinates round-trip**: a colour built from generated coordinates in a space, when valid,
  has those coordinates back.
- **Distances behave**: CIE94, CIEDE2000 (with and without weights), Riemersma, Lab, Luv, linear
  RGB and RGB equal the model; identity, non-negativity, symmetry (CIE94 is asymmetric by
  definition) and the triangle inequality for the Euclidean ones; `AlmostEqualRgb` is the L1 test.
- **Blends interpolate**: every `Blend*` returns its ends at t = 0 and 1, a colour blended with
  itself, `blend(c1, c2, t) == blend(c2, c1, 1-t)`; the Euclidean blends hit the coordinate
  midpoint; the cylindrical ones walk the shorter hue arc and take the other end's hue from a grey.
- **Validity, hex parsing and the color.Color interface**: `IsValid`/`Clamped`, `RGBA`/`RGB255`/
  `Hex` rounding, `MakeColor` undoing alpha premultiplication (false at alpha 0), `Hex()` parsing
  exactly the 3- and 6-digit forms in either case and rejecting the rest (also through
  `HexColor`'s JSON).
- **Palettes and sorting** with a seeded `RandInterface`: the random colours land in their
  documented HSV/HCL ranges, `Fast*Palette` are evenly spaced hues in range, `Warm/Happy/Soft
  Palette` return the count asked, all valid; `Sorted` is a permutation (duplicates included) that
  starts at the colour nearest black, leaving its input alone.
- **White points and adaptation**: `D65ToD50` is the CSS matrix, `D50ToD65` its inverse (to the
  precision noted below), greys stay greys and white is (1, 1, 1) in every wide-gamut space.

## Bugs (4; details in bugs.toml)

| id | summary | severity |
|----|---------|----------|
| go-colorful/1 | `Hcl()`/`LuvLCh()` report hue 0 whenever a\* ≈ b\* or \|a\*\| ≤ 1e-4, whatever the chroma (`LabToHcl(0.5, 0.3, 0.3)` → hue 0, not 45; `Hcl(90, 0.3, 0.6).Hcl()` → hue 0), so the round trip is another colour | medium |
| go-colorful/2 | `Hsv()`/`Hsl()` return hue 360 for `{1, 0.4999999999999999, 0.5}`, and `Hsv(360, s, v)` is a grey | low |
| go-colorful/3 | `BlendLuvLCh` lacks the grey rule the other cylindrical blends got in #60: grey→blue passes through pink | low |
| go-colorful/4 | Oklab's forward (Ottosson, 10 digits) and inverse (CSS Color 4) matrices are inconsistent: `OkLab(c.OkLab())` is off by up to 3.7e-3, 2.5% of 8-bit colours change hex, `BlendOkLab(c1, c2, 0) ≠ c1` | medium |

How they were found: /1 and /4 by the round-trip properties in their first hundred cases (/1 at a
generated hue of 45°, /4 on the first saturated colour), /2 by the colorsys and round-trip
properties on a generated colour with two channels one ulp apart, /3 by the blend property's
symmetry check; each reduced to a one-line probe.

Not bugs, noted: the sRGB curve is discontinuous by 3e-8 at 0.04045 = 12.92 × 0.0031308, as in
every implementation, so `LinearRgb` round-trips to 1e-7 and not 1e-12; the library's D65
(0.95047, 1, 1.08883) and D50 constants differ from the sRGB matrix's white (0.95046, 1, 1.08906)
and CSS's D50, so `Lab` of white is (1, -5e-5, -1e-4), not (1, 0, 0), and Bradford of the D50
constants is not exactly the D65 constants; `D50ToD65` inverts `D65ToD50` to about seven digits
only (both matrices are an earlier CSS draft's, the round trip through `XyzD50` or ProPhoto moves
a channel by up to 1e-5 near black); `FastLinearRgb`'s inverse errs by up to 0.0055 near black
(the README says "roughly 0.5%"), its forward within 0.5%; hue 360 is documented as not allowed as
an input (v1.3.0 changelog) and `Hex()` of an invalid colour wraps (README FAQ); `Get`-style
constructors from out-of-gamut coordinates return invalid colours by design (the FAQ), so the
coordinate round trips ask only valid results; `HPLuv()` saturation exceeds 1 for non-pastel
colours by design; `Sorted` breaks distance ties by index order, so any nearest-black colour may
lead when several are equally dark; `DistanceCIE94` is asymmetric (the first colour is the
reference), as the formula says; the grey rule of `BlendHcl`/`BlendOkLch` (an end of chroma below
1.5e-4 takes the other end's hue) moves a dark near-grey end by up to about 2e-4, so
`BlendHcl(c1, c2, 0)` is only nearly `c1` there; opposite hues (180° apart) blend along whichever
arc the argument order picks, so `blend(c1, c2, t)` and `blend(c2, c1, 1-t)` differ for them; at
L\* = 0 the L\*u\*v\* chromatic coordinates carry nothing, and below a chroma of 1e-6 an HSV/HSL hue
is ill-conditioned in float64 (both excluded from the coordinate round trips).

Gates while the bugs are open (`Known` in hegel_test.go): colours whose (a\*, b\*) or (u\*, v\*)
pair has the guard's shape are skipped by the HCL/LCh checks and blends (/1); a hue of exactly 360
is skipped (/2); `BlendLuvLCh` is not asked for the grey rule (/3); comparisons through the Oklab
inverse allow 5e-3 in RGB and 5e-4 in Oklab coordinates (/4). The properties run clean at 1000
cases.

## History

- 2026-09-17: created at `315b482` (v1.4.1) with 4 bugs.
