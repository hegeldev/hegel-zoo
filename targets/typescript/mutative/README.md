# mutative

[unadlib/mutative](https://github.com/unadlib/mutative): immutable updates through a mutable draft, in
the manner of immer — `create(base, draft => { ... })` proxies the base, records the mutations and
finalizes a new state with structural sharing, with optional patches/inverse patches (`apply`),
auto-freeze, a strict mode, `mark` for class instances, and `current`/`original`/`rawReturn`/`unsafe`.
Pinned at 1.3.0 (63774685, 2026-08-14). MIT; nothing in the repository speaks about AI. The tests are
`hegel/hegel.test.mjs` (node:test, `TestHegel...` properties and `TestHegelPin...` pins), `hegel/gen.mjs`
(the generators, the model and the comparisons) and the zoo's shared `hegel/hegel-zoo.mjs`. See HACKING.md
for the JavaScript mechanics; `hegel/tsconfig.json` compiles `src/` as CommonJS into `.hegel/dist` with
`__DEV__` defined by the tests (the development build, as upstream's jest runs it).

## What is tested

The oracle is plain JavaScript itself: a base state is a random tree of objects, arrays, Maps and Sets
over primitives (with -0, NaN, bigints, undefined) and Dates (atomic); a script is a list of ordinary
operations (`set`/`delete`/`Object.assign`, `push`/`pop`/`shift`/`unshift`/`splice`/`reverse`/`sort`/
`fill`/`copyWithin`/index and `length` writes, `Map.set`/`delete`/`clear`, `Set.add`/`delete`/`clear`,
assignments of one subtree into another place — the same draft at two paths, plain or wrapped in a new
object/array — and assignments of the base's own child object back into the tree), each addressed by a
path and generated against a live clone of the base, so indexes and keys are valid when drawn. `exec`
performs the very same operation on a clone (the model), on a mutative draft and on an immer 10.2 draft
(`enableMapSet`, auto-freeze off, its own clone of the base); the model is the verdict and immer's
agreement is counted, since immer has its own defects (a revoked draft left in a result, `applyPatches`
dropping `add` of null to a Set, `current` running out of memory on a Set with an aliased element).

- *TestHegelCreateMatchesTheModelAndImmer* — the state equals the model (key order, Map and Set order
  included), the base is unchanged, no draft or frozen node leaks, an empty script returns the base
  itself, and every base subtree no op touched is the very same object in the state (structural sharing).
- *TestHegelPatchesReplayAndInvert* — with `enablePatches` in its four shapes (`pathAsArray`,
  `arrayLengthAssignment`): `apply(base, patches)` is the state and `apply(state, inverse)` the base
  (up to order — a re-added key or element lands at the end), `apply(..., { mutable: true })` on a copy
  agrees, immer's `applyPatches` accepts the array-path patches (except paths into Set elements, which
  immer does not have), fast-json-patch applies and validates the JSON-pointer patches of JSON-like
  states, the patches of two consecutive `create`s compose, and `apply` accepts immer's patches for the
  same script.
- *TestHegelCurrentAndOriginalDuringTheDraft* — after each op `current(root)` equals the model so far and
  holds no draft, `original(root)` is the base, an untouched node read through the draft is a draft whose
  `original` and `current` are the base's own object, and `current` just before the end equals the state.
- *TestHegelReadsThroughTheDraftMatchTheModel* — `Object.keys`/`Reflect.ownKeys`/`in`/`hasOwnProperty`/
  descriptors/spread/`JSON.stringify`, array `length`/`indexOf`/`includes`/`at`/`entries`/`slice`, Map
  `keys`/`values`/`has`/`get`/`forEach`, Set `has`/iteration/`forEach` and the new Set methods (`union`,
  `intersection`, ..., `isSubsetOf`) read through the draft agree with the model at every step.
- *TestHegelFrozenBasesAndAutoFreeze* — a deep-frozen base gives the same state; `enableAutoFreeze`
  freezes every object and array of the state and makes every Map and Set throw on mutation.
- *TestHegelCurriedAsyncAndMakeCreatorAgree* — `create(fn)(base)`, `create(base)` + `finalize`,
  `makeCreator(options)` in its forms, a curried producer with extra arguments and an async draft function
  with awaits between the ops all give the state and patches of the plain call.
- *TestHegelReturnValuesFollowTheRules* — a fresh value or `rawReturn` replaces the root (patches
  `replace []`), the draft or `undefined` finalizes the mutations, an untouched child draft is the base's
  child, a spread of the root draft finalizes to the base's children, mutating and returning a fresh
  value throws, `isDraft`/`isDraftable` on nodes and leaves.
- *TestHegelClassInstancesUnderMark* — class instances marked `"immutable"` are drafted like objects
  (immer: `immerable`), with patches replayed through `apply(..., { mark })`.
- *TestHegelStrictModeGuardsNonDraftables* — in `strict` mode reading a Date through the draft throws,
  `unsafe` reads it, other leaves read normally, and a script without Dates gives the plain state.

Conventions, not bugs: each path to a shared object in the base gets its own draft (documented), so the
second step of the compose check models the state as a clone without sharing; `current()` returns plain
objects inserted during the draft by reference (later mutations through the draft show in an earlier
`current()` result — immer too); `Set` patches address element changes by index path, which immer's
`applyPatches` cannot follow, and a Set `remove` patch carries the element by reference (`apply` calls
`delete(patch.value)`, as immer does), so a replay on a *copy* of the base cannot remove a Date or
object element; immer's `applyPatches` stringifies path segments that are not strings or numbers, so
Maps keyed by booleans, null or NaN are not replayed through immer; with `pathAsArray: false` Map keys
become strings, so a Map with number or
boolean keys does not round-trip through string patches; `enableAutoFreeze` leaves `Object.isFrozen`
false on Maps and Sets (their mutators throw); in strict mode a Set holding a Date cannot be iterated at
all; assigning the base's own object at another key and mutating it there mutates the base (immer
likewise).

Not covered: `mark` returning a custom shallow-copy function or `"mutable"`, subclasses of Map/Set,
getters/setters and non-enumerable or symbol properties, `castDraft`/`castImmutable` (types only), the
production build (`__DEV__` false: same logic, shorter errors), circular references (rejected under
auto-freeze in development).

## Bugs

Fourteen, all pinned (`TestHegelPin...`) and recorded in `bugs.toml`: a Set draft moved to another key
(`reverse`, `unshift`, `sort`, `d.b = d.a; delete d.a`, or wrapped into a new array that replaces it)
finalizes to its unmodified value (mutative/1, high); a Set draft iterates the -0 it was given where a
Set holds +0 (/2); assigning the base's own child back after modifying its draft emits a `remove` patch
(/3); `x[k] = undefined` after deleting `k` (or after `pop`/`shift`/a shorter `length`) is ignored when
the key existed in the base (/4); a second iteration of a Set draft yields `null` for an array element
the first one drafted — `[...d][0].push(2); [...d][0].push(3)` throws — and `current()` shows the null
(/5, high); `apply` cannot replay the root `replace` patch `create` emits when the draft function returns
a Date (/6); returning an untouched child draft after mutating the root silently drops the mutation (/7);
`current()` throws when a Set added during the draft holds a draft or a NaN (/8); patches for a Set whose
element was modified and another element added or removed describe the element twice, so the inverse
fails and a replay on a copy duplicates the element (/9); an array with a modified element draft, moved
by its parent's `unshift` and modified again, emits its element patches under its old index, so the
inverse does not apply (/10); array patches do not tell 0 from -0, so `d[0] = -0` over a 0 (or a
`reverse` swapping them) emits no patch and a replay misses the change (/11); an element draft that
was only read into and then moved by its parent (`d[0][0]; d.reverse()`) finalizes to a shallow copy
instead of the base object (/12, found 2026-10-06 with /11); under `enableAutoFreeze` the development build
throws `Forbids circular reference` for a state without a cycle that holds a modified copy of a base node
beside the node itself - its draft aliased into a sibling, the base's node assigned back, the new draft
changed to hold the sibling - because `deepFreeze` canonicalizes every finalized copy to its original
(/13, found 2026-10-06 by the unsteered Frozen property); a draft assigned into an object, array, Map or Set that
the same draft function then replaces by a primitive still emits its patch at the vanished path, ahead of the
container's replace, so `apply(state, inverse)` throws (/14, found 2026-10-06 by the Patches property under
`HEGEL_NO_KNOWN=1`, one case in a few thousand).
Drawn by default (STYLE.md rule 11, the whole target since 2026-10-06): the generators draw the shapes
of all fourteen recorded bugs, and a mismatch whose scenario has a recorded shape fails with
`(shape of mutative/N)` on its first line, so the wide properties fail at their natural rates and are
expected failures mapped to the bug they most often shrink to: `TestHegelPatchesReplayAndInvert` fails
every run (the /1, /3, /4, /5 and /9 shapes are 5% of its cases together; it shrinks to /4 most often,
also to /3, /9, /1, /5, and to /11 and /14 at a few cases in ten thousand), and the other seven fail in about
half the 100-case runs and every 1000-case run, mapped intermittent: Create → /5 (also /4, /1, /12),
Current → /5 (also /1, /4, /8), Reads → /2 (also /5), Frozen → /5 (also /4, /1, /13), ReturnValues → /6
(its /7 and /5 cases shrink to /6's smaller one), Mark → /3 (also /9, /1), Strict → /5 (also /1). Beside
them one narrow property per bug (`TestHegelMovedSetDraftsKeepTheirChanges`,
`TestHegelSetDraftsIterateZeroForNegativeZero`, `TestHegelAssigningTheOriginalChildBackEmitsNoPatch`,
`TestHegelUndefinedAssignedToAVacatedKeyIsKept`, `TestHegelSetDraftsYieldTheirArrayElementOnEveryIteration`,
`TestHegelApplyReplaysARootReplaceToADate`, `TestHegelReturningAnUntouchedChildDraftAfterAMutationThrows`,
`TestHegelCurrentWorksWithAFreshSetHoldingDraftsOrNaN`, `TestHegelSetElementChangePatchesInvertBesideAnAddOrRemoval`,
`TestHegelMovedArrayPatchesUseTheirNewIndex`, `TestHegelArrayPatchesTellZeroFromNegativeZero`,
`TestHegelMovedUntouchedDraftsFinalizeToTheBaseObject`, `TestHegelAutoFreezeAcceptsARestoredNodeBesideItsModifiedCopy`,
`TestHegelPatchesOfAContainerReplacedAfterHoldingADraftInvert`),
each over the bug's shape region with random contents and the same oracle, failing every run; and the
pins. `HEGEL_NO_KNOWN=1` (read once) counts such mismatches as `known mutative/N` and rejects the case
(assume) or leaves the check out, and skips the narrow properties whole; the skips are 5% of Patches'
cases, 3.5% of Strict's and under 2% elsewhere. The documented conventions above are tolerated in both
modes. The rare Patches failure seen under the switch on 2026-10-06 (one in some ten thousand cases)
was two shapes, found and classified in 650 000 cases on 2026-10-07: the mutative/4 set trap reached
through `apply` (a composed inverse removes a key the base held `undefined` and a later patch adds it
back without a value: the assignment of undefined after the delete in one draft is dropped), named
mutative/4; and an immer patch whose value carries one of immer's own drafts (a Map draft aliased into
a new object and changed through the alias), which immer's applyPatches still replays but mutative's
apply copies as an object, counted as `immer patches carry a draft` beside `immer patches incomplete`.
With both named, 750 000 more cases under the switch had two mismatches, in one 5000-case run whose
messages were not kept, so a shape rarer than one in 300 000 may remain; the property runs 5000
cases a second, so a hunt is cheap. `ZOO_COLLECT=1` prints the counts at the end of each property.

## History

- 2026-09-19: created at 63774685 (1.3.0, 2026-08-14) with 9 properties and 10 bugs.
- 2026-10-06: unsteered (STYLE.md rule 11): the ten older gates became failures naming their shape, one narrow property per
  bug, `HEGEL_NO_KNOWN=1` the only way past them; the Frozen property then found mutative/13 and the Patches property, under the switch, mutative/14.
- 2026-10-06: weekly 1000-case run 37296133806 failed the Create and Patches properties; triage found mutative/11 (array patches blind to the sign of zero) and /12 (moved untouched draft finalizes to a copy), narrow properties and pins for both, the wide properties mapped intermittent; test flaws fixed on the way (untouched-path tracking follows moved nodes, `restore` drawn only into the base's own containers, immer's incomplete alias patches and 0/-0 replay counted as oracle defects, /4 and /10 gates widened to new routes).
