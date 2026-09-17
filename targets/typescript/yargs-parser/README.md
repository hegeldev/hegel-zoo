# typescript/yargs-parser — yargs/yargs-parser (the option parser under yargs)

Hegel property tests for [`yargs-parser`](https://github.com/yargs/yargs-parser) 22.0.0, pinned
at `913df9d1` (main, 2026-09-04): the tokenizer and option parser used by yargs and, through it,
by a large share of Node command-line tools (about 190 million weekly downloads). It turns an
argument array or string plus a set of hints (`boolean`, `string`, `number`, `array`, `count`,
`narg`, `alias`, `default`, `coerce`, `configuration`) into an `argv` object with positionals in
`_`, camel-case twins of dashed keys, dot-notation objects and negated booleans. TypeScript, ISC,
no runtime dependencies. No AI-contribution policy is published (README, SECURITY.md and
`.github/` checked 2026-09-16; there is no CONTRIBUTING); the zoo only records bugs.

Tests are `test/hegel.test.mjs` (ESM, run by `node --test`) with the zoo's harness
`test/hegel-zoo.mjs`. Hegel is `@hegeldev/hegel` 0.4.5.

## How it is built

`build/` is not committed and the package's `tsconfig.json` extends `gts`'s, so the setup installs
Hegel and TypeScript 5.9.3 under `.hegel/` (a root `npm install` would pull the whole dev tree,
puppeteer included) and compiles `lib/*.ts` to `build/lib` with the zoo's own
`test/tsconfig.hegel.json` (`module: es2022`, `--noCheck`, no `@types/node`). The tests import
`../build/lib/index.js`, the harness imports Hegel from `.hegel/node_modules`.

## How it is tested

There is no reference option parser to compare with, so the tests build their own expectation
from the README's grammar. A random *spec* (one to four options with distinct names such as
`alpha`, `foo-bar`, `x-y-z`, optional single-letter and long aliases, a type — boolean, string,
number, array with an element type, count, narg 1–3, or untyped — and sometimes a default) is
turned into the parser's `opts`; the arguments are either an *intent* rendered in a documented
syntax or a random *soup* of documented shapes (`--name`, `--name=v`, `--no-name`, `-a`, `-ab`,
`-n5`, words, numbers, `true`/`false`, `--`, `-3`) over the spec's names.

- **The intent round trip** (`TestHegelIntentRoundTrip`): a sequence of assignments and
  positionals is rendered in random syntaxes (`--key=v`, `--key v`, `-k v`, `-k5`, `--no-key`,
  `--key=false`, `-ab` groups, `--arr a b`, `--arr=a b`, `--nn v1 v2`, a trailing `-- rest`) and
  the parse must equal the model: last write wins for booleans, repeated scalars collect into a
  list, arrays concatenate, counts count, nargs take exactly n, aliases and camel twins carry the
  same value, unset options take their default (an array's scalar default wrapped), counts
  default to 0, untyped values are number-coerced when `looksLikeNumber` says so. Found bugs 1
  and 8.
- **Configuration laws** (`TestHegelConfigurationLaws`): the same soup under one switch against
  the default parse — `strip-dashed` removes exactly the dashed keys; `strip-aliased` removes the
  declared aliases and their twins; `populate--` moves the arguments after `--` from `_` to `--`
  and nothing else; `dot-notation: false` gives the flattened default parse; `duplicate-arguments-
  array: false` keeps the last value; `boolean-negation: false` makes `--no-x` the key `no-x`;
  `short-option-groups: false` makes `-abc` the key `abc`; `halt-at-non-option` leaves the raw
  rest in `_` from the first positional; `parse-numbers: false` turns every coerced number of an
  undeclared key back into its text; `camel-case-expansion: false` only drops twins. Found bugs
  4, 5 and 6.
- **Types and aliases hold** (`TestHegelTypesAndAliasesHold`): over soup (with `__proto__`,
  `constructor.prototype` and `nest.__proto__` keys mixed in) `detailed()` never throws, the only
  errors are the documented nargs ones, `Object.prototype` is never polluted, every alias and
  twin of an option carries the same value, booleans are booleans, strings strings, numbers
  numbers (or `undefined` for a bare flag), arrays arrays of their element type, counts
  non-negative integers, and `newAliases` are twins. Found bugs 4 and 7.
- **`coerce` returns the value** (`TestHegelCoerceReturnsTheValue`): a coerce function on one key
  (by name, alias or twin) is called exactly once with the parsed value, its result (a word, a
  numeric string, an object, an array, or the value itself) is the value of every key of the
  option, no other key changes, and it is not called for an unset option. Found bug 3.
- **String input matches array input** (`TestHegelStringInputMatchesArray`): `parser(args.join(" "))`
  equals `parser(args)` for soup without spaces or quotes, and a quoted value with a space
  (`--name "a b"`, `--name='a b'`) survives as one token without its quotes.
- **String utilities** (`TestHegelStringUtils`): `camelCase`/`decamelize` invert each other on
  kebab and snake names and `camelCase` is idempotent; every generated number spelling
  (integers, decimals, `.5`, `1e3`, `0x1f`, `1.5e2`, negatives) satisfies `looksLikeNumber`, parses
  the same after `=` and after a space, to the number when it is a safe integer's worth and to the
  text otherwise, and to the number under `number:`; non-numbers (`a1`, `0123`, `+5`, `1_000`,
  `Infinity`) stay strings.

Each known bug has a `Known` switch: the properties skip its shape while the pin below asserts
the correct behaviour and fails until it is fixed.

## Bugs

| id | title | kind | severity |
|---|---|---|---|
| yargs-parser/1 | A negative number with an exponent or a trailing dot is not taken as a value: `--num -1e3` sets the flags `1` and `e` | wrong-result | low |
| yargs-parser/2 | An argument like `-5.` or `-.` creates the empty key: `{'': {'': true}}` | wrong-result | low |
| yargs-parser/3 | The value a `coerce` function returns is number-coerced afterwards: `() => '5'` gives `5`, and a `number` option's coerce returning a word gives NaN | contract | low |
| yargs-parser/4 | With `duplicate-arguments-array: false`, a repeated `narg` option keeps the last value under its name but every value under its aliases and camel-case twin | wrong-result | medium |
| yargs-parser/5 | A short option takes the `--` end-of-options marker as its value: `-x -- a` is `{x: '--', _: ['a']}` | wrong-result | medium |
| yargs-parser/6 | `strip-aliased` leaves the dashed twin of a camel-case alias in argv | inconsistent | low |
| yargs-parser/7 | A string or number array flag inside a short group gets a placeholder element: `-bu` gives `b: [undefined]` where `-b -u` gives `[]` | wrong-result | low |
| yargs-parser/8 | The value 1 is mistaken for a count increment: `--x 1 --x 1` is `x: 2` and `--x 2 --x 1` is `x: 3` | wrong-result | medium |

## Design decisions and quirks the tests accept (not counted)

- `--no-x` negates any key, typed or not: a `string` or `array` option given `--no-x` holds
  `false` (`[false]`), and a count given `--no-v` is incremented (asserted by upstream's own
  "should increment regardless of arg value"). The type invariant skips negated options.
- Arguments after `--` are pushed into `_` (or `--`) as raw strings: `5 -- 6` is `_: [5, "6"]`
  (upstream's tests assert the string form).
- `parse-numbers: false` also stops the coercion of positionals, whatever
  `parse-positional-numbers` says; `parse-positional-numbers` alone is not exercised.
- `--x true` on an untyped option is the string `"true"`, only declared booleans read
  `true`/`false` words; `--x` on a `number` option is `undefined`, on a `string` option `""`.
- An array's scalar default is wrapped (`default: {arr: "a"}` → `["a"]`); a boolean array's bare
  flag is `[true]`; a value that does not fit a safe integer (`1e20`) stays a string unless the
  option is declared `number`; `0123` is a string (a leading zero is kept).
- `set-placeholder-key` adds `undefined` placeholders for declared names only, not for their
  aliases or twins, and `-x --` (bug 5) also swallows `---`.
- Mixing a key and its dotted child (`--nest 1 --nest.b 2` → `nest: [1, {b: 2}]`) has no flat
  twin; the dot-notation law skips such soups. Environment variables (`envPrefix`), `config`
  files and `configObjects` are not exercised.

## History

- 2026-09-16: created against 913df9d1 (22.0.0); 6 properties, 8 bugs.
