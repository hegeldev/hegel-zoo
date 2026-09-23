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
   `weighted` helper: one `Integers(0, total-1)` draw `FlatMap`ped to the generator whose
   cumulative weight it falls under (see the go-shellquote or go-units patch), which shrinks
   towards the first choice and takes percentages as weights; a `OneOf` with each generator
   repeated `weight` times does the same for small weights. `chance(pct)` is likewise
   `Map(Integers(0, 99), x >= 100-pct)`, shrinking to false: the draw shrinks to 0, so the
   comparison must make 0 the false case (`x < pct` shrinks to true - the rewrites of turns
   413-418 had it that way and were corrected in turn 419's sweep).
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
   entries; the `FlatMap`-over-an-integer helper the rewrites use works in every binding but is
   twenty lines of boilerplate per test file and hides the choice from the printer (the draw
   report shows the index, not which alternative it selected). Alphabets are sets: Rust's
   `text().alphabet("aab")` draws `b` half the time (the binding passes it as
   `include_characters`), so a pool that weights characters by repetition has to stay a
   `vecs(sampled_from(POOL))`.
2. **`Booleans(p)` / `chance(p)` shrinking to false** (Rust has `weighted_booleans`; Java's
   `generateBoolean(double)` is public but unwrapped; Go and TS have nothing). The stand-in
   `Map(Integers(0, 99), x < pct)` is not a fair coin: integer draws are boundary-biased, so in
   re2j `chance(20)`, `chance(15)`, `chance(15)` gave the all-three-on corner 11% of cases
   (0.45% if uniform) and no flag 26% (58%); good for coverage, wrong for anyone reading the
   percentage literally.
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
   `java.util.Random` in 18 Java sites. The shrinkable stand-in (go/shortuuid `permuted`) is a
   stable sort by one drawn key per element, so all-equal keys are the identity; it should not
   have to be invented per target.
8. **A recursive combinator that is easy to find** (`Recursive(base, extend, maxLeaves)`; Rust
   has `recursive()` with zero users, Java has `deferred()` with zero users - and no size bound,
   so a grammar whose branching factor exceeds one cannot use it safely: java/re2j keeps a
   depth parameter) and a doc example shaped like "an arbitrary JSON value".
9. **Statistics and a keep-going mode**: `tc.event(label)` with an end-of-run histogram, and a
   documented `reportMultipleFailures` that groups by shrink key, would replace the zoo's
   per-target collect harness (62 Go, 54 TS, 34 Java copies).
10. **Stateful testing that fits the zoo's shape**: a recipe (or API) for per-case fixtures, a
    model+system pair and rule arguments drawn from live state; a TS state-machine API; a
    fluent Java builder instead of annotations (`Generated` is package-private).
11. **Small things**: tuples/concat/join for Go (Rust has `hegel::tuples!(a, b)`, TS
    `gs.tuples`, Java `Generators.tuples` up to eight - the rewrites' `seq` is a Composite only in
    Go); a fixed-size `Lists(g).Size(n)`; `FromRegex` more visible (one Go user, four
    Rust `.alphabet()` users); Java `oneOf` generics (`@SafeVarargs`, `Generator.or`), sizes
    surviving `map`/`oneOf`, a `ThrowingConsumer` overload of `Hegel.test`, a public `StopTest`,
    `nullable(g)`; a clearer Rust error than "cannot print the values it draws" for a missing
    `PrintableGenerator` bound; hegel-go `Lists` returning an empty non-nil slice; a draw-free
    generator in Go (`Composite(func(hegel.TestCase) T {...})` is the only spelling for "the
    current time"); `hegel.Integers(uint64(0), n)` needing the typed first argument; Java
    inference of `Generator<Sub>` where `Generator<Super>` is wanted (`w(3, x.map(Sub::new))`
    does not infer, a typed field does).

## Status

Rewritten: go/go-shellquote, typescript/ini, rust/pretty-bytes (turn 413); go/shellescape,
go/go-units, go/go-rpm-version, rust/dyn-fmt, typescript/entities, java/java-diff-utils,
rust/shlex, go/timefmt-go, rust/shell-words, go/shortuuid, typescript/rbush, java/re2j,
go/go-shellwords, rust/human-repr, go/godotenv, typescript/pako (turn 414; the java-diff-utils
rewrite also caught an over-strict check of its own, not a library bug: the per-row "untagged
remainders agree" check is only meaningful for single-line changes; the pako rewrite found a
new bug, pako/5 - drawing the damage and the cut points as one generator reached a shape the
old loop had not); rust/configparser, go/ulid, typescript/shell-quote, java/semver4j,
go/compose-go, rust/dynfmt, java/json-schema-validator, typescript/liquidjs (turn 415);
rust/human_format, go/go-udiff, java/commons-csv, typescript/picomatch (turn 417);
go/iso8601, rust/uv-normalize, typescript/hono, java/gson (turn 418);
go/ssh_config, rust/strfmt, typescript/postcss, java/vavr (turn 419); typescript/ipaddr.js,
go/bbolt, rust/distro-info, java/threeten-extra (turn 422; threeten-extra/7-12 found by the
rewrite); go/golang-lru, java/caffeine, typescript/whatwg-url, rust/parry (turn 423; parry/3-4
found by the rewrite's long runs); rust/printf-compat, java/capsule, go/go-re2,
typescript/superjson (turn 424, quiet); typescript/structured-clone, rust/uv-requirements-txt,
go/validator, java/joda-time (turn 425; joda-time/19-21 found by the rewrite's long runs);
rust/numfmt, typescript/devalue, go/yaml, java/commonmark-java (turn 426; six of the
eight behaviours commonmark-java gated were recorded as commonmark-java/53-58 in turn 427, and the
verifying run found 59); rust/uv-pypi-types, go/miekg-dns, typescript/smol-toml, java/snakeyaml
(turn 427; smol-toml/10 and snakeyaml/17-22 found by the rewrites' long runs); rust/toml,
go/jsonschema, java/commons-text, typescript/js-yaml (turn 428, quiet: two oracle tolerances and
a model gap in js-yaml, no library bug).
Stateful-looking tests (rbush, java-diff-utils, re2j's junk edits, configparser's map edits,
semver4j's version nudges) draw the whole operation or edit list as data, with positions taken
modulo the live size when applied, so the shrinker can delete steps. The order of the rest,
smallest and ugliest first, is in the project notes; each rewrite is one commit, run through
`tools/zoo test` six times and then a few long runs (`HEGEL_TEST_CASES=1000` to `3000`), with
the same properties and pins unless the rewrite finds a new bug (recorded in `bugs.toml` as
usual). The long runs earn their keep: in turn 415 they found a library bug the old generator
reached once in a thousand cases (shell-quote/17), a model bug of the test's own (shell-quote's
brace fixup braced an escaped `\$` too), a node-semver quirk the semver4j property had to skip,
and a known-bug shape (semver4j/11) that one generator path had never been tamed against; none
of them showed in the 100-case rounds. The second batch of the turn did better still: the first
rewritten round of json-schema-validator found json-schema-validator/3 (`uniqueItems` rejecting
an object with two equal members), its long runs json-schema-validator/4 (a count keyword above
`Integer.MAX_VALUE` refused as a schema) and four oracle differences to tolerate, and liquidjs's
long runs found seven Shopify differences now recorded as liquidjs/9-15, plus a float
normalisation hole that had made the committed test flaky. Rewriting the generators as data
rendered by pure functions is what makes the long runs cheap to read: a failing case is a small
tree, not a transcript of draws. The sixth batch (turn 417) kept the pattern: commons-csv's long
runs found two latent model bugs of the test's own (an unterminated empty last row, and an escaped
whitespace-only value that `CSVParser.handleNull` keeps as a string), and picomatch's found a nocase
model bug plus three library bugs, picomatch/8-10 (a negated bracket with a POSIX class matching
`/`, a POSIX class after `**/` blocking an explicit dotfile segment, a negated bracket matching a
kept backslash under `windows`), none of which the 100-case rounds had reached in a week of
runs. Two review lessons from the batch: an editor can silently normalise non-NFC test data (a
decomposed `e\u0301` in go-udiff came back composed - write such literals as escapes), and a
known-bug gate written as a high-rate `Assume` trips the filter-too-much check, so the generator
itself has to steer most cases away from the shape (go-udiff's disjoint-words pairs).
The seventh batch (turn 418) was quiet on iso8601 and uv-normalize; hono's long runs
found three more router bugs, hono/8-10 (RegExpRouter attaches a middleware to the routes it
covers by testing its regexp against their path text, so a middle `*` meeting a `:label`, or
`P/*` beside `P*`, loses handlers; TrieRouter and LinearRouter compile the literal after a
slash-spanning regexp as a lookahead with no segment terminator, so `.+` overshoots when the
literal begins twice in the request), and a 1000-case run of gson's collections property found
gson/4 (two parsed JSON numbers are equal `JsonElement`s whenever they round to the same double,
so `9007199254740993` equals `9007199254740992` and `JsonArray.remove(Object)` takes the wrong
element) - a shape the old grammar could produce too, once in many thousand cases. The hono rewrite also settled how a known-bug shape is
kept out of a generator when it is a property of a pair of routes rather than of one: a
`filter` on the table generator (Hegel retries a filter three times before rejecting, so a
shape a few percent of tables have costs almost nothing), with the case generator taking the
router's name so that each property is shaped only for the bugs recorded against its router.
Two review lessons: a build product the setup regenerates (hono's esbuild bundle) must be
deleted before every `zoo save`, or it is swept into the patch; and a `return` after a
documented exception inside a `catch` is the property's verdict, not a skip, and stays.
The eighth batch (turn 419) was quiet in itself: no new library bugs in ssh_config, strfmt,
postcss or vavr, and their long runs (two of 1000 cases and one of 3000 per target) passed. Its
lesson was about the helpers themselves: the `chance(pct)` every earlier rewrite had copied was
`Integers(0, 99)` mapped through `x < pct`, which shrinks to *true* because the draw shrinks to 0,
so a minimal counterexample had every optional feature switched on - the opposite of rule 3.
The ssh_config rewrite spelled it `x >= 100-pct`, and a sweep corrected the eighteen Go,
TypeScript and Java patches that had the inverted form (one line each; the Rust rewrites use
`weighted_booleans`, which was right all along). Two smaller ones: hegel-go prints the drawn
value with `%#v`, so a record's report hook is `GoString()`, not `String()`; and hegel-java's
`tuples` stops at eight values, so a record with more fields is a tuple of tuples read by
`t.value1().value3()` - the record combinator in the ergonomics list would remove the worst
code in the vavr rewrite. A sweep lesson too: liquidjs's setup builds `hegel/liquid.mjs` the
way hono's builds its bundle, and `zoo save` sweeps it in unless it is deleted first. And the
sweep's re-runs of re2j paid for themselves: they showed a design difference the test had no gate
for (Java ends an unbounded loop at an empty iteration, RE2 lets a later, non-empty alternative
go on, so `(?:\B|a)*` matches "a" of "aa" in one and all of it in the other - now the
`empty-iteration-extent` gate) and, in a 1000-case run, re2j/17: on byte input, `group(n)` after
a match that only re2j/2's phantom text start allowed throws an internal IllegalStateException.
The ninth batch (turn 422) settled the stateful shape without `RunStateful`: bbolt draws a
script as `Lists(txn)` of `Composite` records whose positions are indices taken modulo the live
model when the step is walked, so a step that does not fit the state is a no-op (not an `Assume`,
which would reject most scripts) and the shrinker can delete steps; a known-bug shape that is a
property of the path (bbolt/2's cycle) is excluded by construction. ipaddr.js showed the "one
value, many spellings" shape: the text style is an independent record applied by a pure renderer
to derived data. Its old junk alphabet held a raw NUL byte, which had made a source file a binary
hunk in the patch - another reason to write such literals as escapes. distro-info put the oracle
inside a generator once: the empty-list pin draws its date from the windows on which the C tool's
list is constant (probed once, cached), which is acceptable for a pin whose case shape the oracle
defines, and not a pattern for properties. And threeten-extra is the batch's argument for the
whole exercise: its old range gate, written for ISO years, had skipped every International Fixed,
Discordian and Symmetry case in realistic years, and its week oracle added plain days where those
calendars skip weekless days; with per-chronology bounds and a calendar-week model the rewritten
properties found six library bugs on their first runs (threeten-extra/7-12: `plusWeeks` a month
early, two `until(WEEKS)` miscounts, `with(field, 0)` ignored, Pax `plusMonths` computing month 0
and `until()` throwing with it, and a `plus(until())` round trip that misses from a leap week).
A review lesson from it: a `return` that the old test used to skip a shape is worth measuring
before it is kept as an `assume` - here it was skipping everything.
The tenth batch (turn 423) took the four largest tests so far - golang-lru and caffeine are
stateful, whatwg-url a grammar of URLs and setter scripts, parry a geometry kit - and the shapes
held: caffeine's 25-arm draw-inside-switch op loop is a sealed interface of records chosen by
`weighted` with the reads first and applied by a pattern `switch`, and a shuffle the old test
took from a seeded `Collections.shuffle` is drawn as a sort key per element (all-equal keys keep
the declaration order, so it shrinks to the plain order); a bound only the library knows (the
frequency sketch's sample size) is applied in the body by truncating the drawn list, the
modulo-live-size idiom. whatwg-url's old generators threaded a mutable Set of "shapes" through
the draws, which was the reason they had to take the test case; the shapes are now derived from
the drawn record by a pure function. It also repeated threeten-extra's lesson: the setters test
had `return`ed on half its cases (a relative start URL never qualifies), so the start is drawn
valid rather than filtered. And parry's 3000-case run found two library bugs the 100-case
rounds had not reached in months of weekly runs, both from float boundary bias (13% of drawn
triangles have zero area): parry/3, a solid `cast_ray` against a zero-area triangle reporting
`t = 0` for an origin off the shape, and parry/4, `intersection_test` reporting a cuboid and a
clockwise triangle intersecting while `distance` finds the gap. Measurements from the batch for
the ergonomics list: `Lists` with only a `MaxSize` skews short (44% of golang-lru's scripts under
five steps where the old loop was near-uniform), the boundary bias of `Integers(0, 99)` makes
`chance(75)` come out true 59% of the time, and an index draw beside `flatMap`-built siblings
leans on index 1 - so `chance` and `weighted` are shrink-direction devices more than calibrated
coins, and a distribution that matters is worth a throwaway probe test before the patch is saved.
The eleventh batch (turn 424) was quiet - no library bug in printf-compat, capsule, go-re2 or
superjson, and every long run passed - and settled two shapes. Recursive data: go-re2 draws a
regular expression as a syntax tree from a recursive `Composite` with a forward-declared
alternation generator and a depth counter (hegel-go's recursive example, with a `defer` so an
aborted draw cannot leave the counter stale), rendered by a pure function that also numbers
the groups; superjson, whose binding has no recursive combinator, builds a bounded depth as an
eager chain of levels, each level's containers drawing children from the level below. Shared
and cyclic references, which the old superjson generators managed with a mutable pool threaded
through every call, are `ref` nodes in the tree resolved by the builder against the containers
built so far - an ancestor gives a cycle, a finished container a repeated reference - which is
the modulo-live-size idiom applied to a graph. Two places where a `filter` is the wrong tool:
a rejected element inside a `vecs`/`lists` rejects the whole case (printf-compat keeps a fix-up
as a `map`), and a rejection rate near 20% exhausts Hegel's three retries (superjson's RegExp
source/flag pairs fall back through a ladder in the renderer instead). Two measurements more:
hegel-java's `sets(g).maxSize(30)` never reached twenty elements in five hundred draws (median
about four), so capsule draws the count and then a list of exactly that many when the large-trie
shapes are the point; and a property whose case space is small (superjson's nesting case has
fourteen values) stops at the exhaustion point whatever `HEGEL_TEST_CASES` says, which is
correct and worth knowing when a long run looks too fast. A review lesson repeated: the Write
tool NFC-normalised a Kelvin sign (U+212A) in go-re2's alphabet; the subagent caught it with
`od -c` against the committed patch - non-ASCII literals in a rewrite are compared byte for
byte, or written as escapes.
The twelfth batch (turn 425) reached the large tests of the survey's least-idiomatic lists.
validator's seventy formats, each a `func(tc) (any, bool)` before, are one `FlatMap` from the
sampled tag into that format's value generator, so the tag and its value are one draw; its skips
that fired on a fifth or a quarter of the cases (cross-field pairs the tag does not specify,
parameters with a space) are generator shape, and its 3000-case run found a latent model bug of
the old test (a `luhn_checksum` number below ten expected to pass). uv-requirements-txt turned a
once-per-file budget the old generators carried as mutable state into renderer shape: the first
`--index-url`, binary policy and `-e` in file order are admitted and a later one renders as an
empty line, a no-op step the shrinker can delete. structured-clone reused superjson's tree with
`ref` nodes and made a decoration the old test applied by mutating the built value (`toJSON`) a
shape flag on the node. joda-time is the batch's find: its long runs (the subagent went to
30000-case shake-outs) surfaced two model bugs of the old test, one oracle tolerance and three
library bugs (joda-time/19-21: `GJChronology` rejecting a Julian leap day the Gregorian calendar
lacks while `DateTime` accepts it, tail-rule zones whose transitions and offsets disagree in the
last years before `Long.MAX_VALUE`, and an overlap across the date line resolved to the later
instant) - and, in review, that the harness pom had pinned the 2.14.3 release from Maven Central
while the setup installs the tree as 2.14.4, so the tests had run against the wrong jar since the
target was created. A review rule from that: a Java target's harness pom must name the version
the pinned tree installs, and a bump must move both. Two smaller lessons: a `weighted` that mixes
a draw-free `just` with a `sampled_from` alternative can leave a shrunk case on the wrong
alternative, since the shrinker cannot swap between alternatives of different draw counts - for a
small enum a flat `sampled_from` table with the plain spelling repeated is the cheaper spelling; and
Python's `splitlines()` splits on U+2028/U+2029, so a code-point comparison of two patches must
split on the newline alone.
The thirteenth batch (turn 426) took the two largest grammars so far. go/yaml's writer had
interleaved some forty `chance` calls with rendering; once every node of the drawn tree carries a
`style` record (its YAML spelling) beside its `rep` record (its Go typing), the writer is a pure
function of the tree and a document style, and the tree itself is the recursive factory go-re2
introduced, with `Lists` and `Maps` for the collections so keys are distinct by construction.
java/commonmark-java's forty-odd string-building helpers became a sealed record tree (`Md.java`)
drawn from a grammar built once per flavour with a level record per depth and rendered by one
function; its long runs widened several known-bug gates and gated eight behaviours of the library
and its renderer that are documented in `Known.java` as not yet recorded, to be reproduced and
recorded on their own. numfmt showed a rewrite reaching a recorded bug from a new direction (a
round `1e28` under the short scale meets numfmt/4's rounded `log10`), which belongs in that bug's
notes rather than a new entry; and devalue was the third target on the tree-with-ref-nodes shape
without friction. Two smaller points: a `flat_map` that must keep the drawn value beside its
dependent draw has no combinator in Rust (`tuples!(just(v.clone()), ...)` is the spelling), and a
per-node style record doubles the draws per node, which is the price of a pure renderer and worth
paying.

The fourteenth batch (turn 427) was the first whose long runs found bugs in three of four targets,
and each time through the same door: a drawn list of edits or pieces reaches boundary shapes the
old loops drew rarely. smol-toml's mutation property, now a `weighted` list of edit records applied
modulo the live text, met an array-of-tables header closed by one `]` (smol-toml/10) on its second
1000-case run; snakeyaml's stream of drawn documents met a BOM written as a plain scalar, a tab
escape, a tab-then-space in flow context, a folded scalar losing its leading space and a block
scalar taken as an explicit key's value (snakeyaml/17-22, the last two on the second and third
1000-case runs); miekg-dns's `Lists` of zone entries hit dnspython's singleton rule on its first
run, a latent model bug the old generator had reached once in the baseline run of the committed
patch. The lesson for review is that a rewrite's 100-case rounds are not enough: run the
thousand-case rounds more than once, and when the first finds a gate hole, expect the second to
find another (smol-toml needed three). Two gate lessons: a predicate on a record's `String()`
misses what the printer normalises (miekg-dns printed a `\032` escape as a space, so the
message-level Len gate now compares each record's Len with its packed size, which is what the
records property already did on the generated text; the fix followed a red CI run); and a regex
over an inline table cannot cross a nested table, so a trailing comma is looked for on its own.
Shapes: uv-pypi-types's 30-field record is `tuples!` of three 10-tuples (the macro caps at 12),
with the header order a drawn `permutations`; miekg-dns's rdata is a `Composite` per type over
shared value generators chosen by `FlatMap` from the type; snakeyaml's document is a sealed node
tree with per-node style records (`Doc.java`) like go/yaml's, and its dump options two 8-field
records because Java's `tuples` caps at 8. The old smol-toml stringify property had skipped every
case with an astral character because its lone-surrogate regex matched paired surrogates too; the
rewrite runs them (`isWellFormed()`).

The fifteenth batch (turn 428) was quiet - four rewrites, two 1000-case rounds each in review plus
the subagents' own 1000/1000/3000, and no library bug - but three of the four found that the old
test had been testing far less than it looked. rust/toml's parsed-document stability property drew
arbitrary text of which 12% parsed and 94% of that was blank; it now draws a valid document plus up
to three edits (54% parse, 4% blank). commons-text's gate for commons-text/6 was unsatisfiable for
72% of the filtered-source cases, so most of that alternative never ran; the source is now drawn
around an anchor code point its predicates accept. js-yaml `return`ed 6% of its PyYAML-writes
cases on a bang tag; the shapes PyYAML cannot write are excluded by construction and the guard
fires once in a thousand. The rule that follows: before keeping any skip as an `assume`, measure
its rate with a throwaway probe test, and when it is above a few percent it is generator shape,
not a gate. Shapes: toml is the first zoo use of `recursive(scalar, |inner| ..).max_depth(d)`,
which mapped one-to-one onto the old depth parameter and was frictionless; jsonschema's schema is
a data tree from a recursive weighted grammar with references resolved as indices modulo the
definitions declared so far; commons-text's TextStringBuilder operations are 23 sealed records
chosen by `weighted` (each needing a `.<Op>map` witness, since a `Generator<Sub>` is not a
`Generator<Super>`); js-yaml's writer input is a document record with a style record per node,
rendered by a pure writer, and its folded line breaks a drawn coin list recycled modulo the word
boundaries. Two oracle tolerances went into js-yaml's README (Python folds `1`/`True` and
equal-instant `Date`s into one key; PyYAML reads a `?` or `:` that starts a plain scalar in flow
context as an indicator), and its marker-key check for js-yaml/4 now covers Set members. Probe
measurements are also the answer to the skewed distributions the Go and TypeScript bindings
show inside large cases (a nominal 75% came out at 52%): check that every shape is reached rather
than tune the weights.
