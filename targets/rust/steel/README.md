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
- 2026-09-13: base bumped 3a418c9ea586 → 1bc0cc4b752b (2026-09-04, "don't crash on division with i32::MIN (#695)"; 0.8.3); 3 bug(s) still reproduce; fixed upstream: steel/2; 1 ignored reproducer(s) not run. 37 tests pass. steel/2 is fixed by that very commit (PR #695): the division properties no longer exclude an i32::MIN divisor. steel/4 (process-aborting reproducer) was not run.
- 2026-09-15: base bumped 1bc0cc4b752b → 21ea5eaa7880 (2026-09-14, "fix internal define ordering bug (#696)"; 0.8.3); 3 bug(s) still reproduce; 1 ignored reproducer(s) not run. 38 tests pass.
