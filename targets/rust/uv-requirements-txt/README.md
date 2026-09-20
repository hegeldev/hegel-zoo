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
- 2026-09-14: base bumped 83d556d712c7 → c40e652bc385 (2026-09-14, "Exclude backports-zstd from the Sentry PGO corpus (#21678)"; 0.0.80); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-14: base bumped c40e652bc385 → 85f73f491d4c (2026-09-14, "Use cargo nextest via astral-dev-toolchain (#21676)"; 0.0.80); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-14: base bumped 85f73f491d4c → 85fe61435fe5 (2026-09-14, "Use cargo bloat via astral-dev-toolchain (#21681)"; 0.0.80); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-15: base bumped 85fe61435fe5 → 941b557a69d7 (2026-09-14, "Remove unused Serde derives from index locations (#21685)"; 0.0.80); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-15: base bumped 941b557a69d7 → ffc98b158bad (2026-09-14, "Forbid install-action via zizmor (#21682)"; 0.0.80); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-15: base bumped ffc98b158bad → 643950ce49e4 (2026-09-14, "Update Rust crate async-trait to v0.1.92 (#21657)"; 0.0.80); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-15: base bumped 643950ce49e4 → b8aff80900e7 (2026-09-15, "Update dependency astral-sh/uv to v0.12.13 (#21655)"; 0.0.81); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-15: base bumped b8aff80900e7 → 000a665b745a (2026-09-15, "Batch HTTP cache writes in blocking tasks (#21675)"; 0.0.81); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-15: base bumped 000a665b745a → fd89f638d15f (2026-09-15, "Add regression test for symlinks inside install directory (#21693)"; 0.0.81); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-15: base bumped fd89f638d15f → a064ab2f6761 (2026-09-15, "Add regression test for `--target .` (#21695)"; 0.0.81); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-15: base bumped a064ab2f6761 → 2c35bb31de15 (2026-09-15, "Use Packse scenarios to speed up tool tests (#21634)"; 0.0.81); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-15: base bumped 2c35bb31de15 → ad552557b635 (2026-09-15, "Preserve local path intent when merging dependency metadata (#20631)"; 0.0.82); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-15: base bumped ad552557b635 → 694dfd8155ec (2026-09-15, "Verify distribution hashes (#21562)"; 0.0.82); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-15: base bumped 694dfd8155ec → ac9201b10433 (2026-09-15, "Allow manually specifying build dependency hashes in configuration (#21467)"; 0.0.82); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-15: base bumped ac9201b10433 → 1f245a625114 (2026-09-15, "Cover packaged editable self-dependency name mismatches (#21714)"; 0.0.82); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-15: base bumped 1f245a625114 → b44bd4561d97 (2026-09-15, "Use a small native extension in system Python tests (#21713)"; 0.0.82); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-15: base bumped b44bd4561d97 → bf12c8e61b2d (2026-09-15, "Enable Renovate updates for the release workflow (#21722)"; 0.0.82); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-15: base bumped bf12c8e61b2d → 7752bc92b53e (2026-09-15, "Update astral-sh/setup-uv action to v10.1.0 (#21666)"; 0.0.82); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-15: base bumped 7752bc92b53e → a265915acf9e (2026-09-15, "Expand Debian and official Python system-test images (#21726)"; 0.0.82); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-15: base bumped a265915acf9e → 27e80c1498d9 (2026-09-15, "renovate: update uv hashes correctly with setup-uv (#21724)"; 0.0.82); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-15: base bumped 27e80c1498d9 → 9d8d76f4a13d (2026-09-15, "Use cargo-deny from toolchain (#21730)"; 0.0.82); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-16: base bumped 9d8d76f4a13d → c202b35405f1 (2026-09-15, "Encapsulate resolver metadata requests (#21735)"; 0.0.82); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-16: base bumped c202b35405f1 → 005d5cd9922b (2026-09-15, "Extract resolver requirement expansion (#21733)"; 0.0.82); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-16: base bumped 005d5cd9922b → f018faac8db2 (2026-09-16, "Update Python metadata for Pyodide 314.0.7, 0.29.5, 0.27.8 (#21741)"; 0.0.82); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-16: base bumped f018faac8db2 → f67344d87d2a (2026-09-16, "Skip `uv_build` fast path when pinned version differs (#21742)"; 0.0.82); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-16: base bumped f67344d87d2a → 3977dafee977 (2026-09-16, "Remove unused reqwest blocking feature from tests (#21749)"; 0.0.82); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-16: base bumped 3977dafee977 → bafbff9f631e (2026-09-16, "Respect artifact compatibility when initializing platform coverage (#21753)"; 0.0.82); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-16: base bumped bafbff9f631e → 108a3587b857 (2026-09-16, "Refactor HashDigest APIs (#21139)"; 0.0.82); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-16: base bumped 108a3587b857 → cc6880fd22c2 (2026-09-16, "Show captured publish test failures (#21757)"; 0.0.82); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-16: base bumped cc6880fd22c2 → 6b40d9e51d24 (2026-09-16, "Enforce non-staleness of cargo deny's `bans.build` list (#21756)"; 0.0.82); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-17: base bumped 6b40d9e51d24 → ec2783923893 (2026-09-17, "Add regression test for uv#21773 (#21775)"; 0.0.82); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-17: base bumped ec2783923893 → aa324fd49753 (2026-09-17, "Fix `uv check` without a workspace (#21777)"; 0.0.82); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-17: base bumped aa324fd49753 → 5e2ad786d5ae (2026-09-17, "Use astral-dev-toolchain for cargo-xwin (#21316)"; 0.0.82); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-17: base bumped 5e2ad786d5ae → 6dbe16aa4c1c (2026-09-17, "Reject unsupported Git URL schemes in lockfiles (#21779)"; 0.0.82); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-17: base bumped 6dbe16aa4c1c → 7cfd935f89de (2026-09-17, "Reject proxy URLs without a host (#21781)"; 0.0.82); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-17: base bumped 7cfd935f89de → 9ddc43085513 (2026-09-17, "Move shared thread initialization into uv-threads (#21746)"; 0.0.82); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-17: base bumped 9ddc43085513 → 5d64ede21e9e (2026-09-17, "Remove Hash API (#21786)"; 0.0.82); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-17: base bumped 5d64ede21e9e → 7bc36767ae3e (2026-09-17, "Avoid warning when both `native-tls` and `system-certs` are configured (#21806)"; 0.0.82); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-17: base bumped 7bc36767ae3e → 6dffe7e03898 (2026-09-17, "Ignore `UV_NATIVE_TLS` when `UV_SYSTEM_CERTS` is set (#21805)"; 0.0.82); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-17: base bumped 6dffe7e03898 → a2f820ad0ceb (2026-09-17, "Assign release pull requests to the workflow initiator (#21808)"; 0.0.82); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-17: base bumped a2f820ad0ceb → 761ff1379b3b (2026-09-17, "Bump version to 0.12.16 (#21809)"; 0.0.83); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-18: base bumped 761ff1379b3b → 6e093a90d45a (2026-09-17, "Avoid allocations for duplicate OnceMap registrations (#21810)"; 0.0.83); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-18: base bumped 6e093a90d45a → 46184d04b02e (2026-09-17, "Represent resolver package node kinds with an enum (#21802)"; 0.0.83); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-18: base bumped 46184d04b02e → d88bb84e7bd4 (2026-09-17, "Skip CI on `uv-security/main` (#21815)"; 0.0.83); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-18: base bumped d88bb84e7bd4 → a5a0b62c4912 (2026-09-18, "Remove guidance to add changelog introductions (#21818)"; 0.0.83); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-18: base bumped a5a0b62c4912 → b28593f9a5c6 (2026-09-18, "fix docs publication to astral-sh/docs (#21832)"; 0.0.84); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-20: base bumped b28593f9a5c6 → 7b090fba99bc (2026-09-19, "Honor dependency metadata when checking installed requirements (#21843)"; 0.0.84); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-20: base bumped 7b090fba99bc → 7f9bce21fbcb (2026-09-20, "Fix BSD and Haiku platform tag casing (#21853)"; 0.0.84); 4 bug(s) still reproduce. 55 tests pass.
- 2026-09-20: base bumped 7f9bce21fbcb → 25ea3bcfbe6e (2026-09-20, "Materialize fake-uv without checkout symlinks (#21855)"; 0.0.84); 4 bug(s) still reproduce. 55 tests pass.
