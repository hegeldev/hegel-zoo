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
- 2026-09-14: base bumped c0df400a4cf4 → 83d556d712c7 (2026-09-14, "Scope required-environment checks to the current fork (#21672)"; 0.0.80); 6 bug(s) still reproduce. 55 tests pass.
- 2026-09-14: base bumped 83d556d712c7 → c40e652bc385 (2026-09-14, "Exclude backports-zstd from the Sentry PGO corpus (#21678)"; 0.0.80); 6 bug(s) still reproduce. 55 tests pass.
- 2026-09-14: base bumped c40e652bc385 → 595c8e2c6812 (2026-09-14, "Use cargo codspeed via astral-dev-toolchain (#21674)"; 0.0.80); 6 bug(s) still reproduce. 55 tests pass.
- 2026-09-14: base bumped 595c8e2c6812 → 85fe61435fe5 (2026-09-14, "Use cargo bloat via astral-dev-toolchain (#21681)"; 0.0.80); 6 bug(s) still reproduce. 55 tests pass.
- 2026-09-15: base bumped 85fe61435fe5 → 941b557a69d7 (2026-09-14, "Remove unused Serde derives from index locations (#21685)"; 0.0.80); 6 bug(s) still reproduce. 55 tests pass.
- 2026-09-15: base bumped 941b557a69d7 → ffc98b158bad (2026-09-14, "Forbid install-action via zizmor (#21682)"; 0.0.80); 6 bug(s) still reproduce. 55 tests pass.
- 2026-09-15: base bumped ffc98b158bad → 6f7795bb4f6e (2026-09-14, "Update Rust crate axoupdater to v0.10.2 (#21658)"; 0.0.80); 6 bug(s) still reproduce. 55 tests pass.
- 2026-09-15: base bumped 6f7795bb4f6e → b8aff80900e7 (2026-09-15, "Update dependency astral-sh/uv to v0.12.13 (#21655)"; 0.0.81); 6 bug(s) still reproduce. 55 tests pass.
- 2026-09-15: base bumped b8aff80900e7 → 000a665b745a (2026-09-15, "Batch HTTP cache writes in blocking tasks (#21675)"; 0.0.81); 6 bug(s) still reproduce. 55 tests pass.
- 2026-09-15: base bumped 000a665b745a → fd89f638d15f (2026-09-15, "Add regression test for symlinks inside install directory (#21693)"; 0.0.81); 6 bug(s) still reproduce. 55 tests pass.
- 2026-09-15: base bumped fd89f638d15f → cdabfcedb50b (2026-09-15, "Revert "Reject symlinked wheel installation destinations" (#21699)"; 0.0.81); 6 bug(s) still reproduce. 55 tests pass.
- 2026-09-15: base bumped cdabfcedb50b → 2c35bb31de15 (2026-09-15, "Use Packse scenarios to speed up tool tests (#21634)"; 0.0.81); 6 bug(s) still reproduce. 55 tests pass.
- 2026-09-15: base bumped 2c35bb31de15 → ad552557b635 (2026-09-15, "Preserve local path intent when merging dependency metadata (#20631)"; 0.0.82); 6 bug(s) still reproduce. 55 tests pass.
- 2026-09-15: base bumped ad552557b635 → 694dfd8155ec (2026-09-15, "Verify distribution hashes (#21562)"; 0.0.82); 6 bug(s) still reproduce. 55 tests pass.
- 2026-09-15: base bumped 694dfd8155ec → ac9201b10433 (2026-09-15, "Allow manually specifying build dependency hashes in configuration (#21467)"; 0.0.82); 6 bug(s) still reproduce. 55 tests pass.
- 2026-09-15: base bumped ac9201b10433 → 1f245a625114 (2026-09-15, "Cover packaged editable self-dependency name mismatches (#21714)"; 0.0.82); 6 bug(s) still reproduce. 55 tests pass.
- 2026-09-15: base bumped 1f245a625114 → b44bd4561d97 (2026-09-15, "Use a small native extension in system Python tests (#21713)"; 0.0.82); 6 bug(s) still reproduce. 55 tests pass.
- 2026-09-15: base bumped b44bd4561d97 → bf12c8e61b2d (2026-09-15, "Enable Renovate updates for the release workflow (#21722)"; 0.0.82); 6 bug(s) still reproduce. 55 tests pass.
- 2026-09-15: base bumped bf12c8e61b2d → 7752bc92b53e (2026-09-15, "Update astral-sh/setup-uv action to v10.1.0 (#21666)"; 0.0.82); 6 bug(s) still reproduce. 55 tests pass.
- 2026-09-15: base bumped 7752bc92b53e → a265915acf9e (2026-09-15, "Expand Debian and official Python system-test images (#21726)"; 0.0.82); 6 bug(s) still reproduce. 55 tests pass.
- 2026-09-15: base bumped a265915acf9e → 27e80c1498d9 (2026-09-15, "renovate: update uv hashes correctly with setup-uv (#21724)"; 0.0.82); 6 bug(s) still reproduce. 55 tests pass.
- 2026-09-15: base bumped 27e80c1498d9 → b9df2d1d1ac7 (2026-09-15, "Move default-group selection onto project and workspace types (#21689)"; 0.0.82); 6 bug(s) still reproduce. 55 tests pass.
- 2026-09-15: base bumped b9df2d1d1ac7 → 9d8d76f4a13d (2026-09-15, "Use cargo-deny from toolchain (#21730)"; 0.0.82); 6 bug(s) still reproduce. 55 tests pass.
- 2026-09-16: base bumped 9d8d76f4a13d → c202b35405f1 (2026-09-15, "Encapsulate resolver metadata requests (#21735)"; 0.0.82); 6 bug(s) still reproduce. 55 tests pass.
- 2026-09-16: base bumped c202b35405f1 → 005d5cd9922b (2026-09-15, "Extract resolver requirement expansion (#21733)"; 0.0.82); 6 bug(s) still reproduce. 55 tests pass.
- 2026-09-16: base bumped 005d5cd9922b → f018faac8db2 (2026-09-16, "Update Python metadata for Pyodide 314.0.7, 0.29.5, 0.27.8 (#21741)"; 0.0.82); 6 bug(s) still reproduce. 55 tests pass.
- 2026-09-16: base bumped f018faac8db2 → f67344d87d2a (2026-09-16, "Skip `uv_build` fast path when pinned version differs (#21742)"; 0.0.82); 6 bug(s) still reproduce. 55 tests pass.
- 2026-09-16: base bumped f67344d87d2a → 3977dafee977 (2026-09-16, "Remove unused reqwest blocking feature from tests (#21749)"; 0.0.82); 6 bug(s) still reproduce. 55 tests pass.
- 2026-09-16: base bumped 3977dafee977 → bafbff9f631e (2026-09-16, "Respect artifact compatibility when initializing platform coverage (#21753)"; 0.0.82); 6 bug(s) still reproduce. 55 tests pass.
- 2026-09-16: base bumped bafbff9f631e → 108a3587b857 (2026-09-16, "Refactor HashDigest APIs (#21139)"; 0.0.82); 6 bug(s) still reproduce. 55 tests pass.
- 2026-09-16: base bumped 108a3587b857 → cc6880fd22c2 (2026-09-16, "Show captured publish test failures (#21757)"; 0.0.82); 6 bug(s) still reproduce. 55 tests pass.
- 2026-09-16: base bumped cc6880fd22c2 → 6b40d9e51d24 (2026-09-16, "Enforce non-staleness of cargo deny's `bans.build` list (#21756)"; 0.0.82); 6 bug(s) still reproduce. 55 tests pass.
- 2026-09-17: base bumped 6b40d9e51d24 → ec2783923893 (2026-09-17, "Add regression test for uv#21773 (#21775)"; 0.0.82); 6 bug(s) still reproduce. 55 tests pass.
- 2026-09-17: base bumped ec2783923893 → f69944bcc9a1 (2026-09-17, "Respect configured index credentials in `uv upgrade` (#21776)"; 0.0.82); 6 bug(s) still reproduce. 55 tests pass.
