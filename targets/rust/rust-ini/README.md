# rust-ini

[rust-ini](https://github.com/zonyitoo/rust-ini) (crate `ini`, Y. T. Chung) is the most-used
INI parser and writer for Rust (125M downloads): sections, `=`/`:` delimiters, `;`/`#` line
comments, quoted values, backslash escapes with eight `EscapePolicy` levels for the writer,
optional indented multiline values, a multimap (`append`, repeated sections) behind `Properties`
and `Ini`. Written in the zoo at 0.21.3 (upstream HEAD `a0aa25c`); tests in `tests/hegel.rs`.
Default features only (`inline-comment`, `case-insensitive`, `brackets-in-section-names` off).

## Oracles

- **Python's `configparser`**, one child process, configured to the intersection of the two
  grammars (`interpolation=None`, `strict=False`, `;`/`#` line comments, no inline comments,
  `allow_no_value=False`, option names kept as written) against the crate with
  `enabled_quote: false`, `enabled_escape: false` and either multiline setting. The generated
  text keeps to what both read the same way — each restriction is a documented divergence:
  headers never `DEFAULT`, never containing `[`/`]` (Python takes up to the last `]`, the crate
  the first), never padded (Python keeps it), never followed by text (Python ignores it; crate:
  rust-ini/5); keys never starting with `[`/`;`/`#`, no delimiter, no backslash; a value never
  ends in a backslash (rust-ini/6); continuation lines indented deeper than their key (Python's
  rule), never starting with a comment symbol (Python drops it, the crate keeps it), never after
  a comment line (Python still continues, the crate has closed the value); sectionless keys
  never generated (Python needs a header, the crate has a general section); an indented comment
  never directly after a comment or blank line (rust-ini/9); CRLF only without continuation
  lines (rust-ini/4). Duplicate keys and sections are compared as Python sees them (last value
  wins) against the crate's multimap; the crate trims line feeds off both ends of a multiline
  value where Python keeps a leading one (`k=` + indented line), normalised.
- **The writer against the reader**: a random `Ini` written with any `EscapePolicy`,
  `LineSeparator`, `kv_separator` and `indent_multiline_value` must read back under the matching
  `ParseOption` — through a writer, a file, and the policy-only and default entry points.
- **The rustdoc**: `should_escape` per policy, the `ParseOption` examples, `Properties` and the
  `Ini` API against models.

Properties: `parsing_agrees_with_python`, `every_entry_point_parses_alike` (str/reader/opt,
BOM), `crlf_and_lf_parse_alike`, `written_ini_reads_back`,
`write_to_file_and_load_from_file_agree_with_the_writer`, `quotes_and_escapes_follow_the_docs`,
`should_escape_follows_the_policy_docs`, `properties_follow_a_model`, `ini_api_follows_a_model`,
`doc_examples`; ten pinned expected failures below.

## Bugs (10)

- **rust-ini/1** (wrong-result, medium): `\f`/`\v` written, `f`/`v` read.
- **rust-ini/2** (wrong-result, medium): astral characters written as `\x` + 5–6 hex digits
  under the `*Extended`/`Everything` policies; the reader takes four (`🐱` → `ὃ1`).
- **rust-ini/3** (contract, medium): no policy escapes a quote; a value starting with `"`/`'`
  is misread or rejected by the crate's own reader (`k="x` → EOF error).
- **rust-ini/4** (wrong-result, medium): CRLF + indented multiline values → an extra line feed
  per continuation line (`a\n\nb` for `a\nb`).
- **rust-ini/5** (wrong-result, low): a line without a delimiter is glued onto the next line's
  key (`foo\nbar=1` → key `"foo\nbar"`).
- **rust-ini/6** (contract, low): `enabled_escape: false` still joins lines on a trailing
  backslash and hides a delimiter after one.
- **rust-ini/7** (contract, low): `indent_multiline_value` indents line feeds in section names
  and keys, which do not read back.
- **rust-ini/8** (contract, low): `remove`/`delete` documented "first", remove all.
- **rust-ini/9** (wrong-result, medium): two consecutive indented comment lines (or, with CRLF,
  a whitespace-only line then an indented comment) → "doesn't support inline comment".
- **rust-ini/10** (wrong-result, medium): values are trimmed after unescaping, so escaped
  whitespace at either end (`\t`, `\r`, `\n`, `\x0020`) is lost.

## Not bugs

- Padding around section names, keys and values is trimmed (INI convention; Python trims keys
  and values too); keys containing `=`/`:` need a `Reserved*` policy to round-trip (that is the
  policy's purpose); `[]` is a section named `""` and round-trips.
- `Nothing` is documented "dangerous": backslashes and control characters do not round-trip
  under it.
- `LineSeparator::CR` is `"\n"` (named oddly, documented plainly).
- `Ini::len` counts distinct section names, not sections; `sections()` yields distinct names.
- The README's sample output (`unicode=Raspberry\x6811\x8393`) is what `BasicsUnicode` writes;
  the default `Basics` policy writes the UTF-8 raw — a stale README, not counted.
