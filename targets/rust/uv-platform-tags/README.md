# uv-platform-tags

[uv-platform-tags](https://github.com/astral-sh/uv/tree/main/crates/uv-platform-tags) is the
crate of [uv](https://github.com/astral-sh/uv) that types wheel tags — `LanguageTag`, `AbiTag`,
`PlatformTag` (PEP 425, PEP 600 manylinux, PEP 656 musllinux, the macOS/iOS/Android/BSD
conventions) — and computes the ordered list of tags an interpreter on a platform accepts
(`Tags::from_env`), with `is_compatible`/`compatibility` answering for a wheel's tag sets. Written
in the zoo at 0.0.80 (uv HEAD `c0df400`, 2026-09-12); tests in
`crates/uv-platform-tags/tests/hegel.rs`, run in that crate's directory.

## The oracle

One persistent Python child (the first of `python3`, `/usr/bin/python3` that imports it; `[run]
setup` pip-installs it if neither does) running PyPA's **`packaging.tags`** (26.3):
`parse_tag` for the grammar; `mac_platforms`, `ios_platforms`, `android_platforms` for the
platform lists of those systems; `cpython_tags`/`generic_tags` + `compatible_tags` for the ordered
tag list of an interpreter over a given platform list (the crate's own, so the platform order is
factored out); `_normalize_string` for the BSD tags. Linux platform lists cannot come from
`packaging` (it reads the running system's glibc/musl), so they are checked against a model of
PEP 600/656; the compatibility queries are checked against the crate's own `Display` of the list.

## Properties

- **Tag lists** (`tag_lists_match_packaging`): for a CPython 3.3–3.15 (free-threaded, debug,
  pymalloc variants) on any supported platform — manylinux 2.5–2.42 × 12 architectures,
  musllinux, Windows, macOS 10.4–16 (x86_64, arm64), FreeBSD/NetBSD/OpenBSD/DragonFly/Haiku,
  Android 16–36, iOS 12–18 (device/simulator), Pyodide/Emscripten — the crate's list is exactly
  `packaging`'s, in order; the "best" tag accessors give the first line.
- **Platform lists** (`platform_tag_lists_match_the_reference`): the platform tags of every
  `Os` are the reference's — `mac_platforms` (read through `packaging` 26.3's `fat3` spelling,
  below), `ios_platforms`, `android_platforms`, the PEP 600 model (glibc minors down to the
  architecture's baseline with the legacy aliases after 2.17/2.12/2.5, `manylinux_compatible =
  false` dropping them), the PEP 656 model, the single Windows/BSD tags — and each re-parses to
  the same text.
- **Tag texts** (`tag_texts_round_trip`): structurally generated `LanguageTag`s, canonical ABI
  and platform texts over every variant: `Display` re-parses to an equal value, parse-then-Display
  is the identity, `parse_tag` accepts the triple.
- **Compatibility** (`compatibility_follows_the_tag_list`): for random triples in and out of the
  list, `compatibility_tag` is `Compatible` with priorities following the list order or
  `Incompatible` with the first mismatching component (the free-threaded ABI gate first, then
  Python, ABI, platform); `is_compatible` and `compatibility` over tag sets are the best over
  their members.

The general generators stay away from the pinned shapes: no illumos platforms (bug 2), GraalPy
implementation versions with a single-digit major (bug 3), CPython only in the tag-list
property (bug 4); the number-spelling bug (1) is only reachable through texts no generator
produces.

## Bugs (4, all zoo-original, found 2026-09-14)

- **uv-platform-tags/1** (low) — the typed parsers read numbers with `str::parse`, so `pp3+9`,
  `cp3013`, `manylinux_02_17_x86_64`, `macosx_+11_0_arm64` are accepted and `Display` rewrites
  them; a tag is a string for PEP 425 and `packaging`. The root of uv-distribution-filename/1
  and /3.
- **uv-platform-tags/2** (medium) — the Solaris platform tag carries `_64bit` twice
  (`solaris_2_11_i86pc_64bit_64bit`): appended when the tag is built and again by `Display`.
- **uv-platform-tags/3** (high) — GraalPy ABI tags run the implementation's major and minor
  together (`graalpy241_311_native`) and the parser takes the first digit as the major, so the
  interpreter's own tag for GraalPy 24.1 re-parses as 2.41 and every native GraalPy wheel is
  incompatible; the crate's unit test asserts the wrong reading.
- **uv-platform-tags/4** (medium) — PyPy, GraalPy and Pyston get no `<interpreter>-none-<platform>`
  and `<interpreter>-none-any` tags (`packaging` gives them to every interpreter), so
  `pp310-none-any` wheels are incompatible with PyPy 3.10.

## Not bugs

- `packaging` 26.3 (and its `main`) spells the macOS `fat32` binary format `fat3` in
  `_mac_binary_formats` (24.0 said `fat32`, as does the crate and the macOS convention): read
  through as `fat32` in the comparison — a reference defect, not the crate's.
- On Linux the crate lists `linux_{arch}` after the manylinux/musllinux tags where `packaging`
  lists it first: a preference between compatible wheels, not a compatibility matter; the PEP 600
  model puts it last.
- Case: `packaging.tags.Tag` lowercases every component, so its tags compare
  case-insensitively (`CP33-NONE-ANY` is `cp33-none-any`); the crate's typed tags are lowercase by
  construction except a BSD release string, whose case it keeps (FreeBSD's it lowercases:
  `14_0_release`). What a given BSD's Python reports is the platform's business — the lists are
  compared lowercased.
- Interpreters below 3.3 are left out: `packaging` adds the `u` (UCS-4) ABI flag from the build
  configuration there.
- The illumos release spelling this crate expects (`5_11`, SunOS form, mapped to Solaris 2.11)
  is not settled by the crate or uv's interpreter script (`sysconfig` reports `solaris-2.11-…`
  and the script only knows `illumos`); only the doubled suffix is recorded.

## History

- 2026-09-14: created at c0df400 (0.0.80); 4 bugs.
- 2026-09-14: base bumped c0df400a4cf4 → 83d556d712c7 (2026-09-14, "Scope required-environment checks to the current fork (#21672)"; 0.0.80); 4 bug(s) still reproduce. 58 tests pass.
- 2026-09-14: base bumped 83d556d712c7 → c40e652bc385 (2026-09-14, "Exclude backports-zstd from the Sentry PGO corpus (#21678)"; 0.0.80); 4 bug(s) still reproduce. 58 tests pass.
- 2026-09-14: base bumped c40e652bc385 → 85f73f491d4c (2026-09-14, "Use cargo nextest via astral-dev-toolchain (#21676)"; 0.0.80); 4 bug(s) still reproduce. 58 tests pass.
- 2026-09-14: base bumped 85f73f491d4c → 85fe61435fe5 (2026-09-14, "Use cargo bloat via astral-dev-toolchain (#21681)"; 0.0.80); 4 bug(s) still reproduce. 58 tests pass.
- 2026-09-15: base bumped 85fe61435fe5 → 941b557a69d7 (2026-09-14, "Remove unused Serde derives from index locations (#21685)"; 0.0.80); 4 bug(s) still reproduce. 58 tests pass.
- 2026-09-15: base bumped 941b557a69d7 → ffc98b158bad (2026-09-14, "Forbid install-action via zizmor (#21682)"; 0.0.80); 4 bug(s) still reproduce. 58 tests pass.
- 2026-09-15: base bumped ffc98b158bad → 6f7795bb4f6e (2026-09-14, "Update Rust crate axoupdater to v0.10.2 (#21658)"; 0.0.80); 4 bug(s) still reproduce. 58 tests pass.
- 2026-09-15: base bumped 6f7795bb4f6e → b8aff80900e7 (2026-09-15, "Update dependency astral-sh/uv to v0.12.13 (#21655)"; 0.0.81); 4 bug(s) still reproduce. 58 tests pass.
- 2026-09-15: base bumped b8aff80900e7 → 000a665b745a (2026-09-15, "Batch HTTP cache writes in blocking tasks (#21675)"; 0.0.81); 4 bug(s) still reproduce. 58 tests pass.
- 2026-09-15: base bumped 000a665b745a → fd89f638d15f (2026-09-15, "Add regression test for symlinks inside install directory (#21693)"; 0.0.81); 4 bug(s) still reproduce. 58 tests pass.
- 2026-09-15: base bumped fd89f638d15f → a064ab2f6761 (2026-09-15, "Add regression test for `--target .` (#21695)"; 0.0.81); 4 bug(s) still reproduce. 58 tests pass.
- 2026-09-15: base bumped a064ab2f6761 → 2c35bb31de15 (2026-09-15, "Use Packse scenarios to speed up tool tests (#21634)"; 0.0.81); 4 bug(s) still reproduce. 58 tests pass.
- 2026-09-15: base bumped 2c35bb31de15 → ad552557b635 (2026-09-15, "Preserve local path intent when merging dependency metadata (#20631)"; 0.0.82); 4 bug(s) still reproduce. 58 tests pass.
- 2026-09-15: base bumped ad552557b635 → 694dfd8155ec (2026-09-15, "Verify distribution hashes (#21562)"; 0.0.82); 4 bug(s) still reproduce. 58 tests pass.
- 2026-09-15: base bumped 694dfd8155ec → ac9201b10433 (2026-09-15, "Allow manually specifying build dependency hashes in configuration (#21467)"; 0.0.82); 4 bug(s) still reproduce. 58 tests pass.
- 2026-09-15: base bumped ac9201b10433 → 1f245a625114 (2026-09-15, "Cover packaged editable self-dependency name mismatches (#21714)"; 0.0.82); 4 bug(s) still reproduce. 58 tests pass.
- 2026-09-15: base bumped 1f245a625114 → b44bd4561d97 (2026-09-15, "Use a small native extension in system Python tests (#21713)"; 0.0.82); 4 bug(s) still reproduce. 58 tests pass.
- 2026-09-15: base bumped b44bd4561d97 → bf12c8e61b2d (2026-09-15, "Enable Renovate updates for the release workflow (#21722)"; 0.0.82); 4 bug(s) still reproduce. 58 tests pass.
- 2026-09-15: base bumped bf12c8e61b2d → 7752bc92b53e (2026-09-15, "Update astral-sh/setup-uv action to v10.1.0 (#21666)"; 0.0.82); 4 bug(s) still reproduce. 58 tests pass.
- 2026-09-15: base bumped 7752bc92b53e → a265915acf9e (2026-09-15, "Expand Debian and official Python system-test images (#21726)"; 0.0.82); 4 bug(s) still reproduce. 58 tests pass.
- 2026-09-15: base bumped a265915acf9e → 27e80c1498d9 (2026-09-15, "renovate: update uv hashes correctly with setup-uv (#21724)"; 0.0.82); 4 bug(s) still reproduce. 58 tests pass.
- 2026-09-15: base bumped 27e80c1498d9 → 9d8d76f4a13d (2026-09-15, "Use cargo-deny from toolchain (#21730)"; 0.0.82); 4 bug(s) still reproduce. 58 tests pass.
- 2026-09-16: base bumped 9d8d76f4a13d → c202b35405f1 (2026-09-15, "Encapsulate resolver metadata requests (#21735)"; 0.0.82); 4 bug(s) still reproduce. 58 tests pass.
- 2026-09-16: base bumped c202b35405f1 → 005d5cd9922b (2026-09-15, "Extract resolver requirement expansion (#21733)"; 0.0.82); 4 bug(s) still reproduce. 58 tests pass.
- 2026-09-16: base bumped 005d5cd9922b → f018faac8db2 (2026-09-16, "Update Python metadata for Pyodide 314.0.7, 0.29.5, 0.27.8 (#21741)"; 0.0.82); 4 bug(s) still reproduce. 58 tests pass.
- 2026-09-16: base bumped f018faac8db2 → f67344d87d2a (2026-09-16, "Skip `uv_build` fast path when pinned version differs (#21742)"; 0.0.82); 4 bug(s) still reproduce. 58 tests pass.
- 2026-09-16: base bumped f67344d87d2a → 3977dafee977 (2026-09-16, "Remove unused reqwest blocking feature from tests (#21749)"; 0.0.82); 4 bug(s) still reproduce. 58 tests pass.
- 2026-09-16: base bumped 3977dafee977 → bafbff9f631e (2026-09-16, "Respect artifact compatibility when initializing platform coverage (#21753)"; 0.0.82); 4 bug(s) still reproduce. 58 tests pass.
- 2026-09-16: base bumped bafbff9f631e → 108a3587b857 (2026-09-16, "Refactor HashDigest APIs (#21139)"; 0.0.82); 4 bug(s) still reproduce. 58 tests pass.
- 2026-09-16: base bumped 108a3587b857 → cc6880fd22c2 (2026-09-16, "Show captured publish test failures (#21757)"; 0.0.82); 4 bug(s) still reproduce. 58 tests pass.
- 2026-09-16: base bumped cc6880fd22c2 → 6b40d9e51d24 (2026-09-16, "Enforce non-staleness of cargo deny's `bans.build` list (#21756)"; 0.0.82); 4 bug(s) still reproduce. 58 tests pass.
- 2026-09-17: base bumped 6b40d9e51d24 → ec2783923893 (2026-09-17, "Add regression test for uv#21773 (#21775)"; 0.0.82); 4 bug(s) still reproduce. 58 tests pass.
- 2026-09-17: base bumped ec2783923893 → aa324fd49753 (2026-09-17, "Fix `uv check` without a workspace (#21777)"; 0.0.82); 4 bug(s) still reproduce. 58 tests pass.
- 2026-09-17: base bumped aa324fd49753 → 5e2ad786d5ae (2026-09-17, "Use astral-dev-toolchain for cargo-xwin (#21316)"; 0.0.82); 4 bug(s) still reproduce. 58 tests pass.
- 2026-09-17: base bumped 5e2ad786d5ae → 6dbe16aa4c1c (2026-09-17, "Reject unsupported Git URL schemes in lockfiles (#21779)"; 0.0.82); 4 bug(s) still reproduce. 58 tests pass.
- 2026-09-17: base bumped 6dbe16aa4c1c → 7cfd935f89de (2026-09-17, "Reject proxy URLs without a host (#21781)"; 0.0.82); 4 bug(s) still reproduce. 58 tests pass.
- 2026-09-17: base bumped 7cfd935f89de → ef1e0689b461 (2026-09-17, "Make Git stamping opt-in for development builds (#21750)"; 0.0.82); 4 bug(s) still reproduce. 58 tests pass.
- 2026-09-17: base bumped ef1e0689b461 → 5d64ede21e9e (2026-09-17, "Remove Hash API (#21786)"; 0.0.82); 4 bug(s) still reproduce. 58 tests pass.
- 2026-09-17: base bumped 5d64ede21e9e → 7bc36767ae3e (2026-09-17, "Avoid warning when both `native-tls` and `system-certs` are configured (#21806)"; 0.0.82); 4 bug(s) still reproduce. 58 tests pass.
- 2026-09-17: base bumped 7bc36767ae3e → 6dffe7e03898 (2026-09-17, "Ignore `UV_NATIVE_TLS` when `UV_SYSTEM_CERTS` is set (#21805)"; 0.0.82); 4 bug(s) still reproduce. 58 tests pass.
- 2026-09-17: base bumped 6dffe7e03898 → a2f820ad0ceb (2026-09-17, "Assign release pull requests to the workflow initiator (#21808)"; 0.0.82); 4 bug(s) still reproduce. 58 tests pass.
- 2026-09-17: base bumped a2f820ad0ceb → 761ff1379b3b (2026-09-17, "Bump version to 0.12.16 (#21809)"; 0.0.83); 4 bug(s) still reproduce. 58 tests pass.
- 2026-09-18: base bumped 761ff1379b3b → 6e093a90d45a (2026-09-17, "Avoid allocations for duplicate OnceMap registrations (#21810)"; 0.0.83); 4 bug(s) still reproduce. 58 tests pass.
