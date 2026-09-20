# typescript/path-to-regexp — pillarjs/path-to-regexp (against models of its own grammar)

path-to-regexp turns route strings such as `/users/:id{.:ext}` into regular expressions,
matchers and path builders (~160M weekly downloads: Express 5's router, many others). The patch
checks the v8 syntax end to end — parse/stringify and compile/match round trips, `compile` and
`parse` against reference models written from the Readme, group expansion and path arrays,
the matching options, and the ReDoS safety of every generated regular expression with
`recheck` — and pins 4 bugs.

## How it is built

`src/index.ts` is one file with no dependencies. The setup installs Hegel, TypeScript and
`recheck` under `.hegel/` and compiles the file to `dist/index.js` (CommonJS, ES2022) with
`tsc` directly, since upstream's build runs through `@borderless/ts-scripts`. Node 22 or later.

## How it is tested

`hegel/hegel.test.mjs` runs under `node --test`; `hegel/hegel-zoo.mjs` is the zoo's shared
harness; `hegel/ptr.mjs` holds the generators and models.

| Property | What it checks |
|---|---|
| `TestHegelStringifyParseRoundTrip` | generated token data (text, params, wildcards, nested groups; identifier, astral, combining-mark and arbitrary names; text starting with identifier characters or syntax) stringifies to a path that parses back to the same tokens, `stringify` is stable, `originalPath` is kept; a random path string parsed, stringified and parsed again gives the same tokens and the same regexp; unnormalized token data (empty and adjacent text tokens) denotes the same path |
| `TestHegelParseAgreesWithTheModel` | on stringified, mutated and random strings, `parse` (with and without `encodePath`) agrees with a reference parser written from the Readme's grammar: the same tokens, or a `PathError` (a `TypeError` with `originalPath`) with the same message and index |
| `TestHegelCompileFollowsTheModel` | `compile` on token data and on its stringified path, with `encode` default, `false` or custom and any delimiter, agrees with a reference builder: the path, or the exact `TypeError` for missing parameters, wrong types, empty strings and arrays; optional groups omitted when a parameter is missing, kept when all are present |
| `TestHegelCompiledPathsMatchBack` | `match(compile(params))` on a route with random parameters, raw or percent-encoded, with any delimiter, returns the whole path and, when the values share no character with the delimiter or the route's text (matching is case-insensitive), exactly the parameters, and recompiling the match gives the path; case-flipped paths still match |
| `TestHegelOptionsShapeTheMatch` | with `end`, `trailing`, `sensitive` and `delimiter` combined: `match` and `pathToRegexp` agree on every input, keys are the captures of every expansion in order and one per capturing group, flags follow `sensitive`; a trailing delimiter is accepted exactly under `trailing` (or stopped before under `end: false`), more path after a delimiter only under `end: false` with the match stopping at the delimiter, glued junk rejected, text case respected exactly under `sensitive` |
| `TestHegelArraysAndGroupsAreAlternatives` | a path with groups compiles to the same regexp and keys as the array of its flat expansions (with each group first, then without), up to the documented 256 combinations and `Too many path combinations` beyond; an array of paths matches like the first path that matches, with concatenated keys; arrays of plain paths of any length |
| `TestHegelRegExpsAreSafe` | every generated regexp (any options, custom delimiters, multiple wildcards and params per segment) is reported `safe` by `recheck`; a `vulnerable` report is confirmed by timing the attack string and 4000 pumps of it |
| `TestHegelHostileInputNeverCrashes` | on syntax-like strings and odd options (empty and multi-character delimiters), `match` throws only `PathError` at build time and only `URIError` (from `decodeURIComponent`) when matching, results have a string `path` that prefixes the input; `compile` throws only `TypeError` for parameters of every type; unknown token types are `TypeError`s from `pathToRegexp`, `compile` and `stringify` |

`ZOO_COLLECT=1` turns mismatches into `# COLLECT` counts and `HEGEL_TEST_CASES` (default 100)
widens the sweep. Known bugs are gated in `hegel/known.mjs` by shape (array length, astral
characters in the path, parameter names inherited from `Object.prototype`, empty text tokens);
`ZOO_NO_KNOWN=1` lifts the gates.

## Bugs

4 open, all pinned (see `bugs.toml`). In 300-case sweeps every property agrees with its model
on every case not touched by them:

- An array of more than 256 plain paths is rejected as `Too many path combinations`: the
  group-expansion counter is shared across the array (1).
- Parse error indices count code points, so an astral character before the error shifts them
  from the string position (2).
- `compile` reads `data[name]` without an own-property check, so parameters named
  `constructor`, `toString`, `valueOf`, `hasOwnProperty` or `__proto__` come from
  `Object.prototype`: a wrong error instead of `Missing parameters`, and an optional group
  that should be omitted throws (3).
- `stringify` of `[param foo, text "", text "bar"]` is `:foobar`, one parameter when parsed
  back; the empty text token hides the text from the quoting check (4).

## Accepted differences and notes (not counted as bugs)

- Parameters match "up to the end of the segment or any preceding tokens": the regexp for a
  parameter excludes the delimiter and, after another capture in the segment, the text between
  them (`/:a-:b` gives `b` the class `[^/-]`, or the literal `-`). A compiled path whose values
  contain such characters may therefore match back with a different split
  (`/:from-:to` with `2024-01`/`2024-02` matches as `2024-01-2024`/`02`) or not at all
  (`/:a-:b` with `a=x`, `b=y-`); `encodeURIComponent` leaves `-`, `.`, `_`, `~`, `!`, `*`,
  `'`, `(`, `)` in place. This is the v8 design (the ReDoS fixes of 2024); such cases are
  counted (`ambiguous-*`), and the path is still required to be returned whole when it matches.
- A wildcard at the end absorbs a trailing delimiter (`/*w` on `/a/b/` gives `["a","b",""]`)
  and, under `end: false`, everything after; upstream's own cases expect this.
- `match` throws `URIError` when a captured value holds a malformed percent-escape
  (`decodeURIComponent`); Express catches it. Counted.
- `recheck` reports some large generated patterns as polynomially `vulnerable` by fuzzing;
  none was confirmed by timing (the attack strings and 4000 pumps of them run in under a
  millisecond), so they are counted, not judged.
- A path ending in text that ends with the delimiter does not match a longer input under
  `end: false` (`/foo/` against `/foo/bar` is false: the lookahead wants a delimiter after the
  text). Upstream's cases expect this.
- `delimiter: ""` makes every character a segment boundary; not judged.

Not tested: the `encodePath`/`encode`/`decode` functions beyond identity, upper-casing and the
URI functions; the TypeScript types.

## History

- 2026-09-20: created against 8877f41 (8.4.2); 4 bugs.
