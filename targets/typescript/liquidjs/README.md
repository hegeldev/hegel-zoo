# liquidjs

[liquidjs](https://github.com/harttle/liquidjs) is a Liquid template engine for JavaScript, written
to be compatible with Shopify's Ruby liquid (its documentation keeps a list of the differences it
accepts). Pinned at 10.29.0, a2cdfb8 (2026-09-20), MIT.

The source is TypeScript with extensionless imports, so the setup bundles `src/index.ts` with
esbuild into `hegel/liquid.mjs` (tslib, its one runtime import, is installed under `.hegel/` and
resolved through `NODE_PATH`). Tests: `hegel/hegel.test.mjs`, run with `node --test`.
`ZOO_FULL=1` opens the gates around the known bugs and the documented differences; `ZOO_COLLECT=1`
prints mismatch statistics.

## Oracle

Shopify's Ruby liquid gem, version 5.5.1 (`gem install --user-install liquid -v 5.5.1`; later
versions pull in a `strscan` that needs a native build), run as one persistent `ruby
hegel/oracle.rb` process that takes a JSON request per line (`template`, `data`, strict parsing) and
answers with the output or the parse error; `hegel/oracle.mjs` is the bridge and the properties are
asynchronous. A template is rendered by both engines from the same JSON context; Ruby's parse errors
must be liquidjs parse errors too, Ruby render errors (which it writes into the output) are counted
and skipped, and otherwise the outputs must agree after one normalisation: Ruby prints floats with a
trailing `.0` (and a negative zero as `-0.0`) and JavaScript does not (a documented difference).

`hegel/gen.mjs` builds the context (strings, integers, a quarter-fraction float, booleans, nil,
string and integer arrays, an array of objects, a nested hash) and templates of text with random
whitespace control (`{%-`, `-%}`) around output, `assign`, `capture`, `if`/`elsif`/`else`,
`unless`, `case`/`when` (`,` and `or` alternatives), `for` over arrays and ranges (`reversed`,
`limit`, `offset` including `continue`, `forloop.*`, `break`/`continue`, `else`), `comment`, `raw`,
`cycle` (named and unnamed), `increment`/`decrement` and `echo`. Expressions are typed and chain up to
three of the filters both engines share (string, array, math and `default`), with argument shapes
kept to the types each filter accepts.

Documented differences are kept out of the generator rather than normalised: arrays of objects are
never printed directly (Ruby inspects hashes, JavaScript gives `[object Object]`), filters are not
applied in a `for` collection (a liquidjs extension), `divided_by` only gets non-integral divisors
(Ruby divides integers as integers), `size` is not applied to numbers (8 for a Ruby integer, 0 in
liquidjs), `first`/`last` are only applied to arrays (liquidjs also accepts strings), `default` is
typed by its argument and takes no arrays or booleans, and float literals are binary fractions (Ruby
computes in BigDecimal, so `7 | times: 0.1` is `0.7` there and `0.7000000000000001` in
JavaScript). Two Shopify-side quirks are avoided too: `reversed` is written right after the
collection (Shopify's strict parser rejects it after `limit`/`offset`, liquidjs accepts both), and
the alternatives of a `when` are distinct (Shopify renders the body once per matching alternative).

## Properties

| Test | Checks |
| --- | --- |
| `TestHegelTemplatesRenderLikeShopifyLiquid` | A random template over the random context renders the same in liquidjs and Shopify's liquid (or both reject it) |
| `TestHegelFilterChainsRenderLikeShopifyLiquid` | A single output of a typed filter chain renders the same in both engines |

In the default run the shapes of the recorded bugs are kept out of the generator (`{%- endraw`,
unnamed cycles with different candidates, `truncatewords` at a count a string could have exactly,
`modulo` on floats, `0` among cycle candidates, `else` on a `for` with `limit`/`offset`, booleans
reaching math filters, block bodies of only whitespace). Pins (`TestHegelPin*`) reproduce the bugs in
`bugs.toml` and are listed as expected failures.

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
