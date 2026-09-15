# jsondiffpatch

[benjamine/jsondiffpatch](https://github.com/benjamine/jsondiffpatch) (npm `jsondiffpatch`):
diff, patch, unpatch and reverse for JSON values with a compact delta format, LCS array diffs
with move detection, text diffs through diff-match-patch, and formatters (JSON-Patch RFC 6902,
annotated, html, console). Pinned at 0.7.6 (a60db8a2, 2026-05-14), the `packages/jsondiffpatch`
member of the workspace. The tests are `test/hegel.test.mjs` with the zoo's harness
`test/hegel-zoo.mjs`, next to upstream's vitest specs.

The repository is an npm workspace root, so the setup installs at the root with workspaces off
(Hegel, the one runtime dependency `@dmsnell/diff-match-patch`, `@types/node` for the package's
tsconfig and `fast-json-patch` as the RFC 6902 oracle) and builds `lib/` with the package's own
tsconfig (TypeScript 5.8.2, the lock's version); the tests import `../lib/`.

## What is tested

The oracles are the library's own inverse pairs, an LCS length computed in the test,
fast-json-patch (a validating RFC 6902 implementation) and the documented delta format. Values
are JSON of depth up to 3 with property names the format cares about (numeric strings, `""`,
`"-"`, `/` and `~`, non-ASCII, and rarely `constructor`/`toString`/`hasOwnProperty`/`valueOf`/
`length`), numbers including `-0`, `1e21` and `2**53`, short strings and long ones for text
diffs; the second value is a few edits of the first (insert/delete/rename/replace properties,
insert/delete/move/duplicate/reverse/shuffle array items, edit strings by code points) either
sharing unchanged parts by reference or deep-copied, or an unrelated value; "id lists" are arrays
of `{id, v}` objects diffed with an `objectHash`. Options are drawn per case: `detectMove`,
`includeValueOnMove`, `matchByPosition`, `cloneDiffValues`, `omitRemovedValues`, `textDiff.minLength`.

- **TestHegelPatchUnpatchAndReverseInvertDiff** — `diff` does not mutate its inputs; no delta
  only for equal values; the delta survives `JSON.parse(JSON.stringify(…))`; `patch(a, delta)`
  and `patch(a, wire delta)` are `b`; with `cloneDiffValues` the delta shares no object with
  the inputs; unless `omitRemovedValues`, `unpatch(b, delta)` is `a`, `patch(b, reverse(delta))`
  is `a`, `patch(a, reverse(reverse(delta)))` is `b`, `unpatch(a, reverse(delta))` is `b`; the
  annotated, html and console formatters return a string without rendering an error.
- **TestHegelArrayDeltasAreLcsMinimalAndWellFormed** — arrays of primitives from a small
  alphabet, or id lists with an `objectHash`: the delta has `_t: "a"`; `_i` keys are left
  indices holding a deletion of the left item or a move to a right index whose item matches (with
  `""` or, with `includeValueOnMove`, the value); numeric keys are right indices holding an
  insertion of the right item or (id lists only) a nested delta; deletions + moves = n − LCS
  and insertions + moves = m − LCS (no moves with `detectMove: false`); patch and unpatch invert.
- **TestHegelJsonPatchFormatterMatchesRfc6902** — `formatters/jsonpatch.format(delta)` gives
  add/remove/replace/move ops with well-formed pointers; **fast-json-patch applies them** (validating)
  to `a` and gets `b`; the library's own `formatters/jsonpatch.patch` gets `b` too (except for
  whole-document ops, which an in-place applier cannot do); the ops of `reverse(delta)` take `b` to `a`.
- **TestHegelTextDiffsPatchUnpatchAndReverse** — with the `with-text-diffs` entry point and
  every `minLength`: two strings both at least `minLength` long give a `[unidiff, 0, 2]` delta
  and shorter ones `[a, b]` (bare, in an object, in an array item object); patch, the JSON-serialised
  delta, unpatch, double reverse; `formatters/jsonpatch.format` refuses text diffs as documented.
  Strings mix newlines, tabs, CR, `%`/`%20`/`%0A` (the format URL-encodes), `+`/`-`/`@@`, non-ASCII
  and emoji (surrogate pairs).
- **TestHegelDatesRegExpsAndCloneRoundTrip** — values with Dates and RegExps (flags from `""` to
  `dgimsy`, `u`, `v`): `clone` is equal (Dates by time, RegExps by source and flags) and shares no
  object; `JSON.parse(…, dateReviver)` restores the Dates; diff/patch/unpatch invert.

## Bugs

Nine, all recorded in `bugs.toml` with a pin each:

- **jsondiffpatch/1** (medium) — properties named after `Object.prototype` members: an added
  `toString` is not diffed, a removed `constructor` makes `diff` throw "functions are not
  supported", and the html/annotated formatters render "cannot format delta type: unknown".
- **jsondiffpatch/2** (low) — `clone(/a/s)` throws "Invalid RegExp" (flags `s`, `d`, `v`).
- **jsondiffpatch/3** (low) — `patch(/a/, diff(/a/, /b/))` is the string `"/b/"` (no flag, or
  `s`/`d`/`v`); conversely an array or string replacing a RegExp is parsed as a RegExp string.
- **jsondiffpatch/4** (low) — the diff-match-patch instance is cached per process: an instance
  created without it produces text diffs once any text-diffing instance ran.
- **jsondiffpatch/5** (high) — `reverse` misplaces item deltas (nested deltas and
  modifications of matched items) in array deltas with insertions/deletions/moves (the index
  arithmetic compares against the running index), so `unpatch` changes the wrong item, leaves an
  `undefined` hole or throws; about 3% of id-list cases.
- **jsondiffpatch/6** (low) — the bundled RFC 6902 applier rejects `/-` paths on objects, which
  the formatter emits for a `"-"` property and fast-json-patch applies.
- **jsondiffpatch/7** (low) — `diff({_t: 1}, {_t: 2})` gives a delta `patch` refuses ("patch failed").
- **jsondiffpatch/8** (low) — `diff(/a/i, /a/i)` (equal, distinct RegExps) is a modification delta.
- **jsondiffpatch/9** (medium) — a RegExp against a plain object is diffed as an empty object:
  `diff({}, /a/)` is `undefined`, `diff({x: 1}, /a/)` deletes `x`.

## Limits

- A changed primitive array item is a removal plus an insertion (only objects match by position
  or by hash), so no text diff appears for strings directly in arrays — by design.
- `omitRemovedValues` deltas are irreversible (documented): only the forward direction is checked.
- `formatters/jsonpatch.patch` works in place, so whole-document ops (a root replacement, e.g.
  array against object) are only checked with fast-json-patch.
- The html/annotated/console formatters are only checked for returning a string without an error
  node; their output is not modelled. The formatters print stack traces with `console.error` on
  the way (visible as `# Error:` lines in the TAP output for bug /1 cases).

## Not tested

- `propertyFilter`, custom pipes/filters (plugins), `DiffPatcher.options()`, the `bin/` CLI, the
  MCP package, the demos, the `console` formatter's colours, the html formatter's move arrows,
  `jsonpatch.patch` with `copy`/`test` ops (the formatter never emits them).

## History

- 2026-09-15: created at a60db8a2 (0.7.6); nine bugs (jsondiffpatch/1–9).
