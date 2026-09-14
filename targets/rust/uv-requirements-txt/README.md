# uv-requirements-txt

[uv-requirements-txt](https://github.com/astral-sh/uv/tree/main/crates/uv-requirements-txt) is the
crate of [uv](https://github.com/astral-sh/uv) that parses `requirements.txt` files
(`RequirementsTxt::parse`): PEP 508 requirements with `--hash` tails, `-r`/`-c` includes
(flattened, relative to the including file), `-e` editables, `--index-url`,
`--extra-index-url`, `--find-links`, `--no-index`, `--require-hashes`, `--no-binary`,
`--only-binary`, comments, backslash continuations, `${VAR}` expansion, and the unsupported
options it warns about. Written in the zoo at 0.0.80 (uv HEAD `c0df400`, 2026-09-12); tests in
`crates/uv-requirements-txt/tests/hegel.rs`, run in that crate's directory (the crate pulls
`uv-client`, so the test build takes about three minutes).

## The oracle

**pip's own requirements-file parser** (`pip._internal.req.req_file`: `RequirementsFileParser`,
`preprocess`, `get_line_parser` — the format's owner; pip 24.0 here, the format is stable), run
in one persistent Python child (the first of `python3`, `/usr/bin/python3` that imports it) over
the same generated tree of files as the crate; each yielded line is reported as a JSON record
(requirement text parsed with `packaging.requirements`, `--hash` dict, option values, the
`FormatControl` sets). The records are folded the way uv flattens a tree and compared with the
crate's `RequirementsTxt`.

## Properties

- **Trees** (`trees_flatten_like_pip`): a generated tree — `requirements.txt` optionally
  including `sub.txt` (which may include `nested/inner.txt`) and a `constraints.txt`, with
  requirement lines (names, extras, specifiers, markers, `--hash` tails on continuation lines,
  trailing comments), option lines in every spelling (`-i`/`--index-url[=]`, `-f`, quoted
  values, `${HEGEL_ZOO_REQ_VAR}` expansion in file names and URLs, `./wheels` find-links,
  `--no-index`, `--require-hashes`, `--no-binary`/`--only-binary` with `:all:`/`:none:`/a
  name, `--pre`, `--trusted-host`), `-e ./pkg`, trivia lines and CRLF files — parses to exactly
  what pip yields: requirements in order (canonical name, specifiers, extras, marker presence,
  hashes), constraint names, editables, index/extra-index/find-links URLs (with credentials,
  relative paths as `file://` URLs), and the boolean and binary flags. Neither fails when the
  other parses.
- **Determinism and composition** (`parsing_is_deterministic_and_compositional`): parsing
  twice agrees; parsing `sub.txt` alone gives a subset of the whole tree's result.

## Bugs (4)

- **uv-requirements-txt/1** (wrong-result, low; `hash_in_option_values_is_not_a_comment`): a
  `#` inside an option's value ends the value (`is_terminal` treats `#` like a newline), where
  pip only starts a comment at a `#` preceded by whitespace — `--index-url
  https://h/simple#frag` loses the fragment, `-r sub#1.txt` reads `sub`.
- **uv-requirements-txt/2** (contract, low; `binary_options_take_comma_lists`):
  `--no-binary a,b` / `--only-binary :none:,a` — pip's documented comma lists — fail as an
  invalid package name.
- **uv-requirements-txt/3** (contract, low; `option_values_may_follow_a_line_continuation`):
  the grammar allows `wrappable_whitespaces` between an option and its value and pip joins
  continued lines first, but `parse_value` eats plain whitespace only, so `--index-url \`
  + newline + URL fails (`-r \` + newline + file reads the directory).
- **uv-requirements-txt/4** (contract, low; `hash_values_have_the_documented_shape`): `--hash`
  values are not checked against the documented `name:digest` shape; `--hash=0000` is kept as
  a hash (pip refuses; uv catches it later, in `HashDigest`).

## Not bugs (documented deviations from pip, kept out of the generators)

- Options on a requirement line other than `--hash` are an error (pip ignores them); a second
  `--index-url` is an error (pip: last wins); `-r` inside a constraints file yields
  constraints (pip: requirements); a file included twice is read once; a relative
  `--find-links` path that does not exist is an error (pip keeps the string); `-e` needs a
  local directory; a backslash continuation inside a token (`requ\` + `ests`) is not joined
  (pip joins any line ending in `\`); tabs before an option on a requirement line are fine for
  uv but break pip's space-only `break_args_options`.
- Extras are compared as sets: `requests[a,a]` keeps both in uv's list, packaging
  de-duplicates.
- `VerbatimUrl`'s `Display` masks credentials; the properties compare
  `displayable_with_credentials`.
- 2026-09-14: base bumped c0df400a4cf4 → 83d556d712c7 (2026-09-14, "Scope required-environment checks to the current fork (#21672)"; 0.0.80); 4 bug(s) still reproduce. 55 tests pass.
