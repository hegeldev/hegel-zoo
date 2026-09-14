# go-ini

[go-ini/ini](https://github.com/go-ini/ini) (`gopkg.in/ini.v1`, Unknwon) is the most-used INI
reader and writer for Go: sections with `.`-nested children, `=`/`:` delimiters, `#`/`;`
comments, backslash continuation and Python-style indented continuation, quoted keys and
values (`"`, `'`, `` ` ``, `"""`), shadow (repeated) keys, `%(name)s` interpolation, typed
getters, struct mapping, and a pretty-printing writer. Pinned at e2db55b (v1.67.3+,
2026-09-05), Apache-2.0, no AI policy in the contributing guide.

## Oracles

- **Python's `configparser`**, one child process over JSON lines, configured to the
  intersection of the grammars (`interpolation=None`, `strict=False`, `allow_no_value=False`,
  `=`/`:` delimiters, `#`/`;` comments, inline comments on or off to match the go-ini option,
  `optionxform` = identity or lower to match `InsensitiveKeys`, `[DEFAULT]` prepended so
  go-ini's sectionless keys are Python's defaults). The generated text keeps to what both read
  alike; every restriction is a documented divergence (below or a pinned bug): values never
  start with a quote, backtick, `#` or `;`, never end with a backslash; keys never start with
  a quote, backtick, `[`, `#`, `;` and are never `-`; in the default mode values contain no
  comment symbol at all (go-ini cuts at any `#`/`;`, Python only after whitespace); with
  `SpaceBeforeInlineComment` at most one symbol, no tab before it and a non-empty value before
  a comment; with `AllowPythonMultilineValues` continuation lines only right after a key line,
  no blank, whitespace-only or comment lines in or after them, and go-ini's kept indentation
  stripped before comparing.
- **The writer against the reader**: a `File` built through the API and written with
  `WriteTo`/`WriteToIndent`/`SaveToIndent` under every combination of `PrettyFormat`,
  `PrettyEqual`, `PrettySection` and `DefaultHeader` reads back with `Load`.
- **Models**: `Strings` (delimiter split with `\<delim>` and `\\` escapes, trimmed parts),
  `Bool` (the documented word list), the integer and float getters (strconv, base 0),
  `Ints`/`ValidInts`/`StrictInts`, `MustInt`/`MustBool`, `In`, `RangeInt`, and `%(name)s`
  interpolation (same section, then default; stop at the first unresolvable name).

## Properties

- `TestHegelParseAgreesWithPython` — five option modes (default, `SpaceBeforeInlineComment`,
  `InsensitiveKeys`, `IgnoreInlineComment`, `AllowPythonMultilineValues`), 0–8 lines of
  headers (with trailing comments/junk), keys, comments, blanks, LF or CRLF.
- `TestHegelEntryPointsAgree` — `[]byte`, file, `io.Reader`, `io.ReadCloser`, UTF-8 BOM,
  `LooseLoad` with a missing file, two sources vs their concatenation, `Append`, `Empty()`.
- `TestHegelWrittenFileReadsBack` — sections, keys and values from broad alphabets (line
  feeds, backticks, quotes, comment symbols, padding, delimiters in keys), any indent.
- `TestHegelKeyHelpersFollowTheirDocs`.
- `TestHegelInterpolationFollowsTheModel` — acyclic references across the default and a named
  section; `Value()` stays raw, `Validate` sees the interpolated value.

All general properties pass at 1000 cases × 3 (a few seconds; the Python child does most of
the work). Eight pinned expected failures; go-ini/1's check runs the crashing call in a child
process (this test binary with `HEGEL_INI_LOOP=1`), since a stack overflow is fatal.

## Bugs (8)

| id | title | severity |
|----|-------|----------|
| go-ini/1 | Two values that reference each other (`%(a)s` / `%(b)s`) make `Key.String()` recurse without bound: fatal stack overflow | high |
| go-ini/2 | Values the writer leaves raw or wraps in plain double quotes do not read back: `'abc'`, `"abc"`, `abc\`, `"""`, `" x""` | medium |
| go-ini/3 | Keys starting with `#` `;` `[`, the key `-`, padded keys, keys with a line feed or a backtick plus a quote/delimiter, section names with a line feed are written unreadably | low |
| go-ini/4 | `AllowPythonMultilineValues`: a quoted first line makes the indented continuation an error | low |
| go-ini/5 | `SpaceBeforeInlineComment` recognises only a space inside the trimmed value (tab, comment right after the delimiter) | low |
| go-ini/6 | `Key.Strings` drops an empty last element but keeps an empty first one; drops a trailing backslash | low |
| go-ini/7 | `SpaceBeforeInlineComment` looks for ` ;` only when there is no ` #` | low |
| go-ini/8 | `UnescapeValueCommentSymbols` never sees the escaped symbol (the inline comment is cut first) | low |

## Not bugs (documented, asserted upstream, or design)

- By default any `#` or `;` in a value starts a comment (upstream's own test is titled
  "cannot properly parse INI files containing `#` or `;` in value"); `SpaceBeforeInlineComment`
  and `IgnoreInlineComment` are the documented ways out.
- A trailing backslash joins the next line (`IgnoreContinuation` turns it off); a value
  surrounded by `'` or `"` loses the quotes (`PreserveSurroundedQuote`); `"""…"""` and
  `` `…` `` are multi-line quotes; `-` is the auto-increment key (`#1`, `#2`…).
- Python-style continuation lines keep their indentation (asserted upstream:
  `"a\n  b"`); a truly blank line ends such a value, a whitespace-only or indented comment
  line continues it, and a continuation after an inline comment is kept while Python would
  strip the comment from continuation lines — all divergences from Python that follow from
  the regexp `^([\t\f ]+)(.*)`.
- Each data source starts in the default section, so `Load(a, b)` differs from `Load(a+b)`
  when `b` has sectionless keys (Python would raise `MissingSectionHeaderError`).
- `[DEFAULT]` is the default section; `[default]` is another section unless `Insensitive`,
  which also renames the default section to `default`. Section names are not trimmed
  (`[ a ]` → `" a "`); text after `]` is ignored; the last `]` closes the header.
- The integer getters use `strconv.ParseInt(s, 0, 64)`: `0x10` is 16, `1_000` is 1000.
- `Strings` escapes: `\,` is a literal delimiter, `\\` a backslash, `\x` stays `\x`.
- Shadow keys deduplicate equal values unless `AllowDuplicateShadowValues`; `Value()` is the
  first value.
- Interpolation stops at the first `%(name)s` it cannot resolve and returns the value as it
  stands (later resolvable references included); a self-reference falls through to the
  default section; `Value()` is always raw.

## Conventions

External test package with a dot import; `HEGEL_TEST_CASES` via `hegelOpts`; `property()`
turns panics into test-case failures; one `python3` child held open for the whole run.
