# How the zoo's tests should be written

The zoo's early targets were written for yield: they found bugs, but the tests read badly.
David's direction (2026-09-23) is to turn from finding new bugs to making the tests already
written idiomatic Hegel, and to report what Hegel itself could do to make good tests easier
to write. This file is the style the rewrites aim at, the survey of what was wrong, and the
list of ergonomics asks for Hegel. The [hegel-skill](https://github.com/hegeldev/hegel-skill)
(`skills/hegel/SKILL.md`, its `techniques/`, and the `hegel-review` checklist) is the general
guidance; this file is the zoo-specific part.

## The rules

1. **A generator is a value, not a function that draws.** Build `Generator[T]` values from the
   binding's primitives and combinators and draw them in the test body with one `Draw`. A
   helper that takes a `TestCase` and returns a value is the exception, not the norm: it is right
   only when the draw has to interleave with live state (walking an open transaction, picking a
   node of a tree the test is mutating), and then the test is probably a state machine in
   disguise (see rule 9). In Go that means `hegel.Composite`, in Rust `#[hegel::composite]` /
   `compose!`, in TypeScript `gs.composite` / `gs.record`, in Java `Generators.composite`.
   Composite is for *dependent* draws (the second draw's range depends on the first); when the
   parts are independent, combine them with `Map`/`tuples`/`record` instead.
2. **Choice is `OneOf`/`SampledFrom`, never a `switch` or `if`-chain over a drawn integer.** A
   `switch n(tc, 1, 100)` hides the branch from the shrinker (no `ONE_OF` span, so it cannot
   swap branches) and burns a meaningless draw. Until Hegel has weights, use the local
   `weighted` helper (a `OneOf` with each generator repeated `weight` times) and keep the
   weights small integers.
3. **The simplest alternative comes first.** `OneOf` shrinks towards its first generator and
   `Integers(lo, hi)` towards `lo`. The old `chance(tc, pct) = n(tc, 1, 100) <= pct` shrank
   towards *true*, so minimal counterexamples arrived with every optional feature switched on;
   `switch n(tc, 1, 20) { case 1: /* the 2000-byte key */ ... default: /* the normal key */ }`
   shrank towards the exotic case. Write "absent" before "present", "plain" before "decorated".
4. **Collections come from `Lists`/`arrays`/`vecs`/`lists`, strings from `Text`/`text`/
   `FromRegex`, bytes from `Binary`.** A `for i := 0; i < n(tc, 0, 5); i++ { append(...) }` loop
   draws the length up front, so the shrinker can only shorten the list, never delete the
   third element; `Lists` uses the engine's collection protocol and can. Same for
   `strings.Builder` loops over `pick(tc, alphabet)`: that is `Text().Alphabet(...)`.
5. **Optional values are `Optional` (or a `OneOf` with the absent case first)**, not
   `if chance(tc, 50) { x := gen(tc); p = &x }`.
6. **Recursion is a self-referencing generator with a depth or size bound in the closure**
   (`ExampleComposite_recursive` in hegel-go; `recursive()` in Rust; `deferred()` in Java), not
   a `depth` parameter threaded through five helper functions, and never a package-level mode
   variable.
7. **Reject with `Assume`, not `return`.** An early `return` out of an uninteresting case counts
   as a pass, hides the rejection rate from the engine's health checks, and lets the shrinker
   walk into the rejected region. Better still, construct the subset directly in the generator
   (`Filter` only when the rejection rate is small).
8. **One property per test; draw the variant instead of looping over variants.** A property
   with forty `fail` sites shrinks against whichever assertion fired first; a `for _, mode :=
   range modes` inside the body makes every case eight times as expensive and stops the
   shrinker from isolating the failing mode. `SampledFrom(modes)` is a draw.
9. **A model-versus-system op loop is a state machine.** `for i := 0; i < n(tc, 1, 8); i++ {
   switch n(tc, 0, 9) { case 0: /* run op on both, compare */ ... } }` should be `RunStateful`
   (Go), `#[hegel::state_machine]` (Rust), `Stateful.run` (Java): the engine then owns rule
   selection and can delete a whole step while shrinking. TypeScript has no state-machine API
   yet: draw `arrays(opGen)` and `note` each op.
10. **Say less in notes.** The draw report already prints every top-level `Draw` with its value,
    so a `note("input=%q", input)` repeating a drawn value is noise; note derived values (the
    oracle's answer, a normalised form).
11. **Pins stay plain tests** (`TestHegelPin...`, `pin(...)`, `#[test]`), named after the bug,
    listed in `[expected_failures]`; a pin is not a property and needs no Hegel.
12. **The harness is as small as the binding forces it to be.** What remains and why is in
    HACKING.md: Go needs `hegelOpts()` (hegel-go reads no environment variable) and the panic
    wrapper (hegel-go re-raises a panic after shrinking, aborting the test binary); TypeScript
    and Java need `settings()`. Everything else (`n`, `pick`, `chance`, `word`, collect mode,
    `Known` switches) is either replaced by Hegel's own generators or kept only while a target is
    being developed.

## What the rewrites look like

go/go-shellquote (commit 6a1e315), a shell word:

```go
// before
func genWord(tc hegel.TestCase) string {
	var sb strings.Builder
	for i, k := 0, n(tc, 1, 3); i < k; i++ {
		switch w := n(tc, 1, 100); {
		case w <= 40:
			if sb.Len() == 0 { sb.WriteRune(pick(tc, bareRunes)) }
			sb.WriteString(genRunes(tc, append(bareRunes, innerRunes...), 0, 6))
		case w <= 55:
			sb.WriteByte('\\'); sb.WriteRune(pick(tc, escapableRunes))
		...
		}
	}
	return sb.String()
}

// after
func text(pool string, lo, hi int) hegel.Generator[string] {
	return hegel.Text().Alphabet(pool).MinSize(lo).MaxSize(hi)
}
var (
	bareText     = text(bareRunes+innerRunes, 0, 6)
	escape       = weighted(choice[string]{9, prefixed(`\`, text(escapableRunes, 1, 1))}, choice[string]{1, hegel.Just("\\\xff")})
	singleQuoted = quoted(`'`, text(singleRunes, 0, 8))
	firstPiece   = weighted(choice[string]{40, seq(bareStart, bareText)}, choice[string]{15, escape}, ..., choice[string]{20, singleQuoted}, ...)
	word         = seq(firstPiece, many(laterPiece, 2))
)
// in the property:
line := hegel.Draw(ht, lines(blanksNL))
```

typescript/ini (63e766c): `genOptions(tc)` with seven `if (chance(tc, 30)) opt.x = true` lines
became `gs.record({ whitespace: maybe(30, true), ... }).map(dropUndefined)`; `genObject(tc,
depth)` with its duplicate-key `continue` became `gs.maps(key, value, { maxSize: 5 })`, which
yields distinct keys by construction.

rust/pretty-bytes (fea0d90): `fn arb_size(tc: &mut TestCase, max_exp: i64) -> (f64, i32)` with
`if chance(tc, 30) {...} else {...}` became `#[hegel::composite] fn size(tc: &TestCase, max_exp:
i64)` drawing `one_of!(ints(1, 999).map(...), compose!(|tc| { ... }))`.

Things learnt on the way: hegel-go's `Lists` yields a nil slice for zero elements (compare with
`slices.Equal`, not `reflect.DeepEqual` against `[]string{}`); a Rust generator returned as `impl
Generator<T>` cannot be drawn (`impl PrintableGenerator<T>`), and `compose!`'s body needs braces.

## What the survey found (turn 413, four language surveys over the committed patches)

- **Go (159 targets)**: the API in use was five names: `Test`, `Draw`, `Integers`,
  `SampledFrom`, `WithTestCases`. 125 targets had exactly two `hegel.Draw` calls in the whole
  patch, inside their own `n()` and `pick()`. 1 734 value-returning `func x(tc hegel.TestCase)
  T` helpers and zero `Composite`; 548 `switch` on a draw, 2 443 `if chance(...)`, ~924 length
  loops versus 7 `Lists`, 341 string-builder loops versus 1 `Text`, 106 dedupe loops, depth
  parameters in 82 targets. ~15 800 lines of identical harness (`hegelOpts`, the panic wrapper,
  `n`/`chance`/`pick`, a collector, a `Known` struct) copied into 158 targets, with two names
  for the collect variable (`ZOO_COLLECT` 63, `HEGEL_COLLECT` 38). Two systematic shrinking
  defects: `chance` shrinks to true, and 102 switches number the exotic case first. 26 op-loop
  targets are `RunStateful` customers; none uses it. Zero targets use the example database.
- **Rust (222 targets)**: better (552 `#[hegel::composite]`, 429 `one_of!`) but 643 plain
  `fn gen_*(tc) -> T` helpers in 138 targets, 297 `match tc.draw(integers(..))` chains,
  `recursive()` unused while 39 targets thread a depth, 1 180 `.print_as_debug()`, a 26-target
  family with `n`/`chance`/`pick` helpers, a byte-identical `int!` macro in 49 targets. And the
  "pin" `hegeltest = "0.44.1"` is a caret requirement: cargo resolves 0.44.2.
- **TypeScript (54 targets)**: every target used exactly one generator, `gs.integers`, inside
  the shared harness; `tc.draw` appeared 54 times, once per target; `tc.assume` never; 588
  `genX(tc)` helpers, 590 `if (r < N)` lines, 432 length loops, 137 depth counters, hand-rolled
  LCG PRNGs in three targets. The harness is 13% of the corpus. `Settings.reportMultipleFailures`
  exists and is unused.
- **Java (34 targets)**: five of ~40 `Generators` factories used; `tc.draw` 86 times, 71 of them
  inside the copied `Zoo.java`; 407 static `genX(tc)` helpers plus seven generator classes of
  400-1 800 lines each; 195 `pick(tc, a(tc), b(tc), ...)` calls that draw every alternative
  eagerly; `Stateful`, `deferred`, `composite`, `records`, `text` all unused; checked exceptions
  worked around with sneaky throws; `dev.hegel.StopTest` string-matched because it is
  package-private. The Java corpus is oracle-rich; the problem is entirely on the generation side.
- Review-checklist items that recur in every language: known bugs dodged by narrowing the
  generator (gated by `Known` switches, which is the disciplined form, but the neighbouring
  shapes go untested); invalid cases skipped with a `return` (a silent pass); forty-assertion
  properties; configuration knobs at defaults or biased 30% each so the all-on corner is never
  reached; health checks suppressed instead of generators bounded; resource bounds in the drawn
  domain (`maxNodes = 7`).
- Hygiene: `targets/go/ultraviolet/hegel.patch` carried a 93 MB Rust build tree (fixed,
  turn 413); `go-diff`'s test sources contain raw bytes, so their hunks are binary.

The full per-language surveys, with file and line references, are in the project notes.

## What Hegel could do (ergonomics asks, most impact first)

1. **Weighted choice**: `OneOf` with weights (or `Weighted`/`frequency`), and `sampledFrom` with
   weights. Every language faked it with `chance()` dice, `switch` ladders or duplicated list
   entries; the repetition trick the rewrites use allocates sum-of-weights generators and reads
   oddly.
2. **`Booleans(p)` / `chance(p)` shrinking to false** (Rust has `weighted_booleans`; Java's
   `generateBoolean(double)` is public but unwrapped; Go and TS have nothing).
3. **Optional with a probability** (`Optional(g).Probability(p)`); it is 50/50 today, which is
   why 2 443 Go sites and 185 TS sites wrote `if chance(...)` instead.
4. **Read the environment in every binding** (`HEGEL_TEST_CASES`, `HEGEL_DATABASE`,
   `HEGEL_SEED`, ...) as hegeltest does: 159 Go, 54 TS and 34 Java copies of the same ten lines
   exist only for this, and it is why no Go target uses the example database.
5. **Panics as failures in hegel-go**: an option (`WithPanicPolicy`) or the default under `go
   test` to report a panic as the failure of the shrunk case instead of re-raising and aborting
   the binary; export `IsInternalPanic` meanwhile so the wrapper stops sniffing type names.
6. **Draw-report attribution through helpers**: hegel-go resolves the reported statement by a
   fixed frame skip, so a draw inside any helper prints `return hegel.Draw(tc, ...) = 37`;
   honouring `t.Helper()`-style marks (or a `DrawAt(skip)`) would remove the motive for the
   865 manual notes.
7. **Unique-by, permutations, subsets**: 106 dedupe loops in Go, Fisher-Yates shuffles in every
   language (unshrinkable: shrinking the swap index reorders, it does not simplify), seeded
   `java.util.Random` in 18 Java sites.
8. **A recursive combinator that is easy to find** (`Recursive(base, extend, maxLeaves)`; Rust
   has `recursive()` with zero users, Java has `deferred()` with zero users) and a doc example
   shaped like "an arbitrary JSON value".
9. **Statistics and a keep-going mode**: `tc.event(label)` with an end-of-run histogram, and a
   documented `reportMultipleFailures` that groups by shrink key, would replace the zoo's
   per-target collect harness (62 Go, 54 TS, 34 Java copies).
10. **Stateful testing that fits the zoo's shape**: a recipe (or API) for per-case fixtures, a
    model+system pair and rule arguments drawn from live state; a TS state-machine API; a
    fluent Java builder instead of annotations (`Generated` is package-private).
11. **Small things**: tuples/concat/join for Go; `FromRegex` more visible (one Go user, four
    Rust `.alphabet()` users); Java `oneOf` generics (`@SafeVarargs`, `Generator.or`), sizes
    surviving `map`/`oneOf`, a `ThrowingConsumer` overload of `Hegel.test`, a public `StopTest`,
    `nullable(g)`; a clearer Rust error than "cannot print the values it draws" for a missing
    `PrintableGenerator` bound; hegel-go `Lists` returning an empty non-nil slice.

## Status

Rewritten: go/go-shellquote, typescript/ini, rust/pretty-bytes (turn 413). The order of the
rest, smallest and ugliest first, is in the project notes; each rewrite is one commit, run
through `tools/zoo test` six times, with the same properties and pins unless the rewrite finds
a new bug (recorded in `bugs.toml` as usual).
