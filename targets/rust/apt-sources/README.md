# apt-sources

Hegel property tests for [apt-sources](https://github.com/jelmer/debian-parsers)
(`apt-sources/` member of the debian-parsers workspace, 0.3.0): the parser
for APT source files in both formats — the one-line `sources.list` format
(`legacy::LegacyRepositories`) and the deb822 `.sources` format
(`Repositories`, built on deb822-fast's derive), their `Display`s and the
conversions between them.

Written for the zoo (no upstream property tests to import). The references
are **APT itself** — `apt-get update --print-uris` on a temporary
configuration, run offline, lists the index URIs APT derives from a sources
file; a model turns them and the crate's parse into the same set of
(type, base URI, suite, component, architecture/language) targets — and
python-apt's `aptsources.sourceslist.SourceEntry` as a persistent Python
child for the one-line format, plus the generators' own model of both
formats.

## Properties

* `legacy_lines_are_read_as_the_model_says`, `legacy_lines_are_read_like_python_apt`,
  `legacy_lines_yield_the_indexes_apt_fetches`: generated one-line files
  (types, all documented options, http(s) URIs, suites, components, tabs,
  comment and blank lines) parse to exactly the modelled `LegacyRepository`s,
  agree with python-apt (type, URI, suite, components, architectures,
  trusted) and yield the indexes APT fetches.
* `legacy_display_round_trips`: parse → `Display` → parse is the identity,
  one line per repository, and APT reads the display the same way.
* `stanzas_are_read_as_the_model_says`, `stanzas_yield_the_indexes_apt_fetches`,
  `stanza_display_round_trips`: the same for deb822 stanzas (all fields the
  crate knows, random field order, flat repositories, `Enabled: no`).
* `legacy_to_deb822_and_back_is_the_identity`,
  `deb822_to_legacy_lines_keeps_the_indexes`: the `From` conversions in both
  directions preserve every field and the set of indexes; a stanza becomes
  |types| × |URIs| × |suites| distinct lines.

## Bugs

All eleven bugs in `bugs.toml` are zoo-original (found 2026-09-13 at 4dc04da).
The one-line parser is a single regex applied with `captures_iter`, so every
line it does not match vanishes silently:

1. components containing `-` (`non-free`, `non-free-firmware`) — the default
   Debian 12 line is dropped (high);
2. flat repositories (no component), and `Display` writes them with a
   trailing space;
3. a trailing `# comment`;
4. commented-out (`# deb`) entries, documented as disabled repositories, are
   not read;
11. two or more spaces between components.

Round trips and the deb822 side:

5. `Display` writes `pdiffs` as `pdiff`;
6. `Allow-Insecure`, `Allow-Weak`, `Allow-Downgrade-To-Insecure` and
   `Trusted` are parsed with `bool::from_str` — `yes`/`no` rejected;
7. `PDiffs: yes` is displayed as `PDiffs: true`, which the parser rejects;
8. an embedded `Signed-By` key block gains an empty line per round trip;
9. the regex spans lines (`deb http://a/ s` + `main` on the next line is one
   entry);
10. `arch+=` / `arch-=` are rejected.

## Notes

* The general properties skip exactly the pinned shapes (dashed components,
  flat one-line repositories, trailing comments, disabled entries, multiple
  spaces between components, `pdiffs`/`PDiffs`, the four yes/no fields, key
  blocks).
* APT facts used by the model: `--print-uris` works without network and
  without a lock; a source whose (type, URI, suite, component) repeats is an
  error ("configured multiple times"), so every generated line has its own
  host; a flat repository with components or a non-flat one without is an
  error; `binary-all` is fetched implicitly and ignored by the model;
  `Enabled: no` yields no URIs; unknown one-line options are accepted by APT
  (the crate refuses the file — documented as unsupported, not recorded);
  `target=` changes the indexes, so lines with it are not compared with APT.
* python-apt's `SourceEntry` marks every option other than `arch`/`trusted`
  as invalid, so only such lines are compared with it; its `trusted` is an
  int from `apt_pkg.string_to_bool`.
* Not recorded: `Types` is a `HashSet`, so the order of `deb`/`deb-src` in
  `Display` is not deterministic across processes; `Url` normalises URIs
  (`http://a` → `http://a/`), which APT does not mind.
- 2026-09-17: base bumped 4dc04da82229 → 3caf83edab73 (2026-09-17, "Merge pull request #474 from jelmer/issue-471"; 0.3.0); 11 bug(s) still reproduce. 63 tests pass.
