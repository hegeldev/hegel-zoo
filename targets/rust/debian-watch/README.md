# debian-watch

Hegel property tests for [debian-watch](https://github.com/jelmer/debian-parsers)
(`debian-watch/` member of the debian-parsers workspace, 0.4.12): the
lossless (rowan) parser for `debian/watch` files in the line-based formats
(`linebased::WatchFile`, `Entry`, `EntryBuilder`, setters), the mangling
rules of uscan(1) (`mangle::apply_mangle`: `s///`, `tr///`, `y///`), the
`@…@` substitutions (`subst::subst`) and the typed option values.

Written for the zoo (no upstream property tests to import). The references
are **uscan itself** — devscripts' `Devscripts::Uscan::Utils::safe_replace`
(the function uscan applies mangling rules with) and the substitution
constants of `Devscripts::Uscan::WatchFile`, driven as a persistent Perl
child — and python-debian's `debian.watch` (`WatchFile.from_lines`, `expand`)
as a persistent Python child, plus the generators' own model of the watch
file grammar.

## Properties

* `substitution_rules_mangle_like_uscan`, `translation_rules_mangle_like_uscan`,
  `unmatched_rules_leave_the_input_alone`: generated `s`/`tr`/`y` rules
  (seven delimiters, a small regex grammar with up to two groups, `${N}`/`$N`
  replacements, the `g` flag, equal-length `tr` lists) applied to
  version-like strings give exactly what `safe_replace` gives, and are
  refused exactly when uscan refuses them; `parse_mangle_expr` reads back
  the generated parts.
* `substitutions_expand_like_python_debian`, `expanded_patterns_match_like_uscan`:
  `subst` agrees with python-debian's `expand` on the shared variables, and
  a template expanded by the crate matches (and captures) the same as the
  uscan-expanded template on generated `package-version.ext` filenames.
* `watch_files_are_read_like_python_debian`: generated files (version 3/4,
  quoted/unquoted options from the documented set, URLs with and without an
  inline pattern, patterns with `@…@` and `=`, policies, scripts, tabs,
  comments, blank lines, `\` continuations) read to the same version and
  entries as python-debian, which in turn agree with the model.
* `the_tree_is_lossless_and_the_parse_is_consistent`: `to_string` is the
  identity for `from_str`, `parse_watch_file`, `from_str_relaxed` and
  `from_reader`; `line_col` points at the entry's line.
* `typed_accessors_follow_the_options`: every typed accessor (`compression`,
  `mode`, `pgpmode`, `gitmode`, `gitexport`, `searchmode`, `ctype`,
  `pretty`, `repack`, `bare`, `decompress`, `passive`, `component`, `date`,
  the mangle getters and the `versionmangle` fallbacks, `version`) matches
  the generated options; `apply_*mangle` delegate to `apply_mangle`;
  `format_url` is `subst` of the URL.
* `built_entries_are_read_back`, `edits_are_read_back`: `EntryBuilder` +
  `add_entry` and the setters (`set_url`, `set_matching_pattern`,
  `set_version_policy`, `set_script`, `set_opt`, `del_opt_str`,
  `set_version`) render text that re-parses to the model, live and
  re-parsed, and that python-debian reads the same way.
* `option_types_round_trip_through_display`: the option enums and
  `VersionPolicy` survive `Display` → `FromStr`.

## Bugs

All thirteen bugs in `bugs.toml` are zoo-original (found 2026-09-13 at
4dc04da). Mangling (against `safe_replace`):

1. bracketing delimiters `s{…}{…}` are mis-split;
2. the `i`/`x` flags are ignored;
3. flags uscan rejects are accepted;
4. replacements are not Perl-processed: `\.` stays `\.` (so
   `uversionmangle=s/_/\./g` yields `1\.2\.3`), `\1`/`$&` literal (high);
5. `tr` demands equal lengths (Perl pads/ignores) and ignores `c`/`d`/`s`;
6. `@ANY_VERSION@` lacks `[Vv]?`, `@ARCHIVE_EXT@` lacks `tar.zst`.

The line-based parser and editor:

7. a flag option ending the list (`opts=bare https://…`) is a parse error;
   `EntryBuilder::flag` produces exactly that text (high);
8. `version=4` at end of file without a newline is rejected;
9. the default `pretty` is `0.0~git%cd.h%` (typo of `%cd.%h`);
10. after a URL with an inline pattern the policy is reported as the pattern;
11. `#foo` (no space) is an entry, not a comment;
12. option values containing `=` are truncated at the `=`;
13. `set_opt` on a quoted list appends after the closing quote.

## Notes

* The general properties skip exactly the pinned shapes: only the `g`
  flag, no backslashes or `$&` in replacements, equal-length `tr` lists,
  `/`-style delimiters; a valued option last, spaced comments, no policy
  after an inline-pattern URL, no `=` in option values, no `set_opt` on
  quoted lists, `v`-prefixed and `.zst` inputs excluded from the uscan
  match comparison.
* uscan quirks not counted against the crate: `safe_replace` implements
  `g` as a loop of single substitutions on the modified string, so
  `s/^x//g` strips repeatedly (skipped for `^`-anchored patterns); Perl
  allows an empty match right after a non-empty one where the regex crate
  does not (`s/a*/A/g`; nullable patterns skipped with `g`).
* python-debian quirks normalised: after a quoted `opts="…" \`
  continuation it leaves a leading space on the URL; option strings are
  compared trimmed. The pins compare option lists as sets where the
  builder's `HashMap` makes the order random.
* Documented, not recorded: `set_matching_pattern`, `set_version_policy`
  and `set_script` only replace an existing field (the edits model follows
  that); `format_url` unwraps `Url::parse`, so it panics on an entry whose
  first field is not a URL (e.g. the `#foo` entry of bug 11).
