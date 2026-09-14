# dep3

Hegel property tests for [dep3](https://github.com/jelmer/debian-parsers)
(`dep3/` member of the debian-parsers workspace, 0.2.4): the parser and
generator for DEP-3 patch headers — `lossless::PatchHeader` (a
deb822-lossless paragraph with typed getters and setters),
`lossy::PatchHeader` (a deb822-fast derive struct), `header_end` /
`parse_relaxed`, and the field types `Forwarded`, `Origin`,
`OriginCategory`, `AppliedUpstream`, `parse_debian_bug_id`.

Written for the zoo (no upstream property tests to import). The references
are the [DEP-3 specification](https://dep-team.pages.debian.net/deps/dep3/)
as a generated model (every field, repeated fields, `Subject`/`From` git
aliases, `.` blank-line markers, categorised origins, `commit:` references,
a trailing unified diff behind `---` / `diff ` / `Index:`), **dpkg's deb822
reader** (`Dpkg::Control::HashCore` in a persistent Perl child) for the raw
field values of the header paragraph, and the crate's two layers against
each other.

## Properties

* `lossless_headers_are_read_like_the_model_and_dpkg`: `header_end` and
  `parse_relaxed` split at the diff, `to_string` is the identity on the
  header, `as_deb822().items()` is the model's field list in order, dpkg
  reads the same (key, value) set (headers without duplicate keys, which
  dpkg refuses), and every typed getter (`description`, `author`, `origin`,
  `forwarded`, `reviewed_by`, `last_update`, `applied_upstream`, `bugs`,
  `vendor_bugs`, `debian_bug_ids`, `long_description` when present) follows
  the model.
* `lossy_headers_are_read_like_the_model`: the derive struct's fields,
  `synopsis` and `long_description` follow the model; `Display` re-parses
  to an equal struct; the two layers agree on every typed field.
* `field_types_round_trip_through_display`: the enums survive
  `Display` → `FromStr`, an origin with a category reads back through a
  header, `parse_debian_bug_id` accepts its four documented forms.
* `built_headers_are_read_back`: a header built with the setters from
  scratch is read back by its own getters, by a re-parse, by dpkg and by
  the lossy layer.
* `paragraph_edits_are_seen_by_the_getters`: edits through
  `as_deb822_mut()` (`set`/`insert`/`remove`) are visible to the typed
  getters, live and after a re-parse.

## Bugs

All eight bugs in `bugs.toml` are zoo-original (found 2026-09-14 at
4dc04da):

1. everything after the first blank line is dropped (lossless, silently) or
   a parse error (lossy) — the `git format-patch` body and DEP-3's
   pseudo-header are never read (high);
2. the mbox `From <sha> <date>` first line of a `git format-patch` file is a
   parse error — the spec's own first sample does not parse;
3. every setter appends a second field instead of replacing, and the
   getters keep the old value (high);
4. `set_description`/`set_long_description` panic when the existing field
   has no long description (high);
5. after `set_description` with a blank line the live header reads the
   marker as ` .`, a re-parse as `.`;
6. lossless `long_description` is `Some("")` for a one-line description and
   keeps the `.` markers; lossy says `None` and decodes them;
7. `Acked-by` is not recognised;
8. the lossy struct keeps only the first of repeated `Bug-Debian` /
   `Reviewed-by` / `Author` fields and drops `Bug-<Vendor>` for other
   vendors, so its `Display` loses them.

## Notes

* The general generators avoid exactly the pinned shapes: no free-form
  body or second paragraph, no mbox line, setters only on absent fields, no
  blank lines in set descriptions, long descriptions only with
  `Description` (with `Subject` DEP-3 puts them outside the fields).
* Inherited from the deb822 layers and not recorded again: an indented `#`
  continuation line is a comment/error (deb822-lossless/4 — no
  long-description line starts with `#`), inserting after an unterminated
  last line glues the lines (deb822-lossless/9 — the edit property needs a
  final newline), CRLF handling (deb822-lossless/3, deb822-fast/3).
* Not recorded: `Origin: vendor` (category without a reference, common in
  the archive) renders as `Origin: vendor, ` with a trailing space, but
  reads back correctly in both layers and in lintian's `\s*,\s*` split;
  `Origin: upstream,url` without the space after the comma is read as
  uncategorised (the spec says "a comma and a space"; lintian is lenient);
  the lossy layer rejects a header with an unparsable `Last-Update` or a
  non-URL `Bug` where the lossless one returns `None` (strictness, not a
  disagreement on valid input); the dpatch `# Field:` comment form is not
  supported (dpatch is gone from Debian).
