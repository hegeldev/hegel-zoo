# steel

[mattwparas/steel](https://github.com/mattwparas/steel).

## What is tested

(no hegel tests found?)

## Oracles

## Not tested

## History

- 2026-07-18: predecessor base commit `3a418c9ea586` (clear out the stack that isn't used on the spawned thread (#674)).
- 2026-07: tests written with hegeltest 0.28.2 in DRMacIver/hegel-rust-oss-bug-finding (`patches/steel.patch`).
- 2026-09-12: imported into the zoo; ported to hegeltest 0.44.1. The upstream testbench test
  `static_site_generator_modules` fails in the zoo's environment (it loads installed cogs from
  `~/.local/share/steel/cogs/`, which the zoo does not install); not a patch test, so it is
  reported as an upstream failure and not judged.
