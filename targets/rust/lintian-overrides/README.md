# lintian-overrides

Hegel property tests for [lintian-overrides](https://github.com/jelmer/debian-parsers)
(`lintian-overrides/` member of the debian-parsers workspace, 0.1.7): the
format-preserving (rowan) parser for Debian `lintian-overrides` files, its
line/spec accessors and offset lookups, the `matches`/`info_matches`
wildcard matching, `LintianOverridesBuilder`, and the rewriters
`filter_overrides`, `rename_tags` and `map_overrides`.

Written for the zoo (no upstream property tests to import). The reference
is **lintian itself**: `Lintian::Processable::Overrides::parse_overrides`
applied to a fake processable (Moo role consumer) carrying the generated
package name and type, and `Lintian::Util::match_glob`
(`Regexp::Wildcards`, type `jokers`: `*` → `.*`, `?` → `.`, `\*` literal),
both driven as one persistent Perl child (`use lib
'/usr/share/lintian/lib'`); plus the generators' own model of the grammar
from the lintian manual, `[[<package>][ <archlist>][ <type>]: ]<tag>[ <context>]`.

## Properties

* `files_are_read_like_lintian`: generated files (empty and comment lines,
  spec-only lines, overrides with any subset of name / `[arch …]` / type,
  tabs and multiple spaces, trailing whitespace, optional final newline)
  give the same tags, architecture lists, patterns (whitespace-normalised)
  and malformed line numbers as lintian, and the accessors (`package`,
  `package_type`, `arch_list`, `has_arch_list`, `has_colon`, `is_comment`,
  `is_empty`, `info`) follow the model; `ok()` is `Ok` iff there are no
  errors; `errors_with_offsets` points at the malformed lines.
* `the_tree_is_lossless`, `any_text_round_trips`: `text()`/`Display` are the
  identity, line ranges slice back to the line texts, `snapshot`/`tree_eq`
  behave; arbitrary text (CR, unterminated brackets, stray colons) round
  trips with one line node per source line.
* `offsets_follow_the_layout`: `tag_range`, `info_range`,
  `package_type_range`, `contains_offset`, `arch_list_contains_offset`,
  `package_name_at_offset` and `line_at_offset` (inclusive, first line wins
  a shared boundary) against offsets computed from the source.
* `info_matches_is_lintians_glob`: `*`-globs whose literal parts share no
  character agree with `match_glob` (and with a small recursive model) on
  random values and on values built by filling the stars.
* `matches_follows_lintian`: `OverrideLine::matches` for a hint with the
  processable's name and type equals "same tag, and the pattern is empty
  or `match_glob` accepts the context"; a spec naming another package or
  type never matches.
* `built_files_are_read_back`: the builder's tree equals the parse of its
  text, the lines carry what was built, and lintian reads the same
  tag/pattern list.
* `filter_keeps_exactly_the_selected_lines`, `rename_tags_changes_only_the_tags`,
  `map_overrides_writes_the_transformed_lines`: the rewriters' output has
  exactly the expected lines (everything but the tag verbatim for
  `rename_tags`), and each result tree equals the parse of its own text.

## Bugs

All eleven bugs in `bugs.toml` are zoo-original (found 2026-09-14 at
4dc04da). Parser, against lintian:

1. `foo:some-tag` (colon glued to the name) is read as a tag, not a spec;
2. `[amd64] some-tag` (spec without a colon) is an override with the tag
   `[amd64]` instead of an error;
3. whitespace between a bare type keyword and its colon is dropped from
   the tree — `source : tag` renders as `source: tag`, all later ranges
   shift;
4. `info()` keeps the line's trailing whitespace.

Matching, against `match_glob`:

5. `info_matches` lets literal parts overlap (`ab*b` matches `ab`,
   `*foo*foo` matches `xfoo`);
6. `?` is not a wildcard;
7. `\*` is not an escape;
8. `matches()` with no issue info is true for an override that has a
   context pattern.

Rewriters and builder:

9. `map_overrides` drops the package type when the transform returns no
   package name;
10. `map_overrides` drops the architecture list of every transformed line;
11. `add_comment` emits the text without `#`, so the built tree's comment
    re-parses as an override.

## Notes

* The general generators avoid exactly the pinned shapes: a space after
  every spec colon, no spec without a colon, no whitespace before a bare
  type's colon (`any_text_round_trips` skips such lines), `?`/`\` and
  overlapping literal parts kept out of the matched patterns, hints without
  context not compared for overrides with a pattern, `map_overrides`
  transforms keep the type with a name and skip lines with an arch list,
  built comments start with `#`.
* lintian's parser is context-dependent (Debian #699628): it strips the
  package name and type only when they equal the processable's, and a tag
  equal to the package name or to a type keyword is an error there. The
  generators use the processable's own name/type in specs and tags from a
  disjoint list, so both sides see the same file.
* Not compared: lintian's comment "justification" (the crate has no
  accessor for comments attached to an override); `try_find_override_files`
  / `try_iter_overrides` (filesystem).
* The Perl child needs lintian's library (`/usr/share/lintian/lib`), Moo,
  Regexp::Wildcards and JSON::PP — all pulled in by the `lintian` package.
