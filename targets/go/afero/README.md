# spf13/afero

[afero](https://github.com/spf13/afero) (Apache-2.0), pinned at `768f1fb` (v1.15.0+, 2026-06-09): a file
system abstraction for Go with an OS-backed implementation (`OsFs`), an in-memory one (`MemMapFs`),
wrappers that restrict (`BasePathFs`, `ReadOnlyFs`, `RegexpFs`) or layer (`CopyOnWriteFs`,
`CacheOnReadFs`) file systems, an `io/fs` adapter (`IOFS`) and the usual helpers (`ReadDir`, `ReadFile`,
`WriteFile`, `Walk`, `Glob`, `TempFile`, ...).

The patch adds `hegel/`, a test-only package inside the module: `hegel_test.go` (plumbing), one file per
area, `hegel_pins_test.go` (one plain test per recorded bug) and `known.go` (one switch per bug the
properties gate on). The oracle for `MemMapFs` and the helpers is `OsFs` itself (restricted to a fresh
temporary directory through `BasePathFs`) together with `os` and `path/filepath`; the wrappers are checked
against small models of their documented semantics and the adapter against `testing/fstest`. The process
umask is cleared so that both sides keep the modes they are given.

## What is tested

- `hegel_memmap_test.go` - the same random sequence of `Mkdir`, `MkdirAll`, `Create`, `Open`, `OpenFile`
  (every access mode with `O_CREATE`, `O_EXCL`, `O_TRUNC`, `O_APPEND`), `Remove`, `RemoveAll`, `Rename`,
  `Chmod`, `Chtimes`, `Stat`, `ReadDir` and `ReadFile` on a `MemMapFs` and on an `OsFs` in a temporary
  directory, with a short random sequence of `Write`, `WriteString`, `Read`, `ReadAt`, `WriteAt`, `Seek`,
  `Truncate`, `Stat`, `Sync`, `Readdir`/`Readdirnames` pages and `Close` on every opened handle. Every
  result (error class, counts, data, positions, `FileInfo`) must agree and, after every step, the tree
  reachable from the root (kinds, modes, sizes, contents) and `Stat` of every path the generator can name.
- `hegel_util_test.go` - on a random tree present on both file systems: `ReadDir` (sorted), `ReadFile`,
  `ReadAll`, `Exists`/`DirExists`/`IsDir`/`IsEmpty`, `Walk` and `WalkDir` (visited paths, `SkipDir` and
  `SkipAll` at a random point, against `filepath.Walk`), `Glob` against `filepath.Glob` on generated
  patterns, `FileContainsBytes`/`FileContainsAnyBytes` against `bytes.Contains`, `TempFile`/`TempDir`
  (location, name, mode, separator in the prefix), `WriteReader`/`SafeWriteReader`/`WriteFile`,
  `UnicodeSanitize` and `NeuterAccents` against their documented rules.
- `hegel_wrappers_test.go` - `ReadOnlyFs`: every mutating call returns `EPERM` and leaves the source alone,
  every reading call answers like the source. `CopyOnWriteFs` over two `OsFs` directories against a model
  (base fixed, layer map, view = layer over base): writes land in the layer, the base never changes,
  removing a layer copy exposes the base file, base-only entries cannot be renamed, merged directory
  listings. `CacheOnReadFs` (unlimited cache time) over two `OsFs` directories against a plain `OsFs`
  receiving the same calls: the base is that tree and the cache answers like it. `RegexpFs`: directories
  and matching files behave as on the source, hidden names give `ENOENT` and touch nothing, listings are
  filtered. `BasePathFs`: escaping paths (`..`) are not-exist for every call and nothing outside the base is
  touched, `RealPath`, `File.Name`, `FullBaseFsPath`. `IOFS`: `fstest.TestFS` on a random tree, bare and
  behind a `BasePathFs`, plus `ReadFile`/`ReadDir` and the leading-slash check.

## Known bugs (38, see bugs.toml)

`MemMapFs` (1-18, 29-31): `Mkdir` creates parents (1) and so do `Create`, `OpenFile(O_CREATE)` and `Rename`
(2); `Remove` deletes a non-empty directory, its children stay reachable and removing one of them panics
(3); `MkdirAll` over a file returns nil (4); creating below a file turns the file into a directory (5);
`Create` over a directory replaces it (6); `Rename` overwrites a destination of another kind or a non-empty
directory (7) and into its own subtree detaches the tree (8); `Seek` to a negative position then `Read`
panics (9), past the end reads give `ErrUnexpectedEOF` (10); `O_APPEND` seeks once at open (11); access
modes are not enforced (12); `OpenFile(O_RDONLY)` needs write permission (13); directory handles act as
files (14); `Create` of an existing file resets its mode and detaches open handles (15) and ignores a
read-only mode (30); `RemoveAll("")` wipes the file system (16), `Mkdir("")` adds an entry named `""` (17);
`Seek` accepts any whence (18); `Rename(x, x)` of a missing file is nil (29); an empty `WriteAt` past the
end grows the file (31). Helpers: `FileContainsBytes` matches its buffer's zero padding (19), `Walk` returns
`SkipDir`/`SkipAll` (27), `Glob` ignores backslash escapes (28). Unions: `UnionFile.Close` returns `BADFD`
so `WriteFile` through a `CacheOnReadFs` fails after writing (20); `CopyOnWriteFs` `Remove`/`RemoveAll` of
a base-only file are not `EPERM` (21), `Mkdir`/`MkdirAll` only check the base (22), `Rename` into a
base-only directory fails (37); `CacheOnReadFs.Remove` of an uncached file removes it but reports not-exist
(23), `OpenFile(O_WRONLY...)` of a file not in the layer fails after `O_TRUNC` emptied the base file (36),
`Create`/`Rename` into a directory not in the layer fail (38); copying a directory into the layer fails
(`Chmod`/`Chtimes`/`Rename` of base-only directories, 32), the layer copy of a file gets mode 0666 (33) and a
recreated parent directory the child's mode (34). `RegexpFs`: `Rename` of a directory is a no-op (24),
`OpenFile(O_CREATE)` cannot create (25), `Readdir(n)` returns empty pages (26), `RemoveAll` of a missing
path errors (35).

## Conventions followed, not recorded

Go's `os.Rename` refuses any existing directory as destination (even an empty one, or the directory
itself) with `EEXIST`, while `MemMapFs` replaces an empty one and treats equal names as a no-op: renames onto
a directory are not compared. `os.RemoveAll` below a regular file returns `ENOTDIR` where `MemMapFs` returns
nil. `O_TRUNC` without a write flag (Linux truncates) and `O_EXCL` without `O_CREATE` (undefined; `MemMapFs`
reports exists) are not generated. `MemMapFs` reports `ENOENT` where the OS reports `ENOTDIR` for a path
through a file, and directories have size 42. `ReadOnlyFs.MkdirAll` of an existing directory returns nil
(fixed upstream in #356, the pinned commit). `IsEmpty` of a missing path is an error. `Stat` of the root
has an empty name on `MemMapFs`. `CopyOnWriteFs.Create` over a base directory fails with `EIO` rather than
`EISDIR`. With an `OsFs` layer the modes the layer bugs (33, 34) produce are additionally reduced by the
umask.
