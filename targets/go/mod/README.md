# golang.org/x/mod

[golang.org/x/mod](https://github.com/golang/mod) (BSD-3-Clause), pinned at `d0a27b2` (v0.39.0+,
2026-08-24): the go command's module machinery as a library - `semver` (version grammar and precedence),
`module` (path and version rules, escaping, pseudo-versions), `modfile` (the go.mod parser, formatter and
editing API), `sumdb/tlog` (the Merkle tree of the checksum database and its tiles), `sumdb/note` (signed
notes) and `zip` (module zip files).

The patch adds `hegel/`, a test-only package inside the module: `hegel_test.go` (plumbing), one file per
area, `hegel_pins_test.go` (one plain test per recorded bug) and `known.go` (one switch per bug the
properties gate on). No external oracle: the models are the packages' own documentation - the version
grammar and Semantic Versioning 2.0.0 precedence, the path rules of `CheckPath`/`CheckImportPath`/
`CheckFilePath`, RFC 6962's tree hash written out, the signed-note format - and the round trips the
packages promise.

## What is tested

- `hegel_semver_test.go` - `semver.IsValid` accepts exactly the documented grammar and `Canonical`/`Major`/
  `MajorMinor`/`Prerelease`/`Build` return its parts; `Compare` is Semantic Versioning 2.0.0 precedence
  (invalid versions below and equal to each other), antisymmetric, transitive, zero exactly when the
  canonical forms agree; `Sort`/`ByVersion`/`Max`. `module.CheckImportPath`/`CheckPath`/`CheckFilePath`
  against their documented rules on generated paths (Windows names, short names, dots, dashes, Unicode,
  `/vN` and `gopkg.in` suffixes); `SplitPathVersion` as documented; `EscapePath`/`UnescapePath` and
  `EscapeVersion`/`UnescapeVersion` round trips; `Check` = valid path and version with matching majors
  (`MatchPathMajor`, `CheckPathMajor`); `CanonicalVersion`; `Version.String`; `module.Sort`;
  `PseudoVersion` in its five forms gives back its time, revision and base, passes `Check` and sorts
  between its base and the next tagged version; `ZeroPseudoVersion`; `MatchPrefixPatterns` against
  `path.Match` on every prefix.
- `hegel_modfile_test.go` - a random sequence of `Add*`/`Drop*`/`Set*` edits (require, exclude, replace,
  retract, tool, ignore, godebug, go, toolchain, `SortBlocks`, `Cleanup`) against a model of the content;
  after `Cleanup` the `File` struct, the text `Format` writes and `Parse` of that text all agree with the
  model, `Format` is a fixed point and `SortBlocks` keeps the content. Generated go.mod texts with
  formatting noise (blocks, comments, CRLF, quoting, `// indirect`, `// Deprecated:`, retract rationales):
  `Parse`/`Format`/`Parse` round trip, `ParseLax` agrees on what it keeps, `ModulePath`, unknown directives
  fail `Parse` but not `ParseLax`. `MustQuote`/`AutoQuote` round-trip through a directive.
- `hegel_tlog_test.go` - a log built with `StoredHashes`: `TreeHash` is the RFC 6962 tree hash of the
  records, `RecordHash`/`NodeHash` the leaf and node hashes, `StoredHashCount`/`StoredHashIndex`/
  `SplitStoredHashIndex` consistent; `ProveRecord`/`CheckRecord` and `ProveTree`/`CheckTree` verify and
  reject every tampering (record hash, index, tree hash, proof, truncation, other sizes), also through
  `TileHashReader`, which catches a corrupted tile; `TileForIndex`/`ReadTileData`/`HashFromTile`,
  `Tile.Path`/`ParseTilePath`, `NewTiles` covers the storage incrementally; `FormatTree`/`ParseTree`,
  `FormatRecord`/`ParseRecord` (with the rest returned), `Hash` text and JSON. `note.GenerateKey`/`Sign`/
  `Open` round trips with one to three signers, missing verifiers, tampered text and signatures,
  documented name and text restrictions, deterministic signatures.
- `hegel_zip_test.go` - generated file sets (vendor and submodule directories, symlinks and directories,
  case-fold collisions, `go.mod` in the wrong place, invalid names, Unicode): `CheckFiles` puts every file in
  exactly one list and its `Err` is nil exactly when nothing is invalid; `Create` succeeds exactly then
  (and rejects bad module versions); `CheckZip` and `Unzip` of the result give back exactly the valid files
  with their content; `Unzip` refuses a non-empty directory and a zip for another version.

## Known bugs (10, see bugs.toml)

`module`: `CheckImportPath`, `CheckPath` and `CheckFilePath` accept `a..b`, which the doc forbids (1);
`EscapeVersion` returns an internal error for a version with a non-ASCII letter although `CheckFilePath`
accepts it (2). `modfile`: `AddRetract` never records the retract in `f.Retract`, so `DropRetract` cannot
remove it (3); `SetRequire` panics with a nil pointer after a `DropRequire` or an earlier `SetRequire`
without `Cleanup` in between (4); `AddIgnore` writes an unquoted path, so `./x y` gives a go.mod `Parse`
rejects (8); `Cleanup` leaves dropped tool and ignore entries in `f.Tool`/`f.Ignore` (9); a version-less
`AddReplace` over a versioned one rewrites the line but keeps the version in `Old`, so the version-less
`DropReplace` misses it (10). `sumdb/note`: `GenerateKey` accepts names its own `NewSigner`/`NewVerifier`
reject (5); `Sign` accepts control characters and invalid UTF-8 and produces notes `Open` calls malformed
(6). `sumdb/tlog`: `FormatRecord` accepts a text starting with a blank line (7).

## Conventions followed, not recorded

`CheckImportPath` accepts `+` (the code says: for binary names like `c++`) and rejects a leading dash (the
doc states both only for module paths); the Windows short-name rule is applied to the element prefix before
the first dot, where a short name's `~1` sits (the doc says "suffix of the element"); `CheckFilePath` skips
the short-name and leading-dash rules (the code says so). Form (2) pseudo-versions sort above explicit
prereleases whose identifiers start with a numeric `0` followed by more (`-0.1`); the doc's examples are
`-rc1` and `-1`. `module.Sort` treats two invalid versions as equal regardless of a `/file` suffix.
`MatchPrefixPatterns` matches a glob against the target prefix with the same number of slashes, so a `/`
inside a character class is not matched across elements. `ParseLax` keeps only `module`, `go`, `require`,
`retract` and `ignore`. `AddReplace` with an empty old version supersedes every versioned replacement of the
path (the code's comment: "delete other replacements for same"); `Retract`s are not de-duplicated.
`FormatRecord` accepts U+007F (the doc excludes only characters below U+0020); `Sign`/`Open` accept blank
lines inside the text. `zip.CheckFiles` reports an irregular file with an invalid name as invalid rather
than omitted; `CheckZip` lists paths with the `module@version/` prefix; `Unzip` writes the files straight
into the target directory.
