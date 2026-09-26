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
    listed in `[expected_failures]`; a pin is not a property and needs no Hegel. But a pin is
    never the only evidence of a bug (2026-09-24, David): the property that found it keeps
    drawing the failing shape and is itself the expected failure, mapped to the bug. Known-bug
    gates in a property are therefore off by default and switched on by `HEGEL_NO_KNOWN=1`
    (one env var read once, in the harness), for a run that looks past the known bugs; a gate
    that is on by default sidesteps the bug, which DESIGN.md decision 3 forbids and `zoo check
    --warn` flags. Rewrites done before this date kept the old gates on; unsteering them is a
    worklist, starting with targets whose bugs have been fixed upstream (those get sibling
    targets, DESIGN.md decision 6). A call that may never return (a hang is the bug) runs in a
    child process with a capped address space and a deadline, never in a goroutine behind a
    `select` timeout: the goroutine cannot be stopped, and one that allocates as it spins
    reaches the machine's memory once more tests run after it (golang-ical/7, 2026-09-25).
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
a model gap in js-yaml, no library bug); rust/full_moon,
java/roaringbitmap, go/kaptinlin-jsonschema, typescript/js-joda (turn 429; kaptinlin-jsonschema/9-10
and js-joda/34 found by the long runs); rust/glam, java/dnsjava, go/mod, typescript/css-tree
(turn 431; css-tree/17-24 found by the rewrite's new shapes and the reviewer's 20000-case collect
runs of the fixpoint property); rust/rust-ini, go/x-text, typescript/yaml, java/jsqlparser (turn 432;
x-text/44-45, yaml/32-40 and jsqlparser/18-19 found by the rewrites' new shapes and long runs);
rust/pep508_rs, go/ugorji-codec, java/json-java, typescript/es-toolkit (turn 433; es-toolkit/43-54,
nine from the rewrite's shapes and collect runs, three from the reviewer's 2000-case rounds);
rust/uv-pep508, typescript/mnemonist, go/go-pretty, java/javaparser (turns 434-435; uv-pep508/7
found by the reviewer's second 1000-case run, javaparser/22 by the reviewer's first round);
go/sonic, typescript/qs, rust/fancy-regex, java/jackson-yaml (turn 436; qs/13-14 and
jackson-yaml/12-13 from the subagents' candidates, fancy-regex/2 from the reviewer's 2000-case
rounds); go/go-ini, rust/diamond-types, java/sbe, typescript/minimatch (turn 440; go-ini/9 and
minimatch/10-12 from the subagents' candidates, diamond-types/3 from the reviewer's 3000-case
rounds); go/cron, rust/chalk, typescript/semver, java/commons-collections (turn 441; cron/6 and
semver/15-16 from the subagents' candidates); go/now, rust/bs58, typescript/pathe,
java/snakeyaml-engine (turn 442; pathe/16 from the subagent's candidate); go/go-humanize, rust/xml-rs
(turn 443, the first rewrites under the unsteering standard of rule 11: the properties find the recorded
bugs and are the expected failures). Unsteered without a restyle (turn 443): typescript/ini, java/jsqlparser,
and the sibling go/go-runewidth@14205cc; (turn 444) go/ssh_config, go/go-udiff, go/godotenv (whose
`HEGEL_NO_KNOWN` used to lift the gates and now switches the shapes off like everywhere else) and
typescript/rbush; (turn 445) go/compose-go, go/go-re2 and typescript/picomatch. Unsteered (turn 446) go/sonic, typescript/shell-quote and go/now; (turn 449) typescript/liquidjs and go/jsonschema; (turn 450) typescript/node-csv; (turn 486) java/commons-csv, typescript/structured-clone, go/miekg-dns, typescript/jsonrepair and typescript/css-tree. Rewritten and unsteered together (turn 487) go/mapstructure and go/termenv; unsteered (turn 487) java/jackson-yaml, java/semver4j and java/sbe. Rewritten and unsteered together (turn 488) go/gofrs-uuid, go/bitset, go/go-version and go/uuid; unsteered (turn 488) java/javaparser. Rewritten and unsteered together (turn 489) go/uniseg, go/xstrings, go/properties, go/x-input and go/go-git. Rewritten and unsteered together (turn 490) go/cast, go/masterminds-semver, go/koanf, go/brotli and go/compress. Rewritten and unsteered together (turn 491) go/go-ldap, go/pflag, go/enmime, go/terminfo and go/tcell. Rewritten and unsteered together (turns 492-496) go/fasthttp, go/golang-ical and go/lz4. Rewritten and unsteered together (turn 497) go/go-geom and go/hujson. Rewritten and unsteered together (turn 498) go/gofeed. Rewritten and unsteered together (turn 503) go/prometheus-common and go/json-gold; json-gold's narrow properties followed (turn 547). Rewritten and unsteered together (turn 547) go/json-iterator and go/go-json. Rewritten and unsteered together (turn 548) go/afero, go/tablewriter and go/sh. Rewritten and unsteered together (turn 549) go/kin-openapi, go/testify and go/gofumpt. Rewritten and unsteered together (turn 550) go/form, go/echo and go/cel-go. Rewritten and unsteered together (turn 551) go/hcl and go/ultraviolet. Narrow follow-ups (turn 552) go/gofumpt and go/sh; unsteered (turn 552) java/jts. Narrow follow-ups (turn 554) go/afero and go/tablewriter.
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

The sixteenth batch (turn 429) applied the probe rule from the start and every subagent reported
its rates. full_moon's arbitrary-text round-trip property drew `text()` that almost never parsed as
non-blank Lua; it now draws a program from the grammar plus up to three edits. roaringbitmap's
BitSet bridge was skipped in 62% of the serialization cases (the drawn bitmap was too wide) and is
now its own small-bitmap draw; a 35% forEach gate became a check on a run-decompressed clone
instead of a skip. kaptinlin-jsonschema's defaults property skipped 24.5% of its cases under
unmodelled applicators; the unmodelled keywords are now stripped from the rendered schema, and the
property found two library bugs at once (a `default: null` never applied, `not`/`contains`/`if`
with an empty subschema dropped by `json/v2`'s omitempty on marshal). js-joda's parsing
properties draw a pattern as parts and separators and an edited text as a list of edits, both
rendered by pure functions; the long runs then produced texts that the old pattern-shape guards for
three recorded bugs never saw (a six-digit offset text for js-joda/20, a quarter conflict without
adjacency for /24) and one new bug (the offset parser passes hours 24-59, js-joda/34), so those
are recognised on the mismatch itself and counted. Shapes: full_moon builds a syntax tree from two
`recursive()` generators, the statement grammar nested inside the expression one's closure with
the inner subtree boxed - the way to mutual recursion until proptest offers one - and its
`max_leaves` default of 100 had to be cut hard for a grammar; the kaptinlin rewrite ported the
go/jsonschema rewrite almost whole, one more argument for a shared Go schema harness (see
Ergonomics). Lesson on delegation: a subagent that leaves its final 1000/3000-case runs in the
background reports before they finish, and the runs die with the turn; the reviewer's own two
1000-case rounds are what actually catch what those runs would have.

The seventeenth batch (turn 431) told the subagents to run every verification run in the
foreground, and all four reported after their runs. glam's helpers became `arrays` of bounded
reals mapped to the vector types, with the unit-length and near-singular gates as `filter`s at
0.1-0.5% and the glam/1 region a filter at 1.7%; a record defined inside a `macro_rules!` cannot
derive `PrettyPrintable` (the macro's field types break the derive's hygiene), so it prints as
Debug. dnsjava's fifty-arm rdata switch became per-type generator values with `sets` for the
distinct type lists and ports and sealed record families for SVCB parameters, update operations,
master-file entries and zone shapes; a probe showed the truncation property reaching its
"message fits" checks in only 3.7% of cases, so the length spec gained a Fits alternative (now
19%). go/mod's three latent model bugs surfaced in the 1000-case runs (a symlink `sub/go.mod` is
no submodule, a base64 tamper that decodes to the same bytes, equal tlog proofs for two sizes),
and the old `TrimRight` over the identifier characters had made two version shapes degenerate.
css-tree's rewrite moved the fixpoint property's clean path from 60% to 84% of cases and found
eight bugs: five from the new shapes themselves (whitespace before a media comma, quoted grammar
tokens before commas, signed numbers after unicode ranges, an escaped quote ending an unterminated
string, operator whitespace after a comment) and three from the reviewer's collect runs after a
plain 100-case round failed once without detail - which is the lesson of this batch: a plain
`tools/zoo test` round that fails keeps only its summary line, so the review rounds want
`--show-failures` (or the log copied after each), and `ZOO_COLLECT=1 HEGEL_TEST_CASES=20000
node --test --test-name-pattern=<Name>` in the work dir is how a one-in-20000 mismatch is seen
and shrunk. The css-tree pin file was a binary hunk of the patch because one pin held a raw
NUL; it is an escape now, and the go-diff patch has the same problem still.

The eighteenth batch (turn 432) took the largest targets so far and found thirteen bugs. x-text
(4921 lines, seven test files, 43 pins) went file by file with a test after each; its baseline
was not even green (three deterministic failures: an oracle table difference, a latent model
bug, a known bug reaching an ungated property), ten known-bug skips became count-and-continue
(one had been dropping 69% of the tag test), and the new shapes found the ISO-2022-JP encoder
passing ESC through (x-text/44) and NFKC `BoundaryBefore` wrong for the compatibility jamo
(x-text/45). yaml's writer draws a tree whose nodes carry style records and renders it with a
pure function instead of sixty coin flips inside the rendering; the new shapes found nine bugs
(yaml/32-40: a mixed dash-dot line rejected and lost from the CST, an anchor cut at a no-break
space, three more CST losses, a plain flow scalar with a colon before a line break read back as
a map, NaN from `0b_`, a flow `!!omap` long key, the explicit-key sequence indentation under
`indent: 4`). jsqlparser's SQL programs are a generator value built from a drawn schema, with
scope-parameterised expression generators memoised per case - the honest compromise when column
references need the drawn schema - and trivia drawn as one record applied at the end; its
3000-case runs failed six times in a row on latent gaps of the old model before passing, and an
oracle normaliser that stripped `--` inside string literals was among them (jsqlparser/18-19 from
the new shapes). rust-ini reached zero filters: alphabets computed per escape policy replace the
retry loops, and a `Source` tree rendered by a pure fitter replaces the hand-rolled state machine.
Lessons: a rewrite's baseline must be run and classified before the generators are touched; TS
work dirs hold build products the setup regenerates (yaml3.mjs, test-events.mjs) that `zoo save`
sweeps into the patch unless deleted first; and the binary-hunk sweep was closed the same turn
(`grep -l '^GIT binary patch$' targets/*/*/hegel.patch` is empty: diamond-types carried three
data files its own tests write, and jsonrepair, msgpackr and regexp-tree held raw control
characters in one-character string literals - go-diff never had one, its test text merely
mentions the header).

The nineteenth batch (turn 433) found twelve bugs, all in es-toolkit. Its rewrite draws one
record per compat function through a per-function generator table (`casesOf`) and shapes the
recorded bugs out of the inputs by flags instead of skipping them, which took the per-property
skip rates from 3-17% per hotspot to under 2.2%; the subagent's 20000-case collect runs found
nine differences from lodash (es-toolkit/43-51), and the reviewer's extra rounds three more
(52-54) plus two lodash quirks now listed as accepted. The lesson is about the review: a pair of
1000-case runs passed the saved patch, and each of four further 2000-case rounds failed on a
different rare shape (a gate that inspected the object before the write and missed what the
write creates, a known shape read through a primitive's wrapper, a shared function constant
that earlier cases had written properties onto, so the failure was not reproducible from its
own draw), so a differential target with a large value space wants several 2000-3000-case
rounds before its commit, and every module-level constant a property might mutate must be drawn
fresh. pep508_rs's markers are a `recursive` tree rendered by a pure function with one
whitespace tape for all gaps; its deprecated-key gate had fired on 40% of cases because a text
`contains` test saw `python_implementation` inside `platform_python_implementation` - gate on
the drawn structure, never on the rendered text. ugorji-codec's loose msgpack and CBOR writers
became pure functions of the value and a drawn tape, so an empty tape is the canonical encoding.
json-java's baseline was not green either (a cookie model keeping blank attributes the library
drops), hegel-java's small-budget integer draws lean toward 0 enough that a declared expected
failure depending on a 15% alternative passed a 100-case round until that alternative was put
first, and its `longs()` favour NaN/Infinity bit patterns so a finite-double filter rejected
47% (draw sign, exponent and mantissa instead). The same turn made `zoo save` refuse a patch
with a binary hunk (`--allow-binary` to override) and `zoo check` report one.

The twentieth batch (turns 434-435) found uv-pep508/7 and javaparser/22. uv-pep508 mirrors
pep508_rs (a ten-arm comparison `one_of!`, `flat_map` from the key to a version fit for it, a
`recursive` marker tree, one record per requirement with a whitespace tape) and the bug was a
`Display` that narrows a `!=` star range, missed by the two 1000-case runs and found by the next
one: a Rust tree-shaped domain wants the 2000-3000-case rounds too, not only the differential
targets. mnemonist's model-based properties stopped ending a case at a known bug: an operation
the bug would corrupt is counted and not applied, a check it would falsify is counted and
skipped, and only the one shape that poisons every later step is still an assume (about 1% of
cases instead of case-ending returns in nine properties). go-pretty's package-level generators
initialise after the known-bug switches (`loadKnown()` first), its `Size.WidthMax` is mapped
onto the checkable range instead of assumed, and its second 1000-case run found four latent
model gaps of the old test (a NaN sort key, a greedy row matcher, a slice index after dropped
rows). javaparser's 1800-line `JavaGen` of `if (chance)` sites became Generator values over a
small `Gen` library (`w`/`v` weighted choices, `all` for tuples of any arity, `opt`, `many`) with
a tower of depth levels memoised per flag set, so a property picks `PROGRAM`, `PRINTABLE_PROGRAM`
or `LEXICAL_PROGRAM` and draws once; a 1000-case run of it takes three to eight minutes, so its
long rounds are single 1000-case runs, one per ten-minute command, not 2000-case ones. The
javaparser subagent's report never arrived (its 2000-case runs hit the command cap twice); the
review recovered its edits with `zoo save` and its trace from the session's subagent transcript.

The twenty-first batch (turn 436) found qs/13-14, fancy-regex/2 and jackson-yaml/12-13. qs draws
its round-trip object from alphabets and literal pools filtered by the classifier itself, so
98% of round trips are checked where the old test explained 55% away, and its model now treats
keys as it treats values; `keep(o)` (an already drawn record as `just` fields) lets a `flatMap`
hold the options beside the draws that depend on them. fancy-regex draws patterns as syntax
trees through `recursive` (the leaf budget wants a probe: the default made 75-character
patterns) and splices a witness of the pattern into the haystack instead of skipping a miss
(31% of cases before); its captures property needed a tolerance no one had written down -
engines disagree on the capture of a final empty iteration of a repeated group, and the regex
crate does not even agree with itself between `*` and `{0,3}` - narrowed to the groups
fancy-regex runs on its own VM. jackson-yaml's writer is a pure function over a `Node` tree,
style records and two tapes, and its options record shapes the tree it draws, so the
recorded-loss gates fire on about 1% instead of being the bulk of the cases; a 1000-case run is
14 seconds, so the single-1000-case-run rule is javaparser's, not Java's. sonic was quiet. Two
of the four verifies failed only in the 2000-case rounds after the 1000-case pair had passed,
once more: the extra rounds stay.

The twenty-second batch (turns 437-440) found go-ini/9, diamond-types/3 and minimatch/10-12.
go-ini's grammar is built once per parse mode and its records rendered by pure functions; the
writer's value pool needed a filter for a go-ini/2 shape (`"""` inside the writer's own `"""`
quotes) that the old generator never drew. diamond-types' corruptions are records applied by a
pure function, and its verify was the batch's lesson: a 3000-case round printed "63 passed, 13
patch tests not run" with no failure text, which is the signature of a test binary killed by an
abort (here `memory allocation of 1170968169863 bytes failed`, SIGABRT, from a corrupted LZ4
chunk's declared length); the full text lives only in `work/<t>.log`, overwritten by the next run.
An uncatchable crash cannot be a `should_panic` pin: the properties reject the recognisable shape
after walking the header with the crate's own `pub(super)` reader, and the pin re-runs the test
binary on itself (`std::env::current_exe()`, `--exact`, a marker environment variable) and asserts
the child's exit status. sbe's schema is a record tree from a grammar built once per `extended`
flag, rendered to XML and a named layout by a pure function, the message values a tree matched to
that layout; its 1000-case run (three and a half minutes each, so no 3000-case run fits the
ten-minute cap) met a wider shape of the recorded sbe/10 that the new `sinceVersion` field made
reachable, resolved by padding to the current schema's block length rather than skipping.
minimatch's atoms are records carrying their own solutions, so the candidate paths derive from
the pattern tree; its bash oracle needed two more recorded limits (an empty brace alternative, the
empty alternative of `@(...)` after a star), found only in the 1000- and 3000-case rounds. Two
process restarts cut the batch's subagents short; a subagent resumed by message is not waited for
and dies with the turn, so a cut-short subagent is relaunched with a continuation prompt that
describes the partial work in its work dir.

The twenty-third batch (turn 441) found cron/6 and semver/15-16, and rewrote chalk and
commons-collections without a new bug. cron's grammar is data built once per parser layout, an
invalid spec a good spec plus a corruption record applied by a pure render; its old "too few
fields" corruption rendered a bare `TZ=` prefix (the cron/1 panic) in 0.56% of bad specs and made
the committed test fail at 1000 cases, fixed by shape. The Next property drew Lord Howe and
Chatham as schedule zones and met cron/6 (Next steps whole hours as if every wall-clock hour
began on a step, so a 30- or 45-minute DST shift loses or misplaces runs). chalk's term is a data
tree from `recursive()` over a leaf grammar built once per variable mode, since `one_of!` cannot
make an alternative conditional and the function form `generators::one_of(Vec<Boxed...>)` can;
the old shift property silently passed 3.2% of its cases when `shifted_out` failed, now a filter
on the tree. semver's range grammar is data rendered by pure functions and its candidates are
drawn up front; the rewrite reached semver/12, /4 and /13 from new directions and found semver/15
(an increment that returns its input) and /16 (`<0.0.0-alpha` intersects nothing). The batch's
lesson is about the bindings themselves: an integer draw over 0..99 lands on the value 1 about 15%
of the time (hegel-go v0.6.33, measured with 5000 cases; the Java binding shows the same), so a
`weighted` choice built on it gives ~15 extra points to whichever alternative owns that value -
the first when its weight is 2 or more - and a rare alternative must not come first; `chance`
spelled `x >= 100-pct` is unaffected. The commons-collections rewrite moved its rare `""` key to
the second alternative for this reason.

The twenty-fourth batch (turn 442) found pathe/16 and rewrote now, bs58 and snakeyaml-engine
without a new bug. now's cases are records with the pinned DST-boundary shapes kept out by a
`Filter` on the case generator (1-2% raw rejection), and its layout table is a flat `SampledFrom`
with repetition because a draw-free `Just` alternative wins shrinking over every drawing one,
whatever the order. bs58's alphabet and candidate alphabets are enums rendered by pure functions
and its checksum corruption a record applied modulo the live length; a `no_std` crate needs
`use std::{format, string::ToString}` for the `#[hegel::test]` expansion. pathe's globs are
segments of atoms carrying their own regex and solutions, and the candidates derive from the
glob; the rewrite reached an escaped character glued to `**` (pathe/16, the `**` crosses slashes
because the folding rule cannot see the escape token) and closed several latent gaps of the old
model. snakeyaml-engine's stream is a sealed node tree with style records, drawn by a grammar
built once per schema, replacing a generator object that drew while writing. This batch was
the last under the old rule on known bugs: the same day David asked for the gate pattern in
rule 11 (the property finds the bug and is the expected failure; `HEGEL_NO_KNOWN=1` looks past
it) and for sibling targets that keep failing suites for fixed bugs (DESIGN.md decision 6), so
the rewrites from here on unsteer as they go, and the 70 targets `zoo check --warn` lists are
the worklist for the ones already done.
The twenty-fifth batch (turn 443) was the first under rule 11 and settled its shape. A wide
property reaches a recorded bug at the shape's natural rate, and at 100 cases Hegel finds a
shape drawn in 4.6% of cases in only about six runs of ten (go-humanize/3), a 1% one rarely; so
the deterministic evidence for each bug is a narrow property (its shape region with random
contents, named after what it tests: `TestHegelDecimalSizesParseExactly`,
`TestHegelKeysContainingEqualsRoundTrip`, `collateAfterIsNullAgreesWithSqlite`), and the wide
properties that also reach it are declared `{ bug = "...", intermittent = true }` in
`target.toml`: honest data on what Hegel finds at the default budget, rather than generators
bent toward the bugs. Where one wide property covers several bugs it is mapped to the one it
shrinks to, and shrinking can land in either of two equally minimal basins (ini's
`UnsafeUndoesSafe` on `\;` three runs in four and on a lone quote otherwise), which the mapping
tolerates. `HEGEL_NO_KNOWN=1` is read once into a boolean; `zoo test` under it reports the
properties that then pass as "known shapes off", not as unexpected passes. xml-rs's shapes were
common enough (16-26% of cases) that its three round-trip properties fail every run without
a narrow property; ini's classifier, which had excused mismatches with a known shape, now names
the shape in the failure and is what `HEGEL_NO_KNOWN=1` filters with.

The twenty-sixth batch (turn 444) unsteered four rewritten targets and confirmed the shape. Three
Go targets (ssh_config, go-udiff, godotenv) had a classifier that discarded, with `Assume`, every
mismatch a recorded bug explains, and a `HEGEL_NO_KNOWN` that lifted the gates; the classifier is
kept as the shape test, but by default it names the shape in the failure and only under
`HEGEL_NO_KNOWN=1` does it skip (godotenv's skips fell to 0% by shaping the generators under the
flag; ssh_config keeps a 3% skip for the `?` disagreements that only the oracle can tell). A wide
property that covers several bugs at once (ssh_config's `MatchesSSH`: /1 at 9%, /2 and /3 at 4%)
fails every run but shrinks to different bugs in different runs; it is mapped to the majority
basin and is not intermittent. rbush showed the other end of the finding-rate curve: a property
whose failing shape is in 2.5% of its cases passed a 1000-case run, so the effective number of
independent samples is well below the case count and `intermittent` is right even at 1000. rbush/1
needs a leaf of 200000 items, which no sequence property can afford: a narrow property that
bulk-loads one is the only property that finds it, which is the honest answer. Second TypeScript
harness (after ini) whose properties shared one example-database key; check the rest when they
come up.

The twenty-seventh batch (turn 445: compose-go, go-re2, picomatch) added two data points on the
finding rate. A shape drawn in 14% of a property's cases (picomatch's literal brace group before
`scan`) still passes a 100-case run a third of the time, and one in 47% (go-re2's limit 0) fails
every run; between them lies the line where a wide property is intermittent rather than plain.
Some shapes are so rare in the wide generator (go-re2's `\B` before a multi-byte character: 0 of
3000 cases; picomatch's /3 and /8-/10 at 0.05% or less) that the narrow property is the only
property that finds them, and a wide property that can reach a shape only in principle is not
mapped to it. When a classifier cannot be an assume under `HEGEL_NO_KNOWN=1` because the shape is
still drawn often (compose-go's distinct defaults, 8%), the check of that one item is skipped and
the rest of the case is judged. Third TypeScript harness with the shared example-database key
(picomatch, after ini and rbush): every TypeScript target that comes up gets `keyed`.

The twenty-eighth batch (turn 446: sonic, shell-quote, now) was the first in which every target
had the shapes gated by the oracle as well as by the generators. Removing a shape gate is only
half the job when the model was written beside it: now's clock model rebuilt the hour with
`time.Date` and its calendar and parse models took `time.Date` for midnight, sharing the very
assumptions (a repeated hour, a missing midnight) that now/2-5 and now/11 are about, and sonic's
stream oracle compared only the presence of an error, so io.EOF against a syntax error (sonic/6)
was invisible even on the truncated literals the generator did draw. Both showed up as failures
outside the recorded shapes once the gates went; the remedy is to state the oracle on the
calendar or the specification and let the library's own primitive be suspect. Shape data
computed at start-up (now's per-zone transition table from tzdata, 1974-2062) makes a narrow
property a real property: a zone, one of its shape dates and a random instant, not a fixed
example. shell-quote's classifier had excused every recorded shape with a `return`, which is
the TypeScript form of the same steering; two of its bugs (/7, /13) had no property at all
because the generator never drew special parameters or object env values, which the narrow
properties now do. Standalone reproduction paid off again: sonic's top-level `-0` keeps its sign
on the first decode of a process and loses it on every later one (the JIT path), which a
one-shot probe would have called a non-bug.

The twenty-ninth batch (turn 449: liquidjs, jsonschema) was a short one, run late in a day's
budget, and mostly confirmed the pattern. liquidjs's `ZOO_FULL` had been doing two jobs, lifting
the known-bug gates and the documented-difference gates together; they are different things (one
is the standard's `HEGEL_NO_KNOWN=1`, the other a tolerance of the oracle's environment) and are
now two switches. jsonschema shows the intermittent case cleanly: every shape is a few cases per
hundred of its wide property, so all four wide properties are intermittent at 100 cases and the
narrow properties carry the determinism; one shape (/7, the aliased `instanceLocation`) is not
reached by the wide grammar at all in 2000 cases. Two `bugs.toml` notes were wrong in details a
standalone check against both engines settled (liquidjs/9's list of flattening filters,
liquidjs/12's claim about `replace_first`): the notes deserve the same reproduction discipline
as the bugs. Fifth TypeScript harness with the shared example-database key.

The thirtieth batch (turn 450: node-csv alone, the last of a day's budget) added two things.
The gate was not only in `known.mjs`: the Python comparison canonicalised `[]` to `[""]` at width
one and the README listed it as an accepted difference, when it is exactly the shape of
node-csv/2 (a lone empty field written as an empty line). A tolerance in the comparison is a gate
with a different name; an accepted difference must be a difference of the oracle's environment,
not of the library. Two bugs (/7, /8) had a pin and no property at all; a property for `raw`
(the records' raw text concatenates to the input) widened /7 from delimiters to multi-byte quotes
and escapes within its first run. And a helper shrinking the wrong way (`chance` shrank to true,
so every shrunk case had every option on) had gone unnoticed while the shapes were gated: the
direction a helper shrinks in only shows once something fails.

The thirty-first batch (turn 486: commons-csv, structured-clone, miekg-dns, jsonrepair,
css-tree; 89 narrow properties between them) was the first with a fresh day's budget since the
standard settled, and the largest. Three things stand out. A wide property over a grammar with
several bugs at comparable rates has no stable shrink basin: css-tree's fixpoint property landed
on css-tree/3, /9, /14, /12 and /11 across sixteen runs (Hegel's shrinker cannot cross from one
failing shape to a structurally different one, so where it lands is where the first failure was),
and the mapping names the most frequent basin while the narrow properties carry the certainty;
where a single-piece pool decides the shape, putting the smallest shape first in the pool (css-tree's
`SOUP`) makes the basin stable. Filter rates are not what a uniform estimate says: miekg-dns's
`exactSeconds` filter rejected 7% of draws where uniform sampling would reject 0.6%, because Hegel
biases integers towards small values, so a filter over a numeric shape should be a table of the
shapes wanted (`SampledFrom`) rather than a rejection, and the rate has to be measured, not
computed. And freeing the shapes finds bugs: jsonrepair's unsteered generators met ten shapes the
gated ones had never drawn (an output chunk boundary splitting a surrogate pair, `{undefined:1}`
becoming `{null:1}`, a numeric entity for a control character decoded raw, escaped empty strings
and missing commas in JSON-stringified documents, ...), reproduced standalone and recorded as
jsonrepair/23-31 with pins and properties of their own; miekg-dns's met three dnspython printing
differences that had been hidden behind the same gates and are now tolerated narrowly, with the
oracle's spelling normalised rather than the shape avoided. Also seen again: the oracle written
beside the gate shares its assumption (commons-csv's duplicate-header check was case-sensitive,
like the library's, and now lower-cases under `ignoreHeaderCase`); a wide property can be plain
only after enough runs - miekg-dns's `TruncateFits` failed seventeen runs for the subagent and
passed one of eight for the reviewer, and is intermittent; and Java's `--show-failures` prints
only unexpected failures, so a Java target's shapes are read from the surefire reports.

The thirty-second batch (turn 487: mapstructure and termenv rewritten straight to the standard,
jackson-yaml, semver4j and sbe unsteered; 48 narrow properties) added two lessons about the
tests' own tooling. Escapes do not survive every editor: jackson-yaml's pool of NEL strings had
been written as `"\u0085"` and reached the file as an empty string, because the tool that wrote
it decoded the escape, so bug 1's shape had never been drawn and the test passed on it for a
week - a literal that matters is checked with `od -c` after writing, and a generator whose shape
is a single character is worth a probe that prints what it drew. And an `assume` that rejects
every case is silent in hegel-java (sbe's evolution region computed the acting version from the
IR tokens, whose member versions are raised to the field's, rejected every on-shape case and
passed vacuously; Hegel's filter-too-much check did not trip), so a region's acceptance rate is
measured before it is trusted, in every binding. Freed generators again found what the gates had
hidden: semver4j desugars partial and x-range upper bounds without node-semver's `-0` (`<0.1` is
`<0.1.0`, node `<0.1.0-0`), a difference visible only when the set also names a pre-release of
the excluded version, met about twice in 100 000 cases by the wide property and recorded as
semver4j/13 with a narrow property that meets it every time; jackson-yaml's met an engine-side
defect (snakeyaml-engine folds a NEL inside a single-quoted scalar it wrote itself), listed among
the engine's defects rather than recorded. Also seen: a wide property that had failed every one
of the subagent's runs passed once in the reviewer's (semver4j's fluent property), so
`intermittent` is earned by observation, never by argument; and where the library panics inside
a drawn call, the property has to recover the panic itself for the failure to be attributed to a
shape (termenv's `catching`).

The thirty-third batch (turn 488: gofrs-uuid, bitset, go-version and uuid rewritten straight to
the standard, javaparser unsteered; 47 narrow properties) was mostly quiet, which is the point
of the template by now, and its lessons are about what a title asserts. Bug 17 of javaparser
said `x * this::m` was a parse error; a probe of that claim with the library and javac's tree
API, made to name the narrow property's region precisely, showed the text is accepted and parsed
as `(x * this)::m` - a wrong tree that no rejection check can see, recorded as javaparser/23
with a pin, a narrow property and a right-operand shape in the wide generators, and bug 17's
title corrected. A bug's title is a claim about the library like any other and is checked
before a property is built on it. Two more model gaps were found by the freed generators
rather than by the library (go-version compared numeric identifiers by length, so leading zeros
could never mismatch; its `~> 1` was unbounded in the model as in the library), a reminder that
a model written beside a gate often shares the gate's assumption. Three wide properties were
declared intermittent after passing once in the reviewer's rounds (bitset's ExtractAndDeposit at
100 cases, go-version's malformed and constraint properties at 3-4% of cases), and a race
property (uuid/1) stays intermittent on a two-core machine whatever its rounds, with hegel-go
printing no failure line when the shrunk case's final replay passes. Java targets of
javaparser's size verify at 1000 cases in four to nine minutes and 3000 does not fit a
ten-minute command; the impossible headers of bitset/7 are drawn from 2^52 up because 2^51 is a
fatal out-of-memory rather than a recoverable panic.

The thirty-fourth batch (turn 489: uniseg, xstrings, properties, x-input and go-git rewritten
straight to the standard; 39 narrow properties) found its bug where the previous batches did,
in the region a gate had kept closed: go-git's differential, once it drew `**` before a wildcard
segment, met a `**` that never backtracks (`**/*/b` misses a/c/b where git ignores it), two cases
in twenty-one thousand, recorded as go-git/7 after a standalone reproduction against the library
and git, with the wide grammar seeding a false-start path into one tree in a hundred so the
shape is met at a rate the property can report. The rest of the batch's findings were about
the recorded bugs' edges: xstrings/5 and /6 are wider than their titles (the range's last rune
is lost whenever its penultimate lands on a non-final single; U+FFFD is dropped from any
pattern of two or more runes), the committed xstrings baseline was already failing on the
wider /5 through a hole in its own gate, and uniseg/3 has two more directions (SARA AM, LB31).
An oracle can over-reach the way a gate does: uniseg's width rule gave every Hangul-initial
cluster its first code point's width, where doc.go speaks only of clusters composed of
conjoining jamo, so a syllable followed by a spacing mark is now left open rather than judged.
Three classifier defects came out with the gates (xstrings excused `a__b` and `ab_C_`, which the
library gets right, and never compared Scrub on invalid input; properties' separator classifier
excused agreeing texts), the usual shape of a gate written beside the model. Six wide
properties were declared intermittent on an observed pass (uniseg's widths at 100 cases twice
in three), and go-git's example database lives under the package directory
(`work/go/go-git/hegel/.hegel`), which the cleanup between runs has to know.

The thirty-fifth batch (turn 490: cast, masterminds-semver, koanf, brotli and compress rewritten
straight to the standard; 37 narrow properties) found no new bug and several things the gates
had been hiding in the tests themselves. koanf's model had three latent defects that only a
drawn shape could reach (the strict conflict check ran after the existing subtree was removed,
so a strict `Set` over a leaf reported no error; the koanf/5 shape test missed a `map[any]any`
under a `map[string]any` in a slice in a slice; the Copy/Cut comparisons lacked the koanf/2
shape). compress's corruption property, once it drew the truncated-deflate shape, also met two
oracle differences the old test had never reached: klauspost refuses a gzip header with a
reserved FLG bit where the standard library ignores it (RFC 1952 says the bits must be zero,
so tolerated, not recorded), and a zstd frame asking for a 144 MiB window is decoded by
klauspost up to its documented 512 MiB cap but refused by the tool's default 128 MiB limit,
so the property now passes `--memory` to the tool. One shape cannot be drawn by a wide
generator and lives in its narrow property alone: koanf/6, a key containing the delimiter,
which the flat-key model cannot represent; others are drawn but never the basin (cast/7 and
cast/11 sit behind cast/12 in the map property, which a failing run reports first). Basin
splits were as before (brotli's Encoders 4:3 between /6 and /1, koanf's Operations 10:3:1,
masterminds-semver's Constraints mostly /5 with /3, /4 and /7 in the rest): mapped to the
majority, plain. A nominally rare shape can be met every run because Hegel starts at the
smallest case (compress/4 is the empty `EncodeAll` frame, 0.1 % of cases and found first in
every run so far); it is declared intermittent on its rate, not its record. A check that only
a recorded bug can fail and that fires on a large share of cases (cast's out-of-range
integers at 60 %, brotli's Reset after trailing bytes at 11.6 %) is skipped by name under
`HEGEL_NO_KNOWN=1` rather than assumed away, the rest of the case still judged. One rewrite
hung for ten minutes on a tape-driven reader that could return `(0, nil)` forever where the
PRNG it replaced could not: a drawn list that drives a reader needs the progress guarantee the
random source gave for free. Two subagents put the mapping into target.toml for their own
verification runs and restored the committed file before reporting; that is fine, and the
template now says so.

The thirty-sixth batch (turn 491: go-ldap, pflag, enmime, terminfo and tcell rewritten straight
to the standard; 33 narrow properties) found no new bug and widened one: go-ldap's freed
`EscapeDN` round trip met the go-ldap/8 defect in a second function (`EscapeDN("\xff")` is
U+FFFD, reproduced standalone and added to the notes). The batch's other findings were about
oracles and the harness. Two oracle models built beside a tool were incomplete in ways only a
freed shape reached: tic synthesizes the VT100 `acsc` when `smacs` and `rmacs` are present and
`acsc` absent, and infocmp trims a trailing `% ` from the last capability it prints (terminfo
and tcell both, the same ncurses behind them); enmime's Python oracle disagreed on the charset of
a part with none declared and a hundred runes of content, where enmime's detector still runs
under `DisableCharacterDetection`. A bug whose symptom is nondeterministic (pflag/7, a map
default rendered in Go's map order) can make a property's verdict random, and Hegel's final
replay of the shrunk case may then pass and swallow the counterexample, printing a failure with
no message: the property now checks `Value.String()` is stable across calls, which turns the
shape into a deterministic failure (a "replay disagreed with the found failure" message from
Hegel would have saved a round). A classifier defect came out with the gates again (go-ldap
named every lenient acceptance of a compound filter go-ldap/5; it now walks the tree). enmime
was the last target with the inverse `HEGEL_NO_KNOWN` meaning; it is flipped. Every wide
property whose shape is a few percent of the cases is intermittent (all five of go-ldap's),
and a wide property that reaches several bugs maps to the one it shrinks to (tcell's TParm
reaches four, shrinks to /2).

The thirty-seventh batch (turns 492 to 496: fasthttp, golang-ical and lz4, all rewritten and
unsteered together, 35 narrow properties) cost four turns to a bug of the old tests rather
than of the libraries. golang-ical/7 is a `Serialize` that never returns; its pin ran the call
in a goroutine behind a three-second `select`, which was harmless while the suite ended
seconds later and fatal once fourteen narrow properties ran after it: the goroutine kept
allocating, the test process reached 7 GB, and the machine's OOM killer ended three turns in a
row before `dmesg` gave the cause. Rule 11 now says where such a call belongs (a child process
with a capped address space and a deadline); getting the narrow property for it right took
four designs, since a deadline-limited child costs the deadline on every one of the hundreds
of candidates the shrinker revisits, and a per-case verdict cache brought it from minutes to
two seconds. fasthttp was another target with the inverse `HEGEL_NO_KNOWN` meaning (enmime was
not the last); it is flipped. lz4/6 gained a third cut (a block-size field followed by nothing
reads as an empty stream with a nil error, reproduced standalone), and two latent defects of
the old lz4 test came out under the freed shapes: the block builder's tail budget assumed a
trailing match, and `Size()` was demanded of a legacy reference frame, which carries none.

The thirty-eighth batch (turn 497: go-geom and hujson, rewritten and unsteered together, 14
narrow properties) was small by budget. Both subagents needed a count-first `FlatMap` where
`Lists(...).MaxSize(60)` would have made the region a bug lives in (more than fifty points,
go-geom/6) a quarter of a percent of the cases: draw the size, then a fixed-size list. Two
latent defects of the old hujson model came out under the freed shapes, one of them a
steering that judged "beyond the end" on the document before a `move`'s removal and so never
drew the case; drawn, it found hujson/1's second route (`move` and `copy` to an out-of-range
index append too, reproduced standalone), and the bug's notes carry it.

The thirty-ninth batch (turn 498: gofeed alone, rewritten and unsteered, ten narrow
properties) is the pattern of the last several in one target: the freed JSON Feed property
met gofeed/1 by a route the bug's notes did not name (the JSON translator runs a free-text
author name through the same address parser, reproduced standalone), and the oracle needed
two tolerances the gated test had never reached, both in feedparser's loose parser paths.
The BOM-prefixed document, whose old check ran a possibly slow parse behind a timeout, now
follows rule 11's child-process form.

The fortieth batch (turn 503: prometheus-common and json-gold, rewritten and unsteered) adds
two shapes to the catalogue. prometheus-common's grammar is built once per option set as
generator values and memoised, the text writer reads a drawn tape, and edits are drawn data
applied modulo the live size; its two wide properties with several basins (the parser meets
five bugs, the OpenMetrics writer three) are mapped to the basin the shrinker lands in, and
the message names the shape met. Freed, the properties widened two bugs' notes after
standalone reproduction: `ExtractSamples` with nil options panics on every summary and
histogram family, and NaN, +Inf and huge summary counts parse to 1<<63 without error.
json-gold shows the other half of rule 11: generator factories over an options struct
(`documents(docOpts)`) let one grammar serve nine properties with different shapes switched
off under HEGEL_NO_KNOWN, which is fine - the rule forbids helpers over the test case, not
over options; and bugs that show only in the output of ordinary inputs (`{}` compacting
differently, an empty `@list`) cannot be switched off in the generator and stay as
count-and-agree recognisers under the switch. json-gold's narrow one-per-bug properties
followed in the forty-first batch (turn 547): thirteen of them, the wide checks extracted into
package helpers (`checkExpand`, `checkCompact`, ...) so that both kinds of property share one
judge, and the documentation-default bug left to its pin, since a property over it would test
nothing.

The forty-first batch (turn 547: json-iterator and go-json, rewritten and unsteered) shows
the second way a narrow property can behave under `HEGEL_NO_KNOWN=1`: instead of skipping,
it draws the neighbouring region the bug does not touch (spaces for the odd indent, a member
for the empty map, a two-digit exponent, a letter for the stray closer) through the same
`shaped(known, past)` swap the wide generators use, and passes. Both ways are fine; skipping
is right when the whole domain is the bug (a `null` term, a lang-string without a language),
the neighbouring region when the property's check is worth running on the bug's border. Both
targets found more once the shapes were free: go-json's three-digit exponents (drawn for the
Valid bug) met a new bug in the Number decoder (go-json/26), and json-iterator's bare
top-level numbers showed that no unsigned integer passes `Valid` either, correcting a bug's
notes. Two cautions from the batch: a Go 1.27.1 `encoding/json.Indent` defect (a hang with a
non-blank prefix and trailing whitespace) posed as a test hang until it was reproduced
standalone, so an oracle that is a standard library is still an oracle to doubt; and a new
shape a subagent gates behind a `candidate/` name is steering until the bug is recorded, so
the gate is folded into the `Known` struct (off by default) and the shape given its own
narrow property in the same commit as the bugs.toml entry.

The forty-second batch (turn 548: afero, tablewriter and sh, rewritten and unsteered) was the
first of the large stateful and grammar-shaped Go targets, and every one of the three found a
bug once its shapes were free: afero/39 (a `Rename` that kills the process), tablewriter/40 (a
streamed merge writing into the caller's slice, caught by comparing the inputs before and after
the call), sh/27 and sh/28 (a heredoc body after `(`, and the incremental parser yielding
statements twice at its read boundary). Two shapes of the standard that the batch settled. A
bug that kills the test binary (a fatal runtime error after a panic, which no `recover`
reaches) cannot be an expected failure of the property that meets it: the property keeps that
one shape out in both modes, says so, and the pin runs the call in a child process (the test
binary itself, `-test.run` and an environment variable, a deadline and `WaitDelay`) and reads
its fate; that is the one exception to "the property draws the shape". And for a stateful
target the known shapes are recognised when a step is applied, not when it is drawn: by default
the step runs and the mismatch names the bug, under `HEGEL_NO_KNOWN=1` the step is a counted
no-op, so nothing is rejected and the filter check stays quiet; the wide properties of such a
target land in several basins and are mapped to the most frequent one, intermittent. The
grammar-shaped target met libhegel's nesting cap (a hundred spans, every combinator a span): a
naive combinator grammar marked a third of its cases invalid and `hegel.Test` reported only a
bare failure, so chains became single composites drawing their operators as a list, forward
references choices read at draw time, and the fallback for depth and budget part of the weighted
choice itself. None of the three has narrow one-per-bug properties yet; for stateful and
grammar-shaped bugs a narrow property is a script or a program over the bug's region, and those
are the follow-up the json-gold one was.

The forty-third batch (turn 549: kin-openapi, testify and gofumpt, rewritten and unsteered)
brought the narrow properties into the rewrite itself where the bugs have value shapes:
kin-openapi (eighteen) and testify (nineteen) came back with a `hegel_*_shapes_test.go` beside
the wide properties, each narrow property a generator over one bug's region judged by the same
oracle and, under `HEGEL_NO_KNOWN=1`, drawing the neighbouring region instead (`shaped(known,
past)`), so the run with the shapes off still exercises the library where it is right. Freeing
the slice/array pairs of testify's EqualValues model found testify/19 (a slice EqualValues an
array holding its prefix): the subagent had left it behind a `candidate` gate that assumed the
case away by default, which is steering, so the gate became a `Known` switch that is off, the
shape a named mismatch of the wide property, and the bug got its pin and narrow property in the
same commit as its bugs.toml entry. Two lessons about rates. A wide property whose shapes are a
few percent of cases passes some 100-case runs and is intermittent; gofumpt's subagent instead
raised the drawn rate of two shapes (documented declarations 30% to 60%, an explicit
continuation kind for var statements) so the formatting properties fail every run, which is a
distortion of the corpus that the README names and that the narrow properties will make
unnecessary, since a narrow property is the deterministic failure and the wide one can draw
the corpus at its natural rates. And a high skip rate under `HEGEL_NO_KNOWN=1` is turned into
shape rather than tolerated: kin-openapi's legacy-router comparison skipped 37% of requests
until the requests it would mishandle were reshaped (`%2F` to `%20`, trailing slashes dropped,
a method the item has) by a pure map applied only under the flag. Where the shapes depend on
the rendered text (gofumpt's comment placement and line spans) the avoidance under the flag
lives in the renderer and the fixup pass rather than in the generators, and that is fine as
long as by default nothing is kept out.

The forty-fourth batch (turn 550: form, echo and cel-go, rewritten and unsteered, the rewrite
prompt now asking for the narrow properties itself and forbidding raised shape rates) cleared
the Go part of the worklist but for hcl, ultraviolet and the waiting go-runewidth. Three things
it settled. The CI machine is another test binary: two of testify's wide properties that had
failed in every local run passed there (hegel-go's case sequence is per binary, the lz4
lesson), so a wide property whose shape is a few percent of cases is intermittent whatever the
local runs say, and the batch's mappings were written that way from the start. A gate the
subagent leaves on in every mode is steering however it is spelled: cel-go's came as two
`const hzSkip... = true` with careful comments explaining the discrepancies they hid; both
were library bugs (the ANTLR parser's literal ranges end in bytes, cel-go/10, which the old
test had tolerated as cel-go/2; the Pratt parser rejects `[,]`, cel-go/11), reproduced
standalone, folded into the switches and given their narrow property and pin. And a model that
follows the code is steering too: echo's model had stopped at a `RouteNotFound` node and
dropped text after `*` as the router does, so echo/3 and echo/5 could never fail by default;
the model now says what the documentation promises, and the shapes fail. Smaller points: a
subagent raising a shape's drawn rate for reliability (form's panic keys, 20% to 50%) is put
back and the property mapped intermittent; narrow properties named `TestHegelShapeX` are
renamed to read as properties (`TestHegelWildcardBelowParam`); a mismatch met one time in ten
by Go's map order (echo/10) is bound two hundred times in the property so its verdict is
stable, since hegel-go reports a nondeterministic replay as a bare failure with no message.

The forty-fifth batch (go/hcl, go/ultraviolet) settled three things. A gate a subagent leaves
behind because it thinks the finding is not the library's bug is still a gate: ultraviolet's
scanner passes every read to x/ansi's `DecodeSequence`, which panics on a CSI with 33
parameters, and the subagent capped the scanner's CSIs at 32 as "GATE, not a recorded bug";
the panic reaches every program reading a terminal through `TerminalReader`, so it is
ultraviolet's crash (ultraviolet/35), the cap became `shaped(1..40, 1..32)`, the scanner calls
run under a recovering wrapper that names the shape, and the shape got its narrow property and
pin. Likewise hcl's two "candidates" (a bare template keeps `$$${` verbatim after a lone
carriage return; `Format` spaces a unary minus after an inline comment), both reproduced
standalone and recorded; a candidate is recorded or refuted before the commit, never carried.
Second, the bug a wide property is mapped to is read off the runs, not the subagent's guess:
hcl's edits property lands on hcl/1 in every run though the subagent proposed hcl/5, and its
Format property on hcl/3 in four runs of five; the shape names in the failure output (`awk` over
"the shape of" lines, which in `go test -v` precede the `--- FAIL` line of their test) give the
majority basin. Third, a narrow property's oracle is the wide property's, spelled for the
region: hcl/7 is visible only in what the writer emits (`Bytes` of a parsed file formats the
minus too), so the narrow property parses `a = /* c */ 1`, sets a negative number and asks
whether the output is in Format's form, as the edits property does. Smaller points: a stream
event's shape is per path (a 33-parameter CSI is ultraviolet/10 through `Decode` and /35
through the scanner), so the shape helper takes the path; a whole-read panic is named before the
per-event shapes, since it happens first.

The forty-sixth batch (go/gofumpt and go/sh narrow follow-ups, java/jts unsteered) added four
lessons. A wide property mapped intermittent to one bug can absorb a second, unrecorded shape
in silence: jts's predicatesAgree was mapped to jts/4 (RelateOp counting a line's self-crossing
on a polygon edge as a line) and a 1000-case run then failed it on a line collinear with a
segment of a self-crossing line, which the mapping would have passed as /4; the failure text of
every long run is read, not only its verdict, and the second shape became jts/5 with its own
recogniser, narrow property and pin. A rate a subagent raises so the wide property meets a
shape more often (jts's strange ordinates 10% to 25%, gofumpt's doc comments to 60%) is put
back: the narrow property carries the deterministic failure, and the wide property at its
natural rate is intermittent when it passes some runs (gofumpt's GofmtStable passed one run in
four). A Java candidate is reproduced the way a Go one is, standalone against the installed
artifact: a jshell script on the jts-core jar in `~/.m2`, ending in `/exit`. And a hegel-java
narrow property avoids a generator's inexact region by redrawing rather than assuming: jts's
midpoint construction is exact on the integer and eighths grids but not on thousandths, so the
generator is redrawn while the grid is thousandths, and the crossing lines take their
directions from a fixed list of pairwise non-parallel vectors instead of filtering random ones.
On the sh side, the narrow properties are built from the grammar's pieces, exposed as fields of
the grammar record (lines, and-or lists, simple commands, redirects, heredocs, words) so a
property composes the bug's construct from the same generators the wide grammar uses; a
`oneLine` variant of the grammar leaves out the quoted texts holding a newline and flattens
substitutions to one and-or list, since the line-shaped bugs never need them and they only cost
the shrinker; and the narrow properties pass `hegel.WithReportMultipleFailures(false)`, because
hegel-go otherwise keeps running a failing property for a fixed time looking for distinct
failures, which a region that is all one bug has none of. The turn was cut short by a service
restart with the sh subagent mid-verification; its work was on disk and its transcript showed
how far the runs had got, so the verification was taken over rather than the subagent
relaunched.

The forty-seventh batch (go/afero and go/tablewriter narrow follow-ups, the last two of the
list) closed the narrow-property work for the Go targets. Its lesson is about what a
`HEGEL_NO_KNOWN=1` run is for: the mode is not only the proof that the properties pass without
the recorded shapes, it is a run of the wide properties over a region the default run never
reaches at length, and a failure there is a candidate like any other. afero's helpers property
failed once in about twenty 1000-case runs under the switch on a class decoration that split a
multi-byte name, a malformed pattern; `afero.Glob` skips the up-front `Match(pattern, "")`
check `filepath.Glob` does, so over an empty directory the malformed pattern returns `[], nil`
(afero/40). The subagent reported it and left the wide property alone, which is right; the
integrator then records it and folds it in: the glob decorations draw an unclosed class by
default, the malformed-pattern shape is named in the failure and left out under the switch,
and the narrow property adds the malformed element below a fresh empty directory (a `Sub`
field of the step the wide generator never sets, since the pattern has to end in the bad
element and list an empty directory). Two idioms from tablewriter: a wide record can carry a
field only a narrow property draws (`columnMax`, modelled as the documented per-column
maximum) without touching the wide generator, and a bug no wide property reaches (a setter
overwritten by a later detection, an AutoFormat rewriting escapes, a table bound that is not
enforced) gets a narrow property against the documented behaviour spelled out in the property,
since there is no wide helper to share. Reviewing a large extraction, the lines the wide
files truly lost are read by diffing the old and new file's line sets: an extraction leaves
only `continue` turned `return` and setup rewritten as record construction, anything else is
a change to look at.

The lz4 subagent also observed that hegel-go's case sequence is reproducible per test binary,
so a wide property with two basins (WriterFramesFollowTheSpec, lz4/2 or lz4/8) lands in one of
them for as long as the binary is unchanged and moves when it changes: "run it six times" proves
little, and it is declared intermittent. A note on the harness: net/http drops a `Max-Age` with
a leading zero (RFC 6265's grammar) where fasthttp reads it (the algorithm of 5.2.2), tolerated
by drawing the narrow properties' digits without one.
