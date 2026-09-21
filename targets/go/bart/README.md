# go/bart

[gaissmai/bart](https://github.com/gaissmai/bart) is a Go routing table (Balanced ART: a
popcount-compressed multibit trie after Knuth's ART) for IPv4 and IPv6 prefixes, with three
variants — `Table[V]`, the rank-cached `Fast[V]` and the payload-less `Lite` — longest-prefix
match, exact lookups, supernet/subnet enumeration, overlap tests, union, equality, clone,
copy-on-write `...Persist` operations for lock-free readers, `Lite.Aggregate`, and text/JSON
dumps. Pinned at `5c4dbe1` (eleven commits after v0.29.1, 2026-09-21, MIT; no AI policy in
CONTRIBUTING.md, README or `.github`).

## Build

The tests live in a new package directory `hegel/` of the upstream module and use the library
as a black box; `go.mod` gains `hegel.dev/go/hegel`. The run command is
`go test -count=1 -run TestHegel -v ./hegel`. No oracle outside Go is needed.

## Oracle

A routing table is a map from canonical (masked) prefix to value, and every query is answered
by brute force over the map with `net/netip`: the longest prefix containing an address, the
longest prefix covering a query prefix, all covering or covered prefixes, overlap through
`Prefix.Overlaps`, CIDR sort order by address then length (IPv4 before IPv6), the dump tree
by closest covering prefix, and aggregation to a fixpoint of removing covered prefixes and
merging sibling pairs. Prefixes are generated in clusters (a few /8 and /16 bases, the
documentation and link-local IPv6 ranges, the extremes 0.0.0.0 and 255.255.255.255) with
lengths biased to octet and bit boundaries, unmasked host bits included, so that they cover,
neighbour and overlap each other; queries are drawn from the table's prefixes, their subnets,
supernets and unmasked forms, and addresses from inside a prefix, at its ends and just past
them. `Table`, `Fast` and `Lite` are driven through one adapter interface by the same
sequences.

## Properties

- `TestHegelTable`: random sequences of Insert (unmasked prefixes canonicalized), Delete,
  Modify (callback called once with the current value and existence, insert/update/delete
  as returned), InsertPersist/DeletePersist/ModifyPersist (receiver unchanged, result as
  modelled, continuing from the result), Union/UnionPersist with a fresh table (argument
  unchanged), Clone independence, and invalid prefixes and addresses as no-ops or negative
  answers; after every step Size/Size4/Size6, All/All4/All6 as sets, AllSorted per family in
  CIDR order, DumpList4/6 trees, and Get, LookupPrefix, LookupPrefixLPM, Supernets (longest
  first), Subnets (sorted), OverlapsPrefix, Lookup, Contains and zone stripping on
  table-related queries.
- `TestHegelSetOps`: Overlaps/Overlaps4/Overlaps6 between two random tables (as modelled,
  symmetric), Equal (reflexive, with clones, false after a value change), Union as the merge
  with the argument's values winning, UnionPersist equal to Union, union with itself or an
  empty table the identity.
- `TestHegelDump`: MarshalJSON is the two DumpLists with the values intact; Fprint (and
  MarshalText) prints one header per non-empty family and every prefix once, in sorted order.
- `TestHegelAggregate`: `Lite.Aggregate` gives the modelled minimal covering set, keeps
  every address's membership, never grows the table, and is idempotent.
- `TestHegelPersistVersions`: a chain of Persist operations leaves every earlier version
  matching its own model (no write leaks through the shared nodes).
- `TestHegelConcurrentPersist`: readers of one version see stable answers while a writer
  creates new versions with Persist operations; both ends match their models (clean under
  `-race` in development).

## Bugs

None found: 500-case runs of every property showed no mismatch, and the edge probes
(invalid prefixes in Modify call no callback, `Fprint(nil)` errors, IPv4-mapped IPv6
addresses are plain IPv6 as documented, `Equal` on a non-comparable payload panics as
documented, `UnionPersist` with an empty argument returns the receiver) match the
documentation. The library ships its own extensive fuzz and golden tests.

## Modelled as recorded, not counted

- Mutating a `...Persist` result in place (Insert/Delete) while the original is still read
  corrupts the original and can panic a later read ("logic error: unknown child node type"),
  since untouched nodes are shared by design and documented as such; the properties never
  mutate a version in place once another version exists.
- `Lite.Fprint` prints prefixes without a value part.
