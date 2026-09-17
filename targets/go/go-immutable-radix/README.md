# go-immutable-radix

[hashicorp/go-immutable-radix](https://github.com/hashicorp/go-immutable-radix) v2 is the
immutable, generic radix tree under Consul's and Nomad's `go-memdb`: `Tree[T]` with
`Insert`/`Delete`/`DeletePrefix` returning new trees, `Txn` batching writes with a
copy-on-write cache and `Clone`, `Node` reads (`Get`, `GetWatch`, `LongestPrefix`,
`Minimum`/`Maximum`, `Walk`/`WalkBackwards`/`WalkPrefix`/`WalkPath`), forward, reverse and
path iterators with `SeekPrefix`/`SeekLowerBound`/`SeekReverseLowerBound`, and mutation
tracking (`TrackMutate`, `GetWatch`, `SeekPrefixWatch`, `Notify`) through channels closed on
commit. About 1 600 lines plus 2 300 of tests (two of them `testing/quick`), MPL-2.0, pinned at
`581942a` (master 2026-07-27; v2.1.0 is the last tag). README, CHANGELOG and LICENSE are the
project documents and say nothing about AI-written code.

## Build

`go test -count=1 -race -run TestHegel -v .` in the module root. The patch adds `hegel_test.go`
(the model and the properties) and `hegel_pins_test.go` (one plain test per bug) and requires
`hegel.dev/go/hegel v0.6.33` in go.mod (the `go` directive moves from 1.18 to 1.26). The race
detector is part of the check: committed trees are documented safe to read concurrently.

## Oracles

- **A map model**: keys of up to five bytes from a small alphabet (`a`, `b`, `/`, with a few
  `\x00`, `\xff`, `z`) so prefixes share, split and merge often; the model is a `map[string]int`
  sorted on demand, and every read is derived from it — `Get`/`GetWatch`, `Len`,
  `Minimum`/`Maximum`, forward and reverse iteration, `LongestPrefix` (the longest key that is a
  prefix of the probe), `WalkPath`/`PathIterator` (the keys that are prefixes of the probe,
  shortest first), `WalkPrefix`/`SeekPrefix` (the keys under a prefix), `SeekLowerBound` (keys
  >= k ascending), `SeekReverseLowerBound` (keys <= k descending). Operations go through the
  tree's one-shot methods and through transactions (`Commit` and `CommitOnly`), with `Txn.Get`
  and `Txn.Root()` read mid-transaction; `DeletePrefix` reports true when a key was deleted or
  the prefix is empty (the root node always matches).
- **Immutability**: every committed version is kept with its model and re-checked after later
  transactions, while a goroutine reads an older version during each transaction.
- **Clones**: `Txn.Clone` carries the uncommitted writes; the source transaction, the clone and
  clones of clones then diverge, each committing to its own model, the source tree untouched.
- **Mutation tracking** (from `TrackMutate`'s and `GetWatch`'s documentation and the package's
  own tests): a `GetWatch` or `SeekPrefixWatch` channel taken on the old tree must be closed
  after the commit when that lookup's answer changed; a leaf's channel stays open when no
  operation touched its key; the new tree's channels are open; `Notify` after `CommitOnly` is
  idempotent. A tenth of the cases insert 8 300 keys to overflow the tracking limit into the
  slow tree-comparison path.
- **Iterator contracts**: after a seek, `Next`/`Previous` yield exactly the model's sequence and
  keep returning false once exhausted; walks stop as soon as the function returns true, having
  visited exactly the first entries of the full order.

## Bugs (4; details in bugs.toml)

| id | summary | severity |
|----|---------|----------|
| go-immutable-radix/1 | a second seek on an iterator panics (nil node after a lower-bound seek or a missed prefix seek) or seeks from the node a prefix seek left it at, giving keys below the bound | medium |
| go-immutable-radix/2 | `Insert` keeps the caller's key slice as the leaf key and node prefixes: overwriting it afterwards rewrites the tree | low |
| go-immutable-radix/3 | `WalkBackwards` visits a node's leaf before its children, so a key comes before the longer keys it is a prefix of (`ReverseIterator` gets it right) | medium |
| go-immutable-radix/4 | `DeletePrefix` on a node the transaction already wrote clears it before counting: `Len` keeps the deleted keys and watchers under the prefix are never notified | medium |

How they were found: /1 and /2 by probing the iterator and key contracts while reading the
code, before the properties ran (the property re-seeks only without the gate); /3 on the first
run of the model property with keys `""` and `"\x00"`; /4 on the first run of the immutability
and clone properties with `insert("")` then `deletePrefix("")` in one transaction, and again at
3000 cases through a merge (`delete("a\x00\x00")` merged the parent node into the sibling
`"a\xff\x00"`, which `deletePrefix("a\xff")` then landed on) — the gate turns a `DeletePrefix`
whose prefix shares its first byte with an earlier write of the same transaction (or is empty)
into an insert, so one-shot and first-write `DeletePrefix` stay checked. Not bugs, noted: the keys the
iterators and walks hand out are the tree's own slices (usual for Go iterators); `DeletePrefix`
of an empty prefix on an empty tree reports true (the root node matched). The properties run
clean at 3000 cases under the race detector.
