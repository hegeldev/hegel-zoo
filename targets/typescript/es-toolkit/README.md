# typescript/es-toolkit — toss/es-toolkit (`es-toolkit/compat` against lodash)

Hegel property tests for [`es-toolkit`](https://github.com/toss/es-toolkit) 1.52.0, pinned at
`60fe20d3` (main, 2026-09-17): the modern utility library whose `es-toolkit/compat` entry point
reimplements lodash's 300 functions (minus the `sortedUniq` pair) for drop-in migration and
promises to "match lodash behavior exactly". TypeScript, MIT, a yarn 4 workspace whose package
`exports` point at the `.ts` sources. `.github/CONTRIBUTING.md` (checked 2026-09-17) has an AI
Usage Policy — AI tools are welcome, issue and PR descriptions must be written by a human — and
`AGENTS.md`/`CLAUDE.md` instruct coding agents; the zoo only records bugs. The tests target
compat only: the strict `es-toolkit` API has no oracle.

Tests are `hegel/hegel.test.mjs` (ESM, run by `node --test`) with the zoo's harness
`hegel/hegel-zoo.mjs` (under `hegel/`, since upstream's `.gitignore` hides `/test`). Hegel is `@hegeldev/hegel` 0.4.5.

## How it is built

`dist/` is not committed and `yarn` is the package manager, so the setup installs Hegel, lodash
4.17.21 (the oracle) and TypeScript 5.9.3 under `.hegel/` in one `npm install --prefix .hegel`
(a second install there would remove the first, there being no package.json) and compiles `src/`
to CommonJS into `.hegel/dist` with `hegel/tsconfig.hegel.json` (`module: commonjs`,
`rewriteRelativeImportExtensions` for the `.ts` import specifiers, `--noCheck`, the spec files
excluded; about two seconds). `hegel/hegel-dist-package.json` marks the output CommonJS. The tests
`require()` `.hegel/dist/compat/index.js` and `.hegel/node_modules/lodash`.

## How it is tested

Differential testing against lodash 4.17.21, the library compat reimplements. Every case draws a
function and generated inputs, runs the same call in both libraries — through `same(what, f)`,
which runs `f(compat)` and `f(lodash)` and compares canonical descriptions of the results (or the
class of the error thrown), or `sameMutating`, which also compares the input afterwards — and
reports the first difference. `describe()` renders `-0`, `NaN`, holes, symbols, prototypes,
Dates, RegExps, Maps, Sets, typed arrays, boxed primitives and cycles so that two equal-looking
results really are equal. Nothing is drawn inside a `same` callback (it runs twice).

Upstream's scope, from `.github/CONTRIBUTING.md` and `docs/compat/intro.md`, decides what counts:
a compat difference is a bug only if the call compiles against `@types/lodash` in strict mode or
real code makes it; implicit type conversions, the `sortedUniq` family, chaining, modified
prototypes and realms are out of scope. The properties therefore have two kinds of switch:
`Known` (a typed-reachable difference, recorded in `bugs.toml` with a pin) and `Accepted` (a
documented or out-of-type difference, listed below).

- **Collections** (`TestHegelCollectionsLikeLodash`): about fifty-five collection functions
  (map/filter/reduce and friends, the aggregators, `sortBy`/`orderBy`, `find*`, `some`/`every`,
  `partition`, `sample*`, `shuffle`, `size`, `includes`, `invokeMap`, `flatMap*`, `forEach*`) over
  arrays, plain objects, records, array-likes, strings, Maps and Sets, with lodash's iteratee
  shorthands (path, `matches`, `matchesProperty` pair, identity, functions of every arity,
  constants).
- **Arrays** (`TestHegelArraysLikeLodash`): about seventy array functions (`chunk`, `compact`,
  `concat`, the difference/intersection/union/xor families with `By`/`With`, take/drop, flatten,
  `fill`, indexOf family, `sortedIndex*`, `uniq*`, `unzip*`/`zip*`, `zipObject(Deep)`, the mutating
  `pull*`/`remove`/`reverse`, `nth`, `slice`, `castArray`) over generated arrays, arguments
  objects, array-likes and strings.
- **Paths** (`TestHegelPathsLikeLodash`): `get`/`has`/`hasIn`/`set`/`setWith`/`unset`/`update`/
  `updateWith`/`result`/`property`/`propertyOf`/`invoke`/`method`/`methodOf`/`toPath`/`at`/
  `matchesProperty`/`pick`/`omit`/`isKey` with generated paths (dotted, bracketed, quoted,
  arrays, numbers, symbols, malformed).
- **Strings** (`TestHegelStringsLikeLodash`): the thirty-three string functions (case functions,
  `words`, `deburr`, `escape`/`unescape`, `pad*`, `trim*`, `truncate`, `repeat`, `split`,
  `startsWith`/`endsWith`, `template`, `parseInt`, `toLower`/`toUpper`) over ASCII, Latin-1,
  astral and combining-mark strings and generated options.
- **Numbers** (`TestHegelNumbersLikeLodash`): the `to*` conversions, rounding, `clamp`, `inRange`,
  `range`/`rangeRight` (bounded to 100 000 elements), the arithmetic, `sum`/`mean`/`max`/`min`, the
  comparisons, the numeric predicates, `defaultTo`, `times`, `random` (shape only) over numbers,
  numeric strings, `null`/`undefined`, bigints and objects with `valueOf`.
- **Objects** (`TestHegelObjectsLikeLodash`): the assign/defaults/merge family (result and input
  after), `clone*`, `isEqual(With)`, `isMatch(With)`, `conformsTo`, `invert(By)`, `mapKeys`/
  `mapValues`, `keys*`/`values*`/`toPairs*`/`entries*`, `fromPairs`, `functions*`, `toPlainObject`,
  `create`, `findKey`/`findLastKey`, `forOwnRight`/`forInRight`, `pickBy`/`omitBy`, `transform`,
  `isEmpty`, `isPlainObject` over generated targets and sources including class instances,
  inherited properties, symbol keys, Dates, Maps, typed arrays and null-prototype objects.
- **Predicates** (`TestHegelPredicatesLikeLodash`): the thirty-four `is*` predicates over a zoo of
  values (every primitive, boxed primitives, arguments, typed arrays, buffers, Dates, RegExps,
  Errors, Maps, Sets, WeakMaps, Promises, generators, class instances, tag-spoofed and
  prototype-only objects), plus the predicates' own laws on compat alone.
- **Functions** (`TestHegelFunctionsLikeLodash`): about fifty function utilities (`ary`, `unary`,
  `rearg`, `flip`, `negate`, `partial(Right)` with placeholders, `bind`/`bindKey`, `curry(Right)`
  with placeholders and arities, `spread`, `rest`, `nthArg`, `over*`, `flow(Right)`, `before`/
  `after`/`once`, `memoize`, `wrap`, `cond`, `conforms`, `attempt`, the stubs, `iteratee`,
  `matches`, `property`, `toPath`, `uniqueId`; `debounce`/`throttle`/`delay`/`defer` by shape only)
  traced through sequences of calls.

`ZOO_COLLECT=1` prints, per property, the number of differences and the per-function/skip
statistics instead of failing on the first; `HEGEL_TEST_CASES` sets the case count (1000 cases
of all eight properties run clean at the pin).

## Bugs

All 54 are open at the pin; each has a pin `TestHegelPin…` asserting lodash's result that fails
while the bug exists (see `bugs.toml` for the exact inputs).

| id | function(s) | difference from lodash |
| --- | --- | --- |
| 1 | array functions on strings | split into code points, not UTF-16 units (`compact("😀a")`) |
| 2 | transform, pickBy, omitBy, shuffle, sample(Size), findLast, some | array-like objects iterated as lists (`length`/extra keys dropped); `some({length: 0}, p)` iterates keys |
| 3 | chunk, split | no iteratee-call guard: `[[1, 2]].map(chunk)` is `[[]]` |
| 4 | clone, cloneDeep | cloned `arguments` keep `length` and the iterator |
| 5 | invoke, method, methodOf | a missing parent path calls the method on the root |
| 6 | pad, padStart, padEnd | `RangeError` for an infinite length |
| 7 | truncate | `{ length: undefined }` means 30, lodash means 0 |
| 8 | remove | `TypeError` on a string, lodash returns `[]` |
| 9 | set, setWith, update, updateWith | `TypeError` on a primitive target, lodash returns it |
| 10 | toPath, get | malformed brackets kept as key text (`"a]"` → `["a]"]`) |
| 11 | template | `imports._` has two keys, `_.map` in a template throws |
| 12 | clamp, toLength | -0 becomes 0 |
| 13 | merge, mergeWith | symbol-keyed source properties copied |
| 14 | assign family, conformsTo | `TypeError` on a primitive/null target, lodash boxes it |
| 15 | merge, mergeWith | Date/Map/Set/RegExp/typed-array/class-instance sources deep-copied into plain objects |
| 16 | defaultsDeep | undefined array elements and holes left unfilled |
| 17 | matchesProperty (and the shorthand) | `null` matches `undefined` |
| 18 | matchesProperty (and the shorthand) | a primitive value matches any object or `undefined` |
| 19 | merge, defaults, assignIn, extend (+With) | inherited enumerable source properties ignored |
| 20 | isMatch | Map/Set/string sources never match; `{ a: [] }` matches `{ a: 1 }` |
| 21 | isArguments, isDate, isMap, isRegExp | true for spoofed tags and prototype-only objects |
| 22 | isMatch, matches, filter/find shorthands | Dates, RegExps, typed arrays, boxed values compared as `{}` |
| 23 | cloneWith, cloneDeepWith | customizer not applied to Map/Set/typed-array entries |
| 24 | rest | variadic `f`, negative or NaN start: only the last argument grouped |
| 25 | trim, trimStart, trimEnd | astral `chars` compared by code point, lone surrogates stripped |
| 26 | truncate | a string `separator` is compiled as a RegExp |
| 27 | sortBy, orderBy | function iteratee orders `undefined` before `null` |
| 28 | cloneDeep | functions/WeakMaps/Promises returned by reference, Errors cloned as Errors |
| 29 | isEqual | Maps with equal object keys are unequal |
| 30 | isPlainObject | true through a null-prototype ancestor |
| 31 | toNumber (and toFinite/toInteger/toSafeInteger/toLength) | object `valueOf` falls back to `toString` |
| 32 | iteratee, every shorthand | an array iteratee of length ≠ 2 is a `matches` pattern |
| 33 | pad*, truncate, toArray, split | combining sequences, ZWJ emoji, flags counted per code point |
| 34 | concat | `arguments` objects not flattened (flatten does) |
| 35 | cloneDeep, clone, omit, pick(By), omitBy, mapValues/Keys, assign(In), defaultsDeep, zipObject, groupBy/keyBy | an own `__proto__` data key (JSON.parse output) becomes the prototype of the result |
| 36 | cloneDeep, cloneDeepWith | nested null-prototype objects keep the null prototype, the root does not |
| 37 | sortBy, orderBy | an object (`matches`) iteratee is ignored |
| 38 | invert, invertBy | `TypeError` on a value without `toString` (null-prototype object) |
| 39 | startsWith, endsWith | `false` for a nullish string and an empty target (lodash: `true`) |
| 40 | xorBy, xorWith | with three or more arrays, a value shared by non-adjacent arrays survives |
| 41 | cloneDeep, cloneDeepWith | a boxed Symbol is cloned without its symbol data (`valueOf()` throws) |
| 42 | get, has, hasIn, at, property, unset, pick, omit | an empty segment of a string path (`"a."`, `".a"`) is dropped; `toPath`/`set`/`invoke` keep it |
| 43 | findKey, findLastKey | `undefined` on a string (lodash: the key of the matching character) |
| 44 | truncate | `{ length: NaN }` on `""` gives `"..."`, `{ length: -1 }` gives `""` (lodash: the reverse) |
| 45 | truncate | a separator match at the start of the kept part is ignored (`"abcd..."` for lodash `"..."`) |
| 46 | defaultsDeep | an array and a plain object at a shared key are not merged |
| 47 | defaultsDeep | an inherited key gets an own default (lodash leaves it inherited) |
| 48 | merge, mergeWith, defaultsDeep | source objects are mutated when a later source merges into them (lodash clones) |
| 49 | defaultsDeep | an `arguments` object is kept as is (lodash: copied to a plain object) |
| 50 | merge, mergeWith | a `0`/`-0` source value replaces a SameValueZero-equal target value |
| 51 | intersectionWith | a string argument counts as an array of characters (lodash: dropped, as `intersection` does) |
| 52 | isMatch, matches, matchesProperty | a `null` element of an array source matches any element |
| 53 | clone, cloneWith | a function with own properties clones to `{}` (lodash copies the properties) |
| 54 | omit | with a deep path, an array under a nested own `constructor` key is cloned (lodash keeps the reference) |

## Accepted differences (skipped, not counted)

Upstream's documented scope or lodash's own defects, kept out of `bugs.toml`:

- `__proto__` path segments are refused by `get`/`set`/`unset`/`merge` (prototype-pollution
  guard, `tests/__proto__.spec.ts`), and `merge`/`mergeWith`/`defaults` skip an own `__proto__`
  key of a source where lodash copies it as an own key; the properties never write through
  `__proto__` and skip reading it. (Bug 35 is the opposite case: the other object functions turn
  an own `__proto__` key into the result's prototype.)
- The aggregators (`groupBy`, `countBy`, `keyBy`, `partition`, `sumBy`, …) call the iteratee with
  `(value, index, collection)`; lodash passes one argument (the types declare one).
- String collections: lodash passes the boxed `String` to callbacks and as the third argument,
  compat passes the primitive (as lodash's own types say).
- BigInt operands: lodash predates BigInt (`toNumber(1n)` and `toString(0n)` throw), compat
  converts them.
- Word splitting is Unicode-aware in compat (Cyrillic/Greek case splits, ZWJ/regional/skin-tone/
  VS16 emoji, `µ`, `©`, `ª`, `º`): the case functions, `words` and `deburr` are compared on ASCII
  and Latin-1 only.
- Out-of-type inputs: symbols and numbers to string functions, `trim(s, null)`, `pick(obj,
  undefined)`, `omit(obj, null)`, `pick(obj, true)`, `unset(obj, undefined)`, `invert(null)`, `findLastIndex(arr, true)`, string merge sources,
  `add("1e3", null)`, symbols in `min`/`max`, the `pull` family on arguments objects, `unzip`/
  `fromPairs` of non-array elements, writing through an inherited function
  (`set(o, "toString.length", v)`, or `updateWith(arr, "length.q", f, Object)` and `setWith(o, "0.1", v, Object)` over
  `o[0] === "zero"`, where the intermediate is a primitive or a boxed string: lodash's sloppy-mode assignment is ignored, compat's throws),
  non-function `conformsTo` predicates.
- `sortedUniq`, `sortedUniqBy`, chaining, `tap`/`thru`/`mixin` are documented out of scope and not
  exported.
- lodash 4.17.21's `lastIndexOf(array, undefined)` returns `array.length` (its strictLastIndexOf
  reads one past the end); compat returns the real index. With a `-0` fromIndex compat returns
  `-0` as the index of a match at 0 where lodash returns `0`.
- lodash 4.17.21 predates `BigInt64Array`/`BigUint64Array`: its `cloneDeep` of one is `{}` (not in its
  cloneable tags), so the clone family is not compared on them (`accepted-lodash-predates-bigint-arrays`).
- `max`/`min`/`sum`/`mean` and their `By` forms over collections containing symbols: lodash throws
  on the comparison, compat skips them.
- `isFunction` of an async generator function is true in compat, false in lodash 4.17.21.
- lodash's `compareAscending` returns 1 for NaN against NaN whichever way round, so `orderBy` with
  a `desc` order reverses tied NaN elements (an inconsistent comparator); compat keeps them
  stable. `orderBy` over a collection holding NaN is skipped.
- lodash's `truncate` tests `string.slice(end).search(separator)` for truthiness, so when the cut-off
  remainder starts with a separator match (index 0) it skips the cut at the last separator
  (`truncate("foo_bar   padded  ", { length: 12, separator: /,? +/ })` is `"foo_bar  ..."`);
  compat cuts (`"foo_bar..."`). Skipped when the remainder starts with a match.

## Not tested

The strict `es-toolkit` API (no oracle), `debounce`/`throttle`/`delay`/`defer` timing, the
compiled source of `template`, `memoize.Cache`'s identity, `bindAll`, realm-crossing values and
modified built-in prototypes.

## History

- 2026-09-17: target added at 60fe20d3 (1.52.0), 8 properties, 42 bugs.
- 2026-09-17: base bumped 60fe20d333e6 → 82ce4af4f35e (2026-09-17, "docs(contributing): limit compat fixes to inputs Lodash's types allow or real code passes (#2108)"; 1.52.0); 42 bug(s) still reproduce. 8 tests pass.
- 2026-09-20: base bumped 82ce4af4f35e → ee72fc74b763 (2026-09-19, "fix(compat/words): match emoji sequences, non-ASCII numerals and symbols (#2110)"; 1.52.0); 42 bug(s) still reproduce. 8 tests pass.
- 2026-09-24: generators rewritten in combinator style (one drawn record per property, shapes for the known bugs instead of skips); twelve more differences found by the new shapes, 20000-case collect runs and 2000-case rounds, es-toolkit/43-54. 8 tests pass.
