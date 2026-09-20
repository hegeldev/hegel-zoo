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

Gates (`hegel/known.go`) match the shapes of the three bugs so the properties stay green;
subnets that split into more than 4000 sequential blocks skip the span and merge checks
(the library builds one block per piece), and nothing else is excluded.
