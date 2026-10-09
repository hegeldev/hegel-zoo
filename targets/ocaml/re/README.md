# re

`Re.Perl` patterns against Python's `re` on bytes: search, `all`, `replace_string`,
`split_delim`, and `Re.Pcre.quote`. Needs Python 3.14+, where `\B` matches the empty string as
in Perl.

## What is tested

- `search_agrees_with_python`, `search_from_position_agrees_with_python`: match and group spans,
  with any of the caseless, multiline and dotall flags.
- `all_agrees_with_finditer`, `replace_agrees_with_sub`, `split_delim_agrees_with_split`: the
  matches found by iterating, with ocaml-re's rule for empty matches (#233) applied to Python's.
- `quote_matches_itself`: a quoted string matches exactly itself.

Loops whose body can match empty are not drawn: there ocaml-re prefers an iteration that
consumes, by design (its own fuzz reference does the same), and Perl and Python stop.

## Not tested

The combinator API (upstream's fuzz test covers it), `longest`/`shortest`, `Posix`, `Emacs`,
`Glob`, `Str`, streams, `~len`, bytes beyond ASCII.

## History

- 2026-10-09: created at 582af1fc (1.14.0+), hegel-ocaml 0.26.1; no bugs at 1000 test cases.
