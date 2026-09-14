# bbolt

[etcd-io/bbolt](https://github.com/etcd-io/bbolt) is etcd's fork of Bolt, the embedded B+tree
key/value store (single file, ACID transactions, nested buckets, cursors, `MoveBucket` since
1.4). Pinned at b6b954a (v1.5.0+, 2026-09-14), MIT, no AI policy in the contributing docs.
The run command is `go test -run TestHegel` only: bbolt's own root-package tests take minutes.

## Oracle

An in-memory model of the key space — a tree of buckets, each with a map of values, a map of
sub-buckets and a sequence counter — driven through the same random transactions as the
database. The observers are the cursor (First/Next, Last/Prev, Seek), `Get`, `ForEach`,
`Bucket`, `Sequence`, `Stats` (KeyN, BucketN, in read-only transactions), `tx.Check()` after
every commit, and the dumps of `Compact` and `CopyFile` outputs.

## Properties

- `TestHegelDatabaseFollowsTheModel` — 1–8 transactions of 1–6 operations each on a fresh
  file (`NoSync`): `Put`/`Delete` (with the incompatible-value errors on bucket entries),
  `CreateBucket`/`CreateBucketIfNotExists`/`DeleteBucket` at any depth (exists / not found /
  incompatible errors), `SetSequence`/`NextSequence`, `MoveBucket` between any two buckets
  (legal cases only — see the bugs), `Cursor.Delete` while iterating, blank-name and
  oversized-key errors, mid-transaction reads; 15 % of transactions roll back by returning an
  error, 15 % of commits are followed by Close/Open. After every commit `tx.Check()` is clean
  and a read-only transaction sees exactly the model; read-only transactions refuse writes.
  Keys: 1–3 bytes from a small alphabet (collisions), single arbitrary bytes, 100–2000-byte
  runs; values: 0–12 arbitrary bytes, empty, 1–20 KB runs.
- `TestHegelCompactAndCopyPreserveContents` — after the same kind of run, `bolt.Compact`
  (random `txMaxSize`) and `tx.CopyFile` give files whose dump equals the model's, with a
  clean `tx.Check()`.

Both pass at 1000 cases × 3 (about 10 s each). Two pinned expected failures.

## Bugs (2)

| id | title | severity |
|----|-------|----------|
| bbolt/1 | `MoveBucket` silently drops the changes made to the moved bucket earlier in the same transaction | high |
| bbolt/2 | `MoveBucket` into the moved bucket itself or one of its descendants succeeds and deletes the bucket; `tx.Check()` then reports unreachable pages | high |

Both came from reading `Bucket.MoveBucket` (v1.4's new API) and were confirmed with a probe
before the properties were written; the general property keeps to moves of buckets untouched
in the current transaction and to destinations outside the moved subtree.

## Not bugs

- `Get` returns nil for a missing key and for a bucket entry, and a non-nil empty slice for an
  empty value; `Put(k, nil)` stores an empty value (documented).
- `Bucket.Stats()` inside a writable transaction reflects the pages of the last commit, not
  the transaction's own changes (`KeyN 0` right after the first puts); the property reads
  stats in read-only transactions only.
- `Cursor.Delete` followed by `Next`/`Prev` visits every element (the old Bolt skip is fixed).
- `Seek` past the last key returns nil; `Next` after the last / `Prev` before the first
  return nil and then step back onto the last / first element.
- Each `Update` that returns an error is rolled back completely, including bucket creation
  and sequences.

## Conventions

External test package with a dot-free import (`bolt`); `HEGEL_TEST_CASES` via `hegelOpts`;
`property()` turns panics into test-case failures; every test case opens its own file in
`t.TempDir()` and removes it. Helper names avoid those of bbolt's own tests (`dumpBucket`,
`pickBucket`, `run`).
