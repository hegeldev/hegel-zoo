# shell-quote

[ljharb/shell-quote](https://github.com/ljharb/shell-quote) (npm `shell-quote`, ~20M weekly
downloads): `quote(args)` turns an argument array into POSIX shell text, `parse(cmd, env, opts)`
turns shell text into words, operators, globs and comments, expanding `$VAR`/`${VAR}` from `env`,
optionally field-splitting unquoted expansions (`splitUnquoted`). Pinned at v1.10.0
(35c9b97a, 2026-07-14). The tests are `test/hegel.test.mjs` with the zoo's small harness
`test/hegel-zoo.mjs`; they need `bash` and `dash` on PATH. The generators are combinator values
(STYLE.md): the word parts, words, programs and `quote` arguments are built from `weighted`
(`integers` flat-mapped to the alternative, simplest first), `record`, `arrays`, `tuples` and
`sampledFrom`, and each property draws one value; a word's three renderings and its model are
computed from the drawn parts and the drawn `env` by a pure function.

## What is tested

- **TestHegelQuotedWordsSurviveTheShell** — random argument arrays (strings over a hostile
  alphabet: quotes, backslashes, `$`, `` ` ``, `!`, `#`, glob characters, blanks, control and
  Unicode-space characters; numbers/booleans/null; `{ op }` tokens; `{ op: 'glob' }` patterns;
  a trailing `{ comment }`) are `quote`d and read back by **dash** and **bash** through
  `printf '%s\0'` (pathname expansion off, an empty cwd), and by `parse`. Every shell must
  read exactly the strings given (an `op` token reads back as the literal operator text —
  `quote` deliberately escapes it — and a glob as its pattern); `parse` must give the same,
  with `{ op: 'glob' }` for patterns holding `*`/`?`.
- **TestHegelParseAgreesWithBash** — a *word program*: 1–5 words of 1–3 parts each (bare text,
  a backslash escape, a single-quoted span, a double-quoted span with `\"`/`\\`/`\$`/`` \` ``
  escapes and `$VAR`s, an unquoted `$VAR`/`${VAR}`), blanks between them, 2% of the joins a
  backslash-newline. `parse(program, env)` must give the words bash reads from the same text
  with each unquoted expansion double-quoted (bash standing in for parse's documented default
  of never splitting an expansion). A model of each word doubles as a check on the generator
  (`model-differs` in collect mode).
- **TestHegelSplitUnquotedAgreesWithBash** — the same programs with `splitUnquoted` set to
  `true` (IFS space/tab/newline) or to a custom IFS (`:`, ` :`, `,`, `\t\n`, `:\t`, or `''`
  which disables splitting), compared with bash running the text under that `IFS`.
- **TestHegelOperatorsAndCommentsTokenize** — words (from the same generator), the sixteen
  control operators and an optional trailing `# comment`, joined with random blanks (none
  needed between a word and an operator); `parse` must return the modelled words (glob tokens
  where an unquoted `*`/`?` occurs), `{ op }` objects and the comment text.

The generators draw the shapes of all seventeen recorded bugs like any other input: `!` and
`` \` `` inside double quotes, `#` inside a word, `\\` before a closing quote or a blank, a
backslash-newline, `$_name`, `$*`/`$!` and `$1x`, prototype names such as `$constructor`,
CR/VT/NBSP and the other odd spaces, escaped glob characters, split expansions next to globs
and empty quotes, `splitUnquoted: ''`; each shape is in 0.1-10% of a wide property's cases,
and a mismatch on one names the recorded bug. The four wide properties therefore fail every
run and are the expected failures mapped to the bug each usually shrinks to (`target.toml`;
`QuotedWordsSurviveTheShell` lands on /11 or /1, `ParseAgreesWithBash` on /5 or /2, the split
and tokenizer properties on /2). Each bug also has a property of its own over its shape region
with random contents (`TestHegelHashInsideAWordAgreesWithBash`, ..., including object env
values for /13, which no wide property draws), so every bug has a deterministic finder, and a
one-line pin (`TestHegelPin...`) as the regression example. `HEGEL_NO_KNOWN=1` looks past the
bugs: the generators draw less of the shapes, a mismatch that still has a recorded shape is
skipped (about 1% of the parse and split cases, none of the others) and the one-bug properties
are skipped whole; the four wide properties then pass at 1000 cases.

## Oracles

`bash` and `dash` (`/bin/sh` on Debian) via `printf '%s\0'` under `set -f`; a word model of the
generated program; `parse`'s own documented token shapes for operators and comments.

## Not tested

- Tilde expansion, brace expansion, `$(...)`, backquotes and arithmetic: the shell performs
  them, `parse` by design does not (README); no `~` starts a generated word and no `{a,b}`
  is drawn, so bash agrees with the model.
- The `escape` option (a custom escape character): only that `parse('a ^"b c^" d', {}, {
  escape: '^' })` behaves like the backslash form was checked by hand.
- The env-function path beyond object values (shell-quote/13).
- Windows quoting: the README says `quote` is POSIX only.

Documented behaviour that looks odd but is not counted: `quote` escapes an `{ op }` token to a
literal word (`a \| b`), so `parse(quote(xs))` turns operators into strings; a `{ comment }`
swallows everything after it (that is what a comment is); a bracket class `[ab]` is not a glob
to `parse` (`limit/bracket-glob` — only `*` and `?` are), so `parse(quote([{ op: 'glob',
pattern: '[ab]c' }]))` is a string; in the default mode an unquoted empty expansion is an empty
word (`parse('a $E b', { E: '' })` is `['a', '', 'b']`), consistent with "an expanded variable
is a single token even when unquoted"; special parameters `$$`, `$?`, `$#` are looked up in
`env` and otherwise empty.

## Bugs

Seventeen, shell-quote/1–17 in `bugs.toml`: `quote` writes `\!` inside double quotes and the
shell keeps the backslash (/1); `parse` keeps the backslash of `` \` `` in double quotes and so
cannot read `quote`'s own output (/2); `#` inside a word starts a comment (/3); the chunker
cannot count backslashes — `"\\" "x"` runs on to the next quote (/4) and `\\ x` is one word,
`\\"..."` loses its quotes, `\\|x` comes back as an `op` that is no operator (/14); no line
continuation (/5); `$_foo` reads `$_` (/6) and the character after a one-character parameter
is dropped (/7); `$1x` looks up `1x` (/8); env lookups walk the prototype chain, so
`$constructor` expands to `function Object() { [native code] }` (/9); CR/VT/FF/NBSP/U+2028/BOM
split words (/10); an escaped `\*` is a glob (/11); with `splitUnquoted` the fields before a
glob character are lost (/12); an object value in an object env leaks the internal marker
(/13); `splitUnquoted: ''` keeps an empty unquoted expansion as an empty word (/15); with
`splitUnquoted` an empty quoted string after a split expansion vanishes (/16), and one before
a split expansion vanishes when a field follows (/17).

Twelve of the seventeen came from a probe file of one-liners written after reading `parse.js`
and `quote.js` end to end; /14, /15, /16 and /17 from the properties (the bash oracle).

## History

- 2026-09-15: created at 35c9b97a (v1.10.0); 16 bugs.
- 2026-09-23: generators rewritten in combinator style (STYLE.md): env, word parts, words,
  programs and `quote` arguments are generator values (`weighted`, `record`, `arrays`, `tuples`,
  `sampledFrom`, a `filter` for the plain words of the tokenizer property), the harness lost
  `n`/`pick`/`chance`/`word`; same properties and pins. Checking the rewrite over many cases
  showed the split-unquoted property failing about once per thousand cases (in the old generator
  too): with `splitUnquoted`, an empty quoted string *before* a split expansion vanishes when a
  field follows (`parse('""$W$C', { W: ' ', C: 'c' }, { splitUnquoted: true })` is `['c']`,
  bash reads `['', 'c']`), the mirror of shell-quote/16; recorded as /17 with a pin and gated
  by the `parse/split-drops-leading-empty-quoted` shape (the gate went with the next entry). The same long runs showed a model bug
  of the test's own (also pre-existing, about once per 3 000 cases): the brace fixup for a
  `$NAME` before a letter inside double quotes was a regex over the rendered text and so also
  rewrote an escaped `"\$Za"` into `"\${Z}a"` while the model kept saying `$Za`; parse (and
  the shell) rightly read `${Z}a`. The fixup now applies to expansion items only.
- 2026-09-24: the shape gates went (STYLE.md rule 11): the classifier and the filters had kept
  every recorded shape out of the properties or excused its mismatches, so the properties find
  the bugs again and are the expected failures; one property per bug over its shape region was
  added (/7 and /13 had no property before: special parameters were never drawn, env values
  were always strings), and `HEGEL_NO_KNOWN=1` switches the shapes off. Three shape tests of
  the test's own were tightened on the way: the /14 shape is read off the parts (the old regex
  also matched a double-quoted span ending in `\\`), the /15 gate had excused any mismatch
  under `splitUnquoted: ''` when any expansion existed, and the model's env lookup now uses
  `Object.hasOwn` (it had special-cased `constructor` alone).
