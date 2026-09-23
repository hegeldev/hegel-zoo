# godotenv

[joho/godotenv](https://github.com/joho/godotenv), the Go port of Ruby's dotenv (`.env` files),
against Ruby dotenv itself: for a generated `.env` text, `Unmarshal` must give the map
`Dotenv::Parser.call` gives, and `Marshal`'s output must read back to the same map with both.

## What is tested

**`hegel/hegel_dotenv_test.go`** (needs `ruby` with the `dotenv` gem; `hegel/oracle.rb` is the
child process, one request per line)
- `TestHegelParseMatchesRuby`: a text of up to six lines (blank and comment lines, `KEY=value`
  with spaces around `=` or the yaml-ish `KEY: value`, an `export` prefix, leading whitespace,
  trailing whitespace and end-of-line comments, LF or CRLF, with or without a final line end;
  keys from a small `[A-Za-z0-9_.]` alphabet with lower-case names; values unquoted, single-quoted
  or double-quoted or empty, with words, `=`, `:`, `#`, quotes, non-ASCII, references `$NAME`,
  `${NAME}` and `\$NAME` to defined, environment (`ZOO_PRE`) and undefined names in any case,
  escapes `\n \r \t \\ \" \$ \q` in double quotes, `\'` and literal backslashes in single quotes,
  newlines inside quotes) is parsed by both; a text godotenv rejects that Ruby accepts fails (a
  panic counts as a rejection), a text Ruby rejects is discarded (`Assume`), and otherwise the
  maps must be equal.
- `TestHegelMarshalRoundTrip`: `Unmarshal(Marshal(m))` is `m` for maps of up to five values with
  newlines, tabs, references, comment markers, quotes and `$(x)`; Ruby dotenv reads `Marshal`'s
  output to `m` too.

**`hegel/hegel_pins_test.go`**: one deterministic reproducer per recorded bug.

## Oracles

Ruby dotenv 3.2.0 (`gem install dotenv`), the library the README names as the compatibility
target, run with `DOTENV_LINEBREAK_MODE=legacy` so that `\n` in double quotes is a newline (dotenv
3 changed the default; godotenv keeps the 2.x behaviour) and an environment of only `PATH`, `HOME`,
`LANG` and `ZOO_PRE=pre` (Ruby keeps a variable already in the environment, and both parsers look
up undefined references there). Node dotenv 18 was consulted by hand for the bugs. Not generated,
because the parsers differ by design: `#` inside an unquoted value without a space before it
(godotenv keeps it, its own tests say so; Ruby and Node start a comment); backslashes in unquoted
values (Ruby unescapes them, godotenv and Node do not); `KEY:value` without a space (Ruby skips the
line); hyphens in keys (Node's charset, not Ruby's); `export KEY` without a value and `export KEY=`
with an empty one (a Ruby error; discarded); two or more backslashes before a quote in a quoted
value (Ruby's regex reads any backslash-quote as an escape, godotenv counts backslashes); `$(`
(command substitution in Ruby); U+00A0 and U+0085 (whitespace for godotenv and JavaScript's trim,
not for Ruby); bare CR inside quotes; garbage Ruby's line scan skips and godotenv rejects (discarded
when it arises). In the round trip, values with a backslash before `n` or `r` or at the end are
not judged by Ruby (only the package's own round trip is): it reads `Marshal`'s `\\n` and `\\"`
differently and cannot express them.

## Known bugs (gated)

Three bugs (`bugs.toml`): references to lower-case names not expanded; a comment as the whole value
crashing the parser; a quoted value ending with an escaped quote losing the quote (and so
`Marshal`'s output for values ending in `"` not reading back). `hegel/known.go` gates them by
shape (an unescaped reference with a lower-case letter outside single quotes; `=` or `:` followed
by spaces and `#`, with the panic; an escaped quote right before the closing quote; a value ending
in `"` in the round trip) and discards a case with a known shape with `Assume`; `HEGEL_NO_KNOWN=1`
lifts the gates.

## Not tested

`Load`/`Overload` against the process environment, `Exec`, the `godotenv` command, `Write` (a file
of `Marshal`), the autoload package.

## History

- 2026-09-20: written against 97a2850142438b3c357c1d3439e325181afdcc1d (2026-05-25, v1.6.0-pre.4)
  with hegel.dev/go/hegel v0.6.33; 3 bugs.
- 2026-09-23: generators rewritten in combinator style (package-level `Lists`/`Maps`/`OneOf`/
  `weighted` values, `Assume` for the known-bug gates and Ruby's rejections); the collect mode and
  the `n`/`chance`/`pick`/`count`/`fail` helpers removed. Same properties and pins.
