# liquidjs

[liquidjs](https://github.com/harttle/liquidjs) is a Liquid template engine for JavaScript, written
to be compatible with Shopify's Ruby liquid (its documentation keeps a list of the differences it
accepts). Pinned at 10.29.0, a2cdfb8 (2026-09-20), MIT.

The source is TypeScript with extensionless imports, so the setup bundles `src/index.ts` with
esbuild into `hegel/liquid.mjs` (tslib, its one runtime import, is installed under `.hegel/` and
resolved through `NODE_PATH`). Tests: `hegel/hegel.test.mjs`, run with `node --test`.
`HEGEL_NO_KNOWN=1` leaves the shapes of the known bugs out of the generators, `ZOO_FULL=1` opens the
gates around the documented differences; `ZOO_COLLECT=1` prints mismatch statistics.

## Oracle

Shopify's Ruby liquid gem, version 5.5.1 (`gem install --user-install liquid -v 5.5.1`; later
versions pull in a `strscan` that needs a native build), run as one persistent `ruby
hegel/oracle.rb` process that takes a JSON request per line (`template`, `data`, strict parsing) and
answers with the output or the parse error; `hegel/oracle.mjs` is the bridge and the properties are
asynchronous. A template is rendered by both engines from the same JSON context; Ruby's parse errors
must be liquidjs parse errors too, Ruby render errors (which it writes into the output) are counted
and the case is discarded with `tc.assume`, and otherwise the outputs must agree exactly. The one
documented difference in the output text, Ruby's `2.0` and `-0.0` for floats where JavaScript
prints `2` and `0`, is removed in the oracle itself: `oracle.rb` prints floats the JavaScript way,
because a textual normalisation of the rendered output cannot tell `2.0` followed by `5` from
`2.05` (the shape the first long runs tripped over). `oracle.rb` also defines ActiveSupport's
`blank?`: Shopify's liquid runs inside Rails, and its `blank` literal is documented with
ActiveSupport's meaning (nil, false, an empty or whitespace string, an empty array or hash), but
the bare gem has no `blank?` at all, so `e == blank` was nil for every value there.

`hegel/gen.mjs` builds everything as Hegel generator values. The context is a `record` (strings,
integers, a quarter-fraction float, booleans, nil, string and integer arrays drawn `unique`, an
array of objects, a nested hash). A template is drawn as a tree of nodes - strings for the parts
that need no state, arrays for sequences, and a few tagged records for the tags that hand out
names (`assign`, `capture`, `for`) or refer to earlier ones (an output of a variable assigned so
far, the loop variable) - and rendered by a pure function that numbers the names and tracks the
assigned variables in document order, so the shrinker can delete or swap whole tags. The items
are text with random whitespace control (`{%-`, `-%}`) around output, `assign`, `capture`,
`if`/`elsif`/`else`, `unless`, `case`/`when` (`,` and `or` alternatives, distinct by `filter`),
`for` over arrays and ranges (`reversed`, `limit`, `offset` including `continue`, `forloop.*`,
`break`/`continue`, `else`), `comment`, `raw`, `cycle` (named and unnamed),
`increment`/`decrement` and `echo`, chosen by a weighted `oneOf` with an output first and the
block tags last, nested to depth 2. Expressions are typed and chain up to three of the filters both
engines share (string, array, math and `default`) by `flatMap` over the type so far, each filter
carrying a generator of the argument shapes its documentation accepts.

Documented differences are kept out of the generator rather than normalised: arrays of objects are
never printed directly (Ruby inspects hashes, JavaScript gives `[object Object]`), filters are not
applied in a `for` collection (a liquidjs extension), `divided_by` only gets non-integral divisors
(Ruby divides integers as integers), `size` is not applied to numbers (8 for a Ruby integer, 0 in
liquidjs; nor to the untyped value of `first`/`last`, which may be one), `first`/`last` are only
applied to arrays (liquidjs also accepts strings), `default` is typed by its argument and takes no
arrays or booleans, and float literals are binary fractions (Ruby computes in BigDecimal, so `7 |
times: 0.1` is `0.7` there and `0.7000000000000001` in JavaScript); a quotient by `f` or a value
rounded to 1-3 places is no longer one (`10.75 | round: 1 | times: 3` is `32.4` there and
`32.400000000000006` here, and even `| minus: n` can round the two apart), so it is typed `dec` and
only the filters that never round (`abs`, `at_least`, `at_most`, `ceil`, `floor`) follow it. Two
Shopify-side quirks are avoided too: `reversed` is written right after the
collection (Shopify's strict parser rejects it after `limit`/`offset`, liquidjs accepts both), and
the alternatives of a `when` are distinct (Shopify renders the body once per matching alternative).

## Properties

| Test | Checks |
| --- | --- |
| `TestHegelTemplatesRenderLikeShopifyLiquid` | A random template over the random context renders the same in liquidjs and Shopify's liquid (or both reject it) |
| `TestHegelFilterChainsRenderLikeShopifyLiquid` | A single output of a typed filter chain renders the same in both engines |

The generators draw the shapes of the recorded bugs like any other input: a whitespace-controlled
`{%- endraw %}`, unnamed cycles with different candidates and `0`/`false` among the candidates,
`truncatewords` at and under its count, a `frac` literal (0.1, 0.3, ...) into `modulo`, booleans
into the math filters and through `default` (and `people | map: "active"` into the array
filters), nested arrays from `map: "tags"` into the array filters, `split: " "`, `replace` with an
empty pattern, block bodies of only whitespace, `else` on a `for` with `limit`/`offset`, `offset:
continue` on loops inside loops, and `"` and `' ( ) ! *` in the string samples for `escape` and
`url_encode`. Each shape is in 0.2-7% of the template property's cases (15% of them mismatch in
all) and 0.1-3% of the filter-chain property's (4%), and a mismatch names the recorded bug;
`TestHegelTemplatesRenderLikeShopifyLiquid` fails every run and is mapped to liquidjs/7, its
usual basin (/4 and /1 the next), `TestHegelFilterChainsRenderLikeShopifyLiquid` passes about one
run in six and is mapped to /7 as intermittent. Each bug also has a property over its shape region
with random contents, named after what it tests (`TestHegelModuloOfAFloatKeepsItsPrecision`,
`TestHegelSplitOnASpaceIsAwkStyle`, ...), and a pin (`TestHegelPin*`) as the regression example;
all are listed as expected failures in `target.toml`. `HEGEL_NO_KNOWN=1` leaves the shapes out
of the generators for a run that looks past the known bugs (the narrow properties are skipped
whole); the two wide properties then pass at 1000 cases. Two shapes the 2026-09-23 long runs
found are differences of the oracle's environment rather than of liquidjs and stay out of the
default run: a literal `nil` against `blank` (`nil == blank` holds only with ActiveSupport's
`blank?`) and `sort_natural` over accented letters of mixed case (Ruby's `casecmp` folds ASCII
only); `ZOO_FULL=1` draws them and the documented differences above.

## Not tested

- The liquidjs-only tags and filters (`layout`, `render`/`include` with files, `json`, `date`
  variants, `where_exp`, `group_by`, ...), and the `date` filter, whose output differs by design.
- Options: lax parsing, `strictVariables`/`strictFilters`, `ownPropertyOnly`, `outputEscape`,
  `jsTruthy`, `orderedFilterParameters`, `catchAllErrors`, the render/parse limits.
- Error messages and line numbers; templates both engines reject are only checked to be rejected by
  both. Object iteration order, sort stability and the stringification of hashes (all documented as
  different).
- The asynchronous and streaming renderers, `Liquid.evalValue`, drops and custom tags/filters.

## History

- 2026-09-20: created (turn 321); 8 bugs recorded.
- 2026-09-23: generators rewritten as Hegel generator values (a template is a tree rendered by a
  pure function; the harness lost `n`/`pick`/`chance`/`word`). The long runs showed the float
  normalisation could not separate `2.0` followed by `5` from `2.05`, so the oracle now prints
  floats the JavaScript way, and that the bare liquid gem has no `blank?` (`e == blank` was
  false for `e = ""`), so the oracle now defines ActiveSupport's; they also found nine candidate
  bugs (nested arrays in array filters, `truncatewords` under its count, `split: " "`, `replace`
  with an empty pattern, literal `nil` against `blank`, `escape` of `"`, `url_encode` of `'`,
  `sort_natural` over mixed-case accented letters, `offset: continue` on a loop that runs twice),
  a route to bug 7 through `map: "active"`, and two documented differences leaking through untyped
  values (`size` after `first`/`last`, BigDecimal arithmetic after `divided_by: f` or `round: n`),
  all gated in the generator; seven of the candidates are recorded as liquidjs/9-15 with pins
  (the `nil == blank` and `sort_natural` ones are the oracle's environment, not liquidjs).
- 2026-09-24: the gates around the recorded bugs went (STYLE.md rule 11): the shapes are drawn
  by default and the two wide properties fail on them; one property per bug over its shape
  region was added; `HEGEL_NO_KNOWN=1` (not `ZOO_FULL`) now switches the known shapes off, and
  the harness keys the example database per property.
