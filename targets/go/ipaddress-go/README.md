# go/ipaddress-go: the ipaddr package against Python's ipaddress and net/netip

[ipaddress-go](https://github.com/seancfoley/ipaddress-go) parses and manipulates IPv4 and IPv6
addresses, subnets, ranges and tries in many string forms (CIDR, wildcards, ranges, inet_aton,
masks, zones, mixed IPv6/IPv4, binary, hex, base 85, reverse DNS). This target checks its
parsing against Python's `ipaddress` module and Go's `net/netip`, and its own string forms,
subnets and tries against what they promise.

The tests live in `hegel/`, a package added by the patch; the oracle is `hegel/oracle.py`, a
child process speaking one JSON line each way (it needs python3, nothing else).

Properties (`HEGEL_COLLECT=1` counts mismatches instead of failing, `HEGEL_TEST_CASES=n` sets
the case count):

- `TestHegelParsesLikePython`: for plain and mutated address, interface and network strings,
  whatever Python accepts ipaddr accepts, and both agree on version, bytes, prefix length, zone,
  canonical and full strings, reverse DNS, loopback/link-local/multicast/unspecified, the prefix
  block's bounds, masks and count, IPv4-mapped and 6to4 embedding; `net/netip` agrees on bytes,
  zone and (mixed notation aside) the string. What ipaddr accepts and Python rejects is counted
  by class (inet_aton forms, whitespace, wildcards, masks) and anything else fails.
- `TestHegelArithmeticLikePython`: `Increment` matches Python's address arithmetic, overflow
  included, and `Compare` matches Python's ordering.
- `TestHegelStringsRoundTrip`: every string form the library writes for an address or subnet
  (canonical, normalized, compressed, full, wildcard, mixed, segmented binary, hex, binary,
  octal, base 85, reverse DNS, inet_aton) parses back to the same address, prefix and zone,
  and `NewIPAddressFromBytes` agrees with `Bytes`.
- `TestHegelIPv4SubnetsAreSets`: wildcard and range IPv4 subnets behave as the sets of
  addresses their segments describe: count, `Contains`, `Overlaps`, `Intersect`, `Subtract`,
  `SpanWithPrefixBlocks`, `SpanWithSequentialBlocks`, `CoverWithPrefixBlock`,
  `MergeToPrefixBlocks`, `ToSequentialRange` and its intersection, and `Iterator`.
- `TestHegelTrieMatchesBruteForce`: an IPv4 address trie answers `Contains`,
  `ElementContains`, `LongestPrefixMatch`, `Size`, `Iterator` and `Remove` as a scan of its keys.
- `TestHegelNeverPanics`: arbitrary strings go through parsing and the common operations
  without a panic, and `Validate` agrees with `IsValid`.

Three bugs, found 2026-09-20 at v1.8.4+, all in strings the library writes: the IPv4
`ToFullString` ("001.002.003.010") is read by the default parser as octal, so it parses to
another address or not at all (1, medium); `ToMixedString` of a CIDR prefix block whose prefix
cuts one of the last two segments gives a string ("1::0.10.0-240.0/116") the library's own
parser refuses, though its documentation says that cannot happen for a CIDR subnet (2, low);
and `ToMixedString` of a prefixed subnet that is not a prefix block writes wildcard last
segments as 0.0.0.0, turning 2^32 addresses into one (3, medium). Parsing agreed with Python
and netip on everything the two accept, and the subnet, range and trie operations were exact.

Known shapes are drawn by default (`hegel/known.go`): the classifier of the three bugs is
consulted only under `HEGEL_NO_KNOWN=1` (read once), and otherwise `TestHegelStringsRoundTrip`
fails on them with the mismatch naming the bug. The string form checked is part of the drawn
case, so the IPv4 full string (ipaddress-go/1, a quarter of IPv4 addresses) is one alternative
among the forms rather than a quarter of every case: the property shrinks to `"0.0.0.8"
through ToFullString` in about three default rounds of four (13 of 17) and is mapped to
ipaddress-go/1 as intermittent; the /2 and /3 shapes are a few hundredths of a percent of
cases once the form is drawn and were not reached by a default round. Under
`HEGEL_NO_KNOWN=1` the classifier skips the three shapes (1% of round-trip cases) and every
property passes while the three pins fail. One narrow property per bug lives in
`hegel/hegel_shapes_test.go`: `IPv4FullStringsParseBack` (1), `IPv6MixedStringsOfPrefixBlocksParseBack`
(2: prefix blocks with a prefix length of 97-111 or 113-127) and `IPv6MixedStringsKeepWildcardTails`
(3: prefixed subnets that are not prefix blocks with full-range last two segments; those the
library reads as a prefix block are a counted class); under `HEGEL_NO_KNOWN=1` each draws the
neighbouring region (IPv6 full strings, prefix lengths on segment boundaries, single-valued or
short-range tails) and passes. The generators are package-level values in combinator style:
addresses as records (octets or groups, a spelling record for IPv6 - compression, padding, case,
embedded tail, zone, prefix - rendered by a pure function), mutations as edits applied modulo the
live length, wide forms as per-segment records, round-trip, arithmetic, subnet and trie cases as
records whose sample points are resolved modulo the live sizes.

Counted, not failed, beyond the classes above (differences between ipaddr and Python's
ipaddress, seen at 3000 cases): a second `%` in a zone (ipaddr's `ValidateZoneStr` refuses
only `:` and `/`, so `::%eth0%zone` reads with the zone `eth0%zone`; Python rejects it); an
embedded IPv4 tail of fewer than four parts, an inet_aton form (`::ff9b:200.0`); and a zone
containing a colon (`::328%1:`), which Python reads and ipaddr and `net/netip` refuse.

Subnets that split into more than 4000 sequential blocks skip the span and merge checks
(the library builds one block per piece); nothing else is excluded.

## History

- 2026-09-20: new target, six properties, three bugs.
- 2026-10-07: generators rewritten in combinator style; known shapes drawn by default
  (`TestHegelStringsRoundTrip` mapped to ipaddress-go/1, intermittent); three narrow properties.
