# semver4j

[semver4j](https://github.com/semver4j/semver4j) (`org.semver4j:semver4j`; the pom carries 0.0.1-SNAPSHOT, releases
are versioned by tag, the last being v6.0.0 of 2025-06-28; pinned at the main commit of 2026-09-01) is the
semantic-versioning library of the Java world: parsing and comparing SemVer 2.0.0 versions, modifying them, and
checking them against ranges in npm (node-semver), CocoaPods (`~>`) and Ivy interval syntax, plus a fluent
`RangeExpression` builder and a processor pipeline for custom range formats. About 3 500 lines of source.

The tests are a Maven module `hegel/` added by the patch; `[run] setup` installs the library from the pinned tree into
the local Maven repository and `npm install`s node-semver 7.8.5 into `hegel/node/node_modules` (pinned by
`hegel/node/package.json`); the tests start `node hegel/node/oracle.js` once and talk to it over stdin/stdout.

## The oracles

- **A model of SemVer 2.0.0** (`Spec`): the grammar (as a regex, with semver4j's two documented extensions — an
  optional `v` and surrounding whitespace), the precedence rules of section 11 with `BigInteger` arithmetic, and the
  canonical text.
- **node-semver 7.8.5** (`Node`, a child process): `parse`, `compare`, `satisfies` and `validRange` (with and without
  `includePrerelease`), `coerce` and `inc`. semver4j documents its npm range support as node-semver's, so every
  syntax it lists (primitive comparators, hyphen ranges, x-ranges, tilde and caret ranges, `||`, whitespace
  variants, `v` prefixes, CocoaPods `~>` as node's `~>`) is compared against it directly.
- **Interval and set models** for what node-semver has no notion of: Ivy intervals as intervals over the model's
  precedence with the pre-release rule; `RangeList`/`Range` built directly from operators and versions as OR of ANDs
  with node's pre-release rule; the fluent `RangeExpression` against the text form written left to right.

`Gen` holds the generators as `Generator` values built from `integers`/`sampledFrom`/`lists`/`tuples`/`oneOf` and
two local combinators the binding lacks (`weighted`, one integer draw `flatMap`ped to the alternative under its
cumulative weight, and `chance(pct)`, both shrinking towards the first/false): versions as values (small and large
numbers, numeric/alphabetic/alphanumeric pre-release identifiers, build metadata; a `Shape` record narrows them per
property), a `Decor` for the text they are written as (canonical, `v`-prefixed, blank-padded), a `Nudge` (a core
`Move` plus fresh identifiers) that makes a version near another, damaged versions for the parser as a list of
`Edit`s applied by a pure function (dropped and inserted characters at a position taken modulo the length, leading
zeros, double dots, `=`, `V`, non-ASCII digits and letters), npm ranges as data (`Alt`s of `*`, one to three
`Comparator`s sharing a set, or one caret/tilde/`Hyphen` piece, each written against a drawn `Core`) rendered to
text while collecting the numbers used so the tested versions can be drawn near them, and Ivy bounds of one to
three numbers. Sets built step by step in the tests (`RangeList` entries, fluent `Chain`s with nested operands) draw
a `Rel` per version — fresh, or near the version at an index modulo those drawn before it — so the shrinker can
delete an entry without invalidating the rest.

## Properties (`Semver4jTest`, 9)

- `parsingMatchesTheSpec`: `parse`/`isValid`/the constructor accept exactly the grammar (numbers above
  `Integer.MAX_VALUE` refused as "too big" with `SemverException`), read the same components as the regex and
  node-semver, and normalise the text (`getVersion`, `toString`, `equals`, `hashCode`, `isStable`).
- `precedenceMatchesTheSpec`: `compareTo` and the ten `is…Than…` methods follow section 11 and node-semver; the
  order is antisymmetric and transitive on triples; `equals`/`isEqualTo` mean equal canonical text,
  `isEquivalentTo` means `compareTo == 0`; `diff` and `isApiCompatible` return the greatest differing component.
- `npmRangesMatchNodeSemver`: `satisfies(version, range[, includePreRelease])` agrees with node-semver, the range
  parses into one set per `||` alternative, and the `String`, `RangeList` and two-argument overloads agree.
- `ivyRangesMatchTheIntervalModel`: `[a,b]`, `[a,b[`, `]a,b]`, `]a,b[`, `[a,)`, `]a,)`, `(,b]`, `(,b[`, `latest`,
  `latest.integration` with bounds of one to three numbers, both pre-release modes.
- `rangeListsEvaluateLikeTheModel`: `Range.isSatisfiedBy` per operator, `RangeList.isSatisfiedBy` as OR of ANDs
  with the pre-release rule, `get()` holds the non-empty sets added.
- `fluentExpressionsMatchStrings`: a chain of `eq/greater/greaterOrEqual/less/lessOrEqual` joined by `and`/`or`,
  with nested operands, builds the same sets and the same answers as the text (`and` = space, `or` = `||`).
- `modifiersMatchTheModel`: `nextMajor/Minor/Patch` (against the model and node-semver's `inc`), `withInc*`,
  `withPreRelease/withBuild`, the three `withCleared*`, `isStable`; malformed identifier lists are refused with
  `SemverException`.
- `coerceMatchesNodeSemver`: `coerce` keeps a valid input whole and otherwise finds the same number groups as
  node-semver's `coerce` (inputs with leading zeros excluded — semver4j strips them, node-semver keeps and then
  rejects them — as are digit runs over 16, which neither matches the same way).
- `buildersRoundTrip`: `Semver.builder()`, `of`, `create` produce the canonical text, equal the parsed version, and
  refuse malformed identifiers and negative numbers with `SemverException`.

The generators draw every recorded bug's shape by default (STYLE.md rule 11): pre-release identifiers with more
than 18 digits and pairs of alphanumeric identifiers containing digits, with same-core siblings half the time
(1, 2); identifiers beginning with a hyphen beside numeric ones (11); caret, tilde and hyphen ranges beside other
comparators in a set (`MIXED`, 3); `^0.x`-shaped carets (4); bare wildcard operands, from depth-0 comparator
bodies (5); Ivy intervals mixing bracket styles (6); junk operators in 3 % of primitives (7); a trailing `||`
in 8 % of ranges (8); range numbers above `Integer.MAX_VALUE` in 1 %, with `fit()` keeping the versions tested
near them (9); identifier lists with a trailing dot (10); a fluent `and()` after an operand containing `or`
(12). The wide properties fail on them and are listed in `[expected_failures]` mapped to the bug they shrink to
(`npmRangesMatchNodeSemver` to 5, `ivyRangesMatchTheIntervalModel` to 6, `modifiersMatchTheModel` to 10,
`fluentExpressionsMatchStrings` to 12; `precedenceMatchesTheSpec` to 1 and `rangeListsEvaluateLikeTheModel` to
11 intermittently); one narrow property per bug, a generator over the bug's shape region with random contents,
fails every run (`longNumericIdentifiersCompare`, `alphanumericIdentifiersCompareInAsciiOrder`,
`caretBesideComparatorsMatchesNodeSemver`, `caretZeroOpenMatchesNodeSemver`, `bareWildcardOperandsMatchNodeSemver`,
`ivyMixedBracketsMatchTheIntervalModel`, `rangesWithJunkPartsAreRefused`, `trailingOrMatchesNodeSemver`,
`bigRangeNumbersAreRefusedAsTooBig`, `trailingDotIdentifierListsAreRefused`, `hyphenIdentifiersRankAboveNumeric`,
`fluentAndAfterMultiSetOperandJoinsTheLastSet`). The pins stay as regression examples. `HEGEL_NO_KNOWN=1` (read
once into `Zoo.NO_KNOWN`) leaves the shapes out, and every property passes. Two node-semver differences are
handled in the oracle rather than reported: node collapses a range with a bare `*` set to `*` alone, so `1.2.3-a`
does not satisfy `* || 1.2.3-a` there without `includePrerelease`, while semver4j evaluates each set and says it
does (the pre-release rule of the npm spec agrees with semver4j), so pre-release versions are not compared
against such ranges; and node reads `>*` as `<0.0.0-0` (nothing) where semver4j reads `>=0.0.0`, so `>*` is
written `>=*`. One shape is skipped as a candidate (`candidate/java/semver4j-1`, about one case in a thousand):
semver4j desugars partial and x-range upper bounds without the `-0` node-semver adds (`<0.1` is `<0.1.0`, node
`<0.1.0-0`), so `0.1.0-5` satisfies `<0.1 >0.1.0-1` in semver4j and not in node.

## Not tested

Custom `Processor` implementations and `CompositeProcessor.of` beyond the library's own; `Semver` serialization;
`RangeList.toString` (its `and`/`or` rendering is not meant to be parsed back); node-semver's `loose` mode and
`diff`, which have no semver4j counterpart; numbers above 2^53 against node-semver (its numeric identifiers are
doubles).

## Bugs found

| id | severity | summary |
|---|---|---|
| semver4j/1 | medium | `compareTo` throws `NumberFormatException` for a pre-release identifier of more than 19 digits |
| semver4j/2 | medium | alphanumeric identifiers containing digits are compared out of ASCII order, and the order is not transitive (`a1b2` > `b1` > `b` > `a1b2`) |
| semver4j/3 | high | a caret, tilde or hyphen range sharing a set with other comparators is dropped (`^1.0.0 <1.5.0` = `<1.5.0`) |
| semver4j/4 | medium | `^0.x`, `^0.0.x`, `^0.0` get the wrong upper bound (`^0.x` matches every version, `^0.0.x` none) |
| semver4j/5 | medium | a wildcard standing for the whole version (`x`, `>=*`, `^*`, `~*`, `1.2.3 - *`, `>=1.0.0 *`) matches nothing or is dropped |
| semver4j/6 | medium | Ivy intervals mixing bracket styles (`[1.0,2.0)`, `(1.0,2.0]`, `(1.0,2.0)`) drop a bound or every version |
| semver4j/7 | low | comparators that are not ranges are silently dropped; an empty result still claims `isSatisfiedByAny` |
| semver4j/8 | low | a trailing `\|\|` is ignored while a leading one matches every version |
| semver4j/9 | low | a range number above `Integer.MAX_VALUE` throws `NumberFormatException` instead of `SemverException` |
| semver4j/10 | low | `withPreRelease`/`withBuild` drop a trailing dot; `"."` clears the identifiers instead of being refused |
| semver4j/11 | low | a pre-release identifier beginning with a hyphen is ordered below numeric identifiers |
| semver4j/12 | medium | `RangeExpression`: an `and()` after an operand holding several sets starts a new set instead of joining the last |

Observed, not recorded: with `includePreRelease`, `1.2.3 - 2.3.4` is `>=1.2.3 <2.3.5-0` in semver4j (as its
Javadoc says) but `>=1.2.3-0 <2.3.5-0` in node-semver, so `1.2.3-alpha` satisfies it only in node — a documented
difference, and hyphen ranges are therefore compared without `includePreRelease` only; `RangeExpression.and(x)` with a multi-set operand flattens it (`a.and(b.or(c))` is
`a b || c`, the text form's reading, not `(a and b) or (a and c)`) — consistent with the Javadoc example, so treated
as the design; `withPreRelease("a+b")` on a version without build metadata yields `1.0.0-a+b` (a pre-release `a`
and build `b`) instead of refusing the `+`; `coerce` strips leading zeros where node-semver returns null
(`coerce("01.1.3")` = 1.1.3) — a deliberate extension; the empty range and `*` are the only wildcards handled as
"any version" (see 5); `RangeList.isSatisfiedByAny()` means "every comparator is `>=0.0.0`", not "some version
satisfies it", contrary to its Javadoc (the empty-list case is in 7).

## History

- 2026-09-16: created (turn 179) at bd961f36a993 (0.0.1-SNAPSHOT of 2026-09-01, after v6.0.0); 12 bugs.
- 2026-09-23: generators rewritten in combinator style (`Gen` as `Generator` values, `weighted`/`chance`, edit and
  entry lists applied by pure functions, `tc.assume` for the coerce skip; `n`/`chance`/`pick`/`word` dropped from
  `Zoo`); same 9 properties, 12 pins and expected failures. A 1 000-case run while checking the rewrite showed
  the `* || 1.2.3-a` pre-release disagreement with node-semver described above (reachable by the old generator
  too, about once in 10 000 cases); judged a node-semver quirk and skipped in `npmRangesMatchNodeSemver`; and that a range's pre-release
  identifiers (`0.0.0-- - 0`) could begin with a hyphen, reaching semver4j/11 through the range property about
  once in 10 000 cases (the old `tamePre` had the same gap) - they are now tame too.
- 2026-09-25: unsteered under rule 11 (the known-bug gates only under `HEGEL_NO_KNOWN=1`; twelve narrow properties;
  `>*` written `>=*`; the precedence transitivity check wraps `compareTo` so bug 1's exception is a failure, not
  an error); the `-0` upper-bound difference above found by the freed generators. 4 tests pass, 29-30 expected
  failures.
