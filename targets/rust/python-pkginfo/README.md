# python-pkginfo

[python-pkginfo](https://github.com/PyO3/python-pkginfo-rs) (PyO3; a Rust port of the Python
`pkginfo` package) reads Python core metadata: `Metadata::parse` parses a `PKG-INFO`/`METADATA`
text (the RFC 822-style email format, via `mailparse` and an RFC 2047 decoder) into a typed
struct, and `Distribution::new` opens an sdist (`.tar.gz`, `.zip`), a wheel or an egg, finds
the metadata file inside and reports the format and the Python tag. Written in the zoo at 0.6.8
(HEAD `58fb074`, 2026-02-24); tests in `tests/hegel.rs`, run with `--features serde`.

## The oracles

One persistent Python child (the first of `python3`, `/usr/bin/python3` that imports the
modules; `[run] setup` pip-installs or upgrades them — `packaging` ≥ 24.1 is needed for
`License-Expression`/`License-File`):

- **`packaging.metadata.parse_email`** — PyPA's reader of the email format: the raw field dict
  (strings, lists, keywords split on commas, project URLs as a map, description from header or
  body) and the set of fields it could not parse;
- **`pkginfo`** (Python) — the crate's namesake: `Distribution.parse` for its header
  conventions (unfolding, the legacy eight-space `Description` indent), and `SDist`/`Wheel`/
  `BDist` for reading archives (shallowest metadata file that contains `Metadata-Version`).

Alongside: RFC 2047 encoded words (what distutils wrote for non-ASCII values) must decode to
the raw text, and the wheel filename convention for `python_version()`.

## Properties

- **Fields** (`metadata_parses_like_packaging`): random metadata texts — the three required
  fields, a random subset of the eleven single-use fields (UTF-8 values, possibly empty or with
  trailing spaces), 0–3 values of each multi-use field, `Keywords`, `Project-URL`s with distinct
  labels, a `Description` as a header or as a body (blank lines, indented lines, optional
  trailing newline), LF or CRLF — parse to the same values as `packaging`'s raw dict: strings,
  lists in order, keywords (split on commas), project URLs (label → URL), description.
- **Encoded words** (`encoded_words_decode_to_the_raw_text`): RFC 2047 `Q`-encoding any header
  values yields the same `Metadata` as the raw text.
- **Archives** (`distributions_read_like_pkginfo`): `.tar.gz` and `.zip` sdists
  (`<name>-<version>/PKG-INFO` among `setup.py`, sources, README, sometimes an `.egg-info` copy
  or a vendored `PKG-INFO` with *different* content listed after it), wheels
  (`<name>-<version>.dist-info/METADATA`, `WHEEL`, `RECORD`, sometimes a vendored `.dist-info`)
  and eggs (`EGG-INFO/PKG-INFO`) are read like Python `pkginfo`: same name, version, summary,
  description; the real metadata file; the right `DistributionType`; `python_version()` is
  `source` for sdists, the wheel's Python tag, the egg's tag.

The general generators stay away from the pinned shapes: no tab after the colon (bug 4), no
folded or multi-line header values (bugs 5, 6), nested metadata files only after the real one
(bugs 1, 2), wheel filenames without a build tag (bug 3); single-use fields appear at most once
(`packaging` treats repeats as unparsed; the crate takes the first), values are never the legacy
`UNKNOWN` placeholder (the crate maps it to `None` by design).

## Bugs (6, all zoo-original, found 2026-09-14)

- **python-pkginfo/1** (medium) — a `.tar.gz` sdist yields whichever `PKG-INFO` the tar lists
  first, at any depth: a vendored package's or the `.egg-info` copy ahead of the top-level one
  is returned as the distribution's metadata (Python `pkginfo` reads the shallowest).
- **python-pkginfo/2** (low) — a `.zip` sdist with the top-level `PKG-INFO` and an
  `.egg-info/PKG-INFO` copy reads whichever is listed first (`file1`, unchecked).
- **python-pkginfo/3** (low) — `python_version()` is `any` for a wheel with a build tag in its
  filename (six parts; the tags are the last three).
- **python-pkginfo/4** (low) — a tab after the colon is kept in the value (`Author:\ty` →
  `\ty`) for every field but the three required ones.
- **python-pkginfo/5** (low) — the legacy eight-space continuation indent of a header-form
  `Description` is kept (Python `pkginfo` dedents; the spec's `       |` form is not handled
  either).
- **python-pkginfo/6** (low) — folded values are unfolded in multi-use fields (`a b`) but kept
  with newline and indent in single-use ones (`a\n  b`).

## Not bugs

- RFC 2047 encoded words are decoded by the crate and not by `packaging`/`pkginfo`; distutils
  wrote them for non-ASCII values, so decoding is the useful reading — checked as a
  self-consistency property instead.
- The legacy `UNKNOWN` placeholder becomes `None`/is dropped from lists (documented intent;
  `packaging` keeps it); repeated single-use fields take the first value (`packaging`: unparsed);
  a `Description` header *and* a body give the body (`packaging`: both unparsed); a line without
  a colon among the headers is skipped by mailparse where `email.parser` starts the body there;
  invalid UTF-8 in a header makes the field `None` (`packaging`: mojibake in unparsed). All are
  choices on invalid or ambiguous input, and the generator avoids them.
- The RFC 2047 decoder drops trailing whitespace of an encoded value.

## History

- 2026-09-14: created at 58fb074 (0.6.8); 6 bugs.
