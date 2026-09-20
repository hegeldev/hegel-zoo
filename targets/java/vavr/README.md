# vavr

[vavr-io/vavr](https://github.com/vavr-io/vavr): persistent, immutable collections (`List`,
`Vector`, `Array`, `Stream`, `Queue`, `CharSeq`, `HashSet`/`LinkedHashSet`/`TreeSet`/`BitSet`,
`HashMap`/`LinkedHashMap`/`TreeMap`, multimaps) and functional control types (`Option`, `Try`,
`Either`, `Lazy`, `Validation`, tuples, `Function1..8`, the `API` pattern matching) for Java.
Pinned at the 2.0.0-SNAPSHOT commit 92f407eb (2026-09-12); Apache-2.0. CONTRIBUTING.md allows
AI-assisted contributions provided the author stands behind every line and opens an issue before
non-trivial work — the zoo only records bugs, it contributes nothing. The sixth Java target: the
patch adds a Maven module `hegel/` depending on `io.vavr:vavr:2.0.0-SNAPSHOT`, which
`[run] setup` builds and installs from the pinned tree (`mvn -DskipTests … install`, about a
minute; needs JDK 21+ and Maven 3.9.9+). The harness `Zoo.java`, the judge's `ZooListener` and
three test classes live in `hegel/src/test/java/zoo/`. See HACKING.md for the Java mechanics.

## What is tested

The oracles are `java.util` collections (`ArrayList`, `HashSet`/`LinkedHashSet`/`TreeSet`,
`BitSet`, `HashMap`/`LinkedHashMap`/`TreeMap`, a `Map<K, Collection<V>>` for multimaps) plus
`String`/`StringBuilder` for `CharSeq`, exact `BigInteger`/`BigDecimal` arithmetic for the range
factories, and the rules stated in the Javadoc of `Traversable`, `Seq`, `Collections`, `Option`,
`Try`, `Lazy`, `Validation` and the function interfaces. Generated sequences are 0–30 small ints
(so duplicates are common) with 12% nulls, built by four different paths per kind (`ofAll`,
varargs `of`, the collector, `tabulate`, and enqueue-after-churn for `Queue`); indices include the
int extremes.

`VavrTest`:

- **sequencesFollowTheirDocumentedRulesAgainstAnArrayListModel** — a `List`, `Vector`, `Array`,
  `Stream` or `Queue` against an `ArrayList`: size and iteration; `head`/`last`/`init`/`tail`/
  `single`/`reduce` and their exceptions; the index rules of `get`, `update`, `removeAt`,
  `asPartialFunction`, `insert`, `insertAll`, `patch`, `iterator(i)` (lazy `Stream`s are forced
  first); the clamping of `take`/`drop`/`takeRight`/`dropRight`/`splitAt` (bug /3 skipped); `slice`
  never throwing (bugs /5 and /6 skipped) and `subSequence` throwing bounds-before-order;
  `span`/`takeWhile`/`dropWhile`/`takeUntil`/`dropUntil`/`takeRightWhile`/`dropRightWhile`/
  `prefixLength`/`partition`/`filter`/`reject`/`count`/`exists`/`forAll`/`find`/`findLast`/
  `segmentLength`; `indexOf`/`lastIndexOf` with and without a start, `indexOfOption`,
  `indexOfSlice`/`lastIndexOfSlice`/`containsSlice`, `startsWith` with an offset, `endsWith`;
  `reverse`, `reverseIterator`, `toJavaList`, the read-only `asJava` view, `toJavaStream`,
  `collect`; `rotateLeft`/`rotateRight`; `intersperse`/`padTo`/`leftPadTo`/`append`/`prepend`/
  `appendAll`/`prependAll`; `remove` (bug /1 skipped), `removeAll`, `removeFirst`, `removeLast`,
  `replace`, `replaceAll`; `distinct`/`distinctBy`/`distinctByKeepLast`; `grouped`/`sliding`/
  `slideBy` and their `IllegalArgumentException`s; `zip`/`zipAll`/`zipWithIndex`/`zipWith`/
  `unzip`; `foldLeft`/`foldRight`/`scanLeft`/`scanRight`/`mkString`/`map`/`flatMap`; `toString`
  as `Kind(a, b)`, `hashCode` equal to `java.util.List`'s, equality across the five kinds and
  inequality with a `HashSet`, `Value.eq`; `sorted` (both orders), `sortBy`, stability, `search`;
  the typed `sum`/`product`/`average`/`min`/`max` rules and the null rules (single null gives
  `Some(null)` — `min` skipped for bug /2 — two or more throw); `sorted(nullsFirst)`; `groupBy`
  key and element order; `combinations`, `combinations(k)`, `permutations` (skipped for the
  `List`/`Queue` shape of bug /1) and `crossProduct(power)` for length ≤ 6; `shuffle` as a
  multiset; `orElse` laziness; spliterator characteristics; a Java serialization round trip;
  `IndexedSeq` classification.
- **rangesMatchExactArithmeticAndStreamsStayLazy** — `range`/`rangeClosed`/`rangeBy`/
  `rangeClosedBy` for int, long and char on `Iterator`, `Vector` (guarded against eager
  materialisation of huge ranges), `Stream`, `List`, `Array` and `CharSeq` against a `BigInteger`
  arithmetic-sequence model at random and extreme bounds and steps (including `Integer.MIN_VALUE`,
  `MAX_VALUE` and the step-0 `IllegalArgumentException`); double ranges against a `BigDecimal`
  model; the documented examples; `Stream.from` wrapping; that infinite `Stream`s stay lazy under
  `take`/`map`/`zipWithIndex`/`iterator`; `Stream.cons`; an exhausted `Iterator` throwing
  `NoSuchElementException`.

`VavrMoreTest`:

- **setsMapsAndMultimapsMatchTheirJavaModels** — a `HashSet`, `LinkedHashSet` or `TreeSet` under
  `add`/`remove`/`addAll`/`removeAll`/`union`/`intersect`/`diff` against the matching `java.util`
  set (elements, insertion or sorted order, `head`, `contains`, the documented unordered
  `hashCode` `1 + Σ hash`, equality across set kinds and with `TreeSet`, inequality with a `Seq`
  or `Map`, `toString`, `toJavaSet`, `toSortedSet`, `map`/`filter`, the algebra with itself, a
  serialization round trip, a `TreeSet` with `reverseOrder`); `BitSet` against `java.util.BitSet`
  (`add`/`remove`/`contains`/`range`/`union`/`intersect`, `toString`, equality with `HashSet`, the
  `IllegalArgumentException` for negatives); a `HashMap`, `LinkedHashMap` or `TreeMap` under
  `put`/`remove`/`merge` (all three resolution forms)/`computeIfAbsent` against the matching
  `java.util` map (`get` as `Option`, `containsKey`, `contains(tuple)`, `getOrElse`, `toJavaMap`,
  `keySet`/`values` and their order, `toString`, `hashCode`, equality across map kinds,
  `mapValues`/`filterKeys`/`filterValues`/`computeIfPresent`, `put` replacing, `remove`,
  serialization, a `TreeMap` with `reverseOrder`); a `HashMultimap` with `Seq`, `Set` or
  `SortedSet` containers under `put`/`remove(k, v)` against a `Map<K, Collection<V>>` (`size`,
  `getContainerType`, `get`, `keySet`, `toJavaMap`).
- **charSeqMirrorsString** — a `CharSeq` built from a generated string (letters, digits,
  whitespace, `ß`, `İ`, a combining accent, an emoji and lone surrogates) against `String`:
  `length`, `charAt`/`codePointAt`/`get`, the code-point `indexOf`/`lastIndexOf(int[, from])`,
  the `Seq` `indexOf(Character)`, `indexOf`/`lastIndexOf`/`contains`/`startsWith`(+offset)/
  `endsWith` with another `CharSeq`, `substring` and `subSequence` with `String`'s exceptions,
  `split` with and without a limit, `replaceAll`/`replaceFirst`/`matches`, `replaceAll(Character)`
  and `replace(Character)`, upper/lower case with and without a locale, `trim`, `repeat`,
  `concat`/`appendAll`/`prependAll`, `toCharArray`, `codePointCount`, `regionMatches`,
  `compareTo`/`compareToIgnoreCase`/`equalsIgnoreCase`, `contentEquals`; equality and `hashCode`
  with a `List<Character>` of the same chars; `reverse` (bug /4 skipped for supplementary
  characters), `distinct`, `sorted`, `take`/`drop`, `mkString`, `filter`, `map`, `stringPrefix`,
  a serialization round trip.
- **controlTypesFunctionsAndTuplesObeyTheirLaws** — `Option` (`of(null)` vs `some(null)`, the
  `None` singleton, `map`/`filter`/`getOrElse`, `Optional` conversion, `sequence`, `when`,
  `Value.eq` across `Option` and `List`); `Try` (`of`, `recover`, `toOption`/`toEither`,
  capture of `AssertionError`, propagation of the fatal `StackOverflowError`/`LinkageError`/
  `InterruptedException`, `run`, `Failure` equality and `toString`, `andFinally` running once,
  `andFinallyTry` suppression, `sequence`, `Function1.lift`/`liftTry`); `Either` (`swap`
  involution, right bias of `map`, `mapLeft`, `fold`, `cond`, projections, `toString`, equality);
  `Lazy` (`Lazy(?)` before evaluation, single evaluation, `equals` forcing, retry after an
  exception, `map`/`filter`, serialization forcing); `Validation.combine` accumulating errors in
  order for two and three operands; `Function1`/`Function2` (`curried`/`tupled`/`reversed`/
  `andThen`/`compose`/partial application, `memoized` computing once and caching null arguments,
  `isMemoized`, `identity`/`constant`); tuples (`toString`, equality, `arity`, `swap`, `map1`,
  `update2`, `apply`, `compareTo`, `toSeq`, serialization, the `Tuple0` singleton);
  `Predicates`; `API.For(...).yield` as a cross product; `Match`/`Case`/`$` with `option` and
  `MatchError`.

`VavrPinsTest` — one pin per bug in bugs.toml, asserting the documented behaviour; each fails
while its bug exists and is listed in `target.toml` `[expected_failures]`.

## Not tested

`Future`/`Promise` and everything concurrent; `Tree`; `PriorityQueue`; `SortedMultimap`s other
than through `HashMultimap.withSortedSet`; the annotation processor and the pattern-matching
`Patterns`; `Iterator` beyond the range factories and `min`; `Function3..8` and `CheckedFunction`s;
`Value` conversions other than the ones listed; serialization compatibility across versions;
performance. Nothing is checked against a previous release: the model is the Javadoc.

## Bugs

See bugs.toml. Six so far: `List`/`Queue.remove(element)` (and hence `List.permutations()`)
throwing on nulls (/1), `min()` of a single null throwing instead of `Some(null)` (/2),
`Vector.takeRight`/`dropRight` overflowing for large negative n (/3), `CharSeq.reverse` keeping
surrogate pairs in order against the `Seq` contract (/4), `Stream.slice` returning the head for a
slice ending at or before index 0 (/5), and `Array.slice` throwing `NegativeArraySizeException`
for negative bounds (/6). All still reproduce.

## Observed and not recorded

- `Stream`s defer the `IndexOutOfBoundsException` of `insert`/`insertAll`/`removeAt`/
  `subSequence` until the tail is evaluated (the `Stream.subSequence` Javadoc says so; the tests
  force the result with `toList()`), and `Stream.subSequence(b, b)` beyond the end is therefore
  an empty stream, while `update` beyond the end throws eagerly.
- `Stream.remove(element)` returns a `List`, not a `Stream` (the static type is `Seq`).
- `Collections.subSequenceRangeCheck` checks the bounds (`IndexOutOfBoundsException`) before the
  order (`IllegalArgumentException`), so `subSequence(-1, -3)` is an index error; the Javadoc
  lists both without an order.
- `Vector.rangeClosedBy(Integer.MIN_VALUE, Integer.MAX_VALUE, 1)` materialises eagerly and runs
  out of heap (documented eagerness; a hazard for tests, which Hegel reports as a flaky test).
- `LinkedHashSet.union(set)` appends the new elements in the *argument's* iteration order
  (documented "encounter order"), so a `HashSet` argument yields hash order.

## History

- 2026-09-16: created at 92f407eb (2.0.0-SNAPSHOT); bugs /1–/6.
- 2026-09-20: base bumped 92f407eb8a91 → d8c77137bf2a (2026-09-19, "Fix sequence rotations by Integer.MIN_VALUE (#3352)"; 2.0.0-SNAPSHOT); 6 bug(s) still reproduce. 5 tests pass.
