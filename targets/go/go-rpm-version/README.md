# go/go-rpm-version

[knqyf263/go-rpm-version](https://github.com/knqyf263/go-rpm-version) (untagged, commit
1815e1f): parsing and comparison of RPM package versions (`[epoch:]version[-release]`), a Go
port of rpm's `rpmvercmp` with tilde and caret separators. Tested here: `NewVersion` and the
`Epoch`/`Version`/`Release` getters, `Compare`, `Equal`, `LessThan`, `GreaterThan`, `String`.

## Build

The upstream repository has no `go.mod`; the patch adds one (module
`github.com/knqyf263/go-rpm-version`, `hegel.dev/go/hegel` required) and a `hegel/` package of
three `hegel_zoo_*_test.go` files that drive the public API.
`go test -count=1 -run TestHegel -v ./hegel`

## Oracles

- A model of rpm's own code, which the package names as its reference: `parseEVR` and
  `rpmverCmp` (rpmio/rpmver.cc: an epoch is leading digits followed by `:`, a missing epoch
  compares as `0`, the release starts at the last `-`, epochs then versions then releases are
  compared with `rpmvercmp`) and `rpmvercmp` (rpmio/rpmvercmp.cc, transcribed byte for byte:
  separators skipped, `~` sorts before everything, `^` after the base version but before
  anything else, numeric segments compared without leading zeros by length then text, alpha
  segments by text, numeric beats alpha, more segments win).
- Compare's own algebra: antisymmetry over pairs, transitivity over triples, `Equal`,
  `LessThan` and `GreaterThan` consistent with `Compare`.
- `String` against the model's printing, and `NewVersion(v.String())` against `v`.

## Properties

- `TestHegelCompare`: two version strings (an epoch prefix in many shapes, including
  non-numeric, signed, space-padded and oversized ones; 1-4 segments of digits with leading
  zeros or 15-22-digit runs, or letters, joined by `. _ + ~ ^ - space : ..`; 0-2 hyphenated
  release parts; the second string often a small edit of the first) parsed and compared.
- `TestHegelOrder`: three such strings, `Compare` transitive and consistent through equal
  pairs.
- `TestHegelString`: `String` of a parsed version, and the version parsed back from it.
- `TestHegelPin…`: one pin per recorded bug, asserting rpm's behaviour (expected failures).

## Bugs

Four, recorded in `bugs.toml`: the release starts at the first `-` where rpm splits at the last
(go-rpm-version/1); any text before the first `:` is the epoch, read as 0 when not a number
(2); an epoch beyond int64 reads as 0 (3); `String` omits an epoch of zero or less, so a
negative epoch or a `:` inside an epoch-0 version does not survive `NewVersion(v.String())` (4).

## Modelled as recorded

All four are in the model behind `HZKnown` switches (`releaseSplitsAtFirstHyphen`,
`epochTextAccepted`, `epochOverflowIsZero`, `stringNotReparsable`); `ZOO_KNOWN_OFF=name` turns
a switch off and the properties then fail.

Design notes the model follows (undocumented, taken from the code): `String` omits an epoch of
0 (rpm's EVR would keep `0:`), trims leading zeros of a positive epoch, and prints the version
and release as parsed; `Compare` and `rpmvercmp` agree with rpm on every generated pair,
including `1.0^` against `1.0` and `1.0.1`, bare `~` and `^`, `1..2` against `1.2`, upper
against lower case, and empty strings.

## Not tested

Sorting helpers beyond `LessThan` (there are none), the package's own table of test cases.

## History

- 2026-09-21: new target, three properties, 4 bugs.
