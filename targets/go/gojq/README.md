# gojq

[gojq](https://github.com/itchyny/gojq) is a pure-Go implementation of the jq query language,
usable as a library (`gojq.Parse`, `Compile`, `Code.Run`, `Marshal`, `Compare`) and as a CLI.
Pinned at c329334 (v0.12.19+, 2026-09-14), MIT, no AI policy.

## Oracles

- **jq 1.8.2**, the reference implementation gojq tracks, run as a child process per case
  (`jq -c --argjson v … <program>` on the rendered input). Ubuntu's jq is 1.7.1, whose
  number formatting, `limit`/`ltrimstr`/`abs` semantics and string handling differ from 1.8,
  so the `[run] setup` step downloads the static 1.8.2 release binary into
  `~/.cache/hegel-zoo/jq-1.8.2/jq` (sha256 checked against the release's `sha256sum.txt`);
  `HEGEL_JQ=/path/to/jq` overrides the lookup.
- gojq against itself: `Query.String()` round trips, `Compare` laws, `Marshal` read-back.
- `encoding/json` for the JSON layer.

Inputs are generated as canonical JSON (sorted distinct keys, integers |n| ≤ 10^6, decimals
with 1–3 fractional digits, valid UTF-8) and fed to gojq both as `encoding/json` values
(int/float64) and as `json.Number` (the form gojq's own CLI passes to the library). Outputs are
compared as canonical trees: sorted keys, numbers by float64 value (so int, float64 and
`json.Number` spellings agree and -0 is 0), a 4-ulp tolerance for libm differences in
transcendental functions, and the kind of ending (values / runtime error / compile error);
error messages are not compared.

## Properties

- `TestHegelProgramsAgreeWithJq` — a program drawn from a grammar of jq constructs (paths,
  slices, pipes, arithmetic, comparisons, `//`, `?`, if/elif/else, try/catch, reduce, foreach,
  `as` bindings and destructuring incl. `?//`, label/break, `def` with filter and `$`
  parameters, ~80 builtins with typed guards, string interpolation and `@formats` on strings,
  object/array construction, `limit`/`range`/`repeat`/`until`/`while`, regex functions with a
  safe regex pool, time functions on epoch seconds in years 1000–9999, plus a final
  object-building stage: `|=`, `=`, `+=` etc., `del`, `setpath`, `delpaths`, `+`/`*` with
  objects, `with_entries`, `pick`) on a generated input and a `$v` variable gives the same
  outputs and ending in gojq and jq.
- `TestHegelPrintedProgramsParseAndRunTheSame` — `Query.String()` of a parsed program parses
  again in gojq, is a fixpoint, runs to the same outcome as the original text, and is accepted
  by jq whenever jq accepted the original.
- `TestHegelMarshalMatchesJqCompactOutput` — `gojq.Marshal` of a decoded value (both forms) is
  byte for byte `jq -c .` of the same text and reads back to the value.
- `TestHegelCompareIsATotalOrderAgreeingWithJq` — `Compare` is antisymmetric and transitive,
  equal across number spellings, and orders like jq's `sort`.
- `TestHegelStringFormatsAgreeWithJq` — `tostring`, `tojson`, `@text/@json/@html/@uri/@sh/
  @csv/@tsv/@base64/@base32` (and their decoders), format-string interpolation and string
  builtins on generated literal values agree with jq, including computed floats inside
  [1e-4, 1e16) where both print shortest round-trip digits.

All general properties pass at 1000 cases × 3 (the differential also ran clean over 8000
collected cases). Seven pinned expected failures.

## Bugs (7)

| id | title | severity |
|----|-------|----------|
| gojq/1 | Suffixes after a negative number literal are silently dropped by the parser (`-1[0]` → -1, `1 - -1[0]` → 2) | medium |
| gojq/2 | Slices with negative fractional bounds truncate the bound before counting from the end (`.[-0.5:]` → whole array) | medium |
| gojq/3 | `reduce` keeps the previous state when the update produces empty instead of becoming null | medium |
| gojq/4 | Global regex matching skips an empty match right after a non-empty match (`"aaa" \| gsub("a*"; "-")` → "-" not "--") | low |
| gojq/5 | `todate`/`gmtime`/`mktime` turn NaN and infinities into a garbage date instead of an error | low |
| gojq/6 | `abs` errors on strings, arrays and objects that jq returns unchanged | low |
| gojq/7 | `gamma` computes the gamma function where jq's `gamma` is the log-gamma function | low |

## Not bugs (documented or jq-side)

Differences gojq's README declares, which the generators avoid: object keys are kept sorted
(inputs are generated with sorted keys and object-building operations are only the final
stage of a program; `keys_unsorted` is absent); arbitrary-precision integers (no generated
number exceeds 2^53 and cases with results beyond it are skipped); string indexing `.[n]`
(numeric indexing, `first`, `last`, `getpath` with numeric paths are guarded with
`select(type != "string")`); `@base64d` of malformed input yields binary strings (only
`@base64` output is decoded); regex flags `x n s l p`, backreferences and look-arounds;
`fromdate` with offsets, `%f`, nanosecond fractions and `%v`/`%Z` in time formats;
`input`/`inputs`, `env`/`$ENV`, `$__loc__`, `input_line_number`, `input_filename`, `debug`,
`stderr`, `halt`, `get_*_origin`, `have_*` and `builtins`, which gojq lacks or which depend on
the environment.

Other differences observed and left alone:

- Number formatting: jq 1.8 preserves the literal text of unchanged numbers in its own
  canonical form (`1e17` → `1E+17`, `1.50` → `1.50`) while gojq preserves it verbatim or
  (for program literals) converts to float64; computed floats switch to exponent notation at
  1e16 and below 1e-4 in jq, at 1e21 and below 1e-6 in gojq. Comparisons are by value;
  string conversions are only compared for canonical literals and for computed floats in
  [1e-4, 1e16).
- `-(0)` is `-0` in gojq and `0` in jq (both print the literal `-0` as `-0`).
- jq's "naive" definitions return values for wrong-typed inputs where gojq raises type errors:
  `reverse`/`transpose` on null/objects give `[]`, `transpose` on arrays holding non-arrays
  works through `null | length` (`[[1],null] | transpose` → `[[1,null]]`), `indices`/`index`/
  `rindex` on objects give null, `isnan` on non-numbers is false, `null | .[[1]]` errors in jq
  but is null in gojq, `delpaths` with a root path returns null without validating the other
  paths. The generators guard these (`arrays |`, `select(all(.[]; type == "array"))`,
  `select(type == "array" or type == "string")`, …).
- jq's `X[Y]?` only guards the indexing itself: an error raised while evaluating `X` or `Y`
  still propagates (`true | .[."a"]?` errors), although the manual calls `EXP?` a shorthand
  for `try EXP`; gojq guards the whole term. The generator writes `(X[Y])?`.
- `-1 | gmtime | mktime` and `-2 | gmtime | mktime` error in jq ("invalid gmtime
  representation", "mktime not supported on this platform": timegm's -1 and -2 results are
  taken for jq's error sentinels); gojq returns -1 and -2. Both epochs are left out of the
  time inputs.
- jq's `reduce` with a multi-output init evaluates the source on null from the second init
  value on: `[reduce .[] as $x (0, 100; . + $x)]` on `[1,2]` is `[3,100]` in jq 1.8.2 (and
  1.7.1; without `?` it errors "Cannot iterate over null") and `[3,103]` in gojq. `foreach`
  is fine in 1.8.2. The generator wraps inits in `first(...)`.
- jq's `?//` catches `break`: inside `limit`, `first`, `isempty`, `any`/`all` or a `label`
  body it re-runs the body with the next alternative and duplicates outputs (`[limit(1; . as
  [$p] ?// $p | .)]` on `[]` is `[[],[]]`, `isempty(. as [$p] ?// $p | .)` yields `false`
  twice); gojq gives `[[]]` and one `false`. `?//` is only generated at the top level.
- Error messages differ throughout, so a caught error that is a string is replaced before the
  `catch` body sees it; `reduce` updates are wrapped as `[upd] | .[-1]` so that gojq/3 does not
  leak into the general property (`last(empty)` is empty in both, so `last` would not do).
- Time: glibc's `%Y` prints years below 1000 unpadded (`1-01-01T…`) where gojq pads to four
  digits; `strptime` in glibc skips whitespace and leaves unset fields at 0 (day 0, yday -1)
  where gojq defaults to day 1 and normalises out-of-range fields; `fromdate` accepts
  second 61 in jq only; `[2000,0,1,0,0,59.9999999,0,0] | mktime` keeps the fraction in gojq.
  Time functions are exercised on epoch seconds for years 1000–9999 only.
- jq 1.8.2 reports duplicate empty matches on multibyte strings (`"é" | [match(""; "g") |
  .offset]` → [0,1,1]; `gsub(""; "-")` → "-é--") — a jq bug; regexes that can match the empty
  string are only used on ASCII inputs.
- `repeat(empty)` never terminates in either implementation; `repeat` is generated with a
  non-empty body.
- libm last-digit differences (`cbrt`, `sin`, `exp10`, …) are within the 4-ulp tolerance.
- `toarray`, `ascii`, `lgamma_r`, `date`, `dateadd`/`datesub` exist in only one of the two.

## Conventions

External test package with a dot import; `HEGEL_TEST_CASES` via `hegelOpts`; `property()`
turns panics into test-case failures; `GOJQ_COLLECT=1` makes the differential print every
disagreement (`MISMATCH …`), status (`STATUS …`) and slow case (`SLOW …`) instead of failing
— a triage mode. Both implementations run under a 5 s timeout; a case where jq times out (or
gojq times out while jq took over 2 s) is skipped with a note.
- 2026-09-17: base bumped c32933425cc6 → d3fe03ca462e (2026-09-18, "fix date and time functions against fractional epoch timestamps"; v0.12.19+); 7 bug(s) still reproduce. 69 tests pass.
- 2026-09-18: base bumped d3fe03ca462e → 8b5e03a42da9 (2026-09-18, "update go-yaml and fix error handling using the load error API"; v0.12.19+); 6 bug(s) still reproduce; fixed upstream: gojq/4. 69 tests pass.
