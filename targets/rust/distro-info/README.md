# distro-info

[distro-info-rs](https://github.com/OddBloke/distro-info-rs) is the Rust port of Debian's
distro-info: the `distro-info` library (`DistroInfo` trait, `DebianDistroInfo`,
`UbuntuDistroInfo`, `DistroRelease`, `Milestone`) over the `distro-info-data` CSV files, and
the `distro-info-binaries` crate's `debian-distro-info`/`ubuntu-distro-info` re-implementations
of the C tools. The zoo tests both in `binaries/tests/hegel.rs` (the workspace is run with
`cargo test --workspace`). Written in the zoo at 0.4.0 (commit `cbd44a3`, 2023-07-13; the
crate's HEAD, ahead of the crates.io release, which lacks `Milestone` and the binaries).

## The oracle

- **The C `debian-distro-info` and `ubuntu-distro-info`** (package `distro-info`, 1.7 here),
  which read the same `/usr/share/distro-info/*.csv` files (`distro-info-data`). Upstream's
  shell test suite for those tools is what the crate vendors as its acceptance tests
  (`tests/distro-info`), so the C behaviour is the crate's own reference. `[run] setup`
  requires both tools and both data files; CI installs `distro-info distro-info-data`.
- Where the C rule matters it was read from `distro-info-util.c`: a milestone date is
  exclusive (`eol = date >= eol`, with `eol-server` for Ubuntu; `filter_supported = created &&
  !eol`), `--lts` is the latest *released* not-EOL LTS, `--testing` is the latest created,
  unreleased release, and every "days until" of a missing milestone prints `(unknown)`.

## Properties

- **The binaries** (`binaries_agree_with_the_c_tools`): a random `--date` (1997 to mid-2028,
  never a date that appears in the data), any selector of the distro (`--all`, `--devel`,
  `--stable`, `--oldstable`, `--supported`, `--unsupported`, `--lts`, `--elts`, `--latest`,
  `--series=X`, `--alias=X` with real, capitalised and unknown names, short forms), any output
  flag (`-c`/`-f`/`-r` and long forms), optionally `--days=created`/`--days=eol`/`-yeol`, in
  either order: the Rust binary and the C tool give the same exit status and stdout. Skipped
  (pinned) shapes: empty lists, Debian's `--testing`/`--alias`, Ubuntu's `--lts`, `--days` of
  milestones a release may lack, dates on a milestone day.
- **The library** (`debian_selectors_agree_with_the_c_tool`, `ubuntu_selectors_agree_with_the_c_tool`):
  at a random date, `supported`/`unsupported` (Debian: `Milestone::Eol`; Ubuntu:
  `ubuntu_supported`/`ubuntu_unsupported`), `debian_devel`/`ubuntu_devel`, `stable`, `latest`,
  both `oldstable`s, `testing` (while the data has a single unreleased testing), `unstable`,
  `experimental`, and the C `--lts` rule equal the C tool's `--date` answers; `all_at` and
  `released` equal the rows created/released by the date.
- **Milestones** (`milestones_agree_with_the_c_tool`): for a random release and milestone,
  `milestone_date` equals the date the C tool's `--series=X --days=<milestone>` counts to
  (`None` for `(unknown)`), `supported_at` follows `created <= date < milestone` (or `Eol`
  missing), `created_at`/`released_at` follow the CSV.
- **CSV parsing** (`csv_files_parse_like_their_fields`): generated files with the three name
  columns and 0–7 date columns in random order, rows cut after their last date (the shape of
  the real files, read with a `flexible` reader): every getter returns the field written,
  `ubuntu_is_lts` follows "LTS" in the version.

## Bugs (7, all zoo-original, found 2026-09-14)

- **distro-info/1** (high) — `debian-distro-info --testing` (and `--alias`) cannot find a
  testing without a release date — the current testing most of the time — and reports the data
  as outdated (the binary uses `ubuntu_devel`, not the library's `testing`).
- **distro-info/2** (medium) — `ubuntu-distro-info --lts` names the LTS still in development
  for the six months between its creation and release (trusty on 2013-10-18; C: precise).
- **distro-info/3** (medium) — `--days` of a missing milestone aborts the output with an error
  (`release`/`created`) or prints nothing (`eol-lts`/`eol-elts`/`eol-esm`); C prints
  `(unknown)`. `--days=eol-esm` is missing altogether.
- **distro-info/4** (low) — a release is still supported on its EOL day (`date <= eol`); the C
  tools treat milestone dates as exclusive, so every EOL day differs.
- **distro-info/5** (low) — an empty list (`--lts` between Debian LTS periods) exits 1 with
  "Distribution data outdated"; C prints nothing and exits 0.
- **distro-info/6** (low) — `DebianDistroInfo::testing` uses `date > created`: no testing on
  the day it is created (2025-08-09).
- **distro-info/7** (medium) — an empty date field in a CSV row fails the whole parse
  ("premature end of input"); the data files only avoid it by cutting rows short.

## Not bugs

- Beyond the data's horizon (after trixie's EOL, 2028-08-09, or Ubuntu's 2031-05-29) nothing is
  supported; the C tool then calls `--stable` "outdated" while the library's inherent
  `DebianDistroInfo::stable`/`oldstable` still return the last released release (the CLI uses
  `latest`, which agrees with C). Likewise the fictional coexistence of two unreleased Debian
  releases (forky without a release date, duke created 2027-08-01): C picks the latest created
  as testing, the library the first. Neither happens with real data at real dates; the general
  properties stop at mid-2028 and compare `testing` only while there is one unreleased release.
- The C tool's `--testing` before Debian's first release (1993–1996) answers `experimental`;
  out of the tested range.
- Both tools default `--date` to today (C in local time, Rust in UTC); the properties always
  pass `--date`. stderr is not compared (the vendored C suite ignores it too).

## History

- 2026-09-14: created at cbd44a3 (0.4.0); 7 bugs.
