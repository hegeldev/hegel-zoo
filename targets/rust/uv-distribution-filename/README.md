# uv-distribution-filename

[uv-distribution-filename](https://github.com/astral-sh/uv/tree/main/crates/uv-distribution-filename)
is the crate of [uv](https://github.com/astral-sh/uv) that reads distribution filenames:
`WheelFilename` (name, version, optional build tag, compressed Python/ABI/platform tag sets, PEP
427 / the binary distribution format specification), `SourceDistFilename` (`{name}-{version}.{ext}`
for `.tar.gz`, `.zip` and ten legacy extensions, PEP 625), `DistFilename` (either, with or without
a package-name hint, as used on registry indexes), `EggInfoFilename`, `DistExtension` and
`ExpandedTags`. Written in the zoo at 0.0.80 (uv HEAD `c0df400`, 2026-09-12); tests in
`crates/uv-distribution-filename/tests/hegel.rs`, run in that crate's directory.

## The oracle

One persistent Python child (the first of `python3`, `/usr/bin/python3` that imports it; `[run]
setup` pip-installs it if neither does) running PyPA's **`packaging`**:
`packaging.utils.parse_wheel_filename` (normalised name, `Version`, build tag as `(int, str)`,
the expanded tag set), `parse_sdist_filename`, `canonicalize_name`, and `str(Version)` for
PEP 440 normalisation. Alongside: the crate's `Display` must re-parse to the same value and be
the identity on canonical filenames; the recognised tags are exactly the atoms the crate's own
tag types parse (`uv-platform-tags`); the sdist parsers with and without a hint agree; the
documented extension table.

## Properties

- **Wheels** (`wheel_filenames_parse_like_packaging`): filenames built from the convention —
  names in mixed spellings (`Foo_Bar`, `oslo.concurrency`, random `[A-Za-z0-9._]` without runs),
  PEP 440 versions in every normalisable spelling (`v` prefix, epoch, leading zeros, `alpha`/`c`/
  `pre`/`rev`/`r`, `_` and `.` separators, local segments), optional build tags, compressed tag
  sets of 1–3 known or unknown atoms — parse to `packaging`'s name, version and build tag, and
  the typed Python/ABI/platform tags are exactly the atoms `LanguageTag`/`AbiTag`/`PlatformTag`
  parse, in order.
- **Display** (`wheel_display_round_trips`): `to_string()` re-parses to an equal value, is the
  filename itself when name and version are canonical, otherwise normalises exactly those two;
  `stem()`/`from_stem` and serde agree.
- **Mutants** (`wheel_mutants_are_judged_alike`): one-character edits of valid wheel filenames
  are accepted or rejected alike by the crate and `packaging`, except in the documented lenient
  directions (below).
- **Sdists** (`sdist_filenames_parse_like_packaging`, `malformed_sdist_filenames_are_rejected_alike`):
  `{name}-{version}.{ext}` over the twelve extensions parses like `packaging` (its `.tar.gz` twin
  for the legacy ones), the hinted and unhinted parsers agree, `Display` is the escaped normalised
  name + normalised version + extension; missing separator, empty name, bad version or unknown
  extension are rejected by both.
- **Extensions** (`extensions_follow_the_documented_list`), **eggs**
  (`egg_info_filenames_give_name_and_version`).

The general generators stay away from the pinned shapes: no `+` in tag numbers (bug 1), no
trailing `.` in a tag component (bug 2), known tags spelled canonically (bug 3), build tags below
`u64` (bug 4), names without runs of separators (bug 5), lower-case extensions (bug 6).

## Bugs (6, all zoo-original, found 2026-09-14)

- **uv-distribution-filename/1** (low) — the single-tag fast path never checks tag characters
  and its numbers are read with `str::parse`, which takes `+`: `foo-1.0-py3+9-none-any.whl`
  parses (shown as `py39`), also `cp3+9`, `manylinux_+2_17_x86_64`; the compressed-tag path
  and `packaging` reject them.
- **uv-distribution-filename/2** (low) — a trailing `.` in a tag component is ignored (`py3.`,
  `none.`): the splitter yields no empty last atom, while `..` and a leading `.` are rejected
  (`packaging`: "empty component").
- **uv-distribution-filename/3** (low) — `Display` drops leading zeros from single-tag numbers:
  `py307` → `py37`, `cp309` → `cp39`, `manylinux_02_17_x86_64` → `manylinux_2_17_x86_64`; the
  compressed-tag path keeps the text.
- **uv-distribution-filename/4** (low) — a build tag with more digits than a `u64` holds is
  rejected ("number too large"); the specification sorts the digits as an int, `packaging` is
  unbounded.
- **uv-distribution-filename/5** (medium) — with a package-name hint (`DistFilename::try_from_filename`,
  the registry path) an sdist whose name has a run of separators (`foo__bar-1.0.tar.gz`,
  `foo..bar-1.0.tar.gz` for `foo-bar`) is rejected: the hint is matched byte by byte at the
  hint's length. The unhinted parser, the wheel parser with the same hint and `packaging` read
  `foo-bar`; on an index such a file is silently dropped.
- **uv-distribution-filename/6** (low) — `.TAR.gz` is an sdist (`eq_ignore_ascii_case("tar")`)
  but `.tar.GZ` and `.Zip` are not; the conventions and `packaging` are case-sensitive.

## Not bugs

- The crate normalises: `Foo.Bar-1.0-…whl` is displayed `foo_bar-1.0-…whl`, `1.0alpha1` as
  `1.0a1`, `a-1-1.tar.gz` with hint `a` as `a-1.post1.tar.gz` (PEP 440 reads `1-1` as `1.post1`;
  the documented ambiguity of sdist filenames without a hint).
- Lenient where `packaging` is strict: runs of separators in a wheel's name (`foo__bar`,
  `packaging` rejects since 22.0), interpreter atoms that are not identifiers (`3py`), unknown
  tags of any kind — kept in the text, dropped from the typed lists (`is_compatible` is then
  false). Strict where `packaging` is lenient: tag atoms outside `[A-Za-z0-9_]`, build tags
  outside `[A-Za-z0-9_.]` (path traversal), names that start or end with a separator or are not
  ASCII (`_foo`, `é`; PEP 508 names), platform numbers above `u16` (`manylinux_65536_0_x86_64`
  is an unknown tag). All documented in the crate or deliberate; the mutation property allows
  exactly these.
- The typed tag lists keep duplicates (`manylinux_2_17_x86_64.manylinux_2_17_x86_64`);
  `packaging` returns a set.
- The version parsers (`uv-pep440` vs `packaging.version`) agreed on every spelling generated.

## History

- 2026-09-14: created at c0df400 (0.0.80); 6 bugs.
